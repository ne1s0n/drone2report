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
import pprint

from d2r.dataset import dataset_factory
from d2r.render import render_factory
from d2r.task import task_factory

def read_config(infile):
	'''
	Reads the config file in .ini format, parse some data so e.g. there's lists
	and not many keys, returns a three objects: datasets, tasks, renders
	'''
	
	#check if file exists
	if not os.path.exists(infile):
		msg = 'Config file does not exist: ' + infile
		raise FileNotFoundError(msg)
	
	#instantiate a configparser object
	config = configparser.ConfigParser(interpolation = configparser.ExtendedInterpolation())
	config.read(infile)
	
	#prepare the output lists, first level of keys
	datasets = []
	tasks = []
	renders = []
	
	#loading everything
	for section in config.sections():
		#breaking up the section name, which should be "OPERATION qual1 <qual2>"
		pieces = section.split()
		if len(pieces) < 2 or len(pieces) > 3:
			msg = 'Bad section name: ' + section
			raise ValueError(msg)
		op = pieces[0]
		title = " ".join(pieces[1:])
		
		#each section is an instance of an object. Factory methods return
		#always a list, which could be empty or contain more than one object
		found = False
		if op == 'DATA':
			datasets = datasets + dataset_factory(title, config[section])
			found = True
		if op == 'TASK':
			tasks = tasks + task_factory(title, config[section])
			found = True
		if op == 'RENDER':
			renders = renders + render_factory(title, config[section])
			found = True
		if not found:
			raise ValueError('Bad section name: ' + op)
	
	return(datasets, tasks, renders)
