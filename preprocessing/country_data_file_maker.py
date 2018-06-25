import geopandas as gpd 
import itertools
import numpy as np
import netCDF4 as nc
import pandas as pd
from shapely.geometry import Point 


constants = nc.Dataset('/lustre/data/mshaner/merra2/merra2_constants.nc')

land = np.squeeze(constants['FRLAND'][:])
latitude = np.squeeze(constants['lat'][:])
longitude = np.squeeze(constants['lon'][:])
latitude[360/2] = 0
longitude[576/2] = 0 # value for 0 deg is non-zero in array (~5 x 10^-13....close, but not close enough)


def Country_boxes(polygon, area_name):

	latitude_precision = 0.5 # degrees
	longitude_precision = 0.625 # degrees

	########
	# define rectangle of data to retrive
	bounding_box = polygon.envelope
	bounding_box_coords = bounding_box.exterior.coords.xy # produces a list of 2 rows and 5 columns with the first and last column corresponding to the same point.  The first row corresponds to longitude, the second to latitude
	
	northern_most = np.max(bounding_box_coords[1])
	northern_most_degrees = np.ceil(northern_most / latitude_precision) * latitude_precision 
	northern_most_grid = np.where(latitude == northern_most_degrees)[0][0]

	southern_most = np.min(bounding_box_coords[1])
	southern_most_degrees = np.floor(southern_most / latitude_precision) * latitude_precision
	southern_most_grid = np.where(latitude == southern_most_degrees)[0][0]

	western_most = np.min(bounding_box_coords[0])
	western_most_degrees = np.max([np.floor(western_most / longitude_precision) * longitude_precision, -180])
	western_most_grid = np.where(longitude == western_most_degrees)[0][0]

	eastern_most = np.max(bounding_box_coords[0])
	eastern_most_degrees = np.min([np.ceil(eastern_most / longitude_precision) * longitude_precision, 179.375])
	eastern_most_grid = np.where(longitude == eastern_most_degrees)[0][0]

	#print 'north - {}, south - {}, west - {}, east - {}'.format(northern_most_grid, southern_most_grid, western_most_grid, eastern_most_grid)

	########
	# open data file(s) and extract points needed for both solar and windspeed

	gridded_lat_precision = 90.
	gridded_long_precision = 192.

	lat_grid_max = np.int(np.ceil(northern_most_grid / gridded_lat_precision) * gridded_lat_precision)
	lat_grid_min = np.int(np.floor(southern_most_grid / gridded_lat_precision) * gridded_lat_precision)

	long_grid_max = np.int(np.ceil(eastern_most_grid / gridded_long_precision) * gridded_long_precision)
	long_grid_min = np.int(np.floor(western_most_grid / gridded_long_precision) * gridded_long_precision)

	#print 'lat_min - {}, lat_max - {}, long_min - {}, long_max - {}'.format(lat_grid_min, lat_grid_max, long_grid_min, long_grid_max)

	lat_range = np.arange(lat_grid_min, lat_grid_max + 1, np.int(gridded_lat_precision))
	long_range = np.arange(long_grid_min, long_grid_max + 2, np.int(gridded_long_precision))

	return lat_range, long_range, southern_most_grid, northern_most_grid, western_most_grid, eastern_most_grid


def Polygon_2_datafile(area_name, lat_range, long_range, southern_most_grid, northern_most_grid, western_most_grid, eastern_most_grid):

	latitude_precision = 0.5 # degrees
	longitude_precision = 0.625 # degrees
	gridded_lat_precision = 90
	gridded_long_precision = 192

	lat_length = northern_most_grid - southern_most_grid + 1 # need + 1 to include last point
	long_length = eastern_most_grid - western_most_grid + 1

	# loop through all 12 datasets and open them
	# if lat_range and long_range simultaneously equal opened dataset range, collect appropriate boxes and save country file


	solar_resource = np.zeros((315576, lat_length, long_length))

	path = '/lustre/data/mshaner/merra2'

	for (lat_i, lat_f), (long_i, long_f) in itertools.product(zip(lat_range[:-1], lat_range[1:]), zip(long_range[:-1], long_range[1:])):

		# open data files
		if (lat_f == 360):

			solar_flux = np.load('{}/swgdn/all_yrs_grided/swgdn_{}-{}_{}-{}.npy'.format(path, lat_i, lat_f, long_i, long_f - 1))

		else:

			solar_flux = np.load('{}/swgdn/all_yrs_grided/swgdn_{}-{}_{}-{}.npy'.format(path, lat_i, lat_f - 1, long_i, long_f - 1))

		# extract data from files
		# determine array locations to be filled
		lat_fill_start = np.max([southern_most_grid, lat_i]) - southern_most_grid
		lat_fill_finish = np.min([northern_most_grid, lat_f - 1]) - southern_most_grid + 1 # - 1 and + 1 so the last point is included
		long_fill_start = np.max([western_most_grid, long_i]) - western_most_grid
		long_fill_finish = np.min([eastern_most_grid, long_f - 1]) - western_most_grid + 1

		# determine array locations to extract from
		lat_extract_start = np.max([southern_most_grid, lat_i]) - lat_i
		lat_extract_finish = np.min([northern_most_grid, lat_f - 1]) - lat_i + 1
		long_extract_start = np.max([western_most_grid, long_i]) - long_i
		long_extract_finish = np.min([eastern_most_grid, long_f - 1]) - long_i + 1

		# extract data needed from array and place it into the array for the specified polygon
		solar_resource[:, lat_fill_start:lat_fill_finish, long_fill_start:long_fill_finish] = solar_flux[:, lat_extract_start:lat_extract_finish, long_extract_start:long_extract_finish]

	#########
	# save new datasets as name of country

	np.save('{}/country_files/{}_solar-resource'.format(path, area_name), solar_resource)
	
	solar_resource = np.zeros(1) # reduce size of arrays so no memory error
	solar_flux = np.zeros(1)

	windspeed_resource = np.zeros((315576, lat_length, long_length))

	for (lat_i, lat_f), (long_i, long_f) in itertools.product(zip(lat_range[:-1], lat_range[1:]), zip(long_range[:-1], long_range[1:])):

		# open data files
		if (lat_f == 360):

			windspeed = np.load('{}/uv50m/all_years_grided/windspeed_{}-{}_{}-{}.npy'.format(path, lat_i, lat_f, long_i, long_f - 1))

		else:

			windspeed = np.load('{}/uv50m/all_years_grided/windspeed_{}-{}_{}-{}.npy'.format(path, lat_i, lat_f - 1, long_i, long_f - 1))


		# extract data from files
		# determine array locations to be filled
		lat_fill_start = np.max([southern_most_grid, lat_i]) - southern_most_grid
		lat_fill_finish = np.min([northern_most_grid, lat_f - 1]) - southern_most_grid + 1
		long_fill_start = np.max([western_most_grid, long_i]) - western_most_grid
		long_fill_finish = np.min([eastern_most_grid, long_f - 1]) - western_most_grid + 1

		# determine array locations to extract from
		lat_extract_start = np.max([southern_most_grid, lat_i]) - lat_i
		lat_extract_finish = np.min([northern_most_grid, lat_f - 1]) - lat_i + 1
		long_extract_start = np.max([western_most_grid, long_i]) - long_i
		long_extract_finish = np.min([eastern_most_grid, long_f - 1]) - long_i + 1

		# extract data needed from array and place it into the array for the specified polygon
		windspeed_resource[:, lat_fill_start:lat_fill_finish, long_fill_start:long_fill_finish] = windspeed[:, lat_extract_start:lat_extract_finish, long_extract_start:long_extract_finish]


	#########
	# save new datasets as name of country

	np.save('{}/country_files/{}_windspeed-resource'.format(path, area_name), windspeed_resource)

	windspeed_resource = np.zeros(1)
	windspeed = np.zeros(1)

	windCF_resource = np.zeros((315576, lat_length, long_length))

	for (lat_i, lat_f), (long_i, long_f) in itertools.product(zip(lat_range[:-1], lat_range[1:]), zip(long_range[:-1], long_range[1:])):

		# open data files
		if (lat_f == 360):

			windCF = np.load('{}/uv50m/all_years_grided/windCF_uci-3_ur-15_uco-25_{}-{}_{}-{}.npy'.format(path, lat_i, lat_f + 1, long_i, long_f))

		else:

			windCF = np.load('{}/uv50m/all_years_grided/windCF_uci-3_ur-15_uco-25_{}-{}_{}-{}.npy'.format(path, lat_i, lat_f, long_i, long_f))

		# extract data from files
		# determine array locations to be filled
		lat_fill_start = np.max([southern_most_grid, lat_i]) - southern_most_grid
		lat_fill_finish = np.min([northern_most_grid, lat_f - 1]) - southern_most_grid + 1
		long_fill_start = np.max([western_most_grid, long_i]) - western_most_grid
		long_fill_finish = np.min([eastern_most_grid, long_f - 1]) - western_most_grid + 1

		# determine array locations to extract from
		lat_extract_start = np.max([southern_most_grid, lat_i]) - lat_i
		lat_extract_finish = np.min([northern_most_grid, lat_f - 1]) - lat_i + 1
		long_extract_start = np.max([western_most_grid, long_i]) - long_i
		long_extract_finish = np.min([eastern_most_grid, long_f - 1]) - long_i + 1

		# extract data needed from array and place it into the array for the specified polygon
		windCF_resource[:, lat_fill_start:lat_fill_finish, long_fill_start:long_fill_finish] = windCF[:, lat_extract_start:lat_extract_finish, long_extract_start:long_extract_finish]


	#########
	# save new datasets as name of country

	np.save('{}/country_files/{}_windCF-resource'.format(path, area_name), windCF_resource)
	
	windCF_resource = np.zeros(1)
	windCF = np.zeros(1)


def main():

	path = '/lustre/data/mshaner/merra2'
	shapefile = gpd.GeoDataFrame.from_file('{}/country_mask_files/ne_110m_admin_0_countries.shp'.format(path))
	country_names = shapefile.geounit

	multipolygon_country_indexes = np.array([1, 4, 6, 8, 10, 17, 27, 29, 30, 43, 53, 55, 57, 
		64, 72, 79, 82, 111, 118, 120, 121, 125, 126, 135, 142, 162, 168, 172])
		
		# 1 = Angola (2), 4 = Argentina (2), 6 = Antarctica(8), 8 = Australia (2), 10 = Azerbaijan (2),
		# 17 = The Bahamas (3), 27 = Canada (30), 29 = Chile (2), 30 = China (2), 43 = Denmark (2)
		# 53 = Fiji (3), 55 = France (3), 57 = United Kingdom (2), 64 = Greece (2), 72 = Indonesia (13),
		# 79 = Italy (3), 82 = Japan (3), 111 = Malaysia (2), 118 = Norway (4), 120 = New Zealand (2),
		# 121 = Oman (2), 125 = Philippines (7), 126 = Papua New Guinea (4), 135 = Russia (13),
		# 142 = Solomon Islands (5), 162 = Turkey (2), 168 = United States of America (10), 172 = Vanuatu (2)
	
	counter = 0

	# for i in range(country_names.size):

	# 	if i in multipolygon_country_indexes:

	# 		# hard code for each country of interest
	# 		# countries and polygons of interest are (all were figured out by area of polygon):
	# 		# Angola, polygon 1 = mainland; Argentina, polygon 2 = mainland; Australia, polygon 2 = mainland; Azerbaijan, polygon 2, mainland;
	# 		# Canada, polygon 11 = mainland; Chile, polygon 2 = mainland; China, polygon 2 = mainland;
	# 		# Denmark, polygon 2; France, polygon 3 = mainland; United Kingdom, polygon 2 = mainland;
	# 		# Greece, polygon 2 = mainland; Italy, polygon 3 = mainland;
	# 		# Japan, polygon 2; Norway, polygon 1; Oman, polygon 1;
	# 		# Russia, polygon 10; Turkey, polygon 1; CONUS, polygon 6; Alaska, polygon 10

	# 		# countries omitted: Antartica, The Bahamas, Fiji, Indonesia, Malaysia, New Zealand, Philippines,
	# 		# Papua New Guinea, Solomon Islands, Vanuatu

	# 		omitted = ['Antarctica', 'The Bahamas', 'Fiji', 'Indonesia', 'Malaysia', 'New Zealand', \
	# 			'Philippines', 'Papua New Guinea', 'Solomon Islands', 'Vanuatu']

	# 		multi = [['Angola', 0], ['Argentina', 1], ['Australia', 1], ['Azerbaijan', 1], \
	# 			['Canada', 10], ['Chile', 1], ['China', 1], ['Denmark', 1], ['France', 2], \
	# 			['United Kingdom', 1], ['Greece', 1], ['Italy', 2], ['Japan', 1], \
	# 			['Norway', 0], ['Oman', 0], ['Russia', 9], ['Turkey', 0], ['United States of America', 5]]

			

	# 		if country_names[i] in omitted:

	# 			pass

	# 		else:
				
	# 			country = country_names[i]
	# 			polygon_ = shapefile.geometry[i][multi[counter][1]]
	# 			latrange, longrange, smg, nmg, wmg, emg = Country_boxes(polygon_, country)
	# 			Polygon_2_datafile(country, latrange, longrange, smg, nmg, wmg, emg)

	# 			counter += 1

	# 	else: # countries defined by a single polygon

	# 		country = country_names[i]
	# 		polygon_ = shapefile.geometry[i]
	# 		latrange, longrange, smg, nmg, wmg, emg = Country_boxes(polygon_, country)
	# 		Polygon_2_datafile(country, latrange, longrange, smg, nmg, wmg, emg)


	for i in [168]: # do USA

		country = country_names[i]
		polygon_ = shapefile.geometry[i][5]
		latrange, longrange, smg, nmg, wmg, emg = Country_boxes(polygon_, country)
		Polygon_2_datafile(country, latrange, longrange, smg, nmg, wmg, emg)



if __name__ == '__main__':
	main()

