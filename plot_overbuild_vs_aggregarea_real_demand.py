import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pyproj as pp
import scipy.stats as stats
import seaborn as sns
import shapely as spy
import os


def polygon_area_calc(inproj, outproj, polygon, correction):

	# find area of polygon
	input_projection = pp.Proj(init = '{}'.format(inproj))
	
	output_projection = pp.Proj(init = '{}'.format(outproj))

	# collect exterior points of polygon
	[ext_x, ext_y] = polygon.exterior.coords.xy

	# initialize list
	points = []

	# transform the polygon exterior points from the initial coordinate system into the
	# desired coordinate system and add to list
	for i in range(len(ext_y)):
		(x, y) = pp.transform(input_projection, output_projection, ext_x[i], ext_y[i])
		points.append([spy.geometry.Point(x, y).x, spy.geometry.Point(x, y).y])

	# create new geometry in new coordinate system
	areapoly = spy.geometry.Polygon(points)

	# calculate area in squate km; correction is to remedy any inaccuracy in the chosen coordinate
	# system; 10^6 converts from sq m to sq km
	area = areapoly.area * correction / 10**6

	return area 


def main():	

	country = 'USA'
	path = '/lustre/data/mshaner/merra2/country_files/{}'.format(country)
	sfpath = '/lustre/data/mshaner/merra2'

	overbuild_target = 1.5
	overbuild = [np.arange(0.1,5.1,0.1), np.arange(5.0, 30.1, 0.5)]
	overbuild = np.round(np.array([j for list in overbuild for j in list]), 2)
	batsize = [0.50] # days of storage
	SF = np.arange(0,1.01,0.05) # solar fraction of energy production

	# land areas of states and CONUS in square km
	land_area = {'Texas': 676587, 'California': 403466, 'Montana': 376962, 'New Mexico': 314161, \
		'Arizona': 294207, 'Nevada': 284332, 'Colorado': 268431, 'Oregon': 248608, 'Wyoming': 251470, \
		'Michigan': 146435, 'Minnesota': 206232, 'Utah': 212818, 'Idaho': 214045, 'Kansas': 211754, \
		'Nebraska': 198974, 'South Dakota': 196350, 'Washington': 172119, 'North Dakota': 178711, \
		'Oklahoma': 177660, 'Missouri': 178040, 'Florida': 138887, 'Wisconsin': 140268, \
		'Georgia': 148959, 'Illinois': 173793, 'Iowa': 144669, 'New York': 122057, \
		'North Carolina': 125920, 'Arkansas': 134771, 'Alabama': 131171, 'Louisiana': 111898, 'Mississippi': 121531, \
		'Pennsylvania': 115883, 'Ohio': 105829, 'Virginia': 102279, 'Tennessee': 106798, \
		'Kentucky': 102269, 'Indiana': 92789, 'Maine': 79883, 'South Carolina': 77857, \
		'West Virginia': 62259, 'Maryland': 25142, 'Massachusetts': 20202, 'Vermont': 23871, \
		'New Hampshire': 23187, 'New Jersey': 19047, 'Connecticut': 12542, 'Delaware': 5047, \
		'United States of America': 7653004} # 'Rhode Island': 2678,

	#######
	# Given an overbuild and battery size, we will find the fraction of demand satisfied by solar and wind
	# for each region and corresponding area.  Then we will regress demand satisfied by log_10(area) for
	# each solar fraction.  Then we can make a contour plot of demand satisfied as a function of solar
	# fraction and area (on a log scale)
	#######	

	# NERC Regions
	shapefile = gpd.GeoDataFrame.from_file('{}/country_mask_files/NERC_regions/NERC_regions.shp'
		.format(sfpath))
	regions = shapefile.Region
	NERC_results = np.ones((len(regions), SF.size, 2)) # 2 for storing overbuild quantity and area

	# input projection and output projection for calculating area of states
	# native coordinate system is WGS84, EPSG:4326
	inproj = 'epsg:4326'
	# output projection is North American Lambert Conformal Conic (ESRI:102009)
	# this projection underestimates the state area by ~10%, would need to use a higher
	# definition projection to get higher accuracy
	outproj = 'esri:102009'
	# output coordinate system underestimates area by ~10%
	correction = 1 / 0.9 

	j = 0
	for region in regions:

		polygon = shapefile.geometry[j]
		filename_start = '{}_area-weighted-mean_real-demand'.format(region)

		# check if path exists
		if os.path.exists('{}/{}_power_reliability_SF_batsize-{}'
			'-days_overbuild-{}.npy'.format(path, filename_start, batsize[0], overbuild_target)):
			
			# import data
			reliable_array = np.load('{}/{}_power_reliability_SF_batsize-{}'
				'-days_overbuild-{}.npy'.format(path, filename_start, batsize[0], overbuild_target))

			# calculate and collect region area and associated reliability
			NERC_results[j, :, 1] = polygon_area_calc(inproj, outproj, polygon, correction)
			NERC_results[j, :, 0] = reliable_array

			print region, NERC_results[j,0,:]

		j+=1

			

######
	# USA States and CONUS
	
	regions = land_area.keys()
	statesnCONUS_results = np.ones((len(regions), SF.size, 2)) # 2 for storing overbuild quantity and area
	
	j = 0
	for region in regions:

		filename_start = '{}_area-weighted-mean_real-demand'.format(region)

		# check if path exists
		if os.path.exists('{}/{}_power_reliability_SF_batsize-{}-days_'
			'overbuild-{}.npy'.format(path, filename_start, batsize[0], overbuild_target)):
			
			reliable_array = np.load('{}/{}_power_reliability_SF_batsize-{}-days_'
				'overbuild-{}.npy'.format(path, filename_start, batsize[0], overbuild_target))


			# calculate and collect region area and associated reliability
			statesnCONUS_results[j, :, 1] = land_area[region]
			statesnCONUS_results[j, :, 0] = reliable_array

			print region, statesnCONUS_results[j,0,:]

		else:
			print '{} path does not exist'.format(region)
		
		j+=1


	#######
	# Combine all results into one array
	all_reliability_results = np.concatenate((NERC_results, statesnCONUS_results), axis = 0)

	all_reliability_results[:,:,1] = np.log10(all_reliability_results[:,:,1])

	slopes = np.zeros(SF.size)
	intercepts = np.zeros(SF.size)
	r_values = np.zeros(SF.size)
	p_values = np.zeros(SF.size)
	std_errs = np.zeros(SF.size)

	areas = np.array([10**3, 5*10**3, 10**4, 5*10**4, 10**5, 5*10**5, 10**6, 5*10**6, 10**7])

	# axis 0 corresponds to areas and axis 1 corresponds to SFs
	reliabilities2plot = np.zeros((all_reliability_results.shape[1], areas.size))

	i = 0
	for sf in SF:

		slopes[i], intercepts[i], r_values[i], p_values[i], std_errs[i] = \
			stats.linregress(all_reliability_results[:,i,1], all_reliability_results[:,i,0])

		k = 0
		for area in areas:

			# take regression values and make array using areas for plotting
			reliabilities2plot[i, k] = slopes[i] * np.log10(area) + intercepts[i]

			k+=1
		i+=1


	sns.set_style('ticks')
	sns.set_palette('colorblind')
	contour_labels = np.arange(np.round(reliabilities2plot.min(), 2), np.round(reliabilities2plot.max(), 2), 0.01)
	fig = plt.figure(figsize = (12,8))
	ax1 = fig.add_subplot(111)
	cp = ax1.contourf(areas, SF * 100, reliabilities2plot, levels = np.arange(0.4,1.01,0.01),
		cmap = 'inferno', vmin = 0.4, vmax = 1.0)
	cp2 = ax1.contour(cp, levels = [0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 
		0.9, 0.95, 0.99], colors = 'black')
	# plt.clabel(cp2, inline = True, colors = 'black', fontsize = 14)
	cbar_ax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
	cbar = plt.colorbar(cp, cax = cbar_ax)
	cbar.set_ticks(np.arange(0.4,1.01,0.1))
	cbar.ax.set_ylabel('Fraction of Demand Met by Solar and Wind', fontsize = 16)
	cbar.ax.tick_params(labelsize = 14)
	ax1.set_xlabel('Area of resource aggregation (km${^2}$)', fontsize = 20)
	ax1.set_yticks([0, 25, 50, 75, 100])
	ax1.set_yticklabels(['100% Wind', '25% Solar\n75% Wind', '50% Solar\n50% Wind', 
		'75% Solar\n25% Wind', '100% Solar'], fontsize = 20)
	ax1.set_xscale('log')
	ax1.tick_params(direction = 'out', colors = 'black', axis='both', labelsize = 20, width = 2)
	ax1.yaxis.set_ticks_position('left')
	ax1.xaxis.set_ticks_position('bottom')
	fig.subplots_adjust(right=0.8)

	tick_labels = ['CONUS', 'CA', 'NY', 'WECC', 'NH', 'DC']
	ticks = [land_area['United States of America'], land_area['California'], land_area['New York'], \
		NERC_results[0,0,1], land_area['New Hampshire'], land_area['Delaware']]
	ax2 = ax1.twiny()
	ax2.set_xlim(ax1.get_xlim())
	ax2.set_xscale('log')
	ax2.tick_params(axis = 'x', which = 'minor', top = 'off')
	ax2.tick_params(axis = 'x', which = 'major', width = 2)
	ax2.set_xticks(ticks)
	ax2.set_xticklabels(tick_labels, fontsize = 20, rotation = 'vertical')
	
	plt.tight_layout(rect = (0, 0, 0.85, 1))
	
	
	path = '/lustre/data/mshaner/merra2/country_files/USA'
	plt.savefig('{}/Demand-met_area-aggregation_SF_batsize-{}_overbuild-{}_heatmap.svg'.format(path, 
		batsize[0], overbuild_target), format = 'svg', dpi=1000)

	# plt.show()


if __name__ == '__main__':
	main()