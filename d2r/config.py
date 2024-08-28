#This module implements .ini config file parsing, plus several data transformation and
#validation. The core function is read_config(), which requires the .ini infile and
#returns a two (or more) levels dictionary (not a configparser). First level keys are 
#the .ini sections, second level are values.  
#We use the same notation as configparser objects, in particular we refer to "interpolate"
#as the operation of tweaking data, e.g. typing (so that values are actually booleans, int
#and so forth). The main extra functionality injected is the possibility of having lists,
#which are not supported by configparser. When possible we use however configparser
#native interpolation/validation mechanisms

import configparser
import os

def read_config(infile):
	'''
	Reads the config file in .ini format, parse some data so e.g. there's lists
	and not many keys, returns a dictionary
	'''
	
	#check if file exists
	if not os.path.exists(infile):
		msg = 'Config file does not exist: ' + infile
		raise FileNotFoundError(msg)
	
	#instantiate a configparser object
	config = configparser.ConfigParser(interpolation = configparser.ExtendedInterpolation())
	config.read(infile)
	
	#loading everything
	res = {}
	for section in config.sections():
		res[section] = {}
		for key in config[section]:
			#some on-the-fly interpolations for common values in all sections
			if key == 'skip_if_already_done':
				res[section][key] = config[section].getboolean(key)	
			else:
				#just copying the value
				res[section][key] = config[section][key]
	
	return(res)

