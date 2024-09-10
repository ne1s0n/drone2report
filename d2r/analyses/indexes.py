import os
import pathlib
import numpy as np
import pandas as pd

from d2r.analysis import Analysis

class indexes(Analysis):
	def run(self, dataset):
		#the output path
		outfile = os.path.join(self.config['outfolder'], 'indexes_' + dataset.title + '.csv')
		path = pathlib.Path(self.config['outfolder'])
		path.mkdir(parents=True, exist_ok=True)		

		#check if we should do the analysis or not
		if os.path.isfile(outfile) and self.config.getboolean('skip_if_already_done'):
			print('skipping. Output file already exists: ' + outfile)
			return(None)

		#room for results
		df = None
		
		#for each shape in the dataset
		for i in range(len(dataset.shapes)):
			rb = dataset.get_geom_raster(polygon_order=i)
			if rb is not None:
				#starting to build the saved dict
				d = {'polygon' : [i]}
				
				#computing an index
				myindex = GLI(rb, dataset.channels)
				d['GLI_mean'] = np.mean(myindex)
				d['GLI_max'] = np.max(myindex)
				d['GLI_min'] = np.min(myindex)
				
				#storing the results
				df = pd.concat([df, pd.DataFrame.from_dict(d)])
		
		#saving the results
		df.to_csv(outfile, index=False)

def GLI(img, channels):
	"""Green leaf index"""
	red = channels.index('red')
	green = channels.index('green')
	blue = channels.index('blue')
	return(2 * img[:, :, green] - img[:, :, red] - img[:, :, blue]) / (2 * img[:, :, green] + img[:, :, red] + img[:, :, blue])   

def random(img, channels):
	"""a random value between zero and one"""
	return(np.random.rand(img.shape[0], img.shape[1]))   
