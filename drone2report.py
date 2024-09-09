#stub for main file
import sys
import pprint

#drone2report specific submodules
from d2r.config import read_config

def drone2report(infile):
	#reading the config in
	print('========================== DATASET SETUP ===========================')
	datasets, analyses, renders = read_config(infile)
	
	#applying all analyses to all datasets
	print('\n======================== RUNNING ANALYSES ========================')
	for a in analyses:
		print('[ANALYSIS]', a.to_string())
		for d in datasets:
			print(' - [DATASET]', d.to_string())
			if d.skip:
				print('marked to be skipped')
				continue
			a.run(d)

	print('\n=========================== RENDERING ============================')
	print('TBD')

	#stop
	return None
	
	#saving a rastered block, for reference
	from PIL import Image
	import numpy as np
	import d2r.render_tools
	for i in range(len(datasets[0].shapes)):
		rb = datasets[0].get_geom_raster(polygon_order=i)
		if rb is not None:
			print('found a valid shape!')
			print(rb.shape)
			
			#debug
			
			#rb = datasets[0].ds.ReadAsArray(5000, 5000, 1000, 1000) 
			#rb = datasets[0].ds.ReadAsArray(7000, 6265, 1000, 1000) 
			#print(rb.shape)
			#rb = np.moveaxis(rb, 0, -1)
			
			#focusing on visible spectrum of micasense
			if rb.shape[2] == 10:
				rb = rb[:, :, [5, 3, 1]]
				
			#removing a useless channel, if it's there
			if rb.shape[2] == 1:
				rb = np.squeeze(rb, axis=2)
			
			#computing range
			minval=np.min(rb)
			maxval=np.max(rb)
			print('test min-max', minval, maxval)
			if minval == maxval:
				#blank image, skipping
				print("void, skipping")
				continue

			#masking missing values
			rb = np.ma.masked_equal(rb, -32767)
			
			#saving
			foo = Image.fromarray(rb.astype(np.uint8))
			outfile = "/home/nelson/research/drone2report/test_data/plots/img" + str(i) + ".png"
			foo.save(outfile)

			#saving a histogram
			outfile = "/home/nelson/research/drone2report/test_data/plots/img" + str(i) + "_hist.png"
			d2r.render_tools.hist(rb, "min:" + str(minval) + ' max:'+str(maxval), outfile)

			#rescaling
			minval=np.min(rb)
			maxval=np.max(rb)
			rb =  255 * (rb - minval) / (maxval - minval)
			minval=np.min(rb)
			maxval=np.max(rb)

			#saving
			foo = Image.fromarray(rb.astype(np.uint8))
			outfile = "/home/nelson/research/drone2report/test_data/plots/img" + str(i) + "_rescaled.png"
			foo.save(outfile)
			
			#saving a histogram
			outfile = "/home/nelson/research/drone2report/test_data/plots/img" + str(i) + "_rescaled_hist.png"
			d2r.render_tools.hist(rb, "min:" + str(minval) + ' max:'+str(maxval), outfile)
			
			break
			


if __name__ == "__main__":
	print('Welcome to Drone2Report!')
	
	#very simple command line interface
	if len(sys.argv) != 2:
		print('Usage: python3 path/to/drone2report.py config_file.ini')
		exit(0)
	
	#invoking drone2report
	drone2report(sys.argv[1])

	
