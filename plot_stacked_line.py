import numpy as np 
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import sys
# from scipy import signal
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
path_input = dir_path + '/input_data'
path_output = dir_path + '/output_data'
path_figure = dir_path + '/figures'
country = 'United States of America'
filename_start = '{}_area-weighted-mean_real-demand'.format(country)

def time_shift(array, hourstoshift):

	for i in range(hourstoshift):

		row = array.iloc[0] # take stock of first row
		array = array.shift(-1) # remove first entry and shift all data up one row
		array.iloc[-1] = row # put old first row as last row

	
	array = array.values
	array = np.array([f for values in array for f in values])

	return array

def stat_median(groupby_dataframe):

	output = groupby_dataframe.median()

	return output

def stat_quantile(groupby_dataframe, quantile):

	output = groupby_dataframe.quantile(q = quantile)

	return output

def peakdet(v, delta, x = None):
    """
    Converted from MATLAB script at http://billauer.co.il/peakdet.html
    
    Returns two arrays
    
    function [maxtab, mintab]=peakdet(v, delta, x)
    %PEAKDET Detect peaks in a vector
    %        [MAXTAB, MINTAB] = PEAKDET(V, DELTA) finds the local
    %        maxima and minima ("peaks") in the vector V.
    %        MAXTAB and MINTAB consists of two columns. Column 1
    %        contains indices in V, and column 2 the found values.
    %      
    %        With [MAXTAB, MINTAB] = PEAKDET(V, DELTA, X) the indices
    %        in MAXTAB and MINTAB are replaced with the corresponding
    %        X-values.
    %
    %        A point is considered a maximum peak if it has the maximal
    %        value, and was preceded (to the left) by a value lower by
    %        DELTA.
    
    % Eli Billauer, 3.4.05 (Explicitly not copyrighted).
    % This function is released to the public domain; Any use is allowed.
    
    """
    maxtab = []
    mintab = []
       
    if x is None:
        x = np.arange(len(v))
    
    v = np.asarray(v)
    
    if len(v) != len(x):
        sys.exit('Input vectors v and x must have same length')
    
    if not np.isscalar(delta):
        sys.exit('Input argument delta must be a scalar')
    
    if delta <= 0:
        sys.exit('Input argument delta must be positive')
    
    mn, mx = np.Inf, -np.Inf
    mnpos, mxpos = np.NaN, np.NaN
    
    lookformax = True
    
    for i in np.arange(len(v)):
        this = v[i]
        if this > mx:
            mx = this
            mxpos = x[i]
        if this < mn:
            mn = this
            mnpos = x[i]
        
        if lookformax:
            if this < mx-delta:
                maxtab.append((mxpos, mx))
                mn = this
                mnpos = x[i]
                lookformax = False
        else:
            if this > mn+delta:
                mintab.append((mnpos, mn))
                mx = this
                mxpos = x[i]
                lookformax = True

    return np.array(maxtab), np.array(mintab)

def stacked_line(CF_wind, CF_solar, demand):

	dates_hourly = pd.date_range('1980-01-01 00:00:00', '2015-12-31 23:00:00', freq='H')
	dates_daily = pd.date_range('1980-01-01 00:00:00', '2015-12-31 23:00:00', freq='D')

	##############

	normalized_solar = CF_solar / CF_solar.mean()
	normalized_wind = CF_wind / CF_wind.mean()
	normalized_demand = demand / demand.mean()

	normalized_solar_df = pd.DataFrame(normalized_solar.transpose(), index = dates_hourly, columns = [1])
	normalized_wind_df = pd.DataFrame(normalized_wind.transpose(), index = dates_hourly, columns = [1])
	normalized_demand_df = pd.DataFrame(normalized_demand.transpose(), index = dates_hourly, columns = [1])

	solar_df_daily_gp = pd.groupby(normalized_solar_df, lambda x: (x.year, x.month, x.day))
	wind_df_daily_gp = pd.groupby(normalized_wind_df, lambda x: (x.year, x.month, x.day))
	demand_df_daily_gp = pd.groupby(normalized_demand_df, lambda x: (x.year, x.month, x.day))	

	solar_daily_sum = solar_df_daily_gp.sum() / 24 # /24 to normalize to 1 cuz of daily sum
	wind_daily_sum= wind_df_daily_gp.sum() / 24
	demand_daily_sum = demand_df_daily_gp.sum() / 24

	solar_ds_df = pd.DataFrame(solar_daily_sum.values, index = dates_daily)
	wind_ds_df = pd.DataFrame(wind_daily_sum.values, index = dates_daily)
	demand_ds_df = pd.DataFrame(demand_daily_sum.values, index = dates_daily)

	solar_ds_gp = pd.groupby(solar_ds_df, lambda x: (x.month, x.day))
	wind_ds_gp = pd.groupby(wind_ds_df, lambda x: (x.month, x.day))
	demand_ds_gp = pd.groupby(demand_ds_df, lambda x: (x.month, x.day))

	solar_daily_median = time_shift(stat_median(solar_ds_gp), 0)
	solar_daily_fourth_quartile = time_shift(stat_quantile(solar_ds_gp, 1), 0)
	solar_daily_third_quartile = time_shift(stat_quantile(solar_ds_gp, 0.75), 0)
	solar_daily_first_quartile = time_shift(stat_quantile(solar_ds_gp, 0.25), 0)
	solar_daily_zeroth_quartile = time_shift(stat_quantile(solar_ds_gp, 0), 0)
	wind_daily_median = time_shift(stat_median(wind_ds_gp), 0)
	wind_daily_fourth_quartile = time_shift(stat_quantile(wind_ds_gp, 1), 0)
	wind_daily_third_quartile = time_shift(stat_quantile(wind_ds_gp, 0.75), 0)
	wind_daily_first_quartile = time_shift(stat_quantile(wind_ds_gp, 0.25), 0)
	wind_daily_zeroth_quartile = time_shift(stat_quantile(wind_ds_gp, 0), 0)

	demand2plot = demand_ds_gp.mean()

	###########
	sns.set_style('whitegrid')
	sns.set_palette('colorblind')

	########
	# plot monthly means
	months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
	fig = plt.figure()
	ax = fig.add_subplot(111)

	x_values = range(len(solar_daily_median))

	plt.plot(x_values, wind_daily_median, 'blue')
	plt.fill_between(x_values, wind_daily_zeroth_quartile, 
		wind_daily_fourth_quartile, alpha = 0.2, facecolor = 'blue')
	plt.fill_between(x_values, wind_daily_first_quartile, 
		wind_daily_third_quartile, alpha = 0.5, facecolor = 'blue')
	
	plt.plot(x_values, demand2plot, linewidth = 3, color = 'red')

	plt.plot(x_values, solar_daily_median, 'yellow')
	plt.fill_between(x_values, solar_daily_zeroth_quartile, 
		solar_daily_fourth_quartile, alpha = 0.2, facecolor = 'yellow')
	plt.fill_between(x_values, solar_daily_first_quartile, 
		solar_daily_third_quartile, alpha = 0.5, facecolor = 'yellow')

	ax.set_ylabel('Power Normalized by 36 Year Mean', fontsize = 16)
	ax.set_xlim(0,len(solar_daily_median))
	ax.set_xticks(np.arange(10, 360, 31))
	ax.set_xticklabels(months, fontsize = 14)
	ax.set_yticks(np.arange(0, 5, 1))
	ax.set_yticklabels(np.arange(0, 5, 1), fontsize = 14)
	#plt.title('Climatological Daily Mean Power Generation', fontsize = 18)
	plt.legend()
	ax.grid(False)
	#ax.set_rasterized(True)

	# plt.show()

	plt.savefig('{}\Climatological_daily_mean_real-demand_CONUS_area_weighted_solarnwind.svg'
		.format(path_figure), format = 'svg', dpi=1000)
	plt.close()


def stacked_line_winter_hourly(CF_wind, CF_solar, demand):

	dates_hourly = pd.date_range('1980-01-01 00:00:00', '2015-12-31 23:00:00', freq='H')

	##############
	normalized_solar = CF_solar / CF_solar.mean()
	normalized_wind = CF_wind / CF_wind.mean()
	normalized_demand = demand / demand.mean()

	normalized_solar_df = pd.DataFrame(normalized_solar.transpose(), index = dates_hourly, columns = [1])
	normalized_wind_df = pd.DataFrame(normalized_wind.transpose(), index = dates_hourly, columns = [1])
	normalized_demand_df = pd.DataFrame(normalized_demand.transpose(), index = dates_hourly, columns = [1])

	solar_df_daily_gp = pd.groupby(normalized_solar_df, lambda x: (x.year, x.month, x.day, x.hour))
	wind_df_daily_gp = pd.groupby(normalized_wind_df, lambda x: (x.year, x.month, x.day, x.hour))
	demand_df_daily_gp = pd.groupby(normalized_demand_df, lambda x: (x.year, x.month, x.day, x.hour))	

	solar_daily_sum = solar_df_daily_gp.sum()
	wind_daily_sum= wind_df_daily_gp.sum()
	demand_daily_sum = demand_df_daily_gp.sum()

	solar_ds_df = pd.DataFrame(solar_daily_sum.values, index = dates_hourly)
	wind_ds_df = pd.DataFrame(wind_daily_sum.values, index = dates_hourly)
	demand_ds_df = pd.DataFrame(demand_daily_sum.values, index = dates_hourly)

	# group by month
	solar_ds_gp_month = pd.groupby(solar_ds_df, lambda x: (x.month))
	wind_ds_gp_month = pd.groupby(wind_ds_df, lambda x: (x.month))
	demand_ds_gp_month = pd.groupby(demand_ds_df, lambda x: (x.month))

	# collect data for Dec, Jan, Feb as dataframes, join all data and then group by hour
	solar_ds_gp_winter = solar_ds_gp_month.get_group((12)).append(solar_ds_gp_month.get_group((1)))
	solar_ds_gp_winter.append(solar_ds_gp_month.get_group((2)))
	solar_ds_gp_winter_gp_hour = solar_ds_gp_winter.groupby(lambda x: (x.hour))

	wind_ds_gp_winter = wind_ds_gp_month.get_group((12)).append(wind_ds_gp_month.get_group((1)))
	wind_ds_gp_winter.append(wind_ds_gp_month.get_group((2)))
	wind_ds_gp_winter_gp_hour = wind_ds_gp_winter.groupby(lambda x: (x.hour))

	demand_ds_gp_winter = demand_ds_gp_month.get_group((12)).append(demand_ds_gp_month.get_group((1)))
	demand_ds_gp_winter.append(demand_ds_gp_month.get_group((2)))
	demand_ds_gp_winter_gp_hour = demand_ds_gp_winter.groupby(lambda x: (x.hour))

	# manually shift data to pacific standard time from UTC (- 7 hours)

	solar_daily_winter_median = time_shift(stat_median(solar_ds_gp_winter_gp_hour), 7)
	solar_daily_winter_fourth_quartile = time_shift(stat_quantile(solar_ds_gp_winter_gp_hour, 1), 7)
	solar_daily_winter_third_quartile = time_shift(stat_quantile(solar_ds_gp_winter_gp_hour, 0.75), 7)
	solar_daily_winter_first_quartile = time_shift(stat_quantile(solar_ds_gp_winter_gp_hour, 0.25), 7)
	solar_daily_winter_zeroth_quartile = time_shift(stat_quantile(solar_ds_gp_winter_gp_hour, 0), 7)
	wind_daily_winter_median = time_shift(stat_median(wind_ds_gp_winter_gp_hour), 7)
	wind_daily_winter_fourth_quartile = time_shift(stat_quantile(wind_ds_gp_winter_gp_hour, 1), 7)
	wind_daily_winter_third_quartile = time_shift(stat_quantile(wind_ds_gp_winter_gp_hour, 0.75), 7)
	wind_daily_winter_first_quartile = time_shift(stat_quantile(wind_ds_gp_winter_gp_hour, 0.25), 7)
	wind_daily_winter_zeroth_quartile = time_shift(stat_quantile(wind_ds_gp_winter_gp_hour, 0), 7)
	demand_daily_winter_median = time_shift(stat_median(demand_ds_gp_winter_gp_hour), 7)
	demand_daily_winter_fourth_quartile = time_shift(stat_quantile(demand_ds_gp_winter_gp_hour, 1), 7)
	demand_daily_winter_third_quartile = time_shift(stat_quantile(demand_ds_gp_winter_gp_hour, 0.75), 7)
	demand_daily_winter_first_quartile = time_shift(stat_quantile(demand_ds_gp_winter_gp_hour, 0.25), 7)
	demand_daily_winter_zeroth_quartile = time_shift(stat_quantile(demand_ds_gp_winter_gp_hour, 0), 7)


	###########
	sns.set_style('whitegrid')
	sns.set_palette('colorblind')


########
	# plot monthly means
	fig = plt.figure()
	ax = fig.add_subplot(111)

	x_values = range(len(wind_daily_winter_median))

	plt.plot(x_values, wind_daily_winter_median, 'blue')
	plt.fill_between(x_values, wind_daily_winter_zeroth_quartile, 
		wind_daily_winter_fourth_quartile, alpha = 0.2, facecolor = 'blue')
	plt.fill_between(x_values, wind_daily_winter_first_quartile, 
		wind_daily_winter_third_quartile, alpha = 0.5, facecolor = 'blue')
	
	plt.plot(x_values, demand_daily_winter_median, linewidth = 2, color ='red')
	plt.fill_between(x_values, demand_daily_winter_zeroth_quartile, 
		demand_daily_winter_fourth_quartile, alpha = 0.2, facecolor = 'red')
	plt.fill_between(x_values, demand_daily_winter_first_quartile, 
		demand_daily_winter_third_quartile, alpha = 0.5, facecolor = 'red')

	plt.plot(x_values, solar_daily_winter_median, 'yellow')
	plt.fill_between(x_values, solar_daily_winter_zeroth_quartile, 
		solar_daily_winter_fourth_quartile, alpha = 0.2, facecolor = 'yellow')
	plt.fill_between(x_values, solar_daily_winter_first_quartile, 
		solar_daily_winter_third_quartile, alpha = 0.5, facecolor = 'yellow')


	ax.set_ylabel('Power Normalized by 36 Year Mean', fontsize = 16)
	ax.set_xlabel('Hour of the Day (PST)', fontsize = 16)
	ax.set_xlim(0, 23)
	ax.set_xticks(np.arange(0, 24, 4))
	ax.set_xticklabels(np.arange(0, 24, 4), fontsize = 14)
	ax.set_yticks(np.arange(0, 5, 1))
	ax.set_yticklabels(np.arange(0, 5, 1), fontsize = 14)
	#plt.title('Winter (Dec, Jan, Feb) Climatological \n Hourly Mean Power Generation', fontsize = 18)
	plt.legend()
	ax.grid(False)
	#ax.set_rasterized(True)

	# plt.show()

	plt.savefig('{}\Climatological_hourly_mean_real-demand_winter_CONUS_area_weighted_solarnwind.svg'
		.format(path_figure), format = 'svg', dpi=1000)
	plt.close()


def stacked_line_summer_hourly(CF_wind, CF_solar, demand):

	dates_hourly = pd.date_range('1980-01-01 00:00:00', '2015-12-31 23:00:00', freq='H')

	##############
	normalized_solar = CF_solar / CF_solar.mean()
	normalized_wind = CF_wind / CF_wind.mean()
	normalized_demand = demand / demand.mean()

	normalized_solar_df = pd.DataFrame(normalized_solar.transpose(), index = dates_hourly, columns = [1])
	normalized_wind_df = pd.DataFrame(normalized_wind.transpose(), index = dates_hourly, columns = [1])
	normalized_demand_df = pd.DataFrame(normalized_demand.transpose(), index = dates_hourly, columns = [1])

	solar_df_daily_gp = pd.groupby(normalized_solar_df, lambda x: (x.year, x.month, x.day, x.hour))
	wind_df_daily_gp = pd.groupby(normalized_wind_df, lambda x: (x.year, x.month, x.day, x.hour))
	demand_df_daily_gp = pd.groupby(normalized_demand_df, lambda x: (x.year, x.month, x.day, x.hour))	

	solar_daily_sum = solar_df_daily_gp.sum()
	wind_daily_sum= wind_df_daily_gp.sum()
	demand_daily_sum = demand_df_daily_gp.sum()

	solar_ds_df = pd.DataFrame(solar_daily_sum.values, index = dates_hourly)
	wind_ds_df = pd.DataFrame(wind_daily_sum.values, index = dates_hourly)
	demand_ds_df = pd.DataFrame(demand_daily_sum.values, index = dates_hourly)

	# group by month
	solar_ds_gp_month = pd.groupby(solar_ds_df, lambda x: (x.month))
	wind_ds_gp_month = pd.groupby(wind_ds_df, lambda x: (x.month))
	demand_ds_gp_month = pd.groupby(demand_ds_df, lambda x: (x.month))

	# collect data for Dec, Jan, Feb as dataframes, join all data and then group by hour
	solar_ds_gp_summer = solar_ds_gp_month.get_group((6)).append(solar_ds_gp_month.get_group((7)))
	solar_ds_gp_summer.append(solar_ds_gp_month.get_group((8)))
	solar_ds_gp_summer_gp_hour = solar_ds_gp_summer.groupby(lambda x: (x.hour))

	wind_ds_gp_summer = wind_ds_gp_month.get_group((6)).append(wind_ds_gp_month.get_group((7)))
	wind_ds_gp_summer.append(wind_ds_gp_month.get_group((8)))
	wind_ds_gp_summer_gp_hour = wind_ds_gp_summer.groupby(lambda x: (x.hour))

	demand_ds_gp_summer = demand_ds_gp_month.get_group((6)).append(demand_ds_gp_month.get_group((7)))
	demand_ds_gp_summer.append(demand_ds_gp_month.get_group((8)))
	demand_ds_gp_summer_gp_hour = demand_ds_gp_summer.groupby(lambda x: (x.hour))

	# manually shift data to pacific standard time from UTC (- 7 hours)

	solar_daily_summer_median = time_shift(stat_median(solar_ds_gp_summer_gp_hour), 7)
	solar_daily_summer_fourth_quartile = time_shift(stat_quantile(solar_ds_gp_summer_gp_hour, 1), 7)
	solar_daily_summer_third_quartile = time_shift(stat_quantile(solar_ds_gp_summer_gp_hour, 0.75), 7)
	solar_daily_summer_first_quartile = time_shift(stat_quantile(solar_ds_gp_summer_gp_hour, 0.25), 7)
	solar_daily_summer_zeroth_quartile = time_shift(stat_quantile(solar_ds_gp_summer_gp_hour, 0), 7)
	wind_daily_summer_median = time_shift(stat_median(wind_ds_gp_summer_gp_hour), 7)
	wind_daily_summer_fourth_quartile = time_shift(stat_quantile(wind_ds_gp_summer_gp_hour, 1), 7)
	wind_daily_summer_third_quartile = time_shift(stat_quantile(wind_ds_gp_summer_gp_hour, 0.75), 7)
	wind_daily_summer_first_quartile = time_shift(stat_quantile(wind_ds_gp_summer_gp_hour, 0.25), 7)
	wind_daily_summer_zeroth_quartile = time_shift(stat_quantile(wind_ds_gp_summer_gp_hour, 0), 7)
	demand_daily_summer_median = time_shift(stat_median(demand_ds_gp_summer_gp_hour), 7)
	demand_daily_summer_fourth_quartile = time_shift(stat_quantile(demand_ds_gp_summer_gp_hour, 1), 7)
	demand_daily_summer_third_quartile = time_shift(stat_quantile(demand_ds_gp_summer_gp_hour, 0.75), 7)
	demand_daily_summer_first_quartile = time_shift(stat_quantile(demand_ds_gp_summer_gp_hour, 0.25), 7)
	demand_daily_summer_zeroth_quartile = time_shift(stat_quantile(demand_ds_gp_summer_gp_hour, 0), 7)


	###########
	sns.set_style('whitegrid')
	sns.set_palette('colorblind')

########
	# plot monthly means
	fig = plt.figure()
	ax = fig.add_subplot(111)

	x_values = range(len(wind_daily_summer_median))

	plt.plot(x_values, wind_daily_summer_median, 'blue')
	plt.fill_between(x_values, wind_daily_summer_zeroth_quartile, 
		wind_daily_summer_fourth_quartile, alpha = 0.2, facecolor = 'blue')
	plt.fill_between(x_values, wind_daily_summer_first_quartile, 
		wind_daily_summer_third_quartile, alpha = 0.5, facecolor = 'blue')
	
	plt.plot(x_values, demand_daily_summer_median, linewidth = 2, color = 'red')
	plt.fill_between(x_values, demand_daily_summer_zeroth_quartile, 
		demand_daily_summer_fourth_quartile, alpha = 0.2, facecolor = 'red')
	plt.fill_between(x_values, demand_daily_summer_first_quartile, 
		demand_daily_summer_third_quartile, alpha = 0.5, facecolor = 'red')

	plt.plot(x_values, solar_daily_summer_median, 'yellow')
	plt.fill_between(x_values, solar_daily_summer_zeroth_quartile, 
		solar_daily_summer_fourth_quartile, alpha = 0.2, facecolor = 'yellow')
	plt.fill_between(x_values, solar_daily_summer_first_quartile, 
		solar_daily_summer_third_quartile, alpha = 0.5, facecolor = 'yellow')



	ax.set_ylabel('Power Normalized by 36 Year Mean', fontsize = 16)
	ax.set_xlabel('Hour of the Day (PST)', fontsize = 16)
	ax.set_xlim(0, 23)
	ax.set_xticks(np.arange(0, 24, 4))
	ax.set_xticklabels(np.arange(0, 24, 4), fontsize = 14)
	ax.set_yticks(np.arange(0, 5, 1))
	ax.set_yticklabels(np.arange(0, 5, 1), fontsize = 14)
	#plt.title('Summer (Jun, Jul, Aug) Climatological \n Hourly Mean Power Generation', fontsize = 18)
	plt.legend()
	ax.grid(False)
	#ax.set_rasterized(True)

	# plt.show()

	plt.savefig('{}\Climatological_hourly_mean_real-demand_summer_CONUS_area_weighted_solarnwind.svg'
		.format(path_figure), format = 'svg', dpi=1000)
	plt.close()


if __name__ == '__main__':

#   # import data
#	path_input = 'D:\\M\\Shaner2018\\input_data'
#	path_output = 'D:\\M\\Shaner2018\\figures'
#	# country_folder = 'USA' # file system folder name for the country of interest
#	country = 'United States of America'
#	filename_start = '{}_area-weighted-mean_real-demand'.format(country) # start to the file names 
        
   # import solar and wind data
	demand = np.load('{}/conus_real_demand.npy'.format(path_input)) * 10**6 # W
	CF_solar = np.load('{}/{}_CFsolar_area-weighted-mean.npy'.format(path_input, country))
	CF_wind = np.load('{}/{}_CFwind_area-weighted-mean.npy'.format(path_input, country))
    
	stacked_line(CF_wind, CF_solar, demand)
	stacked_line_winter_hourly(CF_wind, CF_solar, demand)
	stacked_line_summer_hourly(CF_wind, CF_solar, demand)



