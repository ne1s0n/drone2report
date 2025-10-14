#stub for main file
import sys
import pprint

#drone2report specific submodules
from d2r.config import read_config

def drone2report(infile):
	print('========================== DATASET SETUP ===========================')
	#reading the config in
	datasets, tasks, renders = read_config(infile)
	
	print('\n========================== RUNNING TASKS ===========================')
	#applying all tasks to all datasets
	for t in tasks:
		print('[TASK]', t.to_string())
		for d in datasets:
			print(' - [DATASET]', d.to_string())
			t.run(d)
		print('')


	print('\n============================ RENDERING =============================')
	#executing all the renderings
	for r in renders:
		print('[RENDER]', r.to_string())
		r.run()
		print('')

	#stop
	return None

if __name__ == "__main__":
	print('Welcome to Drone2Report!')
	
	#very simple command line interface
	if len(sys.argv) != 2:
		print('Usage: python3 path/to/drone2report.py config_file.ini')
		exit(0)
	
	#invoking drone2report
	drone2report(sys.argv[1])

	
