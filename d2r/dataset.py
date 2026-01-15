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

def dataset_factory(title, config):
	if not config.getboolean('active'):
		#just skipping this dataset
		return []
	
	if config['type'] == 'tif_multichannel':
		return [Dataset(title, config)]
	
	#if we get here something went wrong
	raise ValueError('Unknown type "' + config['type'] + '" found when parsing DATA section ' + title)

class Dataset:
	def __init__(self, title, config):
		self.title = title
		
		#parsing series, progressive number (if present)
		pieces = title.split(' ')
		self.series = pieces[0]
		if len(pieces) > 1:
			self.prog = pieces[1]
		else:
			self.prog = None
		
		#parsing meta, config
		(self.config, self.meta) = self.parse_config(config)
			
		#we are ready to initialize the data
		self.__load()

	def parse_config(self, config):
		"""the basic parsing of the config object, returns two dict (config and meta), all keys to lower case"""
		#let's start with the basic parsing
		config = d2r.misc.parse_config(config)
		
		#at this point the config is a dict and we can proceed with the
		#dataset-specific parsing. Here are the resulting output
		res = {}
		meta = {}
		
		#orthomosaic files and channels require a special treatment
		orthofiles = {}
		channels = {}
		
		#and here we set a default
		res['max_value'] = None
		
		#for each available parameter
		for key in config:
			if key.startswith('meta_'):
				meta[key[5:]] = config[key]
			elif key.startswith('orthomosaic'):
				orthofiles[key] = config[key]
			elif key.startswith('channels'):
				channels[key] = config[key]
			elif key in ['max_value', 'nodata']:
				res[key] = float(config[key])
			elif key == 'visible_channels':
				res[key] = d2r.misc.parse_channels(config[key])
			elif key == 'shapes_index':
				res[key] = ''.join(config[key].split()).split(',')
			else:
				#everything else is just copied
				res[key] = config[key]
				
		#some fields are required, let's check on them
		if 'type' not in res:
			raise ValueError('Missing "type" field for dataset: ' + self.title)
		if 'visible_channels' not in res:
			raise ValueError('Missing "visible_channels" field for dataset: ' + self.title)

		#at this point we should have collected orthofiles and channel specs
		self.datasources = self.parse_datasources(orthofiles, channels)
		if len(self.datasources) == 0:
			raise ValueError('You need to specify at least a pair of "orthomosaic" and "channels" fields')

		#if we have duplicate channel names we have a problem
		all_input_channels = []
		for key in self.datasources:
			all_input_channels = all_input_channels + self.datasources[key][1]
		if len(all_input_channels) != len(set(all_input_channels)):
			raise ValueError('Duplicate channel names: ' + str(all_input_channels))

		#visible channels should be valid channels, listed in the channels field
		for ch in res['visible_channels']:
			if ch not in all_input_channels:
				raise ValueError('Channel listed as visibile channels, but not in the proper channel list: ' + ch)

		return(res, meta)

	def parse_datasources(self, orthofiles, channels):
		res = {}
		
		#let's parse the orthofiles first
		for key in orthofiles:
			pieces = key.split('_', 1)
			#making sure that there's an empty string as qualifier for the single-file case
			if len(pieces) == 1:
				pieces.append('')
			
			#storing
			res[pieces[1]] = [orthofiles[key], None]
		
		#let's parse the channels
		for key in channels:
			pieces = key.split('_', 1)
			#making sure that there's an empty string as qualifier for the single-file case
			if len(pieces) == 1:
				pieces.append('')
			
			#check for channels without a file
			if pieces[1] not in res:
				raise ValueError('Orphaned channels field, no orthofile specified: ' + key)
		
			#storing
			res[pieces[1]][1] = d2r.misc.parse_channels(channels[key])

		#checking that all orthofiles have a corresponding channel list
		for key in res:
			if res[key][1] is None:
				raise ValueError('Orphaned orthofile, no channels specified: ' + key)
		
		#if we get here we are good to go
		return(res)

	def to_string(self):
		return(self.title + ' (' + self.config['type'] + ')') 
	def get_meta(self):
		return(self.meta)
	def get_config(self):
		return(self.config)
	def get_channels(self):
		return self.channels
	def get_visible_channels(self):
		return self.config['visible_channels']
	def get_title(self):
		return self.title
	def get_type(self):
		return self.config['type']
	def get_raster_size(self):
		return (self.ds.RasterXSize, self.ds.RasterYSize)
	def get_nodata_value(self):
		return self.nodata
	def get_resized_ds(self, target_width = None, target_height = None):
		#taking notes for simplicity of notation
		width, height = self.get_raster_size()

		#target values: if only one dimension specified we keep the proportions
		if target_width is not None and target_height is None:
			height = int(target_width * (height / width))
			width = target_width
		if target_height is not None and target_width is None:
			height = target_height
			width = int(target_height * (width / height))
		if target_height is not None and target_width is not None:
			width = target_width
			height = target_height
		
		#resize
		resized_ds = gdal.Translate('', self.ds, format='VRT', width=width, height=height, resampleAlg=gdal.GRA_NearestNeighbour)

		#done
		return(resized_ds)

	
	def get_raster_data(self, selected_channels, output_width = None, output_height = None, rescale_to_255=True, normalize_if_possible=False):
		"""
		Returns raster data as a masked np ndarray
		
		selected_channels: array of names of channels to be returned
		output_width, output_height : if passed one of the values, the image will be resized to have 
		                              the value (the other dimension is computed to maintain proportions). If
		                              both values are passed it is possible to change the image proportions
		rescale_to_255 : if True the values will be rescaled to the 0-255 range
		normalize_if_possible : if True, and if "max_value" has been defined in config, all data will be divided by max_value, so to stay in the 0-1 ramge 
		"""
		#a resized gdal dataset
		resized_ds = self.get_resized_ds(target_width = output_width, target_height = output_height)

		#prepare room for output
		raster_output = np.zeros((len(selected_channels), resized_ds.RasterYSize, resized_ds.RasterXSize))
		
		#getting the channels actual indexes
		channels = [self.get_channels().index(x) for x in selected_channels]
		
		#copying each require channel
		for i in range(len(channels)):
			#putting the the channel number i the band number i+1
			raster_output[i, :, :] = resized_ds.GetRasterBand(channels[i] + 1).ReadAsArray()

			#TODO for single channel images we may be in need to do something like this: 
			#raster_output[i, :, :] = resized_ds.ReadAsArray()

		#move from channel-first to channel-last
		raster_output = np.moveaxis(raster_output, 0, -1)

		#fix the nodata value, if present
		if self.get_nodata_value() is not None:
			raster_output = np.ma.masked_equal(raster_output, self.get_nodata_value())
		
		#getting rid of invalid values
		raster_output = np.ma.masked_invalid(raster_output)

		#should we normalize?
		if normalize_if_possible and self.config['max_value'] is not None:
			raster_output = raster_output / self.config['max_value']

		#should we rescale to 0-255 ?
		if rescale_to_255:
			mymin = np.min(raster_output)
			mymax = np.max(raster_output)
			raster_output = 255 * (raster_output - mymin) / (mymax - mymin)

		#and we are done
		return(raster_output)
	
	def __load(self):
		"""initializes the dataset structures for the corresponding datasource entry"""
		self.ds = {}
		
		print('\n---------------------------')
		print('DATASET ' + self.title)
		for key in self.datasources:
			self.__load_one_dataset(key)

		#if more than one image are loaded we join them
		self.__join_datasets()
		
		#should we print some info about the resulting joined dataset?
		if 	self.joined_sources:
			d2r.misc.print_gdal_info(self.ds, 'merged image', self.channels) 
			print('\n')
		
		#listing visible channels
		print(' Visible bands (rendered as RGB): ' + str(self.config['visible_channels']) + '\n')
			
		#opening shapes file
		print('opening shape file ' + self.config['shapes_file'])
		self.shapes = gpd.read_file(self.config['shapes_file'])
		print('- found ' + str(len(self.shapes.index)) + ' ROIs with fields ' + str(list(self.shapes)))
		print('- fields used to uniquely identify a shape: ' + str(self.config['shapes_index']))

		#at this point self.ds is a single gdal dataset (it's not a dict
		#anymore). Let's play it safe and convert the shapefile orthomosaic 
		#projection to an osr SpatialReference object
		spatial_ref = osr.SpatialReference()
		spatial_ref.ImportFromWkt(self.ds.GetProjection())

		#convert to a proj4 string or EPSG code that geopandas can use
		proj4_string = spatial_ref.ExportToProj4()

		#reproject the shapefile to match the orthomosaic's CRS
		self.shapes = self.shapes.to_crs(proj4_string)
		
	def __load_one_dataset(self, dataset_key):
		"""initializes the dataset structures for the corresponding datasource entry"""
		infile = self.datasources[dataset_key][0]
		channels = self.datasources[dataset_key][1]
		print('Opening image file ' + infile)
		self.ds[dataset_key] = gdal.Open(infile, gdal.GA_ReadOnly)
		#local copy for leaner code
		ds =  self.ds[dataset_key]
		d2r.misc.print_gdal_info(ds, dataset_key, channels)
		
		#check on band names
		if len(channels) != ds.RasterCount:
			raise ValueError('Image has ' + str(ds.RasterCount) + ' bands but config specifies ' + 
				str(len(channels)) + ' of them')
		
		#reading the nodata values
		nodata = []
		for i in range(ds.RasterCount):  
			band = ds.GetRasterBand(i+1) # GDAL bands are 1-indexed
			nodata.append(band.GetNoDataValue())

		#checking if there's more than one nodata value 
		nodata = list(set(nodata))
		if len(nodata) > 1:
			raise ValueError('The input image is configured for having different "nodata" values on different bands, not supported: ' + str(nodata))
		if nodata[0] is None:
			nodata = None
		else:
			nodata = int(nodata[0])
		
		#checking if there's already a value from the config, and if there's conflict
		if 'nodata' in self.config:
			#if there's a value in the config file, we'll use that one
			self.nodata = self.config['nodata']
			#what if the config value is different from the one coming directly from the image?
			if self.config['nodata'] != nodata:
				msg = 'Value overwrite for nodata parameter:\n'
				msg = msg + ' - from config ini file   : ' + str(self.config['nodata']) + '\n'
				msg = msg + ' - from actual image file : ' + str(nodata) + '\n'
				msg = msg + 'We will use the config value. To use the image one remove the value from config ini file'
				print(msg)
		else:
			#storing the newfound nodata value from image file
			self.nodata = nodata
		print(' - value used for nodata pixels: ' + str(self.nodata))
		
		#at this point we set the nodata value to what specified
		for i in range(1, ds.RasterCount + 1):  # Bands are 1-indexed
			band = ds.GetRasterBand(i)
			if nodata is not None:
				band.SetNoDataValue(nodata)

		#we are done, print an empty line for formatting
		print("")

	def __join_datasets(self):
		"""joins all available gdal datasets and channels"""
		#let's do the simple case: just one dataset
		if len(self.ds) == 1:
			self.joined_sources = False
			key = list(self.ds.keys())[0]
			self.ds = self.ds[key]
			self.channels = self.datasources[key][1]
			return None

		#if we get here we have two or more datasets to be joined
		self.joined_sources = True
		
		if 'nodata' not in self.config:
			raise ValueError('You defined a joined dataset with data sourced from multiple images. You need to specify a nodata field in the ini file that will be used for all bands')
		
		#joining the channels
		self.channels = []
		for key in self.datasources:
			self.channels = self.channels + self.datasources[key][1]
			
		#creating a joined GDAL dataset, usign VRT (virtual raster table)
		ds = d2r.misc.make_VRT(self.ds, self.config['verbose'])

		#at this point no dataset is open except the merged one
		self.ds = ds

		#the nodata value needs to be specified again for the VRT
		for i in range(1, ds.RasterCount + 1):  # Bands are 1-indexed
			band = ds.GetRasterBand(i)
			band.SetNoDataValue(int(self.config['nodata']))
		
		return(None)
				
	def get_reference_datasource(self):
		"""returns the datasource key for the GDAL dataset to be used as reference for resolution"""
		print('TODO: function get_reference_datasource() just returns the first image, we should implement a smartest strategy')
		return(list(self.datasources.keys())[0])

	def get_files(self):
		"""returns orthomosaic(s) and shapes file names"""
		ortho = []
		for key in self.datasources:
			ortho.append(self.datasources[key][0])
		
		shapes = self.config['shapes_file']
		return(ortho, shapes)

	def get_geom_index(self):
		"""returns a list of the fields in the shape file that should be used as index"""
		return(self.config['shapes_index'])
		
	def get_geom_field(self, polygon_field):
		"""all the values in the passed columns"""
		return(self.shapes[polygon_field])

	def get_geom(self, selector):	
		"""Returns one of the stored geometries, either via index field or simple storing order
		
		The geometry is selected via the "selector" field, which can be either
		an integer (it returns that specific polygon, zero-based ordering)
		or a dictionary with keys the fields(s) to be used to uniquely identify
		the polygon, and values to actually subsed the polygon geodataframe.
		Note that the two above options are incompatible, if both or none are specified an
		error is raised. 
		"""
		
		#sanity
		if not ((isinstance(selector, int)) ^ (isinstance(selector, dict))):
			raise ValueError('Passed selector should be either an int or a dict')

		#let's find the polygon requested
		geom = None
		if isinstance(selector, int):
			shape = self.shapes.iloc[selector, :]
			geom = shape.geometry
		else:
			#building a selector with all the required fields and values
			msg = []
			sel = None
			for key, value in selector.items():
				msg.append(str(key) + '=' + str(value))
				sel_current = self.shapes[key] == value
				if sel is None:
					sel = sel_current
				else:
					sel = sel & sel_current
			#doing the selection
			shape = self.shapes[sel]
			
			#sanity check: did we select just one row?
			if len(shape.index) == 0:
				raise ValueError('The choice of fields+values (from selector) selects zero polygons:\n' + ', '.join(msg))
			if len(shape.index) > 1:
				raise ValueError('The choice of fields+values (from selector) selects more than one polygons:\n' + ', '.join(msg))
			
			#if we get here all is good
			geom = shape.iloc[0,:].geometry
		
		return(geom)
		
	def get_geom_raster(self, selector, rescale_to_255=False, normalize_if_possible=False):
		"""
		Returns the raster data for the specified polygon
		
		Loads in memory and returns the raster data inside the specified polygon as a
		clipped numpy ndarray in the (rows, columns, channel) order. 
		
		selector: see get_geom()
		normalize_if_possible : if True, and if "max_value" has been defined in config, all data will be divided by max_value, so to stay in the 0-1 ramge 
		rescale_to_255 : if True the values will be rescaled to the 0-255 range
		"""
		#getting the requested geometry (or die trying)
		geom = self.get_geom(selector)
		
		#extract the bounding box for the geometry from the raster dataset
		#data is in channel-last at this point format
		raster_box = self.get_bounding_box_raster(geom)
		
		#mask the raster box with the current geometry
		mask = self.get_geom_clipmask(geom)
		
		#fix the nodata value, if present
		if self.get_nodata_value() is not None:
			second_mask = np.ma.getmask(np.ma.masked_equal(raster_box, self.get_nodata_value()))
			mask = np.logical_or(mask, second_mask)
			
		#applying the designed mask
		raster_box = np.ma.masked_array(raster_box, mask)

		#should we normalize?
		if normalize_if_possible and self.config['max_value'] is not None:
			raster_box = raster_box / self.config['max_value']
		
		#should we rescale to 0-255 ?
		if rescale_to_255:
			mymin = np.min(raster_box)
			mymax = np.max(raster_box)
			raster_box = 255 * ((raster_box - mymin) / (mymax - mymin))

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

	def get_geom_centroid(self, selector):
		""""returns the passed geometry centroid"""
		geom = self.get_geom(selector)
		return (geom.centroid.x, geom.centroid.y)
		
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
	"""
	forward_transform = ds.GetGeoTransform()
	reverse_transform = gdal.InvGeoTransform(forward_transform)
	
	if source == 'geo':
		return gdal.ApplyGeoTransform(reverse_transform, point[0], point[1])
	if source == 'pix':
		return gdal.ApplyGeoTransform(forward_transform, point[0], point[1])
	raise ValueError('source needs to be either geo or pix, instead was:', str(source))
