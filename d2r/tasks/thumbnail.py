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
		#I need all the data here, not only the visible channels, for computation
		raster_data_raw = dataset.get_raster_data(selected_channels = dataset.get_channels(), output_width = self.config['output_width'], rescale_to_255=False, normalize_if_possible=True)
		
		#I just need the visible channels here, for output	
		raster_data_visible = dataset.get_raster_data(selected_channels = self.config['visible_channels'], output_width = self.config['output_width'], rescale_to_255=self.config['rescale_to_255'], normalize_if_possible=False)

		#computing the index over all image	
		if self.config['index_investigated'] is not None:
			index_function = getattr(d2r.tasks.matrix_returning_indexes, self.config['index_investigated'])
			myindex = index_function(raster_data_raw, dataset.get_channels())

		#we use the thresholding mechanism putting an extra treshold value 
		#at +infinity, so nothing will pass and we just output the full image, too
		self.config['index_thresholds'].append(np.inf)

		#for each required threshold
		for threshold_current in self.config['index_thresholds']:
			#building the output path
			(ortho, shapes) = dataset.get_files()
			(ortho, ext) = d2r.misc.get_file_corename_ext(ortho)
			
			#building the file name, which is slightly different if we 
			#are doing a regular threshold or an infinite threshold
			outfile = os.path.join(self.config['outfolder'], dataset.get_title() + '_' + ortho)
			if threshold_current != np.inf:
				outfile = outfile + '_index' + self.config['index_investigated'] + '_threshold' + str(threshold_current)
			outfile = outfile + '.png'
			
			#making sure the output folder do exists
			path = pathlib.Path(self.config['outfolder'])
			path.mkdir(parents=True, exist_ok=True)
			
			#check if we should do the task or not
			if os.path.isfile(outfile) and self.config['skip_if_already_done']:
				print('skipping, output file already exists: ' + outfile)
				continue
			
			#a copy of the output raster, to be modified
			output_raster = raster_data_visible.copy()
			
			#thresholding
			if self.config['index_investigated'] is not None:
				selector = myindex > threshold_current
				selector = np.ma.filled(selector, fill_value=False)
				output_raster[selector, :] = (255, 0, 255)
			
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
