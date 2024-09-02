#all the functions in this module share the same interface: first argument is
#an image (numpy array, first two levels are x,y coordinates, third one is the
#channels). Second argument is a dictionary where key are channel names, second
#index is the corresponding channel, e.g.
#	channels = {
#		'R' : 0,
#		'G' : 1,
#		'B' : 2
#	}

import numpy as np

def GLI(img, channels):
	"""Green leaf index"""
	red = channels['red']
	green = channels['green']
	blue = channels['blue']
	return(2 * img[:, :, green] - img[:, :, red] - img[:, :, blue]) / (2 * img[:, :, green] + img[:, :, red] + img[:, :, blue])   

def random(img, channels):
	"""a random value between zero and one"""
	return(np.random.rand(img.shape[0], img.shape[1]))   
