import os
import numpy as np
import skimage.draw
import pprint
import d2r.dataset
import d2r.tasks.matrix_returning_indexes as mri

def find_case_insensitve(dirname, extensions):
	"""find all files in passed folder with the passed extension, case insensitive"""
	res = []
	for filename in os.listdir(dirname):
		#building back the full path
		fullpath = os.path.join(dirname, filename)
		if os.path.isdir(fullpath):
			#this is a folder, skipping
			continue
		#splitting file name and extension
		base, ext = os.path.splitext(fullpath)
		if ext.lower() in extensions:
			res.append(fullpath)
	return(res)

def get_file_corename_ext(filename):
	"""for path/to/filename.ext returns (filename, ext)"""
	core = os.path.basename(filename)
	core, ext = os.path.splitext(core)
	return core, ext

def parse_boolean(val):
	"""parse a string to a boolean value"""
	if val.lower() in ['yes', 'true', 'on']:
		return True
	if val.lower() in ['no', 'false', 'off']:
		return False
	raise ValueError('Found value not parsable as boolean: ' + val)

def parse_channels(value):
	"""parses channels: comma separated string values, which will be forced to lowercase and removed of spaces"""
	return value.lower().replace(" ", "").split(',')

def parse_config(config):
	"""the basic parsing of the config object, returns a dict, all keys to lower case"""
	res = {}
	for key in config:
		if key.lower() in ['active', 'skip_if_already_done', 'verbose']:
			res[key.lower()] = parse_boolean(config[key])
		elif key.lower() == 'cores':
			res[key.lower()] = int(config[key])
		else:
			res[key.lower()] = config[key]
	return(res)

def draw_ROI_perimeter(ROIs, target_img, raster_data, verbose=False):
	for i in range(len(ROIs.index)):
		sh = ROIs.iloc[i,:].geometry
		#check: is this polygon-like?
		if not hasattr(sh, 'exterior'):
			if verbose:
				print('Found that geometry number ' + str(i) + ' is not polygon-like, type: ' + str(type(sh)))
			#if it's not polygon-like we cannot draw it
			continue
		
		#converting the polygon coordinates to pixel coordinates
		coords = list(sh.exterior.coords)
		coords2 = np.zeros((len(coords), 2))
		for i in range(len(coords)):
			(coords2[i,0], coords2[i,1]) = d2r.dataset.transform_coords(target_img, point=(coords[i][0], coords[i][1]), source='geo')
		
		#drawing the polygon in red
		rr, cc = skimage.draw.polygon_perimeter(coords2[:,1], coords2[:,0], raster_data.shape)
		raster_data[rr, cc, :] = (255, 0, 0)

def thresholded_filter(raster, channels, filter_string):
	"""Tries to apply a filtering expression to a raster ROI, or dies trying"""
	#this loop will either assign a value to "sel" or generate an exception and crash
	while True:
		try:
			exec('sel = ' + filter_string)
		except NameError as e:
			#let's define the missing variable, if valid
			if not hasattr(mri, e.name):
				raise ValueError('requested unknown index (case sensitive): ' + e.name)
			index_function = getattr(mri, e.name)
			exec(e.name + '= index_function(raster, channels)')
		
		#checking if we need to keep going or not
		if 'sel' in locals():
			break
	
	#if we get here we have defined sel (in a dynamic context)
	#let's apply the newfound filtering mask to the existing one, once
	#for each existing channel
	for i in range(raster.mask.shape[2]):
		#rembember that the mask tells what values to NOT use, and the
		#user in the ini specify the target areas to ACTUALLY use. Thus,
		#we need a logical not
		raster.mask[:, :, i] = raster.mask[:, :, i] | np.ma.logical_not(eval('sel'))
		
	return(raster)

def print_gdal_info(ds, title, channels=None):
	"""prints information on the passed gdal dataset"""
	print(' - title: ' + title)
	print(" - projection: ", ds.GetProjection())  # get projection
	gt = ds.GetGeoTransform() 
	print(" - geotransform:", 
		' minX=', str(gt[0]), 
		' xRes=', str(gt[1]), 
		' yRot=', str(gt[2]), 
		' minY=', str(gt[3]), 
		' xRot=', str(gt[4]), 
		' yRes=', str(gt[5]))  
	print(" - columns:", ds.RasterXSize)  # number of columns
	print(" - rows:", ds.RasterYSize)  # number of rows
	print(" - band count:", ds.RasterCount)  # number of bands
	if channels is not None:
		print(" - band names: ", str(channels)) 
	else:
		print(" - band names: unspecified") 
		
