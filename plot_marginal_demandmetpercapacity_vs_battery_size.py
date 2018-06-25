import numpy as np 
import matplotlib.pyplot as plt
# import matplotlib.colors as colors
# import pandas as pd
import seaborn as sns
# import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
path_input = dir_path + '/input_data'
path_output = dir_path + '/output_data'
path_figure = dir_path + '/figures'
region = 'United States of America'
filename_start = '{}_area-weighted-mean_real-demand'.format(region)

overbuild = np.arange(0.1,4.1,0.1)
batsize = [0.00, 0.50, 4., 32.] # days
thickness = [2, 2, 2, 2]
SF = np.array([0, 0.25, 0.5, 0.75, 1.]) # solar fraction of energy production
SF2plot = SF

reliability_scale = 'Linear' # 'Linear'

#batsize = [0.0, 0.12, 0.25, 0.50, 1.0, 2, 4, 8, 16, 32]
#thickness = [2, 0.5, 0.5, 2, 0.5, 0.5, 2, 0.5, 0.5, 2]

######

demand = np.load('{}/conus_real_demand.npy'.format(path_input)) / 10**4 # 10 GW

######
# Common arrays and values
#country = 'USA'
#path = '/lustre/data/mshaner/merra2/country_files/{}'.format(country)
#region = 'United States of America'
#filename_start = '{}_area-weighted-mean_real-demand'.format(region)
#demand_path = '/lustre/data/mshaner/merra2/EIA_demand_files'
#demand = np.load('{}/conus_real_demand.npy'.format(demand_path)) / 10**4 # 10 GW

# overbuild = [np.arange(0.1,5.1,0.1), np.arange(5.5, 30.1, 0.5)] # overbuild list
# overbuild = np.round(np.array([j for list in overbuild for j in list]), 2) # single continuous overbuild array
# SF = np.arange(0,1.01,0.05) # solar fraction of energy production
CFs_avg = 0.20 # value from utility scale solar 2013 vintage value page 24 of 2014 report
CFw_avg = 0.38 # average US wind capacity factor (from http://en.openei.org/apps/TCDB/, 2005 - 2014)

# plot reliability vs capacity
def marginal_capacity_vs_capacity_batsize():

	sns.set_style('ticks')
	f, ax = plt.subplots(SF2plot.size, sharex = True, figsize = (8,14))
	colormap = plt.cm.copper
	colors = [colormap(j) for j in np.linspace(0, 1,len(batsize))]

	# make each panel plot
	i = 0
	for sf in SF2plot:

		X = np.zeros((overbuild.size, len(batsize))) # holds reliabilities
		Y = np.zeros((overbuild.size, len(batsize))) # holds d(reliability)/d(capacity)
		Z = np.zeros((overbuild.size, len(batsize))) # holds battery sizes
		capacity = np.zeros((overbuild.size, len(batsize))) # holds capacities

		for bs in range(len(batsize)):

			Z[:,bs] = np.ones(overbuild.size) * batsize[bs]

			# load reliability data
			for ob in range(overbuild.size):

				reliable_array = np.load('{}/{}_power_reliability_SF_batsize-{}-days'
					'_overbuild-{}.npy'.format(path_output, filename_start, batsize[bs], overbuild[ob]))
				SFindex = np.where(SF == sf)

				capacity[ob, bs] = (sf / CFs_avg + (1-sf) / CFw_avg) * overbuild[ob] #* demand.mean()
				X[ob, bs] = reliable_array[SFindex]

				if ob != 0 and X[ob,bs] != 1:
					# Y[ob, bs] = (X[ob, bs] - X[ob - 1, bs]) / (capacity[ob, bs] - capacity[ob - 1, bs])
					Y[ob, bs] = (X[ob, bs] - X[ob - 1, bs]) / (overbuild[ob] - overbuild[ob-1])
				elif ob != 0 and X[ob,bs] == 1:
					Y[ob, bs] = np.NaN
				else:
					# Y[ob, bs] = (X[ob, bs]) / (capacity[ob, bs])
					Y[ob, bs] = (X[ob, bs]) / (overbuild[ob])

			indicies = np.where(X[:,bs] == 1)[0]


			if reliability_scale == 'Linear':
				levels = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
				labels = ['0%', '20%', '40%', '60%', '80%', '100%']
				bounds = np.linspace(Z[0,0], Z[-1,-1], Z[-1,-1] - Z[0,0] + 1)

			elif reliability_scale == 'Log':
				levels = [-np.log(1), -np.log(0.1), -np.log(0.01), -np.log(0.001), -np.log(0.0001)]
				labels = ['0%', '90%', '99%', '99.9%', '99.99%']
		
				# 1 minus reliability because we want to plot on log scale.  Easiest to do this by 
				# powers of 10...0.1, 0.01, etc. rather than 99.9, 99.99, etc. Negative of log because
				# log of a number less 1 is negative, want it to be positive.  Mask array because 
				# where reliability is 1, log value will be NaN
				temp_array = -np.ma.log(1-X[:,bs])

				# set fill value for masked array values to a very large value (1000), this basically 
				# means reliability was 1 as the log of a very small number is a very large negative 
				# number. second line just fills in with the desired value
				# np.ma.set_fill_value(temp_array, 1000)
				X[:,bs] = temp_array # temp_array.filled()


			pcm = ax[i].plot(X[:,bs],Y[:,bs], color = colors[bs], linewidth = thickness[bs]) #, linestyle = style[bs])

		# plot reliability versus capacity of wind and solar combined
		
		ax[i].set_ylim(0,1.1)
		ax[i].set_yticks([0, 0.5, 1])
		ax[i].set_xlim(levels[0],levels[-1])
		ax[i].set_xticks(levels)
		ax[i].set_xticklabels(labels)
		ax[i].tick_params(axis='both', labelsize = 12)
		ax[i].tick_params(direction = 'in', colors = 'black', labelsize = 14)
		if reliability_scale == 'Log':
			ax[i].text(7, 0.7*1.1, '{}% Solar \n{}% Wind'.format(int(sf*100), int((1-sf)*100)),
				fontweight = 'bold')
		else:
			ax[i].text(0.05, 0.1*1.1, '{}% Solar \n{}% Wind'.format(int(sf*100), int((1-sf)*100)),
				fontweight = 'bold')

		i += 1

	f.text(0.06, 0.55, 'Additional % demand met for each additional % of\n total demand that is added as generation', 
		va = 'center', ha = 'center', rotation = 'vertical', fontsize = 18)
	f.text(0.5, 0.03, 'Fraction of electricity demand met by\n by solar, wind and storage', ha = 'center', 
		fontsize = 18)

	plt.tight_layout(rect = (0.1, 0.1, 0.85, 1))

	# show or save plot
	# plt.show()

	plt.savefig('{}/MarginalCapacity_vs_FracDemandSatisfied_{}_{}.png'
		.format(path_figure, reliability_scale, region), format = 'png', dpi=1000)
	plt.close()

if __name__ == '__main__':
	marginal_capacity_vs_capacity_batsize()
