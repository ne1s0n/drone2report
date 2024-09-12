from d2r.render import Render

class collect_tables(Render):
	def run(self):
		print("collecting all tables from these paths:\n - " + '\n - '.join(self._parse_infolders()))

	def _parse_infolders(self):
		res = []
		for key in self.config:
			if key.lower().startswith('infolder'):
				res.append(self.config[key])
		return(res)
