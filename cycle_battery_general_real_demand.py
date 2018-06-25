import general_reliability_functions_real_demand as grfrd
import numpy as np
import os 

dir_path = os.path.dirname(os.path.realpath(__file__))
path_input = dir_path + '/input_data'
path_output = dir_path + '/output_data'
country = 'United States of America'
filename_start = '{}_area-weighted-mean_real-demand'.format(country) # start to the file names

def main():

	# battery_size = np.array([0., round(1/3.,2), 1., 7., 30.]) # storage size in days of demand, later converted to hours, etc.
	# battery_size = np.arange(31,33)
    
	battery_size = np.array([0., 0.5, 4., 32.])

	# SF = np.arange(0,1.01,0.05) # solar fraction of energy production
	SF = np.array([0., 0.25, 0.5, 0.75, 1.])    

#	overbuild = [np.arange(0.1,5.1,0.1), np.arange(5.0, 30.1, 0.5)]
#	overbuild = np.round(np.array([j for list in overbuild for j in list]), 2)
		
	overbuild = np.arange(0.1,4.1,0.1)
    
	# run battery cycling for all permutations of cases of battery size, SF and overbuild
	
	total_hours = CF_wind.size # calculate total number of hours.  This should be identical for wind and solar

	for ob in overbuild:
		
		pwr_avg = demand.mean() * ob # W, calculate the mean power production 
		# based on the mean demand and overbuild

		# calculate wind (wc) and solar (sc) capacities and save
		wc, sc = grfrd.capacity_calc(CF_wind, CF_solar, SF, pwr_avg, total_hours)

		np.save('{}/{}_wind_capacity_overbuild-{}'.format(path_output, filename_start, ob), wc)
		np.save('{}/{}_solar_capacity_overbuild-{}'.format(path_output, filename_start, ob), sc)

		for bs in range(battery_size.size):

			batsize = battery_size[bs] * demand.mean() * 24 # conversion to Wh

			# run the system for one set of parameters and save the data
			# br is binary reliability which counts yes or no whether demand was met that hour
			# brs is the binary reliability for all time; it is a single value that represents all hours
			# pr is power reliability which counts the amount of power unment for each hour
			# prs is power reliability for all time; it sums all power unmet and divides by total power demanded
			# bat_state is the hourly state of the battery
			br, brs, pr, prs, bat_state = grfrd.reliability_calc(CF_wind, wc, CF_solar, sc, 
				demand, batsize, SF, total_hours)

			np.save('{}/{}_binary_reliability_SF_batsize-{}-days_overbuild-{}'.format(path_output, 
				filename_start, battery_size[bs], ob), brs)
			np.save('{}/{}_hourly_binary_reliability_SF_batsize-{}-days_overbuild-{}'.format(path_output, 
				filename_start, battery_size[bs], ob), br)
			np.save('{}/{}_power_reliability_SF_batsize-{}-days_overbuild-{}'.format(path_output, 
				filename_start, battery_size[bs], ob), prs)
			np.save('{}/{}_hourly_power_reliability_SF_batsize-{}-days_overbuild-{}'.format(path_output, 
				filename_start, battery_size[bs], ob), pr)
			np.save('{}/{}_battery_state_SF_batsize-{}-days_overbuild-{}'.format(path_output, 
				filename_start, battery_size[bs], ob), bat_state)

	np.save('{}/{}_battery_size'.format(path_output, filename_start), battery_size)


if __name__ == '__main__':
    
	demand = np.load('{}/conus_real_demand.npy'.format(path_input)) * 10**6 # W 
       	# import solar and wind data
	CF_solar = np.load('{}/{}_CFsolar_area-weighted-mean.npy'.format(path_input, country))

	CF_wind = np.load('{}/{}_CFwind_area-weighted-mean.npy'.format(path_input, country))
    
	main()