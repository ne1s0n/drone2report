import os
class Analysis:
	def __init__(self, title, config):
		self.title = title
		self.config = config
		
		#the title becomes also the actual function we are going to call, so it's better 
		#to check if it exists
		if not callable(getattr(self, title, None)):
			raise ValueError('Requested unknown analysis: ' + title)
		
	def to_string(self):
		return(self.title)
	def run(self, dataset):
		return(getattr(self, self.title)(dataset))


	def thumbnail(self, dataset):
		#check if we should do the analysis or not
		outfile = os.path.join(self.config['outfolder'], 'thumb_' + dataset.title + '.png')
		if os.path.isfile(outfile) and self.config['skip_if_already_done']:
			print('skipping. Output file already exists: ' + outfile)
			return(None)
		
		#if we get here, we should create the thumbnail
		
		return None
		
	def indexes(self, dataset):
		return None
