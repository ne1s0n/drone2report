import importlib

def render_factory(title, config):
	"""factory method for dynamically instantiating Render classes"""
	#importing the module
	dynamic_module = importlib.import_module('d2r.renders.' + title)
	#importing the class
	dynamic_class = getattr(dynamic_module, title)
	#instantiating
	return dynamic_class(title, config)

class Render:
	"""
	This is the base render class, to be subclassed by actual rendering implementations
	
	Place your implementations (in the form of a subclass) under dr2/renders.
	Each module (file) will be dynamically loaded. Only the "run" method
	will be called.
	"""
	def __init__(self, title, config):
		self.title = title
		self.config = config
		
	def to_string(self):
		return(self.title)
		
	def run(self):
		"""this method is meant to be overloaded by the derived subclasses, it's where the actual computation happens"""
		pass
