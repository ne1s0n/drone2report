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

def GNDVI(img, channels):
	"""Green Normalized Difference Vegetation Index, uses NIR, 540:570"""
	try:
		greenYellow = channels.index('540:570')
		NIR = channels.index('nir')
	except ValueError:
		#if this clause is activated it means that the requested channel(s) are not available
		return np.nan
	#if we get here the index can be applied to the current image
	return((img[:, :, NIR] - img[:, :, greenYellow]) / (img[:, :, NIR] + img[:, :, greenYellow])) 

def GNDVI(img, channels):
	"""Simple Ratio 800/670 Ratio Vegetation Index, uses 800, 670"""
	try:
		w800 = channels.index('800')
		w670 = channels.index('670')
	except ValueError:
		#if this clause is activated it means that the requested channel(s) are not available
		return np.nan
	#if we get here the index can be applied to the current image
	return(img[:, :, w800] / img[:, :, w670])

def NDRE(img, channels):
	"""Normalized Difference NIR/Rededge Normalized Difference Red-Edge, uses NIR, rededge"""
	try:
		redEdge = channels.index('rededge')
		NIR = channels.index('nir')
	except ValueError:
		#if this clause is activated it means that the requested channel(s) are not available
		return np.nan
	#if we get here the index can be applied to the current image
	return((img[:, :, NIR] - img[:, :, redEdge]) / (img[:, :, NIR] + img[:, :, redEdge])) 

def NGRDI(img, channels):
	"""Normalized Difference Green/Red Normalized green red difference index, Visible Atmospherically Resistant Indices Green (VIgreen), uses green, red"""
	try:
		green = channels.index('green')
		red = channels.index('red')
	except ValueError:
		#if this clause is activated it means that the requested channel(s) are not available
		return np.nan
	#if we get here the index can be applied to the current image
	return((img[:, :, green] - img[:, :, red]) / (img[:, :, green] + img[:, :, red])) 

def random_matrix(img, channels):
	"""a random value between zero and one"""
	return(np.random.rand(img.shape[0], img.shape[1]))   


