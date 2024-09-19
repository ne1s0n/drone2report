"""
	In this file: functions that takes an image as a input and return a
	matrix as output. Typically they are doing pixel-based computation.
	Function signature is:
		def function(img, channels) -> 2D numpy ndarray, or np.nan if not appliable
	
	With:
	 - img: numpy ndarray, axis are row, columns, channels
	 - channels: list of string, channel names
"""

import numpy as np

def NDVI(img, channels):
	"""Normalized vegetation index, uses red, NIR"""
	try:
		red = channels.index('red')
		NIR = channels.index('nir')
	except ValueError:
		#if this clause is activated it means that the requested channel(s) are not available
		return np.nan
	#if we get here the index can be applied to the current image
	return((img[:, :, NIR] - img[:, :, red]) / (img[:, :, NIR] + img[:, :, red])) 

def GLI(img, channels):
	"""Green leaf index, uses red, green, blue"""
	try:
		red = channels.index('red')
		green = channels.index('green')
		blue = channels.index('blue')
	except ValueError:
		#if this clause is activated it means that the requested channel(s) are not available
		return np.nan
	#if we get here the index can be applied to the current image
	return  ((2.0 * img[:, :, green] - img[:, :, red] - img[:, :, blue]) / (2.0 * img[:, :, green] + img[:, :, red] + img[:, :, blue])) 

def random_matrix(img, channels):
	"""a random value between zero and one"""
	return(np.random.rand(img.shape[0], img.shape[1]))   


