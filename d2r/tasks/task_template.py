from d2r.task import Task

class task_template(Task):
	def run(self, dataset):
		"""the actual function to perform the custom actions"""
		
		#just logging that we invoked this function
		self.logger.info('Invoked the run() method')
		
		pass

	def parse_config(self, config):
		"""parsing config parameters specific to this subclass"""
		res = super().parse_config(config)
		#the parsing should happen here, keeping the keys of the res dictionary
		#but modifying, as required, the values 
		return(res)
