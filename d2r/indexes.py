#all the functions in this module share the same interface: first argument is
#an image (numpy array, first two levels are x,y coordinates, third one is the
#channels). Second argument is a list of channel names, which determine the
#channel order. Some values are fixed: red, green, blue, rededge, nir (all
#small caps, no spaces). 

import numpy as np

def GLI(img, channels):
	"""Green leaf index"""
	red = channels.index('red')
	green = channels.index('green')
	blue = channels.index('blue')
	return(2 * img[:, :, green] - img[:, :, red] - img[:, :, blue]) / (2 * img[:, :, green] + img[:, :, red] + img[:, :, blue])   

def random(img, channels):
	"""a random value between zero and one"""
	return(np.random.rand(img.shape[0], img.shape[1]))   
