import numpy as np 
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
path_input = dir_path + '/input_data'
path_output = dir_path + '/output_data'
path_figure = dir_path + '/figures'
region = 'United States of America'
filename_start = '{}_area-weighted-mean_real-demand'.format(region)

SF = [0.75]
overbuild = [1.0, 1.5]
batsize = [0.00, 0.50] # days
SF_array = np.array([0, 0.25, 0.5, 0.75, 1.]) # solar fraction of energy production

demand = np.load('{}/conus_real_demand.npy'.format(path_input)) * 10**6 # W

######
# Common arrays and values
#country = 'USA'
#path = '/lustre/data/mshaner/merra2/country_files/{}'.format(country)
#region = 'United States of America'
#filename_start = '{}_area-weighted-mean_real-demand'.format(region)
#demand_path = '/lustre/data/mshaner/merra2/EIA_demand_files'
#demand = np.load('{}/conus_real_demand.npy'.format(demand_path)) * 10**6 # W
#
#batsize = [0.00, 0.50] # days of storage
#overbuild = [1.0, 1.5] # overbuild 
#SF = [0.75]
#SF_array = np.arange(0,1.01,0.05) # solar fraction of energy production

sns.set_style('whitegrid')

for bs in range(len(batsize)):
	for ob in range(len(overbuild)):

		reliable_array = np.load('{}/{}_hourly_power_reliability_SF_batsize-{}-days'
			'_overbuild-{}.npy'.format(path_output, filename_start, batsize[bs], overbuild[ob]))
	
		dates_hourly = pd.date_range('1980-01-01 00:00:00', '2015-12-31 23:00:00', freq='H')
		dates_daily = pd.date_range('1980-01-01', '2015-12-31', freq = 'D')
		index = dates_daily.strftime('%m-%d')
		years = dates_daily.year

		sf_index = np.where(SF_array == SF[0])
		rel_array_sf = reliable_array[sf_index, :].squeeze()
		reliability = 1 - rel_array_sf.sum() / demand.sum()
		rel_array_sf = rel_array_sf

		reliable_df = pd.DataFrame(rel_array_sf, index = dates_hourly, columns = [1])
		demand_df = pd.DataFrame(demand, index = dates_hourly, columns = [1])

		reliable_df_gb = pd.groupby(reliable_df, lambda x: (x.year, x.month, x.day)).sum()
		demand_df_gb = pd.groupby(demand_df, lambda x: (x.year, x.month, x.day)).sum()

		daily_unmet = 1 - reliable_df_gb.values / demand_df_gb.values
		daily_unmet_df = pd.DataFrame(np.array([daily_unmet.squeeze(), index, years]).T, 
			index = dates_daily, columns = [SF[0], 'index', 'years'])
		daily_unmet_df = daily_unmet_df[~((daily_unmet_df.index.month == 2) & (daily_unmet_df.index.day == 29))]



		# reliable_df_gb = pd.groupby(reliable_df, lambda x: (x.month, x.day, x.hour))
		# median = reliable_df_gb.median()
		# minimum = reliable_df_gb.quantile(q=0).astype('float')
		# maximum = reliable_df_gb.quantile(q=1).astype('float')
		# first_quantile = reliable_df_gb.quantile(q=0.25).astype('float')
		# third_quantile = reliable_df_gb.quantile(q=0.75).astype('float')


		########
		# plot monthly means
		# months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
		# fig = plt.figure()
		# ax = fig.add_subplot(111)

		# x_values = range(len(median))

		# plt.plot(x_values, median, 'k-')
		# plt.fill_between(x_values, minimum, maximum, alpha = 0.2, facecolor = 'black')
		# plt.fill_between(x_values, first_quantile, third_quantile, alpha = 0.5, facecolor = 'black')

		# ax.set_ylabel('Unmet Demand (Fraction of demand)', fontsize = 16)
		# ax.set_xlim(0,len(median))
		# ax.set_xticks(np.arange(10, 360, 31)*24)
		# ax.set_xticklabels(months, fontsize = 14)
		# ax.set_yticks(np.arange(0, 1.01, 0.25))
		# ax.set_yticklabels(np.arange(0, 1.01, 0.25), fontsize = 14)
		# plt.legend()
		# ax.grid(False)



		df_pivot = daily_unmet_df.pivot(index = 'index', columns = 'years', values = SF[0])
		df_pivot = df_pivot.fillna(value=0)

		data2plot = df_pivot.values.astype('float')
		data2plot[data2plot==0] = np.nan
		data2plot = np.ma.masked_where(np.isnan(data2plot), data2plot)

		x = np.arange(1,367)
		y = np.arange(1980, 2016)
		pcm = plt.pcolormesh(x, y, data2plot.T, cmap = 'inferno', vmin = 0.3, vmax = 1)# rasterized = True)
		plt.xlim(1,366)
		plt.xticks((np.arange(1,13) * 31 - 20), ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 
			'Oct', 'Nov', 'Dec'], fontsize = 14)
		plt.yticks(fontsize = 14)
		plt.ylabel('Year', fontsize = 16)
		# cbar = plt.colorbar(pcm)
		# cbar.ax.set_ylabel('Fraction of Daily Demand Met', fontsize = 16)
		# cbar.ax.tick_params(labelsize = 14)
		# cbar.set_ticks(np.arange(0.3,1.1,0.1))
		plt.title('Reliability = {}%, Overbuild = {}, \nStorage size = {} hours,'
			' SF = {}'.format(np.round(reliability * 100, 2), overbuild[ob], batsize[bs]*24, SF[0]),
			fontsize = 16)

		print data2plot.min(), batsize[bs], overbuild[ob]

		# plt.show()

		plt.savefig('{}/Daily_demandmet_overbuild-{}_storagesize-{}hours_SF-{}_{}_inferno-colormap.svg'
		 	.format(path_figure, overbuild[ob], batsize[bs]*24, SF[0], region), format = 'svg', dpi=1000)
		plt.close()



