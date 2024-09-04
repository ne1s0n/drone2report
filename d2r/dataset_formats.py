from osgeo import gdal
from osgeo import osr
import numpy as np
import geopandas as gpd

def tif_multichannel(obj):
	#opening image file
	print('opening image file ' + obj.config['orthomosaic_file'])
	ds = gdal.Open(obj.config['orthomosaic_file'], gdal.GA_ReadOnly)
	print("Projection: ", ds.GetProjection())  # get projection
	print("Columns:", ds.RasterXSize)  # number of columns
	print("Rows:", ds.RasterYSize)  # number of rows
	print("Band count:", ds.RasterCount)  # number of bands
	
	#opening shapes file
	print('opening image file ' + obj.config['shapes_file'])
	shapes = gpd.read_file(obj.config['shapes_file'])
	
	# let's play it safa and convert the orthomosaic projection to an osr SpatialReference object
	spatial_ref = osr.SpatialReference()
	spatial_ref.ImportFromWkt(ds.GetProjection())

	# Convert to a proj4 string or EPSG code that geopandas can use
	proj4_string = spatial_ref.ExportToProj4()

	# Reproject the shapefile to match the orthomosaic's CRS
	shapes = shapes.to_crs(proj4_string)

	return(ds, shapes)
