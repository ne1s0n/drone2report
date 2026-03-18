import os
import pandas as pd
import numpy as np
import skimage.draw
import pprint
from osgeo import gdal
import plotly.express as px

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
	return ''.join(value.lower().split()).split(',')

def parse_python(value):
	"""evaluates the passed string as a python statement"""
	return eval(value)

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

def draw_ROI_perimeter(ROIs, target_img, raster_data, verbose=False, logger=None):
	for i in range(len(ROIs.index)):
		sh = ROIs.iloc[i,:].geometry
		#check: is this polygon-like?
		if not hasattr(sh, 'exterior'):
			if verbose:
				logger.info('Found that geometry number ' + str(i) + ' is not polygon-like, type: ' + str(type(sh)))
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
			found = False
			
			#is the missing variable an matrix-returning index function?
			if hasattr(mri, e.name):
				found = True
				index_function = getattr(mri, e.name)
				exec(e.name + '= index_function(raster, channels)')
			
			#is the missing variable a channel?
			if e.name in channels:
				found = True
				i = channels.index(e.name)
				exec(e.name + '= raster[:,:,i]')
			
			#have we found something?
			if not found:
				raise ValueError('In .ini file, requested unknown index or channels (case sensitive): ' + e.name)
		
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

def tostring_gdal_info(ds, title, channels=None):
	res = ''
	"""prints information on the passed gdal dataset"""
	if title != '':
		res += ' - title: ' + title
	res += " - projection: " + ds.GetProjection()  # get projection
	gt = ds.GetGeoTransform() 
	res += (" - geotransform:" + 
		' minX=' + str(gt[0]) + 
		' xRes=' + str(gt[1]) + 
		' yRot=' + str(gt[2]) + 
		' minY=' + str(gt[3]) + 
		' xRot=' + str(gt[4]) + 
		' yRes=' + str(gt[5])
		)
	res += " - size (cols, rows, bands): " + str(ds.RasterXSize) + ',' + str(ds.RasterYSize) +  ',' + str(ds.RasterCount)  
		  
	if channels is not None:
		res += " - band names: " + str(channels)
	else:
		res += " - band names: unspecified"
	return(res)
		
def make_VRT(datasets, verbose = True, logger=None):
	"""
	merges all gdal datasets from a dict into a single VRT, max resolution.
	As common, target projection it is used the one of the first dataset
	"""
	
	#extracting the SRS (spatial reference system) from the first image
	first_key = next(iter(datasets))
	target_srs = datasets[first_key].GetProjection()
	if verbose : logger.info('Target SRS taken from ' + str(first_key))
	
	if verbose : logger.info('Merging ' + str(len(datasets)) + ' images')
	cnt = 1
	all_stuff = []
	for key, ds in datasets.items():
		# Reproject into the common SRS, if needed
		if key != first_key:
			reprojected = gdal.Warp('', ds, dstSRS=target_srs, format='MEM', resampleAlg='cubic')
		else:
			#no need to reproject here, it's by definition the same SRS
			reprojected = ds
		
		if verbose: logger.info('Reading from image ' + str(key) + ' band ')
		cnt = cnt + 1
		for i in range(reprojected.RasterCount):
			if verbose: logger.info(str(i+1) + ' ')
			all_stuff.append(gdal.Translate('', reprojected, format='MEM', bandList=[i+1]))
	
	vrt = gdal.BuildVRT('', all_stuff, separate=True, resolution='highest')
	return(vrt)

def indexfile_to_html(infile):
	'''reads the passed .csv file, created by index tasks and returns a
	   dictionary of embeddable html strings, one per dataset/index combination
	'''   

	#all plots (each one html) will be saved into a list
	returned_html = {}

	#reading data in, check if it's in the expected format 
	#TODO
	df = pd.read_csv(infile)

	#----- removing useless columns
	#extract column names from df
	column_names = df.columns

	#select all names that have the "_mean" suffix
	target_traits = [name for name in column_names if name.endswith('_mean')]

	#----- building tooltip
	#selecting columns for tooltip
	column_tooltips = df.columns

	#removing from column_names all items with a suffix that indicates it's a index-related column
	column_tooltips = [name for name in column_tooltips if not name.endswith(('_min', '_max', '_mean', '_median', '_std'))]

	#removing unwanted (constant) columns
	column_tooltips = [name for name in column_tooltips if name not in [
		'type', 'dataset', 'ortho_files', 'shapes_file', 'channels', 
		'centroid_x', 'centroid_y', 'threshold', 'pixels'                                                    
	]]

	#build a temporary dataframe, column by column
	res = pd.DataFrame()
	for column in column_tooltips:
	  #building the target string "column=value"
	  temp_df = pd.DataFrame()
	  temp_df[column + '_name'] = pd.Series(column, index=df.index)
	  temp_df[column] = df[column].astype(str)
	  temp_df = temp_df.T.agg('='.join)
	  #adding to the resulting dataframe
	  res = pd.concat([res, temp_df], axis=1)

	#pasting together all the columns
	res = res.T.agg('<br>'.join)

	#adding to the original dataframe
	df['tooltip'] = res

	#------ build the actual with plotly plot, save the html to be embedded into a file
	#cycle through all subsets for the "dataset" column
	for subset in df['dataset'].unique():
		#filter the rows for the current value of subset
		subset_df = df[df['dataset'] == subset]
		#cycle through target traits
		for trait in target_traits:
			#scatter plot with tooltip
			fig = px.scatter(subset_df, x='centroid_x', y='centroid_y', color=trait, hover_name = 'tooltip')

			#saving
			key = f"subset={subset} trait={trait}"
			returned_html[key] = fig.to_html(full_html=False)

			#building the output file name
			#outfile = key + '.html'
			#outfile = os.path.join(outfolder, outfile) #to be updated with the run date

			#saving
			#fig.write_html(outfile)  

	#and we are done
	return(returned_html)
