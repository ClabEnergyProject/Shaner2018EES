import geopandas as gpd 
import itertools
import numpy as np
import netCDF4 as nc
import pandas as pd
from shapely.geometry import Point 


def Country_boxes(polygon, latitude, longitude, latitude_precision, longitude_precision):

	latitude_precision = 0.5 # degrees
	longitude_precision = 0.625 # degrees

	########
	# define rectangle of data to retrive
	bounding_box = polygon.envelope

	# produces a list of 2 rows and 5 columns with the first and last column corresponding to 
	# the same point.  The first row corresponds to longitude, the second to latitude
	bounding_box_coords = bounding_box.exterior.coords.xy 

	northern_most = np.max(bounding_box_coords[1])
	northern_most_degrees = np.ceil(northern_most / latitude_precision) * latitude_precision 
	northern_most_grid = np.where(latitude == northern_most_degrees)[0][0]

	southern_most = np.min(bounding_box_coords[1])
	southern_most_degrees = np.floor(southern_most / latitude_precision) * latitude_precision
	southern_most_grid = np.where(latitude == southern_most_degrees)[0][0]

	western_most = np.min(bounding_box_coords[0])
	western_most_degrees = np.max([np.floor(western_most / longitude_precision) * 
		longitude_precision, -180])
	western_most_grid = np.where(longitude == western_most_degrees)[0][0]

	eastern_most = np.max(bounding_box_coords[0])
	eastern_most_degrees = np.min([np.ceil(eastern_most / longitude_precision) * 
		longitude_precision, 179.375])
	eastern_most_grid = np.where(longitude == eastern_most_degrees)[0][0]

	return southern_most_grid, southern_most_degrees, northern_most_grid, northern_most_degrees, \
		western_most_grid, western_most_degrees, eastern_most_grid, eastern_most_degrees


def masks(smg, smd, nmg, nmd, wmg, wmd, emg, emd, polygon, latitude_precision, 
	longitude_precision, path):
	#create mask (1's where land is, 0's where land isn't)

	# initialize mask array, +1 to include last point
	mask = np.zeros((nmg - smg + 1, emg - wmg + 1))

	# make arrays of latitude and longitude that correspond to each point in box
	lat_range = np.arange(smd, nmd + latitude_precision, latitude_precision)
	long_range = np.arange(wmd, emd + longitude_precision, longitude_precision)

	c1 = 0 # counter for latitude
	for lat in lat_range:
		c2 = 0 # counter for longitude
		for lon in long_range:

			# convert lat, lon for point of interest into a useable form for the shapefile
			point_of_interest = Point(lon, lat)

			# if point is within the polygon then mask point equals 1, if not mask point equals 0
			if polygon.contains(point_of_interest):
				mask[c1,c2] = 1

			c2 += 1

		c1 += 1


	return mask, lat_range, long_range


def main():

	# definitions
	latitude_precision = 0.5 # degrees
	longitude_precision = 0.625 # degrees
	path = '/lustre/data/mshaner/merra2'

	# import shape file, extract country names and 
	shapefile = gpd.GeoDataFrame.from_file('{}/country_mask_files/ne_110m_admin_0_countries.shp'
		.format(path))
	country_names = shapefile.geounit
	
	# import constants and extract latitude, longitude and area data
	constants = nc.Dataset('{}/merra2_constants.nc'.format(path))
	area = np.squeeze(constants['AREA'][:])
	latitude = np.squeeze(constants['lat'][:])
	longitude = np.squeeze(constants['lon'][:])
	latitude[360/2] = 0
	longitude[576/2] = 0 # value for 0 deg is non-zero in array (~5 x 10^-13....close, but not close enough)


	multipolygon_country_indexes = np.array([1, 4, 6, 8, 10, 17, 27, 29, 30, 43, 53, 55, 57, 
		64, 72, 79, 82, 111, 118, 120, 121, 125, 126, 135, 142, 162, 168, 172])
		
		# 1 = Angola (2), 4 = Argentina (2), 6 = Antarctica(8), 8 = Australia (2), 10 = Azerbaijan (2),
		# 17 = The Bahamas (3), 27 = Canada (30), 29 = Chile (2), 30 = China (2), 43 = Denmark (2)
		# 53 = Fiji (3), 55 = France (3), 57 = United Kingdom (2), 64 = Greece (2), 72 = Indonesia (13),
		# 79 = Italy (3), 82 = Japan (3), 111 = Malaysia (2), 118 = Norway (4), 120 = New Zealand (2),
		# 121 = Oman (2), 125 = Philippines (7), 126 = Papua New Guinea (4), 135 = Russia (13),
		# 142 = Solomon Islands (5), 162 = Turkey (2), 168 = United States of America (10), 172 = Vanuatu (2)
	
	counter = 0

	for i in range(country_names.size):

		if i in multipolygon_country_indexes:

			# hard code for each country of interest
			# countries and polygons of interest are (all were figured out by area of polygon):
			# Angola, polygon 1 = mainland; Argentina, polygon 2 = mainland; Australia, polygon 2 = mainland; Azerbaijan, polygon 2, mainland;
			# Canada, polygon 11 = mainland; Chile, polygon 2 = mainland; China, polygon 2 = mainland;
			# Denmark, polygon 2; France, polygon 3 = mainland; United Kingdom, polygon 2 = mainland;
			# Greece, polygon 2 = mainland; Italy, polygon 3 = mainland;
			# Japan, polygon 2; Norway, polygon 1; Oman, polygon 1;
			# Russia, polygon 10; Turkey, polygon 1; CONUS, polygon 6; Alaska, polygon 10

			# countries omitted: Antartica, The Bahamas, Fiji, Indonesia, Malaysia, New Zealand, Philippines,
			# Papua New Guinea, Solomon Islands, Vanuatu

			omitted = ['Antarctica', 'The Bahamas', 'Fiji', 'Indonesia', 'Malaysia', 'New Zealand', \
				'Philippines', 'Papua New Guinea', 'Solomon Islands', 'Vanuatu']

			multi = [['Angola', 0], ['Argentina', 1], ['Australia', 1], ['Azerbaijan', 1], \
				['Canada', 10], ['Chile', 1], ['China', 1], ['Denmark', 1], ['France', 2], \
				['United Kingdom', 1], ['Greece', 1], ['Italy', 2], ['Japan', 1], \
				['Norway', 0], ['Oman', 0], ['Russia', 9], ['Turkey', 0], ['United States of America', 5]]

			if country_names[i] in omitted:

				pass

			else:
				
				country = country_names[i]
				polygon = shapefile.geometry[i][multi[counter][1]]
				smg, smd, nmg, nmd, wmg, wmd, emg, emd = Country_boxes(polygon, latitude, longitude, 
					latitude_precision, longitude_precision)
				mask, lat_range, long_range = masks(smg, smd, nmg, nmd, wmg, wmd, emg, emd, 
					polygon, latitude_precision, longitude_precision, path)
				cropped_area = area[smg:nmg + 1, wmg:emg + 1]

				np.save('{}/country_files/{}_mask.npy'.format(path, country), mask)
				np.save('{}/country_files/{}_latitudes.npy'.format(path, country), lat_range)
				np.save('{}/country_files/{}_longitudes.npy'.format(path, country), long_range)
				np.save('{}/country_files/{}_areas.npy'.format(path, country), cropped_area)

				counter += 1

		else: # countries defined by a single polygon

			country = country_names[i]
			polygon = shapefile.geometry[i]
			smg, smd, nmg, nmd, wmg, wmd, emg, emd = Country_boxes(polygon, latitude, longitude, 
				latitude_precision, longitude_precision)
			mask, lat_range, long_range = masks(smg, smd, nmg, nmd, wmg, wmd, emg, emd, 
				polygon, latitude_precision, longitude_precision, path)
			cropped_area = area[smg:nmg + 1, wmg:emg + 1]

			np.save('{}/country_files/{}_mask.npy'.format(path, country), mask)
			np.save('{}/country_files/{}_latitude.npy'.format(path, country), lat_range)
			np.save('{}/country_files/{}_longitude.npy'.format(path, country), long_range)
			np.save('{}/country_files/{}_areas.npy'.format(path, country), cropped_area)



if __name__ == '__main__':
	main()

