#stub for main file
import sys
import pprint

#drone2report specific submodules
from d2r.config import read_config

def drone2report(infile):
	#reading the config in
	datasets, analyses, renders = read_config(infile)
	
	#printing the current status
	print('ALL DATASETS')
	for o in datasets:
		print(o.to_string())
		pprint.pprint(o.get_config())
	print('ALL ANALYSES')
	for o in analyses:
		print(o.to_string())
	print('ALL RENDERS')
	for o in renders:
		print(o.to_string())
	
	
	#saving a rastered block, for reference
	rb = datasets[0].get_geom_raster(polygon_order=0)
	from PIL import Image
	import numpy as np
	foo = Image.fromarray(rb.astype(np.uint8))
	foo.save("/home/nelson/research/drone2report/test_data/bounding_box_first_polygon_masked2.png")

if __name__ == "__main__":
	print('Welcome to Drone2Report!')
	
	#very simple command line interface
	if len(sys.argv) != 2:
		print('Usage: python3 path/to/drone2report.py config_file.ini')
		exit(0)
	
	#invoking drone2report
	drone2report(sys.argv[1])

	
