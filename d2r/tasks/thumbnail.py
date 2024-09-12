import os
import pathlib
from osgeo import gdal
import numpy as np
from PIL import Image
from skimage.draw import polygon

from d2r.task import Task
import d2r.config
import d2r.dataset
import d2r.misc

class thumbnail(Task):
	def run(self, dataset):
		#the output path
		(ortho, shapes) = dataset.get_files()
		ortho = d2r.misc.get_file_corename(ortho)
		outfile = os.path.join(self.config['outfolder'], 'thumb_' + dataset.title + '_' + ortho + '.png')
		path = pathlib.Path(self.config['outfolder'])
		path.mkdir(parents=True, exist_ok=True)		

		#check if we should do the task or not
		if os.path.isfile(outfile) and self.config.getboolean('skip_if_already_done'):
			print('skipping. Output file already exists: ' + outfile)
			return(None)
		
		#if we get here, we should create the thumbnail. Compute the output sizes:
		orig_width, orig_height = dataset.get_raster_size()
		width = int(self.config['output_width'])
		height = int(width * (orig_height / orig_width))
		
		#resize
		#resized_ds = gdal.Warp('', dataset.ds, format='VRT', width=width, height=height, resampleAlg=gdal.GRA_NearestNeighbour)
		resized_ds = gdal.Translate('', dataset.ds, format='VRT', width=width, height=height, resampleAlg=gdal.GRA_NearestNeighbour)
		raster_output = resized_ds.ReadAsArray()
		
		#if only one channel: let's replicate it so that it can go through the same cycles as the multichannel case
		if len(dataset.channels) == 1:
			newraster = np.zeros((3, raster_output.shape[0], raster_output.shape[1]))
			newraster[0, :, :] = raster_output
			newraster[1, :, :] = raster_output
			newraster[2, :, :] = raster_output
			raster_output = newraster

		#move from channel-first to channel-last
		raster_output = np.moveaxis(raster_output, 0, -1)
		
		#if more than three channels: focus on the channels specified in the config 
		if len(dataset.channels) > 3:
			#parsing the list of requested channels
			print ('Too many channels, subsetting to the three selected in config file: ' + self.config['channels'])
			channels = d2r.config.parse_channels(self.config['channels'])
			if len(channels) != 3:
				raise ValueError('Too many channels in the config file: '+ self.config['channels'])
			channels = [dataset.channels.index(x) for x in channels]
			raster_output = raster_output[:, :, channels]
		
		#fix the nodata values
		raster_output = np.ma.masked_equal(raster_output, int(dataset.config['nodata']))
		
		#should we rescale to 0-255 ?
		if self.config.getboolean('rescale'):
			mymin = np.min(raster_output)
			mymax = np.max(raster_output)
			raster_output = 255 * (raster_output - mymin) / (mymax - mymin)

		#add polygons
		for i in range(len(dataset.shapes.index)):
			sh = dataset.shapes.iloc[i,:].geometry
			#converting the polygon coordinates to pixel coordinates
			coords = list(sh.exterior.coords)
			coords2 = np.zeros((len(coords), 2))
			for i in range(len(coords)):
				(coords2[i,0], coords2[i,1]) = d2r.dataset.transform_coords(resized_ds, point=(coords[i][0], coords[i][1]), source='geo')
			
			#drawing the polygon in white
			rr, cc = polygon(coords2[:,1], coords2[:,0], raster_output.shape)
			raster_output[rr, cc, :] = 255
		
		#save the thumbnail
		foo = Image.fromarray(raster_output.astype(np.uint8))
		foo.save(outfile)
		
		return None
