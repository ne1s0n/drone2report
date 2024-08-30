import numpy as np
import matplotlib.pyplot as plt

def hist(data, title, outfile):
	plt.hist(data.flatten(), bins=30)

	# Add labels and title
	plt.xlabel('Value')
	plt.ylabel('Frequency')
	plt.title(title)

	# save, close
	plt.savefig(outfile)
	plt.close()
	
	
