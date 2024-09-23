"""
	In this file: functions that takes an image as a input and return a
	matrix as output. Typically they are doing pixel-based computation.
	Function signature is:
		def function(img, channels) -> 2D numpy ndarray, or np.nan if not appliable
	As a convention, in the summary of the docstring just report the name
	of the index plus the list of used band names 
	
	With:
	 - img: numpy ndarray, axis are row, columns, channels
	 - channels: list of string, channel names
"""

import numpy as np

def NDVI(img, channels):
	"""Normalized vegetation index, uses red, NIR"""
	try:
		red = img[:,:,channels.index('red')]
		NIR = img[:,:,channels.index('nir')]
	except ValueError:
		#if this clause is activated it means that the requested channel(s) are not available
		return np.nan
	#if we get here the index can be applied to the current image
	return(
		(NIR - red) /
		(NIR + red)
	) 

def GLI(img, channels):
	"""Green leaf index, uses red, green, blue"""
	try:
		red   = img[:,:,channels.index('red')]
		green = img[:,:,channels.index('green')]
		blue  = img[:,:,channels.index('blue')]
	except ValueError:
		#if this clause is activated it means that the requested channel(s) are not available
		return np.nan
	#if we get here the index can be applied to the current image
	return(
		(2.0*green - red - blue) / 
		(2.0*green + red + blue)
	) 

def HUE(img, channels):
	"""Hue, uses red, green, blue"""
	try:
		red   = img[:,:,channels.index('red')]
		green = img[:,:,channels.index('green')]
		blue  = img[:,:,channels.index('blue')]
	except ValueError:
		#if this clause is activated it means that the requested channel(s) are not available
		return np.nan
	#if we get here the index can be applied to the current image
	return(np.arctan(
		(2*red - green - blue) * (green - blue) / 30.5
	)) 

def GNDVI(img, channels):
	"""Green Normalized Difference Vegetation Index, uses NIR, 540:570"""
	try:
		greenYellow = img[:,:,channels.index('540:570')]
		NIR = img[:,:,channels.index('nir')]
	except ValueError:
		#if this clause is activated it means that the requested channel(s) are not available
		return np.nan
	#if we get here the index can be applied to the current image
	return(
		(NIR - greenYellow) / 
		(NIR + greenYellow)
	) 

def GNDVI(img, channels):
	"""Simple Ratio 800/670 Ratio Vegetation Index, uses 800, 670"""
	try:
		w800 = img[:,:,channels.index('800')]
		w670 = img[:,:,channels.index('670')]
	except ValueError:
		#if this clause is activated it means that the requested channel(s) are not available
		return np.nan
	#if we get here the index can be applied to the current image
	return(w800 / w670)

def NDRE(img, channels):
	"""Normalized Difference NIR/Rededge Normalized Difference Red-Edge, uses NIR, rededge"""
	try:
		redEdge = img[:,:,channels.index('rededge')]
		NIR     = img[:,:,channels.index('nir')]
	except ValueError:
		#if this clause is activated it means that the requested channel(s) are not available
		return np.nan
	#if we get here the index can be applied to the current image
	return(
		(NIR - redEdge) / 
		(NIR + redEdge)
	) 

def NGRDI(img, channels):
	"""Normalized Difference Green/Red Normalized green red difference index, Visible Atmospherically Resistant Indices Green (VIgreen), uses green, red"""
	try:
		red   = img[:,:,channels.index('red')]
		green = img[:,:,channels.index('green')]
	except ValueError:
		#if this clause is activated it means that the requested channel(s) are not available
		return np.nan
	#if we get here the index can be applied to the current image
	return(
		(green - red) / 
		(green + red)
	) 

def VARIgreen(img, channels):
	"""Visible Atmospherically Resistant Index Green, uses 459:490, 545:565, 620:680"""
	try:
		w459 = img[:,:,channels.index('459:490')]
		w545 = img[:,:,channels.index('545:565')]
		w620 = img[:,:,channels.index('620:680')]
	except ValueError:
		#if this clause is activated it means that the requested channel(s) are not available
		return np.nan
	#if we get here the index can be applied to the current image
	return(
		(w545 - w620) / 
		(w545 + w620 - w459)
	) 

def VARI700(img, channels):
	"""Visible Atmospherically Resistant Indices 700, uses 470:490, 660:680, 700"""
	try:
		w470 = img[:,:,channels.index('470:490')]
		w660 = img[:,:,channels.index('660:680')]
		w700 = img[:,:,channels.index('700')]
	except ValueError:
		#if this clause is activated it means that the requested channel(s) are not available
		return np.nan
	#if we get here the index can be applied to the current image
	return(
		(w700 - 1.7*w660 + 0.7*w470) /
		(w700 + 2.3*w660 - 1.3*w470) 
	) 

def VARIrededge(img, channels):
	"""Visible Atmospherically Resistant Indices RedEdge, uses 700:710, 620:680"""
	try:
		w700 = img[:,:,channels.index('700:710')]
		w620 = img[:,:,channels.index('620:680')]
	except ValueError:
		#if this clause is activated it means that the requested channel(s) are not available
		return np.nan
	#if we get here the index can be applied to the current image
	return(
		(w700 - w620) /
		(w700 + w620)
	) 

def random_matrix(img, channels):
	"""a random value between zero and one"""
	return(np.random.rand((img.shape[0], img.shape[1])))   


