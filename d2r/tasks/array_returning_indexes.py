"""
	In this file: functions that takes an image as a input and return a
	named array (implemented as a dictionary) as output. Typically 
	they are doing image-wide computation.
	Function signature is:
		def function(img, channels) -> dictionary (each value should be a scalar), or np.nan if not appliable
	
	With:
	 - img: numpy ndarray, axis are row, columns, channels
	 - channels: list of string, channel names
"""

import numpy as np

def random_array(img, channels):
	"""two random values between zero and one"""
	return({
		'first_random_value' : np.random.rand(1)[0],
		'second_random_value' : np.random.rand(1)[0]
	})
	
def summation(img, channels):
	"""adding everything to a single number"""
	return({'summation' : img.sum()})
	


