import numpy as np
import pandas as pd
import general_reliability_functions_real_demand as grfrd

def main():

	battery_size = np.round((np.arange(0,24.1,1) / 24),2) # storage size in days of demand, later converted to hours, etc.
	# battery_size = np.arange(1,31)

	SF = np.arange(0,1.01,0.05) # solar fraction of energy production
	overbuild = [np.arange(0.1,5.1,0.1), np.arange(5.0, 30.1, 0.5)]
	overbuild = np.round(np.array([j for list in overbuild for j in list]), 2)
	path = '/lustre/data/mshaner/CAISO_Regionalization' # file system common path
	region = 'California'
	filename_start = 'CA_area-weighted-mean_CAISO-demand' # start to the file names

	# import solar and wind data
	dates_36yrs = pd.date_range('1980-01-01 00:00:00', '2015-12-31 23:00:00', freq='H')
	print '1'
	CF = {'CF_solar': np.load('{}/{}_CFsolar_area-weighted-mean.npy'.format(path, region)), 
		'CF_wind': np.load('{}/{}_CFwind_area-weighted-mean.npy'.format(path, region))}
	print '2'
	CF_df = pd.DataFrame(CF, index = dates_36yrs)
	print '3'
	
	demand = pd.read_csv('{}/CAISO_demand_2002-2014_FERC714.csv'.format(path), index_col=0) * 10**6 # W
	print '4'
	start_date = demand.index[0]
	end_date = demand.index[-1]
	CF_df_truncated = CF_df.truncate(start_date, end_date)

	# run battery cycling for all permutations of cases of battery size, SF and overbuild
	
	total_hours = demand.size # calculate total number of hours.  This should be identical for wind and solar

	for ob in overbuild:
		
		pwr_avg = demand.mean().values[0] * ob # W, calculate the mean power production 
		# based on the mean demand and overbuild

		# calculate wind (wc) and solar (sc) capacities and save
		wc, sc = grfrd.capacity_calc(CF_df_truncated['CF_wind'].values, 
			CF_df_truncated['CF_solar'].values, SF, pwr_avg, total_hours)

		np.save('{}/{}_wind_capacity_overbuild-{}'.format(path, filename_start, ob), wc)
		np.save('{}/{}_solar_capacity_overbuild-{}'.format(path, filename_start, ob), sc)

		for bs in range(battery_size.size):

			batsize = battery_size[bs] * demand.mean().values[0] * 24 # conversion to Wh

			# run the system for one set of parameters and save the data
			# br is binary reliability which counts yes or no whether demand was met that hour
			# brs is the binary reliability for all time; it is a single value that represents all hours
			# pr is power reliability which counts the amount of power unment for each hour
			# prs is power reliability for all time; it sums all power unmet and divides by total power demanded
			# bat_state is the hourly state of the battery
			br, brs, pr, prs, bat_state = grfrd.reliability_calc(CF_df_truncated['CF_wind'].values,
				wc, CF_df_truncated['CF_solar'].values, sc, demand.values.T[0], batsize, SF, total_hours)

			np.save('{}/{}_binary_reliability_SF_batsize-{}-days_overbuild-{}'.format(path, 
				filename_start, battery_size[bs], ob), brs)
			np.save('{}/{}_hourly_binary_reliability_SF_batsize-{}-days_overbuild-{}'.format(path, 
				filename_start, battery_size[bs], ob), br)
			np.save('{}/{}_power_reliability_SF_batsize-{}-days_overbuild-{}'.format(path, 
				filename_start, battery_size[bs], ob), prs)
			np.save('{}/{}_hourly_power_reliability_SF_batsize-{}-days_overbuild-{}'.format(path, 
				filename_start, battery_size[bs], ob), pr)
			np.save('{}/{}_battery_state_SF_batsize-{}-days_overbuild-{}'.format(path, 
				filename_start, battery_size[bs], ob), bat_state)

	np.save('{}/{}_battery_size'.format(path, filename_start), battery_size)


if __name__ == '__main__':
	main()