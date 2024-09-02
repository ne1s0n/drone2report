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
	
	#test load
	foo = datasets[0].load()
	

if __name__ == "__main__":
	print('Welcome to Drone2Report!')
	
	#very simple command line interface
	if len(sys.argv) != 2:
		print('Usage: python3 path/to/drone2report.py config_file.ini')
		exit(0)
	
	#invoking drone2report
	drone2report(sys.argv[1])

	
