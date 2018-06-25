import numpy as np 
import matplotlib.pyplot as plt
# import matplotlib.colors as colors
# import pandas as pd
import seaborn as sns
# import scipy.optimize as optimize
# import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
path_input = dir_path + '/input_data'
path_output = dir_path + '/output_data'
path_figure = dir_path + '/figures'
region = 'United States of America'
filename_start = '{}_area-weighted-mean_real-demand'.format(region)

SF = np.array([0, 0.25, 0.5, 0.75, 1.])
overbuild = np.arange(0.1,4.1,0.1)
batsize = np.array([0.00, 0.50, 4. ,32.]) # days
thickness = [2, 0.5, 0.5, 2]

# time_horizon = 'Days' # of storage (hours or days)
reliability_scale = 'Log' # (log or linear)
SF2plot = SF

######
# Common arrays and values
#country = 'USA'
#path = '/lustre/data/mshaner/merra2/country_files/{}'.format(country)
#region = 'United States of America'
#filename_start = '{}_area-weighted-mean_real-demand'.format(region)

# overbuild = [np.arange(0.1,5.1,0.1), np.arange(5.0, 30.1, 0.5)] # overbuild list
# overbuild = np.round(np.array([j for list in overbuild for j in list]), 2) # single continuous overbuild array
#overbuild = np.arange(0,4.2,0.1)# overbuild list
#SF = np.arange(0,1.01,0.05) # solar fraction of energy production


CFs_avg = 0.20 # value from utility scale solar 2013 vintage value page 24 of 2014 report
CFw_avg = 0.38 # average US wind capacity factor (from http://en.openei.org/apps/TCDB/, 2005 - 2014)

######

# if time_horizon == 'Hours':
# 	batsize = np.round((np.arange(0,24.1,1) / 24),2) # 0 to 24 hours, in fractional days to read file
# elif time_horizon == 'Days':
# 	batsize = np.arange(1,31) # 1 to 30 days
# else:
# 	sys.exit('Incorrect time horizon input')

# batsize = [0.0, 0.12, 0.25, 0.50, 1.0, 2, 4, 8, 16, 32]
# thickness = [2, 0.5, 0.5, 2, 0.5, 0.5, 2, 0.5, 0.5, 2]

# batsize = [0.0, 0.50, 4, 32]
# thickness = [2, 2, 2, 2]
# style = ['-','--','--','-','--', '--', '-', '--', '--', '-']
######

# plot reliability vs capacity
def plot_figure():

	sns.set_style('ticks')
	f, ax = plt.subplots(SF2plot.size, sharex = True, figsize = (8,14))
	colormap = plt.cm.copper
	colors = [colormap(j) for j in np.linspace(0, 1,len(batsize))]


	# make each panel plot
	i = 0
	for sf in SF2plot:

		X = np.zeros((overbuild.size, len(batsize))) # holds reliabilities
		Y = np.zeros((overbuild.size, len(batsize))) # holds capacities
		Z = np.zeros((overbuild.size, len(batsize))) # holds battery sizes

		for bs in range(len(batsize)):

			# if time_horizon == 'Hours':
			# 	Z[:,bs] = np.ones(overbuild.size) * batsize[bs] * 24
			# else: # days
			# 	Z[:,bs] = np.ones(overbuild.size) * batsize[bs]

			# load reliability data
			for ob in range(overbuild.size):

				if overbuild[ob] == 0:
					Y[ob, bs] = overbuild[ob] 
					X[ob, bs] = 0

				else:

					reliable_array = np.load('{}/{}_power_reliability_SF_batsize-{}-days'
						'_overbuild-{}.npy'.format(path_output, filename_start, batsize[bs], overbuild[ob]))
					SFindex = np.where(SF == sf)

					Y[ob, bs] = overbuild[ob] #(sf / CFs_avg + (1-sf) / CFw_avg) * overbuild[ob]
					X[ob, bs] = reliable_array[SFindex]

			if X[-1,bs]>0.9999:
				index = np.where(X[:,bs]>0.9999)[0][0]
				X[index::,bs] = X[index,bs]
				Y[index::,bs] = Y[index,bs]

			if reliability_scale == 'Linear':
				levels = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
				labels = ['0%', '20%', '40%', '60%', '80%', '100%']

			elif reliability_scale == 'Log':
				levels = [-np.log10(1), -np.log10(0.1), -np.log10(0.01), -np.log10(0.001), 
					-np.log10(0.0001)]
				labels = ['0%', '90%', '99%', '99.9%', '99.99%']
				ticks_gen = np.array([0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2])
				minor_ticks = -np.log10(np.array([ticks_gen, ticks_gen/10, ticks_gen/100, 
					ticks_gen/1000])).flatten()

		
				# 1 minus reliability because we want to plot on log scale.  Easiest to do this by 
				# powers of 10...0.1, 0.01, etc. rather than 99.9, 99.99, etc. Negative of log because
				# log of a number less 1 is negative, want it to be positive.  Mask array because 
				# where reliability is 1, log value will be NaN
				temp_array = -np.ma.log10(1-X[:,bs])

				# set fill value for masked array values to a very large value (1000), this basically 
				# means reliability was 1 as the log of a very small number is a very large negative 
				# number. second line just fills in with the desired value
				np.ma.set_fill_value(temp_array, 1000)
				X[:,bs] = temp_array.filled()

			pcm = ax[i].plot(X[:,bs],Y[:,bs], color = colors[bs], linewidth = thickness[bs]) #, linestyle = style[bs])

		# calculate capacity for overbuild = 1
		no_overbuild_capacity = [1,1]
		demand_satisfied = [levels[0], levels[-1]]

		# plot reliability versus capacity of wind and solar combined
		
		ax[i].plot(demand_satisfied, no_overbuild_capacity, color = 'grey', linestyle = ':')
		ax[i].set_ylim(0,4)
		ax[i].set_yticks(np.arange(0,5))
		ax[i].set_xlim(levels[0],levels[-1])
		ax[i].set_xticks(levels)
		# if reliability_scale == 'Log':
		# 	ax[i].set_xticks(minor_ticks, minor=True)
		# 	ax[i].tick_params(axis = 'x', which = 'minor', direction = 'in')
		ax[i].set_xticklabels(labels)
		ax[i].tick_params(axis='both', labelsize = 12)
		ax[i].tick_params(direction = 'in', colors = 'black', labelsize = 14)

		# second y-axis that is over-generation
		capmax = 4 * (sf / CFs_avg + (1-sf) / CFw_avg)
		caps_2plot = np.arange(0,capmax,5).astype('int')
		tick_labels = caps_2plot
		ticks =  caps_2plot / (sf / CFs_avg + (1-sf) / CFw_avg)
		ax2 = ax[i].twinx()
		ax2.set_ylim(ax[i].get_ylim())
		ax2.tick_params(axis = 'y', which = 'major', direction = 'in', bottom = 'on')
		ax2.set_yticks(ticks)
		ax2.set_yticklabels(tick_labels, fontsize = 14)


		i += 1


	f.text(0.02, 0.5, 'Generation (times (x) of energy demand)', 
		va = 'center', multialignment = 'center', rotation = 'vertical', fontsize = 20)
	f.text(0.5, 0.02, 'Demand Satisfied by Solar + Wind + Storage (%)', ha = 'center', 
		fontsize = 18)
	f.text(0.91, 0.5, 'Installed Solar and Wind Capacity Normalized by \nMean Demand'
		'($W_{installed}$ / $W_{mean-demand}$)', va = 'center', multialignment = 'center', 
		rotation = 'vertical', fontsize = 20)

	plt.tight_layout(rect = (0.05, 0.05, 0.90, 1))

	# show or save plot
	# plt.show()

	plt.savefig('{}/Peak-Capacity_vs_FracDemandSatisfied_battery-size-{}days_real-demand'
		'_{}_SF_{}_solid-lines.png'
		.format(path_figure, batsize, reliability_scale, region), format = 'png', dpi=1000)
	plt.close()


if __name__ == '__main__':
	plot_figure()