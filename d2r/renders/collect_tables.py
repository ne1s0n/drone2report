import os
import pathlib
import warnings
from d2r.render import Render
import d2r.misc

import pprint

class collect_tables(Render):
	def run(self):
		#room for results
		path = pathlib.Path(self.config['outfolder'])
		path.mkdir(parents=True, exist_ok=True)
		
		#first pass: building a dictionary type => file
		infiles = {}
		for infolder in self._parse_infolders():
			#for all .csv files
			for f in os.listdir(infolder):
				full_path = os.path.join(infolder, f)
				table_type = self._get_table_type(full_path)
				if table_type is None:
					continue
				#taking notes
				if table_type in infiles: 
					infiles[table_type].append(full_path)
				else:
					infiles[table_type] = [full_path]

		#showing what we got
		pprint.pprint(infiles)


	def _parse_infolders(self):
		res = []
		for key in self.config:
			if key.lower().startswith('table_infolder'):
				res.append(self.config[key])
		return(res)


	def _get_table_type(self, path):
		"""the first word before the underscore in the filename is the table type. Can return None"""
		if not os.path.isfile(path):
			return None
		
		
		(core, ext) = d2r.misc.get_file_corename_ext(path)
		if ext.lower() != '.csv':
			#only interested in csv files
			return None
		
		pieces = core.split('_', maxsplit=1)
		if len(pieces) != 2:
			#not in the form <type>_<qualifier>
			return None
		#done
		return(pieces[0])
