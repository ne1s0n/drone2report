from osgeo import gdal
import numpy as np

def tif_multichannel(obj):
	print('opening file ' + obj.config['orthomosaic_file'])
	
	ds = gdal.Open(obj.config['orthomosaic_file'], gdal.GA_ReadOnly)

	print("Projection: ", ds.GetProjection())  # get projection
	print("Columns:", ds.RasterXSize)  # number of columns
	print("Rows:", ds.RasterYSize)  # number of rows
	print("Band count:", ds.RasterCount)  # number of bands

	#putting all the data in a numpy array
	output=np.zeros(shape=(ds.RasterYSize, ds.RasterXSize, ds.RasterCount))
	for i in range(ds.RasterCount):
		output[:, :, i] = ds.GetRasterBand(i+1).ReadAsArray()
	
	return(output, ds.GetProjection())
