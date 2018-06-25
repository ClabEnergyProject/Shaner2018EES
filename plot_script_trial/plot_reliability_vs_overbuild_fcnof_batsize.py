import numpy as np 
import matplotlib.pyplot as plt
import matplotlib.colors as colors
# import pandas as pd
import seaborn as sns
# import scipy.optimize as optimize
import sys
import os

#######
## Common arrays and values
#country = 'USA'
#path = '/lustre/data/mshaner/merra2/country_files/{}'.format(country)
#region = 'United States of America'
#filename_start = '{}_area-weighted-mean_real-demand'.format(region)
#
#batsize = [0., 0.33, 1., 7.] # days of storage
#overbuild = [np.arange(0.1,5.1,0.1), np.arange(5.0, 30.1, 0.5)] # overbuild list
#overbuild = np.round(np.array([j for list in overbuild for j in list]), 2) # single continuous overbuild array
#SF = np.arange(0,1.01,0.05) # solar fraction of energy production

dir_path = os.path.dirname(os.path.realpath(__file__))
path_input = dir_path + '/input_data'
path_output = dir_path + '/output_data'
path_figure = dir_path + '/figures'
region = 'United States of America'
filename_start = '{}_area-weighted-mean_real-demand'.format(region)

SF = np.array([0, 0.25, 0.5, 0.75, 1.])
overbuild = overbuild = np.arange(0.1,4.1,0.1)
batsize = np.array([0.00, 0.50, 4., 32.]) # days
# SF_array = np.array([0, 0.25, 0.5, 0.75, 1.]) # solar fraction of energy production

# demand = np.load('{}/conus_real_demand.npy'.format(path_input)) * 10**6 # W

CFs_avg = 0.20 # value from utility scale solar 2013 vintage value page 24 of 2014 report
CFw_avg = 0.38 # average US wind capacity factor (from http://en.openei.org/apps/TCDB/, 2005 - 2014)

######

time_horizon = 'Days' # of storage (hours or days)
reliability_scale = 'Log' # (log or linear)
SF2plot = np.array([0, 0.25, 0.5, 0.75, 1.])

#if time_horizon == 'Hours':
#	batsize = np.round((np.arange(0,24.1,1) / 24),2) # 0 to 24 hours, in fractional days to read file
#elif time_horizon == 'Days':
#	batsize = np.arange(1,31) # 1 to 30 days
#else:
#	sys.exit('Incorrect time horizon input')

######

# plot reliability vs capacity
def plot_figure():

	sns.set_style('ticks')
	f, ax = plt.subplots(SF2plot.size, sharex = True, figsize = (8,14))

	# make each panel plot
	i = 0
	for sf in SF2plot:

		X = np.zeros((overbuild.size, len(batsize))) # holds reliabilities
		Y = np.zeros((overbuild.size, len(batsize))) # holds capacities
		Z = np.zeros((overbuild.size, len(batsize))) # holds battery sizes

		for bs in range(len(batsize)):

			if time_horizon == 'Hours':
				Z[:,bs] = np.ones(overbuild.size) * batsize[bs] * 24
			else: # days
				Z[:,bs] = np.ones(overbuild.size) * batsize[bs]

			# load reliability data
			for ob in range(overbuild.size):

				reliable_array = np.load('{}/{}_power_reliability_SF_batsize-{}-days'
					'_overbuild-{}.npy'.format(path_output, filename_start, batsize[bs], overbuild[ob]))
				SFindex = np.where(SF == sf)

				Y[ob, bs] = (sf / CFs_avg + (1-sf) / CFw_avg) * overbuild[ob]
				X[ob, bs] = reliable_array[SFindex]

		if reliability_scale == 'Linear':
			levels = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
			labels = ['0%', '20%', '40%', '60%', '80%', '100%']

		elif reliability_scale == 'Log':
			levels = [-np.log(1), -np.log(0.1), -np.log(0.01), -np.log(0.001), -np.log(0.0001)]
			labels = ['0%', '90%', '99%', '99.9%', '99.99%']
	
			# 1 minus reliability because we want to plot on log scale.  Easiest to do this by 
			# powers of 10...0.1, 0.01, etc. rather than 99.9, 99.99, etc. Negative of log because
			# log of a number less 1 is negative, want it to be positive.  Mask array because 
			# where reliability is 1, log value will be NaN
			temp_array = -np.ma.log(1-X)

			# set fill value for masked array values to a very large value (1000), this basically 
			# means reliability was 1 as the log of a very small number is a very large negative 
			# number. second line just fills in with the desired value
			np.ma.set_fill_value(temp_array, 1000)
			X = temp_array.filled()

		# calculate capacity for overbuild = 1
		no_overbuild_capacity = [(sf / CFs_avg + (1-sf) / CFw_avg), (sf / CFs_avg + (1-sf) / CFw_avg)]
		demand_satisfied = [levels[0], levels[-1]]

		# plot reliability versus capacity of wind and solar combined
		bounds = np.linspace(Z[0,0], Z[-1,-1], Z[-1,-1] - Z[0,0] + 1)
		norm = colors.BoundaryNorm(boundaries = bounds, ncolors = 256)
		pcm = ax[i].pcolormesh(X, Y, Z, norm = norm, cmap = 'viridis')
		ax[i].plot(demand_satisfied, no_overbuild_capacity, color = 'black')
		ax[i].set_ylim(0,10)
		ax[i].set_xlim(levels[0],levels[-1])
		ax[i].set_xticks(levels)
		ax[i].set_xticklabels(labels)
		ax[i].tick_params(axis='both', labelsize = 12)
		ax[i].tick_params(direction = 'in', colors = 'black', labelsize = 14)
		
		i += 1


#	cbar_ax = f.add_axes([0.85, 0.15, 0.05, 0.7])
#	cbar = f.colorbar(pcm, cax = cbar_ax)
#	cbar.ax.set_ylabel('Storage Size ({} of Mean Demand)'.format(time_horizon), fontsize = 20)
#	cbar.ax.tick_params(labelsize = 14)
	f.text(0.02, 0.5, 'Installed Solar and Wind Capacity Normalized by \nMean Demand'
		'($W_{installed}$ / $W_{mean-demand}$)', 
		va = 'center', multialignment = 'center', rotation = 'vertical', fontsize = 20)
	f.text(0.5, 0.03, 'Percent of Demand Satisfied \n by Solar + Wind + Storage', ha = 'center', 
		fontsize = 18)

	plt.tight_layout(rect = (0.1, 0.1, 0.85, 1))

	# show or save plot
	# plt.show()

	plt.savefig('{}/Peak-Capacity_vs_FracDemandSatisfied_battery-size-{}_real-demand'
		'_{}_SF_{}.png'
		.format(path_figure, time_horizon, reliability_scale, region), format = 'png', dpi=1000)
	plt.close()


if __name__ == '__main__':
	plot_figure()