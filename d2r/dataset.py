#This module contains the information for one single dataset. When instantiated
#it does not really read the data, but it checks for the required files to be existing

import importlib
import d2r.config

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
				self.skip = d2r.config.parse_boolean(body[key])
			elif key.lower() == 'channels':
				self.channels = d2r.config.parse_channels(body[key])
			elif key.lower() == 'type':
				self.type = body[key]
			else:
				self.config[key] = body[key]
		
		#if we reach the end of the parsing and no type was specified, we have a problem
		if self.type is None:
			raise ValueError('Missing "type" field for dataset: ' + title)
		if self.skip is None:
			raise ValueError('Missing "skip" field for dataset: ' + title)
		if self.channels is None:
			raise ValueError('Missing "channels" field for dataset: ' + title)
		
	def to_string(self):
		return(self.name + ' (' + self.type + ')') 
	def get_meta(self):
		return(self.meta)
	def get_config(self):
		return(self.config)
		
	def get_channels(self):
		return self.channels
			
	def load(self):
		"""loads the dataset, returns a dictionary"""
		#dynamically import the submodule with all the formats definitions
		submodule = importlib.import_module('d2r.dataset_formats')

		#retrieve the loading function for this specific format
		load_function = getattr(submodule, self.type)
		
		#ready to load
		return load_function(self)

