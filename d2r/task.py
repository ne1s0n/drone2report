import importlib
import d2r.misc

def task_factory(title, config):
	"""factory method for dynamically instantiating Task classes"""
	if config.getboolean('skip'):
		#just skipping this task
		return []
	#importing the module
	dynamic_module = importlib.import_module('d2r.tasks.' + title)
	#importing the class
	dynamic_class = getattr(dynamic_module, title)
	#instantiating
	return [dynamic_class(title, config)]

class Task:
	"""
	This is the base task class, to be subclassed by actual implementations of tasks
	
	Place your implementations (in the form of a subclass) under dr2/tasks.
	Each module (file) will be dynamically loaded. Only the "run" method
	will be called.
	"""
	def __init__(self, title, config):
		self.title = title
		self.config = self.parse_config(config)
		
	def to_string(self):
		return(self.title)
		
	def run(self, dataset):
		"""this method is meant to be overloaded by the derived subclasses, it's where the actual computation happens"""
		pass
	
	def parse_config(self, config):
		"""the basic parsing of the config object, returns a dict, all keys to lower case"""
		res = {}
		for key in config:
			if key.lower() in ['skip', 'skip_if_already_done']:
				res[key.lower()] = d2r.misc.parse_boolean(config[key])
			else:
				res[key.lower()] = config[key]
		return(res)
