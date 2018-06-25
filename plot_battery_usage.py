import numpy as np 
import matplotlib.pyplot as plt
# import matplotlib.colors as colors
# import pandas as pd
import seaborn as sns
# import scipy.optimize as optimize
import os

######
# Common arrays and values
#country = 'USA'
#path = '/lustre/data/mshaner/merra2/country_files/{}'.format(country)

dir_path = os.path.dirname(os.path.realpath(__file__))
path_input = dir_path + '/input_data'
path_output = dir_path + '/output_data'
path_figure = dir_path + '/figures'
region = 'United States of America'
filename_start = '{}_area-weighted-mean_real-demand'.format(region)

# overbuild = [np.arange(0.1,5.1,0.1), np.arange(5.0, 30.1, 0.5)] # overbuild list
# overbuild = np.round(np.array([j for list in overbuild for j in list]), 2) # single continuous overbuild array
# SF = np.arange(0,1.01,0.05) # solar fraction of energy production
SF = np.array([0, 0.25, 0.5, 0.75, 1.])
SF2plot = SF
batsize = np.array([0, 0.5, 4., 32.])
overbuild = 1.0

######

# plot reliability vs capacity
def battery_usage_hours(SF2plot, batsize, overbuild):

	# set plot style and type; will be a 4 panel plot for 4 battery sizes (0, 8hrs, 1 day, 7 days)	
	# SF2plot = np.array([0, 0.25, 0.5, 0.75, 1])
	# batsize = np.round((np.arange(0,24.1,1) / 24),2)
	# batsize = np.arange(1,31)
	# overbuild = 1.0
    
    
	sns.set_style('ticks')
	# sns.set_palette('hls')
	f, ax = plt.subplots(2, sharex = True, figsize = (6, 8))

	colors = ['black', 'blue', 'red', 'purple', 'green']
	linestyle = ['solid', 'dashed', 'dashdot', 'dotted', 'dashed']
	legend_labels = ['100% Wind', '25% Solar \n75% Wind', '50% Solar \n50% Wind', \
		'75% Solar \n25% Wind', '100% Solar']

	# demand_path = '/lustre/data/mshaner/merra2/EIA_demand_files'
	demand = np.load('{}/conus_real_demand.npy'.format(path_input)) * 10**6 # W

	# make each panel plot
	i = 0
	for sf in SF2plot:

		cycles_per_year = np.zeros(batsize.size)
		extra_demand_met = np.zeros(batsize.size)

		reliability_no_storage = np.load('{}/{}_power_reliability_SF_batsize-{}-days'
			'_overbuild-{}.npy'.format(path_output, filename_start, 0.0, overbuild))

		for bs in range(batsize.size):

			reliability = np.load('{}/{}_power_reliability_SF_batsize-{}-days'
				'_overbuild-{}.npy'.format(path_output, filename_start, batsize[bs], overbuild))

			bat_capacity = demand.mean() * batsize[bs] * 24
			annual_demand = demand.sum() / 36

			SFindex = np.where(SF == sf)
			extra_demand_met[bs] = reliability[SFindex] - reliability_no_storage[SFindex]
			cycles_per_year[bs] = extra_demand_met[bs] * annual_demand / bat_capacity
		

		ax[0].plot(batsize * 24, cycles_per_year, color = colors[i], linestyle = linestyle[i],
			label = legend_labels[i])
		ax[0].set_xlim(0,24)
		ax[0].set_ylim(0,400)
		ax[0].tick_params(direction = 'in', colors = 'black', labelsize = 14)
		ax[0].legend(loc = 'upper right', frameon = True)

		ax[1].plot(batsize * 24, extra_demand_met * 100, color = colors[i], linestyle = linestyle[i])
		ax[1].set_xlim(0,24)
		ax[1].set_ylim(0, 40)
		ax[1].tick_params(direction = 'in', labelsize = 14)

		i += 1

	ax[0].set_ylabel('Cycles per year', fontsize = 16)
	ax[1].set_ylabel('Additional demand met by storage (%)', fontsize = 16)
	ax[1].set_xlabel('Storage size (hours)', fontsize = 16)

	plt.tight_layout()

	# show or save plot
	# plt.show()

	plt.savefig('{}/Battery-usage-hours_overbuild-{}_{}.svg'
		.format(path_figure, overbuild, region), format = 'svg', dpi=1000)
	plt.close()



def battery_usage_days(SF2plot, batsize, overbuild):

	# set plot style and type; will be a 4 panel plot for 4 battery sizes (0, 8hrs, 1 day, 7 days)	
	# SF2plot = np.array([0, 0.25, 0.5, 0.75, 1])
	# batsize = np.arange(1,31)
	# overbuild = 1.0
    
	sns.set_style('ticks')
	# sns.set_palette('hls')
	f, ax = plt.subplots(2, sharex = True, figsize = (6, 8))

	colors = ['black', 'blue', 'red', 'purple', 'green']
	linestyle = ['solid', 'dashed', 'dashdot', 'dotted', 'dashed']
	legend_labels = ['100% Wind', '25% Solar \n75% Wind', '50% Solar \n50% Wind', \
		'75% Solar \n25% Wind', '100% Solar']

	# demand_path = '/lustre/data/mshaner/merra2/EIA_demand_files'
	demand = np.load('{}/conus_real_demand.npy'.format(path_input)) * 10**6 # W

	# make each panel plot
	i = 0
	for sf in SF2plot:

		cycles_per_year = np.zeros(batsize.size)
		extra_demand_met = np.zeros(batsize.size)

		reliability_no_storage = np.load('{}/{}_power_reliability_SF_batsize-{}-days'
			'_overbuild-{}.npy'.format(path_output, filename_start, 0.0, overbuild))

		for bs in range(batsize.size):

			reliability = np.load('{}/{}_power_reliability_SF_batsize-{}-days'
				'_overbuild-{}.npy'.format(path_output, filename_start, batsize[bs], overbuild))

			bat_capacity = demand.mean() * batsize[bs] * 24
			annual_demand = demand.sum() / 36

			SFindex = np.where(SF == sf)
			extra_demand_met[bs] = reliability[SFindex] - reliability_no_storage[SFindex]
			cycles_per_year[bs] = extra_demand_met[bs] * annual_demand / bat_capacity
		

		ax[0].plot(batsize, cycles_per_year, color = colors[i], linestyle = linestyle[i], 
			label = legend_labels[i])
		ax[0].set_xlim(0,24)
		ax[0].set_ylim(0,120)
		ax[0].tick_params(direction = 'in', colors = 'black', labelsize = 14)
		ax[0].legend(loc = 'upper right', frameon = True)

		ax[1].plot(batsize, extra_demand_met * 100, color = colors[i], linestyle = linestyle[i])
		ax[1].set_xlim(0,24)
		ax[1].set_ylim(0, 50)
		ax[1].tick_params(direction = 'in', labelsize = 14)

		i += 1

	ax[0].set_ylabel('Cycles per year', fontsize = 16)
	ax[1].set_ylabel('Additional demand met by storage (%)', fontsize = 16)
	ax[1].set_xlabel('Storage size (days)', fontsize = 16)

	plt.tight_layout()

	# show or save plot
	# plt.show()

	plt.savefig('{}/Battery-usage-days_overbuild-{}_{}.svg'
		.format(path_figure, overbuild, region), format = 'svg', dpi=1000)
	plt.close()

if __name__ == '__main__':

    
	battery_usage_hours(SF2plot, batsize, overbuild)
	battery_usage_days(SF2plot, batsize, overbuild)


