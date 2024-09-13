import os
import pathlib
import warnings
from d2r.render import Render
import d2r.misc
import pandas as pd

import pprint

class collect_tables(Render):
	def run(self):
		#room for results
		outfolder = pathlib.Path(self.config['outfolder'])
		outfolder.mkdir(parents=True, exist_ok=True)
		
		#first pass: building a type => [files list] dictionary 
		infiles = self._collect_files()
		
		#for each table type
		for table_type in infiles:
			#building a summary table
			sumtab =  self._summary_table(infiles[table_type])
			
			#saving the table
			outfile = os.path.join(outfolder, table_type + '.csv')
			sumtab.to_csv(outfile, index=False)
			print('Collected ' + table_type + ' table into ' + outfile)

	def _summary_table(self, infiles):
		res = None
		for f in infiles:
			res = pd.concat([res, pd.read_csv(f)])
		return res

	def _collect_files(self):
		"""returns all interesting files in a type => [files list] dictionary"""
		res = {}
		for infolder in self._get_infolders():
			#going through all files, keeping only correct ones
			for f in os.listdir(infolder):
				full_path = os.path.join(infolder, f)
				table_type = self._get_table_type(full_path)
				if table_type is None:
					continue
				#taking notes
				if table_type in res: 
					res[table_type].append(full_path)
				else:
					res[table_type] = [full_path]
		return(res)
		
	def _get_infolders(self):
		"""collects all infolders from config"""
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
