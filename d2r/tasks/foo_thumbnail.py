import os
import pathlib
from osgeo import gdal
import numpy as np
from PIL import Image
import skimage.draw

from d2r.task import Task
import d2r.config
import d2r.dataset
import d2r.misc

class thumbnail(Task):
	def run(self, dataset):
		#the output path
		(ortho, shapes) = dataset.get_files()
		(ortho, ext) = d2r.misc.get_file_corename_ext(ortho)
		outfile = os.path.join(self.config['outfolder'], 'thumb_' + dataset.get_title() + '_' + ortho + '.png')
		path = pathlib.Path(self.config['outfolder'])
		path.mkdir(parents=True, exist_ok=True)		

		#check if we should do the task or not
		if os.path.isfile(outfile) and self.config['skip_if_already_done']:
			print('skipping. Output file already exists: ' + outfile)
			return(None)
		
		#if we get here, we should create the thumbnail
		raster_output = dataset.get_raster_data(selected_channels = self.config['visible_channels'], output_width = self.config['output_width'], rescale_to_255=self.config['rescale_to_255'], normalize_if_possible=False)
	
		#add polygons
		resized_ds = dataset.get_resized_ds(target_width = self.config['output_width'])
		d2r.misc.draw_ROI_perimeter(ROIs=dataset.shapes, target_img=resized_ds, raster_data=raster_output, verbose = self.config['verbose'])
		
		#save the thumbnail
		foo = Image.fromarray(raster_output.astype(np.uint8))
		foo.save(outfile)
		
		#and we are done
		return None

	def parse_config(self, config):
		"""parsing thumbnail-specific config parameters"""
		res = super().parse_config(config)
		for key in res:
			if key == 'output_width':
				res[key] = int(res[key])
			elif key == 'rescale_to_255':
				res[key] = d2r.misc.parse_boolean(res[key])
			elif key == 'visible_channels':
				res[key] = d2r.misc.parse_channels(res[key])
		return(res)
		
		
		
