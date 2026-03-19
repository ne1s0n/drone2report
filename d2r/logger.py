#This module takes care of the logging configuration.

import logging
import sys
import os

def get_logger(logname, config):
	logger = logging.getLogger(logname)
	
	if logger.handlers:   #prevents duplication
		return logger
	
	#making sure there's the output folder
	os.makedirs(config['logfolder'], exist_ok=True)
	outfile = os.path.join(config['logfolder'], logname + ".log") #to be updated with the run date
	
	#we use INFO level as default
	logger.setLevel(logging.INFO)

	#formatter (shared by stdout and logfile)
	formatter = logging.Formatter('[%(asctime)s %(levelname)s] %(message)s')

	#console handler (stdout)
	console_handler = logging.StreamHandler(sys.stdout)
	console_handler.setFormatter(formatter)

	#file handler
	file_handler = logging.FileHandler(outfile)
	file_handler.setFormatter(formatter)

	#attach both handlers
	logger.addHandler(console_handler)
	logger.addHandler(file_handler)
	
	#now this would go to BOTH console and file
	#logger.info("test message")
	
	#done
	return(logger)
