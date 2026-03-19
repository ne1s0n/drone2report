from d2r.render import Render

class render_template(Render):
	def run(self):
		#a bit of interface
		self.logger.info('RENDER: template for renders')
		pass
		
	def parse_config(self, config):
		"""parsing config parameters specific to this subclass"""
		res = super().parse_config(config)
		#parse the res dictionary for things specific to this very subclass
		#(if any are preent)
		return(res)
