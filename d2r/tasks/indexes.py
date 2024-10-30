import os
import pathlib
import importlib
import numpy as np
import pandas as pd
from tqdm import tqdm

from d2r.task import Task
import d2r.misc
import d2r.tasks.matrix_returning_indexes as mri
import d2r.tasks.array_returning_indexes  as ari

class indexes(Task):
	def run(self, dataset):
		#the output path
		outfile = os.path.join(self.config['outfolder'], 'indexes_' + dataset.get_title() + '.csv')
		path = pathlib.Path(self.config['outfolder'])
		path.mkdir(parents=True, exist_ok=True)		

		#check if we should do the task or not
		if os.path.isfile(outfile) and self.config['skip_if_already_done']:
			print('skipping. Output file already exists: ' + outfile)
			return(None)

		#room for results
		df = None
		
		#the index list
		index_names = self.config['indexes'].replace(" ", "").split(',')
		
		#the field that is used to index geometries in the shape file
		fields = dataset.get_geom_index()
		geometry_columns = dataset.get_geom_field(fields)
		
		#for each shape in the dataset
		for i in tqdm(range(len(geometry_columns))):
			#selecting the current geometry
			cg = geometry_columns.iloc[i,:]
			selector = {key : cg[key] for key in fields}
			
			#a raster block
			rb = dataset.get_geom_raster(selector, normalize_if_possible=True)
			
			if rb is None:
				#if rb is None it means that we have asked for data outside the image
				msg = ','.join([str(key) + '=' + str(selector[key]) for key in selector])
				print('Warning: ROI marked with ' + msg + ' is outside the image borders. Ignored.')
			else:
				#collecting required data
				(ortho, shapes) = dataset.get_files()
				(cx, cy) = dataset.get_geom_centroid(selector)
				
				#starting to build the saved dict
				d = {
					'type' : [dataset.get_type()], #this is a list for allowing straightforward dict to pd.dataframe conversion
					'dataset' : dataset.get_title(),
					'ortho_files' : ' '.join(ortho), 
					'shapes_file' : shapes,
					'channels' : ' '.join(dataset.get_channels()),
					'centroid_x' : cx,
					'centroid_y' : cy,
					'threshold' : self.config['threshold'],
					'pixels' : np.ma.count(rb)
				}
				
				#adding info on the current geometry
				d = d | selector
				
				#should we apply a thresholded filter?
				if self.config['threshold'] is not None:
					rb = d2r.misc.thresholded_filter(rb, dataset.get_channels(), self.config['threshold'])
				d['pixels_after_threshold'] = np.ma.count(rb)

				#for each required index
				for current_index in index_names:
					found = False
					#if it's a matrix-returning index, we are going to compute it and
					#then store some general statistics
					if hasattr(mri, current_index):
						found = True
						current_index_function = getattr(mri, current_index)
						myindex = current_index_function(rb, dataset.get_channels())
						d[current_index + '_mean'] = np.ma.mean(myindex)
						d[current_index + '_median'] = np.ma.median(myindex)
						d[current_index + '_std'] = np.ma.std(myindex)
						d[current_index + '_max'] = np.ma.max(myindex)
						d[current_index + '_min'] = np.ma.min(myindex)
					
					#if it's the name of a channel we are going to compute its 
					#values and store some general statistics
					if current_index in dataset.get_channels():
						found = True
						i = dataset.get_channels().index(current_index)
						requested_channel = rb[:, :, i]
						
						d[current_index + '_mean'] = np.ma.mean(requested_channel)
						d[current_index + '_median'] = np.ma.median(requested_channel)
						d[current_index + '_std'] = np.ma.std(requested_channel)
						d[current_index + '_max'] = np.ma.max(requested_channel)
						d[current_index + '_min'] = np.ma.min(requested_channel)

					#if it's an array-returning index, we are going to compute 
					#it and then just store the info
					if hasattr(ari, current_index):
						found = True
						current_index_function = getattr(ari, current_index)
						d.update(current_index_function(rb, dataset.get_channels()))
					
					#if we get here and the index is unknown we raise an error
					if not found:
						raise ValueError('In the .ini file it is requested an unknown index: ' + current_index)
					
				#storing the results
				tmp = pd.DataFrame.from_dict(d)
				df = pd.concat([df, pd.DataFrame.from_dict(d)])
		
		#saving the results
		df.to_csv(outfile, index=False)
		
	def parse_config(self, config):
		"""parsing index-specific config parameters"""
		res = super().parse_config(config)
		
		#default values
		if 'threshold' not in res:
			res['threshold'] = None
		
		return(res)
