
import numpy as np 
import matplotlib.pyplot as plt
# import pandas as pd
import seaborn as sns
import os

######

def autolabel(rects, ax):
    # Get y-axis height to calculate label position from.
    (y_bottom, y_top) = ax.get_ylim()
    y_height = y_top - y_bottom

    for rect in rects:
        height = rect.get_height()

        # Fraction of axis height taken up by this rectangle
        p_height = (height / y_height)

        # If we can fit the label above the column, do that;
        # otherwise, put it inside the column.
        if p_height > 0.95: # arbitrary; 95% looked good to me.
            label_position = height - (y_height * 0.05)
        else:
            label_position = height + (y_height * 0.01)

        ax.text(rect.get_x() + rect.get_width()/2., label_position,
                '%d' % int(height),
                ha='center', va='bottom')


dir_path = os.path.dirname(os.path.realpath(__file__))
path_input = dir_path + '/input_data'
path_output = dir_path + '/output_data'
path_figure = dir_path + '/figures'
region = 'United States of America'
filename_start = '{}_area-weighted-mean_real-demand'.format(region)

# SF = [0.75]
overbuild = [1.0, 1.5] # np.arange(0.1,4.1,0.1)
batsize = [0.00, 0.50, 4., 32.] # days
SF = np.array([0, 0.25, 0.5, 0.75, 1.]) # solar fraction of energy production
SF_array = SF

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
#SF = [0.0, 0.25, 0.5, 0.75, 1.0]
#SF_array = np.arange(0,1.01,0.05) # solar fraction of energy production

time_bins = [1,3,6,12,24,48,96,192]
target_power_fraction = 0.5 # 50%

for sf in SF:
	max_value = 0 # initialize value for maximum y axis height
	fig_labels = np.array([['a', 'b'],['c', 'd']])

	sns.set_style('ticks')
	fig, ax = plt.subplots(2,2, sharex = True, sharey = True, figsize = (12,8))

	for bs in range(len(batsize)):
		for ob in range(len(overbuild)):

			reliable_array = np.load('{}/{}_hourly_power_reliability_SF_batsize-{}-days'
				'_overbuild-{}.npy'.format(path_output, filename_start, batsize[bs], overbuild[ob]))

			sf_index = np.where(SF_array == sf)
			rel_array_sf = reliable_array[sf_index, :].squeeze()
			power_delivered_fraction = (demand - rel_array_sf) / demand - target_power_fraction

			sign_change = np.signbit(power_delivered_fraction) # all negative values True (1), 0 and all positive values are False (0)
			sign_change = sign_change.astype(int) # change bools to ints

			neg2pos_indicies = np.where(np.diff(sign_change) == 1)[0] # previous values come from below power of interest and go above
			pos2neg_indicies = np.where(np.diff(sign_change) == -1)[0] # previous values come from above power of interest and go below

			if (len(pos2neg_indicies) > 0) & (len(neg2pos_indicies) > 0):
				
				if pos2neg_indicies[0] < neg2pos_indicies[0]: # starts by coming from above (not enough power)

					if neg2pos_indicies[-1] > pos2neg_indicies[-1]: # ends by staying above

						hours_below_target_power = (pos2neg_indicies[1:] - neg2pos_indicies[:-1])

					else: # ends by staying below

						hours_below_target_power = (pos2neg_indicies[1:] - neg2pos_indicies)

				else: # starts by coming from below (enough power)

					if neg2pos_indicies[-1] > pos2neg_indicies[-1]: # ends by staing above

						hours_below_target_power = (pos2neg_indicies - neg2pos_indicies[:-1])

					else: # ends by staing below

						hours_below_target_power = (pos2neg_indicies - neg2pos_indicies)


			hours_below_target_power = np.array(hours_below_target_power)
			hist, bin = np.histogram(hours_below_target_power, bins = time_bins)

			x_values = np.arange(len(time_bins)-1)

			
			rects = ax[ob,bs].bar(x_values, hist)

			max_holder = hist.max()
			if max_holder > max_value:
				max_value = max_holder

			ax[ob,bs].set_xticks(np.arange(0.5,8,1))
			ax[ob,bs].set_xticklabels(['1-3 hrs', '3-6 hrs', '6-12 hrs', '12-24 hrs', '1-2 days',
				'2-4 days', '4-8 days'], fontsize = 12)
			ax[ob,bs].set_xlim(0,7)
			ax[ob,bs].tick_params(axis='x', bottom = 'off', top = 'off')
			ax[ob,bs].tick_params(axis = 'y', direction = 'in', labelsize = 12)
			ax[ob,bs].set_ylim(0,max_value)
			ax[ob,bs].text(0.75*7, 0.75*max_value, '{}% Solar \n{}% Wind \n{} hrs storage'
				' \n{}x generation'.format(int(sf*100), int((1-sf)*100), int(batsize[bs]*24), overbuild[ob]))
			ax[ob,bs].text(0.1, 0.93*max_value, fig_labels[ob,bs], fontweight = 'bold', fontsize = 16)
			plt.tight_layout(rect = (0.05, 0.05, 1, 1))

			autolabel(rects, ax[ob,bs])


	fig.text(0.55, 0.02,'Continuous period with <{}% hourly electricity demand met'.format(int(target_power_fraction*100)), 
		fontsize = 16, ha = 'center')
	fig.text(0.02, 0.55,'Occurances throughout 36-year period', fontsize = 16, va = 'center', 
		rotation = 'vertical')


	# plt.show()

	plt.savefig('{}/Histogram_without_{}percentpower_panel_plot_SF-{}_{}.png'
		.format(path_figure, int(target_power_fraction*100), sf, region), format = 'png', dpi=1000)
	plt.close()



