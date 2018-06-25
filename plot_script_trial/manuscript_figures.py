import numpy as np 
import matplotlib.pyplot as plt
import matplotlib.colors as colors
# import pandas as pd
import seaborn as sns
import scipy.optimize as optimize
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

# SF = [0.75]
overbuild = np.arange(0.1,4.1,0.1)
batsize = [0.00, 0.50, 4., 32.] # days
SF = np.array([0, 0.25, 0.5, 0.75, 1.]) # solar fraction of energy production
SF2plot = SF

demand = np.load('{}/conus_real_demand.npy'.format(path_input)) * 10**6 # W

CFs_avg = 0.20 # value from utility scale solar 2013 vintage value page 24 of 2014 report
CFw_avg = 0.38 # average US wind capacity factor (from http://en.openei.org/apps/TCDB/, 2005 - 2014)

######


# plot reliability vs capacity
def reliability_vs_capacity():
	
	# set plot style and type; will be a 4 panel plot for 4 battery sizes (0, 8hrs, 1 day, 7 days)
	sns.set_style('whitegrid')
	sns.set_palette('colorblind')
	markers = ['*', '^', '<', 'o', '>']
	f, ax = plt.subplots(2, 2, sharex = True, sharey = True, figsize = (12, 8))

	# make each panel plot
	for n in range(0,4):

		reliable_array = np.zeros((SF.size, overbuild.size))

		counter = 0
		# load reliability data
		for ob in overbuild:

			reliable_array[:, counter] = np.load('{}/{}_power_reliability_SF_batsize-{}-days_overbuild-{}.npy'.format(path_output, filename_start, batsize[n], ob))
			counter += 1
		
		# 1 minus reliability because we want to plot on log scale.  Easiest to do this by powers of 10
		# 0.1, 0.01, etc. rather than 99.9, 99.99, etc. Negative of log because log of a number less
		# 1 is negative, want it to be positive.  Mask array because where reliability is 1,
		# log value will be NaN
		reliable_array_log = -np.ma.log(1-reliable_array)

		# set fill value for masked array values to a very large value (1000), this basically means
		# reliability was 1 as the log of a very small number is a very large negative number.
		# second line just fills in with the desired value
		np.ma.set_fill_value(reliable_array_log, 1000)
		reliable_array_log = reliable_array_log.filled()

		# titles for panels within plot
		if n < 2:
			row = 0
			column = n
			if n == 0:
				title = 'No Storage'
			else:
				title = '8 hours'
		else:
			row = 1
			column = n - 2
			if n == 2:
				title = '1 day'
			else:
				title = '1 week'

		c = 0
		for sf in SF:
			
			# account for capacity factors of wind and solar so plot is of W peak per W mean
			ob_2plot = (sf / CFs_avg + (1-sf) / CFw_avg) * overbuild

			# only plot certain solar fractions
			if sf in [0, 0.25, 0.5, 0.75, 1]:
				# plot reliability versus capacity of wind and solar combined
				ax[row, column].plot(reliable_array[c, :], ob_2plot, marker = markers[np.int(sf*4)], 
					label = '{}% S, {}% W'.format(np.int(sf*100), np.int((1-sf)*100)))
			
			c += 1

		# settings for plot labeling and general asthetics
		# levels = [-np.log(1), -np.log(0.1), -np.log(0.01), -np.log(0.001), -np.log(0.0001)]
		# labels = ['0%', '90%', '99%', '99.9%', '99.99%']
		# ax[row, column].set_xlim(0,9.21)
		ax[row, column].set_ylim(0, 14)
		# ax[row, column].set_xticks(levels)
		# ax[row, column].set_xticklabels(labels)
		ax[row, column].tick_params(axis='both', labelsize = 12)
		ax[row, column].set_title('{} ({} $Wh_{}$ / $W_{}$)'.format(title, np.int(np.ceil(batsize[n] * 24)), '{storage}', '{mean-demand}'), fontsize=14)

	ax[0,0].legend(loc = 'upper left', fontsize = 12, frameon = True)	
	f.text(0.06, 0.5, 'Installed Capacity to Demand ($W_{installed}$ / $W_{mean-demand}$)', va = 'center', rotation = 'vertical', fontsize = 14)
	f.text(0.5, 0.03, 'Fraction of Demand Satisfied by Solar + Wind + Storage', ha = 'center', fontsize = 14)
	plt.suptitle('{}'.format(region), fontsize = 20)

	# show or save plot
	# plt.show()

	plt.savefig('{}/Peak-Capacity_vs_FracDemandSatisfied_real-demand_linear_SF_0days_8hrs_1day_1week_panelplot_{}.png'
		.format(path_figure, region), format = 'png', dpi=600)
	plt.close()

# plot reliability vs capacity
def reliability_vs_capacity_batsize():

	# set plot style and type; will be a 4 panel plot for 4 battery sizes (0, 8hrs, 1 day, 7 days)	
	# SF2plot = np.array([0, 0.25,0.5, 0.75, 1])
	# batsize = np.round((np.arange(0,24.1,1) / 24),2)
	# batsize = np.arange(1,31)
	sns.set_style('ticks')
	# sns.set_palette('hls')
	f, ax = plt.subplots(SF2plot.size, sharex = True, figsize = (8,14))#, sharey = True)#, figsize = (4, 16))

	# make each panel plot
	i = 0
	for sf in SF2plot:

		X = np.zeros((overbuild.size, len(batsize))) # holds reliabilities
		Y = np.zeros((overbuild.size, len(batsize))) # holds capacities
		Z = np.zeros((overbuild.size, len(batsize))) # holds battery sizes

		for bs in range(len(batsize)):

			Z[:,bs] = np.ones(overbuild.size) * batsize[bs] * 24
			# Z[:,bs] = np.ones(overbuild.size) * batsize[bs]


			# load reliability data
			for ob in range(overbuild.size):

				reliable_array = np.load('{}/{}_power_reliability_SF_batsize-{}-days'
					'_overbuild-{}.npy'.format(path_output, filename_start, batsize[bs], overbuild[ob]))
				SFindex = np.where(SF == sf)

				Y[ob, bs] = (sf / CFs_avg + (1-sf) / CFw_avg) * overbuild[ob]
				X[ob, bs] = reliable_array[SFindex]

		# titles for panels within plot
		title = '{}% Solar, {}% Wind'.format(np.int(sf*100), np.int((1-sf)*100))

		no_overbuild_capacity = [(sf / CFs_avg + (1-sf) / CFw_avg), (sf / CFs_avg + (1-sf) / CFw_avg)]
		demand_satisfied = [0, 1]

		# plot reliability versus capacity of wind and solar combined
		bounds = np.linspace(0,24,25)
		# bounds = np.linspace(1,30,30)
		norm = colors.BoundaryNorm(boundaries = bounds, ncolors = 256)
		pcm = ax[i].pcolormesh(X, Y, Z, norm = norm, cmap = 'viridis')
		ax[i].plot(demand_satisfied, no_overbuild_capacity, color = 'black')
		ax[i].set_ylim(0,10)
		ax[i].tick_params(axis='both', labelsize = 12)
		#ax[i].set_title('{}'.format(title), fontsize=14)
		#ax[row, column].grid(False)
		ax[i].tick_params(direction = 'in', colors = 'black', labelsize = 14)
		i += 1


	cbar_ax = f.add_axes([0.85, 0.15, 0.05, 0.7])
	cbar = f.colorbar(pcm, cax = cbar_ax)
	cbar.ax.set_ylabel('Storage Size (Hours of Mean Demand)', fontsize = 20)
	cbar.ax.tick_params(labelsize = 14)
	f.text(0.02, 0.5, 'Installed Solar and Wind Capacity Normalized by \nMean Demand'
		'($W_{installed}$ / $W_{mean-demand}$)', 
		va = 'center', multialignment = 'center', rotation = 'vertical', fontsize = 20)
	f.text(0.5, 0.03, 'Fraction of Demand Satisfied \n by Solar + Wind + Storage', ha = 'center', 
		fontsize = 18)

	plt.tight_layout(rect = (0.1, 0.1, 0.85, 1))

	# show or save plot
	# plt.show()

	plt.savefig('{}/Peak-Capacity_vs_FracDemandSatisfied_battery-size-hours_real-demand'
		'_linear_SF-25to75_0days_8hrs_1day_1week_panelplot_{}.png'
		.format(path_figure, region), format = 'png', dpi=600)
	plt.close()



# plot cost versus reliability
def reliability_vs_cost():

	# define specifics for this plot
	# demand_path = '/lustre/data/mshaner/merra2/EIA_demand_files'
	# demand = np.load('{}/conus_real_demand.npy'.format(demand_path)) * 10**6 # W
	reliability_target = 0.9999

######
	# Cost definitions
	crf = lambda x: (x[0] * (1 + x[0])**x[1] / ((1 + x[0])**x[1] - 1))

	solar_capex = 2 # $/W
	solar_discount = 0.06
	solar_lifetime = 25 # years
	solar_crf = crf([solar_discount, solar_lifetime])
	
	wind_capex = 2 # $/W
	wind_discount = 0.06
	wind_lifetime = 25 # years
	wind_crf = crf([wind_discount, wind_lifetime])

	dispatchable_capex = 1.25 # $/W
	dispatchable_discount = 0.06
	dispatchable_lifetime = 25 # years
	dispatchable_crf = crf([dispatchable_discount, dispatchable_lifetime])
	dispatchable_fuel_cost = 10 # $/MM BTU
	dispatchable_heat_rate = 7658 * 10**-6  # MMBTU / kWh (from https://www.eia.gov/electricity/annual/html/epa_08_02.html, 2014)

	storage_capex = 0.05 # $/Whr, = $100/kWh
	storage_discount = 0.06
	storage_lifetime = 10 # years
	storage_crf = crf([storage_discount, storage_lifetime])

######

	# set plot type and style; 4 panel plot
	sns.set_style('whitegrid')
	sns.set_palette('colorblind')
	markers = ['*', '^', '<', 'o', '>']
	f, ax = plt.subplots(2, 2, sharex = True, sharey = False, figsize = (12, 8))

	for n in range(len(batsize)):

		# initiate arrays for, will reset for each battery size
		dispatch_cap = np.zeros((SF.size, overbuild.size)) # collects dispatchable capacity
		reliable_array = np.zeros((SF.size, overbuild.size)) # collects reliability
		lcoe = np.zeros((SF.size, overbuild.size)) # collects levelized cost of electricity

		counter = 0
		# import both total reliability and hourly power unable to be met
		for ob in overbuild:
			
			hourly_reliable_array = np.load('{}/{}_hourly_power_reliability_SF_batsize-{}-days_overbuild-{}.npy'.format(path_output, filename_start, batsize[n], ob))
			reliable_array[:, counter] = np.load('{}/{}_power_reliability_SF_batsize-{}-days_overbuild-{}.npy'.format(path_output, filename_start, batsize[n], ob))

			c = 0
			for sf in SF:
				
				# find dispatchable capacity needed to meet the reliability target 
				# (this is why the optimization is needed)
				# if reliability of run is less than reliability target
				if reliable_array[c, counter] < reliability_target:

					fun = lambda x: (1 - np.sum(np.clip((hourly_reliable_array[c,:] - x), 0, demand.max())) / 
					demand.sum()) - reliability_target

					dispatch_cap[c, counter] = optimize.newton(fun, 0.05 * demand.max(), maxiter = 10**6)
					
				# if reliability of run is greater than or equal to reliability target
				# no dispatchable capacity needed
				else:

					dispatch_cap[c, counter] = 0

				# calculate the average annual energy demand (kWh/yr)
				total_gen = demand.sum() * reliability_target / (36 * 10**3)

				### calculate installed capacities of production units
				# calculate the solar capacity. sf * demand.mean() will give amount of solar power
				# for ob = 1.  * ob to account for non unity ob (overbuild). Divide by
				# CFs_avg (CONUS average solar capacity factor) to get capacity of solar needed
				# identical for wind for wind
				solar_cap = sf * demand.mean() * ob / CFs_avg # W
				wind_cap = (1 - sf) * demand.mean() * ob / CFw_avg # W

				# dispatchable capacity based on calculation above
				dispatchable_cap = dispatch_cap[c, counter] # W

				# storage capacity is battery size in days x  24 to convert to hours x 
				# mean demand (this is what battery size was based on) in W
				storage_cap = batsize[n] * 24 * demand.mean() # Wh

				# dispatchable fuel usage
				# if reliability is greater than target, no fuel used
				if reliable_array[c, counter] >= reliability_target:
					dispatchable_fuel_usage = 0

				# if reliability lower than target
				else:
					# find amount of energy that would need to be supplied for 100% reliability (1st sum)
					# find amount of energy that would need to be supplied for last 100% - reliability
					# target (second sum).  Take difference between first and second sums to find
					# amount of energy needed from fuel to achieve reliability target
					# these values are in Wh for entire time so divide by 1000 to convert to kWh
					# and 36 to get annual average.  Convert to MM BTU using heat rate for CC NG
					dispatchable_fuel_usage = (np.sum(hourly_reliable_array[c,:]) - \
						np.sum(np.clip(hourly_reliable_array[c, :] - dispatch_cap[c, counter], \
						0, demand.max()))) * dispatchable_heat_rate \
						/ (36 * 10**3) # MMBTU/yr



				### calculate lcoe's for each unit
				# capacity (W) x capital expanse ($/W) x annualized capital recovery factor from 
				# discount rate and lifetime amortized over / annual energy generation (kWh/yr)
				solar_lcoe = solar_cap * solar_capex * solar_crf / total_gen # $/kWh
				
				wind_lcoe = wind_cap * wind_capex * wind_crf / total_gen # $/kWh
				
				dispachable_capex_lcoe = dispatchable_cap * dispatchable_capex \
					* dispatchable_crf / total_gen # $/kWh
				
				dispatchable_fuel_lcoe = dispatchable_fuel_cost * dispatchable_fuel_usage \
					/ total_gen # $/kWh
			
				dispatchable_lcoe = dispachable_capex_lcoe + dispatchable_fuel_lcoe # $/kWh

				storage_lcoe = storage_cap * storage_capex * storage_crf / total_gen # $/kWh

				# sum up all lcoe's
				lcoe[c, counter] = solar_lcoe + wind_lcoe + dispatchable_lcoe + storage_lcoe


				c += 1

			counter += 1
	
		# 1 minus reliability because we want to plot on log scale.  Easiest to do this by powers of 10
		# 0.1, 0.01, etc. rather than 99.9, 99.99, etc. Negative of log because log of a number less
		# 1 is negative, want it to be positive.  Mask array because where reliability is 1,
		# log value will be NaN
		rely_array = -np.ma.log(1-reliable_array)

		# set fill value for masked array values to a very large value (1000), this basically means
		# reliability was 1 as the log of a very small number is a very large negative number.
		# second line just fills in with the desired value
		np.ma.set_fill_value(rely_array, 1000)
		rely_array = rely_array.filled()

		# labels for panels
		if n < 2:
			row = 0
			column = n
			if n == 0:
				title = 'No Storage'
			else:
				title = '8 hours'
		else:
			row = 1
			column = n - 2
			if n == 2:
				title = '1 day'
			else:
				title = '1 week'

		c = 0
		for sf in SF:
						
			# only plot certain solar fractions
			if sf in [0, 0.25, 0.5, 0.75, 1]:
				# plot cost versus amount of reliability provided by solar, wind and storage
				ax[row, column].plot(rely_array[c, 1:], lcoe[c, 1:], marker = markers[c], 
					label = '{}% S, {}% W'.format(np.int(sf*100), np.int((1-sf)*100)))
				
			c += 1

		# settings for plot labeling and general asthetics
		levels = [-np.log(1), -np.log(0.1), -np.log(0.01), -np.log(0.001), -np.log(0.0001)]
		labels = ['0%', '90%', '99%', '99.9%', '99.99%']
		ax[row, column].set_xlim(0,9.21)
		# plt.yscale('log')
		ax[row, column].set_ylim(0, 0.2)
		ax[row, column].set_xticks(levels)
		ax[row, column].set_xticklabels(labels)
		ax[row, column].tick_params(axis='both', labelsize = 12)
		ax[row, column].set_title('{} ({} $Wh_{}$ / $W_{}$)'.format(title, 
			np.int(np.ceil(batsize[n] * 24)), '{storage}', '{mean-demand}'), fontsize=14)

	ax[0,0].legend(loc = 'lower right', fontsize = 12, frameon = True)	
	f.text(0.06, 0.5, 'LCOE to Meet {}% of Demand  ($ / kWh)'.format(reliability_target * 100),  va = 'center', rotation = 'vertical', fontsize = 14)
	f.text(0.5, 0.03,'Demand Satisfied by Solar + Wind + Storage (%)', ha = 'center', fontsize = 14)
	plt.suptitle('Solar - ${}/W, {} yr life, CF-{}; Wind - ${}/W, {} yr life, CF-{}; Storage - ${}/kWh, '
		'{} yr life, Dispatchable - ${}/W, ${}/MMBTU,\n {} BTU/kWh, {} yr life; Discount rate - {}%'.format(solar_capex, 
			solar_lifetime, CFs_avg, wind_capex, wind_lifetime, CFw_avg, np.int(storage_capex * 1000), storage_lifetime, dispatchable_capex, 
			dispatchable_fuel_cost, dispatchable_heat_rate * 1000, dispatchable_lifetime, solar_discount * 100))

	# show or save plot
	# plt.show()

	plt.savefig('{}/{}_LCOE-2-meet-{}%_vs_FracDemandSatisfied-by-S+W+S_real-demand_Solar-${}pW-CF-{}_Wind-${}pW-CF-{}_Storage-${}pkW_Dispatchable-${}pkW_${}pMMBTU.png'
	 	.format(path_figure, region, reliability_target * 100, solar_capex, CFs_avg, wind_capex, CFw_avg,
	 	 storage_capex, dispatchable_capex, dispatchable_fuel_cost), format = 'png', dpi=600)
	plt.close()



if __name__ == '__main__':
	reliability_vs_capacity()
	reliability_vs_capacity_batsize()
	reliability_vs_cost()
