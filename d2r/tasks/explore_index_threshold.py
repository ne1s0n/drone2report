import os
import pathlib
import numpy as np
from osgeo import gdal
from PIL import Image

import d2r.tasks.matrix_returning_indexes
from d2r.task import Task
import d2r.misc

class explore_index_threshold(Task):
	def run(self, dataset):

		#I need all the data here, not only the visible channels, for computation
		raster_data_raw = dataset.get_raster_data(selected_channels = dataset.get_channels(), output_width = self.config['output_width'], rescale_to_255=False, normalize_if_possible=True)
		
		#I just need the visible channels here, for output
		raster_data_visible = dataset.get_raster_data(selected_channels = self.config['visible_channels'], output_width = self.config['output_width'], rescale_to_255=True, normalize_if_possible=False)

		#computing the index over all image	
		index_function = getattr(d2r.tasks.matrix_returning_indexes, self.config['index'])
		myindex = index_function(raster_data_raw, dataset.get_channels())

		#for each required threshold
		for threshold_current in self.config['thresholds']:
			#the output path
			(ortho, shapes) = dataset.get_files()
			(ortho, ext) = d2r.misc.get_file_corename_ext(ortho)
			outfile = os.path.join(self.config['outfolder'], dataset.get_title() + '_' + ortho + '_index' + self.config['index'] + '_threshold' + str(threshold_current) + '.png')
			path = pathlib.Path(self.config['outfolder'])
			path.mkdir(parents=True, exist_ok=True)
			
			#check if we should do the task or not
			if os.path.isfile(outfile) and self.config['skip_if_already_done']:
				print('skipping, output file already exists: ' + outfile)
				return(None)
			
			#a copy of the output raster, to be modified
			output_raster = raster_data_visible.copy()
			
			#thresholding
			selector = myindex > threshold_current
			selector = np.ma.filled(selector, fill_value=False)
			output_raster[selector, :] = (255, 0, 0) 
			
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
			elif key == 'thresholds':
				res[key] = [float(x) for x in res[key].split(',')]
		
		return(res)
