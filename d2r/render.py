import importlib
import os
import d2r.misc

def render_factory(title, config):
	"""factory method for dynamically instantiating Render classes"""
	if config.getboolean('skip'):
		#just skipping this render
		return []
	#importing the module
	dynamic_module = importlib.import_module('d2r.renders.' + title)
	#importing the class
	dynamic_class = getattr(dynamic_module, title)
	#instantiating
	return [dynamic_class(title, config)]

class Render:
	"""
	This is the base render class, to be subclassed by actual rendering implementations
	
	Place your implementations (in the form of a subclass) under dr2/renders.
	Each module (file) will be dynamically loaded. Only the "run" method
	will be called.
	"""
	def __init__(self, title, config):
		self.title = title
		self.config = self.parse_config(config)

	def to_string(self):
		return(self.title)
		
	def run(self):
		"""this method is meant to be overloaded by the derived subclasses, it's where the actual computation happens"""
		pass

	def parse_config(self, config):
		"""the basic parsing of the config for render object, returns a dict, all keys to lower case"""
		parsed_config = d2r.misc.parse_config(config)
		#at this point the config object is a dict. If any specific parsing
		#should happen, it will happen here. Subclasses should invoke
		#this method via super().parse_config(config)
		return(parsed_config)
