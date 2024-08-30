#This module contains the information for one single dataset. When instantiated
#it does not really read the data, but it checks for the required files to be existing

from osgeo import gdal
import numpy as np


class Dataset:
	def __init__(self, title, body):
		self.name = title
		
		#parsing series, progressive number (if present)
		pieces = title.split(' ')
		self.series = pieces[0]
		if len(pieces) > 1:
			self.prog = pieces[1]
		else:
			self.prog = None
		
		#parsing meta, config
		self.type = None
		self.meta = {}
		self.config = {}
		for key in body:
			if key.lower().startswith('meta_'):
				self.meta[key[5:]] = body[key]
			elif key.lower() == 'type':
				self.type = body[key]
			else:
				self.config[key] = body[key]
		
		#if we reach the end of the parsing and no type was specified, we have a problem
		if self.type is None:
			raise ValueError('Missing "type" field for dataset: ' + title)
		
	def to_string(self):
		return(self.name + ' (' + self.type + ')') 
	def get_meta(self):
		return(self.meta)
	def get_config(self):
		return(self.config)
		
	def get_image(self):
		ds = gdal.Open(self.orthomosaic_file, gdal.GA_ReadOnly)

		print("Projection: ", ds.GetProjection())  # get projection
		print("Columns:", ds.RasterXSize)  # number of columns
		print("Rows:", ds.RasterYSize)  # number of rows
		print("Band count:", ds.RasterCount)  # number of bands

		#putting all the data in a numpy array
		output=np.zeros(shape=(ds.RasterYSize, ds.RasterXSize, ds.RasterCount))
		for i in range(ds.RasterCount):
			output[:, :, i] = ds.GetRasterBand(i+1).ReadAsArray()
		
		return(output, ds.GetProjection())

	def get_channels(self):
		return 'RGB'
	def get_polygons(self):
		### load and return ROIs as geometric polygons 
		return None

	
