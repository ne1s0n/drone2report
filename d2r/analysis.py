import importlib

def analysis_factory(title, config):
	#importing the module
	dynamic_module = importlib.import_module('d2r.analyses.' + title)
	#importing the class
	dynamic_class = getattr(dynamic_module, title)
	#instantiating
	return dynamic_class(title, config)

class Analysis:
	def __init__(self, title, config):
		self.title = title
		self.config = config
		
	def to_string(self):
		return(self.title)
		
	def run(self, dataset):
		"""this method is ment to be overloaded by the derived subclasses, it's where the actual computation happens"""
		pass
		
class indexes(Analysis):
	def run(self, dataset):
		#TODO
		return None
