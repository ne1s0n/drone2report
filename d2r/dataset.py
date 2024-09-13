#This module contains the information for one single dataset. When instantiated
#it does not really read the data, but it checks for the required files to be existing

import numpy as np
import warnings
from osgeo import gdal
from osgeo import osr
from skimage.draw import polygon
import geopandas as gpd
import configparser

import os.path
import d2r.config
import d2r.misc

def dataset_factory(title, body):
	if body.getboolean('skip'):
		#just skipping this dataset
		return []
	
	if body['type'] == 'tif_multichannel':
		#sanity
		if not os.path.exists(body['orthomosaic']):
			warnings.warn('Section ' + title + 'contains non-existing orthomosaic path ' + body['orthomosaic'])
			return []
		#either specify a data folder or a single file
		if os.path.isfile(body['orthomosaic']):
			#single file specified. Let's just explicitly inform the class constructor
			return [Dataset(title, body, body['orthomosaic'])]
		if os.path.isdir(body['orthomosaic']):
			#for all the tif in the folder let's instantiate a different Dataset object
			files = d2r.misc.find_case_insensitve(body['orthomosaic'], ['.tif', '.tiff'])
			res = []
			for f in files:
				#instantiating a single dataset object for each single file
				res.append(Dataset(title, body, f))
			return(res)
	
	#if we get here something went wrong
	raise ValueError('Unknown type "' + body['type'] + '" found when parsing DATA section ' + title)

class Dataset:
	def __init__(self, title, body, infile):
		self.title = title
		self.orthomosaic_file = infile
		
		#parsing series, progressive number (if present)
		pieces = title.split(' ')
		self.series = pieces[0]
		if len(pieces) > 1:
			self.prog = pieces[1]
		else:
			self.prog = None
		
		#parsing meta, config
		self.type = None
		self.channels = None
		self.skip = None
		self.meta = {}
		self.config = {}
		for key in body:
			if key.lower().startswith('meta_'):
				self.meta[key[5:]] = body[key]
			elif key.lower() == 'type':
				self.type = body[key]
			elif key.lower() == 'skip':
				self.skip = body.getboolean(key)
			elif key.lower() == 'channels':
				self.channels = d2r.config.parse_channels(body[key])
			elif key.lower() == 'type':
				self.type = body[key]
			elif key.lower() == 'verbose':
				self.verbose = body.getboolean(key)
			else:
				self.config[key] = body[key]
		
		#if we reach the end of the parsing and no type was specified, we have a problem
		if self.type is None:
			raise ValueError('Missing "type" field for dataset: ' + title)
		if self.skip is None:
			raise ValueError('Missing "skip" field for dataset: ' + title)
		if self.channels is None:
			raise ValueError('Missing "channels" field for dataset: ' + title)
			
		#we are ready to initialize the data
		self.__load()
			
	def to_string(self):
		(ortho, shapes) = self.get_files()
		(core, ext) = d2r.misc.get_file_corename_ext(ortho)
		return(self.title + ' (' + self.type + ', ' + core + ')') 
	def get_meta(self):
		return(self.meta)
	def get_config(self):
		return(self.config)
	def get_channels(self):
		return self.channels
	def get_title(self):
		return self.title
	def get_type(self):
		return self.type
	def get_raster_size(self):
		return (self.ds.RasterXSize, self.ds.RasterYSize)
	
	def __load(self):
		"""initializes the dataset structures"""
		print('\n---------------------------')
		print('opening image file ' + self.orthomosaic_file)
		self.ds = gdal.Open(self.orthomosaic_file, gdal.GA_ReadOnly)
		print("Projection: ", self.ds.GetProjection())  # get projection
		print("Columns:", self.ds.RasterXSize)  # number of columns
		print("Rows:", self.ds.RasterYSize)  # number of rows
		print("Band count:", self.ds.RasterCount)  # number of bands
		
		#reading the nodata values
		self.nodata = []
		for i in range(self.ds.RasterCount):  # GDAL bands are 1-indexed
			band = self.ds.GetRasterBand(i+1)
			self.nodata.append(band.GetNoDataValue())
    		
		#opening shapes file
		print('opening shape file ' + self.config['shapes_file'])
		self.shapes = gpd.read_file(self.config['shapes_file'])
		
		# let's play it safe and convert the orthomosaic projection to an osr SpatialReference object
		spatial_ref = osr.SpatialReference()
		spatial_ref.ImportFromWkt(self.ds.GetProjection())

		# Convert to a proj4 string or EPSG code that geopandas can use
		proj4_string = spatial_ref.ExportToProj4()

		# Reproject the shapefile to match the orthomosaic's CRS
		self.shapes = self.shapes.to_crs(proj4_string)
		
	def get_files(self):
		"""returns orthomosaic and shapes file names"""
		ortho = self.orthomosaic_file
		shapes = self.config['shapes_file']
		return(ortho, shapes)

	#def get_geom_meta(self, polygon_id):

	def get_geom_raster(self, polygon_id=None, polygon_field=None, polygon_order=None):
		"""
		Returns the raster data for the specified polygon
		
		Loads in memory and returns the raster data inside the specified polygon as a
		clipped numpy ndarray in the (rows, columns, channel) order. The polygon can
		be selected either:
		- using 'polygon_field' and 'polygon id', if a .dbf file was present
		- using a number representing the reading order from the shape file via the 'polygon_order' parameter
		
		Note that the two above options are incompatible, if both or none are specified an
		error is raised. 
		"""
		#interface 
		if not ((polygon_id is None) ^ (polygon_order is None)):
			raise ValueError('One and only one way to select the polygon should be specified, either via a field or via a numeral')

		#let's find the polygon requested
		geom = None
		if (polygon_id is not None):
			shape = self.shapes.loc[self.shapes[polygon_field] == polygon_id]
			#sanity check: did we select just one row?
			if len(shape.index) != 1:
				raise ValueError('The choice of polygon_field + polygon_id selects either zero or too many polygons: ' + str(polygon_field) + ' = ' + str(polygon_id))
			geom = shape.iloc[0,:].geometry
		if (polygon_order is not None):
			shape = self.shapes.iloc[polygon_order, :]
			geom = shape.geometry

		#check if the polygon is inside the raster data
		if not self.is_bounding_box_inside(geom):
			if self.verbose:
				msg = 'Requested data for a geometry outside the image limits. Returning None\n' + shape.to_string()
				warnings.warn(msg)
			return None
		
		#extract the bounding box for the geometry from the raster dataset
		#data is in channel-last at this point format
		raster_box = self.get_bounding_box_raster(geom)
		
		#mask the raster box with the current geometry
		mask = self.get_geom_clipmask(geom)
		
		#applying the mask
		raster_box = np.ma.masked_array(raster_box, mask)
		
		#and we are done
		return(raster_box)

	def get_bounding_box_size_and_offset(self, geom):
		""""from a georeferenced geometry to pixel coordinates (size and offset)"""
		#the bounding box for the selected geometry, in georeferenced coordinates
		x_min, y_min, x_max, y_max = geom.bounds

		# geo -> pix
		col1, row1 = transform_coords(self.ds, point=(x_min, y_min), source='geo')
		col2, row2 = transform_coords(self.ds, point=(x_max, y_max), source='geo')
		
		#define the region of interest in the required form
		x_size = int(abs(col1 - col2))    # Width of the subset in pixels
		y_size = int(abs(row1 - row2))    # Height of the subset in pixels
		x_offset = int(np.min([col1, col2]))
		y_offset = int(np.min([row1, row2]))
		
		return(x_size, y_size, x_offset, y_offset)
		
	def get_bounding_box_raster(self, geom):
		"""get the raster data for the bounding box of the passed geometry"""
		#getting pixel-wise size and offset of the passed geometry 
		x_size, y_size, x_offset, y_offset = self.get_bounding_box_size_and_offset(geom)
		
		# Read the specified subset as an array
		subset_array = self.ds.ReadAsArray(x_offset, y_offset, x_size, y_size)
		
		#we expect this to be in the shape: channel, columns, rows. But
		#if it's a single channel raster is just columns, rows. Let's cover
		#this case
		if self.ds.RasterCount == 1:
			#double check: are we in the correct case?
			if subset_array.shape != (y_size, x_size):
				raise ValueError('Unexpected shape, found', subset_array.shape, 'expected', (y_size, x_size))
			#let's now add an axis, with a single slot
			subset_array = np.expand_dims(subset_array, axis=0)
		
		#we check that we are in the expected case of channel-first
		#then move to channel-last format
		if subset_array.shape[0] != self.ds.RasterCount:
			raise ValueError('Data is not channel-first format')
		subset_array = np.moveaxis(subset_array, 0, -1)

		return(subset_array)

	def get_geom_clipmask(self, geom):
		"""get a raster clipmask for the passed geometry"""
		#getting pixel-wise size and offset of the passed geometry 
		x_size, y_size, x_offset, y_offset = self.get_bounding_box_size_and_offset(geom)
		
		#let's build a mask where to rasterize the geometry
		mask = np.ones((y_size, x_size, self.ds.RasterCount))

		#converting the polygon coordinates to pixel coordinates
		coords = list(geom.exterior.coords)
		coords2 = np.zeros((len(coords), 2))

		for i in range(len(coords)):
			#from geo to pixel (absolute)
			mycol, myrow = transform_coords(self.ds, point=(coords[i][0], coords[i][1]), source='geo')
			#from pixel (absolute) to image (relative)
			mycol = mycol - x_offset                      
			myrow = myrow - y_offset
			#storing the results
			coords2[i,0] = mycol
			coords2[i,1] = myrow
			
		#drawing the polygon
		rr, cc = polygon(coords2[:,1], coords2[:,0], mask.shape)
		mask[rr, cc, :] = 0
		
		#masking the original raster
		return(mask)

	def is_bounding_box_inside(self, geom):
		"""returns True if all points of the geometry are pixel-wise inside the image, False otherwise"""
		#getting pixel-wise limits of the passed geometry
		x_size, y_size, x_offset, y_offset = self.get_bounding_box_size_and_offset(geom)
		
		#checking if all values are inside the raster size
		return (x_offset >= 0) and (y_offset >= 0) and (x_offset + x_size < self.ds.RasterXSize) and (y_offset + y_size < self.ds.RasterYSize)
		
def transform_coords(ds, point, source):
	"""
	Transforms the coordinates of a point between georeferenced and pixel
	
	Using the geotransformation present in the 'ds' a gdal dataset, transforms
	the coordinates contained in 'point'. The applied transformatio will be 
	from georeferenced to pixel if 'source' is equal to 'geo', or from pixel
	to georeferenced if 'source' is equal to 'pix'. For any other value an
	error will be raised.
	If the parameter 'pixel_relative' is False (the default) the origin 
	"""
	forward_transform = ds.GetGeoTransform()
	reverse_transform = gdal.InvGeoTransform(forward_transform)
	
	if source == 'geo':
		return gdal.ApplyGeoTransform(reverse_transform, point[0], point[1])
	if source == 'pix':
		return gdal.ApplyGeoTransform(forward_transform, point[0], point[1])
	raise ValueError('source needs to be either geo or pix, instead was:', str(source))
