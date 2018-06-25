import numpy as np 
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
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

time_bins = np.array([1,3,6,12,24,48,96,192,384,768,1536])
demand_met_bins = np.arange(0,1.01,0.1)

for sf in SF:
	max_value = 0 # initialize value for maximum y axis height
	fig_labels = np.array([['a', 'b'],['c', 'd']])

	sns.set_style('whitegrid')
	fig, ax = plt.subplots(2,2, sharex = True, sharey = True, figsize = (12,8))
	cbar_ax = fig.add_axes([.91, .3, .03, .4])

	for bs in range(len(batsize)):
		for ob in range(len(overbuild)):

			reliable_array = np.load('{}/{}_hourly_power_reliability_SF_batsize-{}-days'
				'_overbuild-{}.npy'.format(path_output, filename_start, batsize[bs], overbuild[ob]))

			sf_index = np.where(SF_array == sf)
			rel_array_sf = reliable_array[sf_index, :].squeeze()
			power_delivered_fraction = (demand - rel_array_sf) / demand

			sign_change = np.equal(np.ones(power_delivered_fraction.size), power_delivered_fraction) # when all demand is met == True, else == False
			sign_change = sign_change.astype(int) # change bools to ints

			neg2pos_indicies = np.where(np.diff(sign_change) == -1)[0] # previous values come from below power of interest and go above
			pos2neg_indicies = np.where(np.diff(sign_change) == 1)[0] # previous values come from above power of interest and go below

			if (len(pos2neg_indicies) > 0) & (len(neg2pos_indicies) > 0):
				
				if pos2neg_indicies[0] < neg2pos_indicies[0]: # starts by coming from above (not enough power)

					if neg2pos_indicies[-1] > pos2neg_indicies[-1]: # ends by staying above

						hours_below_target_power = np.array((pos2neg_indicies[1:] - 
							neg2pos_indicies[:-1]))
						avg_power_delivered = np.zeros(pos2neg_indicies.size-1)
						for i in range(pos2neg_indicies.size-1):
							avg_power_delivered[i] = np.sum(power_delivered_fraction
								[neg2pos_indicies[i]:pos2neg_indicies[i+1]])

						print 1

					else: # ends by staying below

						hours_below_target_power = np.array((pos2neg_indicies[1:] - neg2pos_indicies))
						avg_power_delivered = np.zeros(pos2neg_indicies.size-1)
						for i in range(pos2neg_indicies.size-1):
							avg_power_delivered[i] = np.sum(power_delivered_fraction
								[neg2pos_indicies[i]:pos2neg_indicies[i+1]])

						print 2

				else: # starts by coming from below (enough power)

					if neg2pos_indicies[-1] > pos2neg_indicies[-1]: # ends by staing above

						hours_below_target_power = np.array((pos2neg_indicies - neg2pos_indicies[:-1]))
						avg_power_delivered = np.zeros(pos2neg_indicies.size)
						for i in range(pos2neg_indicies.size):
							avg_power_delivered[i] = np.sum(power_delivered_fraction
								[neg2pos_indicies[i]:pos2neg_indicies[i]])

						print 3


					else: # ends by staing below

						hours_below_target_power = np.array((pos2neg_indicies - neg2pos_indicies))
						avg_power_delivered = np.zeros(pos2neg_indicies.size)
						for i in range(pos2neg_indicies.size):
							avg_power_delivered[i] = np.sum(power_delivered_fraction
								[neg2pos_indicies[i]:pos2neg_indicies[i]])

						print 4


			avg_power_delivered = avg_power_delivered / hours_below_target_power

			hist, xedges, yedges = np.histogram2d(avg_power_delivered, hours_below_target_power, bins = (demand_met_bins, time_bins))
			hist = hist/36

			mask = np.ones(hist.shape)
			mask[hist>0] = 0

			max_holder = hist.max()
			if max_holder > max_value:
				max_value = max_holder

			x = np.arange(0,time_bins.size)
			y = np.arange(0,demand_met_bins.size)


			im = ax[ob,bs].pcolor(hist, cmap = 'inferno_r', norm = LogNorm(vmin=0.01, 
				vmax=12500/36), edgecolor = 'black', linewidth = 0.1)

			for a in range(hist.shape[0]):
				for b in range(hist.shape[1]):
					if hist[b, a] >0.1:
						if hist[b, a] > 10:
							ax[ob,bs].text(a + 0.5, b + 0.5, '%.0f' % hist[b, a], ha='center', 
									va='center', color = 'white')
						elif hist[b, a] < 10 and hist[b,a] >= 1:
							ax[ob,bs].text(a + 0.5, b + 0.5, '%.1f' % hist[b, a], ha='center', 
									va='center', color = 'white')
						else:
							ax[ob,bs].text(a + 0.5, b + 0.5, '%.2f' % hist[b, a], ha='center', 
								va='center', color = 'white')
					elif hist[b,a] >= 0.01:
						ax[ob,bs].text(a + 0.5, b + 0.5, '%.2f' % hist[b, a], ha='center', 
							va='center', color = 'black')


			ax[ob,bs].set_xlim(0,x.max())
			ax[ob,bs].set_xticks(x[:-1]+0.5)
			ax[ob,bs].set_xticklabels(['1-3 hrs', '3-6 hrs', '6-12 hrs', '12-24 hrs', '1-2 days',
				'2-4 days', '4-8 days', '8-16 days', '16-32 days', '32-64 days'], 
				fontsize = 12, rotation = 'vertical')
			ax[ob,bs].set_ylim(0,y.max())
			ax[ob,bs].set_yticks(y[:-1]+0.5)
			ax[ob,bs].set_yticklabels(['0-10%', '10-20%', '20-30%', '30-40%', '40-50%', '50-60%',
				'60-70%', '70-80%', '80-90%', '90-<100%'], fontsize = 12, rotation = 'horizontal')
			ax[ob,bs].text(-0.4, 0.91*demand_met_bins.size, fig_labels[ob,bs], 
				fontweight = 'bold', fontsize = 16)
			

	plt.tight_layout(rect = (0.05, 0.05, 0.9, 1))
	cbar = fig.colorbar(im, cax = cbar_ax)
	cbar.ax.tick_params(labelsize = 12)
	fig.text(0.55, 0.02,'Duration of continuous period with <100% power demand met', fontsize = 16, ha = 'center')
	fig.text(0.02, 0.55,'Average percentage of power demand met', fontsize = 16, va = 'center', 
		rotation = 'vertical')
	fig.text(0.98, 0.52, 'Number of events per year', rotation = 'vertical', va = 'center', fontsize = 14)


	# plt.show()

	plt.savefig('{}/Heatmap_quantitynduration_with_power_panel_plot_SF-{}_{}.png'
		.format(path_figure, sf, region), format = 'png', dpi=1000)
	plt.close()



