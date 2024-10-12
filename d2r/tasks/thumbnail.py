import os
import pathlib
import numpy as np
from osgeo import gdal
from PIL import Image

import d2r.tasks.matrix_returning_indexes
from d2r.task import Task
import d2r.misc

class thumbnail(Task):
	def run(self, dataset):
		#are all the required channels (from this task config) available
		#in the current image?
		if not set(self.config['visible_channels']).issubset(dataset.get_channels()):
			print('Skipping: required to create a thumbnail with channels ' + str(self.config['visible_channels']) + ' but the image has ' + str(dataset.get_channels()))
			return(None)

		#computing the index/channel over all image
		myindex = self._compute_index(self.config['index_investigated'], dataset)	
		mysubindex = self._compute_index(self.config['subindex_investigated'], dataset)	
		
		#if we have an index, for each required threshold
		if myindex is not None:
			for index_threshold in self.config['index_thresholds']:
				if mysubindex is None:
					#no subindex, just an index
					self._make_thumbnail(dataset=dataset, index=myindex, index_threshold=index_threshold)
				else:
					#for every requested subindex threshold				
					for subindex_threshold in self.config['subindex_thresholds']:
						self._make_thumbnail(dataset=dataset, index=myindex, index_threshold=index_threshold, subindex=mysubindex, subindex_threshold=subindex_threshold)
		
		#extra: no threshold, just the image
		self._make_thumbnail(dataset=dataset)
	
	def _compute_index(self, target, dataset):
		"""compute the target index on the passed dataset, returns a matrix"""
		#we support an empty target
		if target is None:
			return None

		#if we get here we need to work
		res = None	
		
		#I need all the data here, not only the visible channels, for computation
		raster_data_raw = dataset.get_raster_data(
			selected_channels = dataset.get_channels(), 
			output_width = self.config['output_width'], 
			rescale_to_255=False, normalize_if_possible=True)
		
		#is it an actual index?
		if hasattr(d2r.tasks.matrix_returning_indexes, target):
			index_function = getattr(d2r.tasks.matrix_returning_indexes, target)
			res = index_function(raster_data_raw, dataset.get_channels())
		
		#is is a simple channel?
		if target in dataset.get_channels():
			i = dataset.get_channels().index(target)
			res = raster_data_raw[:,:,i]
		
		#have we failed?
		if res is None:
			raise ValueError('In .ini file, requested unknown index or channels (case sensitive): ' + target)
		
		#done
		return(res)

	def _make_thumbnail(self, dataset, index=None, index_threshold=None, subindex=None, subindex_threshold=None):
		#building the file name, which is slightly different if we 
		#are doing no threshold, index, or subindex
		outfile = os.path.join(self.config['outfolder'], dataset.get_title())
		outfile = outfile + '_' + ''.join(self.config['visible_channels'])
		if index is not None:
			outfile = outfile + '_index' + self.config['index_investigated'] + '_threshold' + str(index_threshold)
		if subindex is not None:
			outfile = outfile + '_subindex' + self.config['subindex_investigated'] + '_threshold' + str(subindex_threshold)
		outfile = outfile + '.png'
		
		#making sure the output folder do exists
		path = pathlib.Path(self.config['outfolder'])
		path.mkdir(parents=True, exist_ok=True)
		
		#check if we should do the task or not
		if os.path.isfile(outfile) and self.config['skip_if_already_done']:
			print('skipping, output file already exists: ' + outfile)
			return(None)

		#I just need the visible channels here, for output	
		output_raster = dataset.get_raster_data(
			selected_channels = self.config['visible_channels'], 
			output_width = self.config['output_width'], 
			rescale_to_255=self.config['rescale_to_255'], normalize_if_possible=False)

		#thresholding index
		if index is not None:
			selector = index > index_threshold
			selector = np.ma.filled(selector, fill_value=False)
			output_raster[selector, :] = (0, 255, 255)
		
		#thresholding subindex
		if subindex is not None:
			selector = selector & (subindex > subindex_threshold)
			output_raster[selector, :] = (0, 0, 255)
		
		#should we draw the ROI perimeters, too? 
		if self.config['draw_rois']:
			resized_ds = dataset.get_resized_ds(target_width = self.config['output_width'])
			d2r.misc.draw_ROI_perimeter(ROIs=dataset.shapes, target_img=resized_ds, raster_data=output_raster, verbose = self.config['verbose'])
		
		#save the image
		foo = Image.fromarray(output_raster.astype(np.uint8))
		foo.save(outfile)

	def parse_config(self, config):
		"""parsing config parameters specific to this subclass"""
		res = super().parse_config(config)
		
		for key in res:
			if key == 'output_width':
				res[key] = int(res[key])
			elif key == 'visible_channels':
				res[key] = d2r.misc.parse_channels(res[key])
			elif key in ['index_thresholds', 'subindex_thresholds']:
				res[key] = [float(x) for x in res[key].split(',')]
			elif key in ['rescale_to_255', 'draw_ROIs']:
				res[key] = d2r.misc.parse_boolean(res[key])
		
		#sanity
		if 'index_investigated' in res and 'index_thresholds' not in res:
			raise ValueError('File .ini specifies an index without specifying its thresholds')
		if 'subindex_investigated' in res and 'subindex_thresholds' not in res:
			raise ValueError('File .ini specifies a subindex without specifying its thresholds')
		if 'subindex_investigated' in res and 'index_investigated' not in res:
			raise ValueError('File .ini specifies a subindex without specifying an index')

		#default parameters
		if 'index_investigated' not in res:
			res['index_investigated'] = None
		if 'index_thresholds' not in res:
			res['index_thresholds'] = []
		if 'subindex_investigated' not in res:
			res['subindex_investigated'] = None
		
		return(res)
