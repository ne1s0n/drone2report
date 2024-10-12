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

		#I need all the data here, not only the visible channels, for computation
		raster_data_raw = dataset.get_raster_data(
			selected_channels = dataset.get_channels(), 
			output_width = self.config['output_width'], 
			rescale_to_255=False, normalize_if_possible=True)
		
		#I just need the visible channels here, for output	
		raster_data_visible = dataset.get_raster_data(
			selected_channels = self.config['visible_channels'], 
			output_width = self.config['output_width'], 
			rescale_to_255=self.config['rescale_to_255'], normalize_if_possible=False)

		#computing the index over all image
		myindex = None	
		if self.config['index_investigated'] is not None:
			index_function = getattr(d2r.tasks.matrix_returning_indexes, self.config['index_investigated'])
			myindex = index_function(raster_data_raw, dataset.get_channels())

		#for each required threshold
		for threshold_current in self.config['index_thresholds']:
			self._make_thumbnail(dataset=dataset, raster_data_visible=raster_data_visible, threshold_current = threshold_current, index_current = myindex)
		
		#extra: no threshold, just the image
		self._make_thumbnail(dataset=dataset, raster_data_visible=raster_data_visible, threshold_current = None, index_current = None)
	
	def _make_thumbnail(self, dataset=None, raster_data_visible=None, threshold_current = None, index_current = None):
		#building the file name, which is slightly different if we 
		#are doing a regular threshold or an infinite threshold
		outfile = os.path.join(self.config['outfolder'], dataset.get_title())
		if threshold_current is not None:
			outfile = outfile + '_index' + self.config['index_investigated'] + '_threshold' + str(threshold_current)
		outfile = outfile + '.png'
		
		#making sure the output folder do exists
		path = pathlib.Path(self.config['outfolder'])
		path.mkdir(parents=True, exist_ok=True)
		
		#check if we should do the task or not
		if os.path.isfile(outfile) and self.config['skip_if_already_done']:
			print('skipping, output file already exists: ' + outfile)
			return(None)

		#a copy of the output raster, to be modified
		output_raster = raster_data_visible.copy()
		
		#thresholding
		if index_current is not None:
			selector = index_current > threshold_current
			selector = np.ma.filled(selector, fill_value=False)
			output_raster[selector, :] = (0, 255, 255)
		
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
			elif key == 'index_thresholds':
				res[key] = [float(x) for x in res[key].split(',')]
			elif key in ['rescale_to_255', 'draw_ROIs']:
				res[key] = d2r.misc.parse_boolean(res[key])
		
		
		#default parameters
		if 'index_investigated' not in res:
			res['index_investigated'] = None
		if 'index_thresholds' not in res:
			res['index_thresholds'] = []
		
		return(res)
