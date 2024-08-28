#stub for main file
import sys
from d2r.config import read_config

def drone2report(infile):
	#reading the config in
	conf = read_config(infile)
	print(conf)

if __name__ == "__main__":
	print('Welcome to Drone2Report!')
	
	#very simple command line interface
	if len(sys.argv) != 2:
		print('Usage: python3 path/to/drone2report.py config_file.ini')
		exit(0)
	
	#invoking drone2report
	drone2report(sys.argv[1])

	
