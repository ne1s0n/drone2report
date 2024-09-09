import os
import pathlib
from osgeo import gdal
import numpy as np
from PIL import Image
import d2r.config

class Analysis:
	def __init__(self, title, config):
		self.title = title
		self.config = config
		
		#the title becomes also the actual function we are going to call, so it's better 
		#to check if it exists
		if not callable(getattr(self, title, None)):
			raise ValueError('Requested unknown analysis: ' + title)
		
	def to_string(self):
		return(self.title)
	def run(self, dataset):
		return(getattr(self, self.title)(dataset))

	def thumbnail(self, dataset):
		#check if we should do the analysis or not
		outfile = os.path.join(self.config['outfolder'], 'thumb_' + dataset.title + '.png')
		path = pathlib.Path(self.config['outfolder'])
		path.mkdir(parents=True, exist_ok=True)
		
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
		
		#if more than one channel: move from channel-first to channel-last
		if len(dataset.channels) > 1:
			raster_output = np.moveaxis(raster_output, 0, -1)
		
		#if more than three channels: focus on the specified channels
		if len(dataset.channels) > 3:
			#parsing the list of requested channels
			print ('Too many channels, subsetting to the three selected in config file')
			channels = d2r.config.parse_channels(self.config['channels'])
			if len(channels) != 3:
				raise ValueError('Too many channels in the config file: '+ self.config['channels'])
			channels = [dataset.channels.index(x) for x in channels]
			raster_output = raster_output[:, :, channels]
		
		#fix the nodata issue
		raster_output = np.ma.masked_equal(raster_output, int(dataset.config['nodata']))
		
		#if more than three channels, take the first three
		print('current shape', raster_output.shape)
		
		#should we rescale to 0-255 ?
		if self.config.getboolean('rescale'):
			mymin = np.min(raster_output)
			mymax = np.max(raster_output)
			raster_output = 255 * (raster_output - mymin) / (mymax - mymin)

		#add polygons
		#TODO
		
		#save the thumbnail
		foo = Image.fromarray(raster_output.astype(np.uint8))
		foo.save(outfile)
		
		return None
		
	def indexes(self, dataset):
		#TODO
		return None
