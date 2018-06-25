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

# Each run of the script can only work for one SF.
# Run for the combinations of overbuild and batsize.
#SF = [0.25]
SF = [0.25]
overbuild = [1.0, 1.5]
batsize = [0.00, 0.50] # days
SF_array = np.array([0, 0.25, 0.5, 0.75, 1.]) # solar fraction of energy production

#SF2plot = np.array([0, 0.25, 0.5, 0.75, 1.])
#batsize = np.array([0, 0.5, 4., 32.])
#overbuild = 1.0

#SF = [0.5]
#overbuild = [1.0, 1.5]
#batsize = [0.00, 0.50] # days
#SF_array = np.arange(0,1.01,0.05) # solar fraction of energy production

def stacked_power_plot():
	# import data
#	country = 'USA'
#	path = '/lustre/data/mshaner/merra2/country_files/{}'.format(country)
#	region = 'United States of America'
#	filename_start = '{}_area-weighted-mean_real-demand'.format(region) # start to the file names
#
#	demand_path = '/lustre/data/mshaner/merra2/EIA_demand_files'
	demand = np.load('{}/conus_real_demand.npy'.format(path_input)) * 10**6 # W

	sns.set_style('whitegrid')

	# import solar and wind data
	CF_solar = np.load('{}/{}_CFsolar_area-weighted-mean.npy'.format(path_input, region))
	CF_wind = np.load('{}/{}_CFwind_area-weighted-mean.npy'.format(path_input, region))

	dates_hourly = pd.date_range('1980-01-01 00:00:00', '2015-12-31 23:00:00', freq='H')
	# dates_of_interest = pd.date_range('2014-12-15 00:00:00', '2014-12-21 23:00:00', freq='H')
	dates_of_interest = pd.date_range('2014-08-14 00:00:00', '2014-08-20 23:00:00', freq='H')

	CF_solar_df = pd.DataFrame(CF_solar, index = dates_hourly)
	CF_wind_df = pd.DataFrame(CF_wind, index = dates_hourly)
	demand_df = pd.DataFrame(demand, index = dates_hourly)

	for ob in range(len(overbuild)):

		wind_capacity = np.load('{}/{}_wind_capacity_overbuild-{}.npy'.format(path_output, 
			filename_start, overbuild[ob]))
		solar_capacity = np.load('{}/{}_solar_capacity_overbuild-{}.npy'.format(path_output, 
			filename_start, overbuild[ob]))

		for bs in range(len(batsize)):
 
			unmet_demand = np.load('{}/{}_hourly_power_reliability_SF_batsize-{}-days'
				'_overbuild-{}.npy'.format(path_output, filename_start, batsize[bs], overbuild[ob]))
			battery_state = np.load('{}/{}_battery_state_SF_batsize-{}-days_overbuild-{}.npy'.format(path_output, 
				filename_start, batsize[bs], overbuild[ob]))

			sf_index = np.where(SF_array == SF[0])[0][0]
			unmet_demand_sf = unmet_demand[sf_index, :].squeeze()
			battery_state_sf = battery_state[sf_index, :].squeeze()
			wind_cap = wind_capacity[sf_index]
			solar_cap = solar_capacity[sf_index]

			battery_charging = battery_state_sf[1:] - battery_state_sf[:-1]
			battery_charging[battery_charging < 0] = 0
			battery_discharging = battery_state_sf[1:] - battery_state_sf[:-1]
			battery_discharging[battery_discharging > 0] = 0
			battery_discharging = np.absolute(battery_discharging)

			if batsize[bs] != 0:
				bc_nz_indicies = battery_charging.nonzero()[0]
				bc_diff = np.diff(bc_nz_indicies)
				bc_gone = np.where(bc_diff > 1)[0]
				battery_charging[bc_nz_indicies[bc_gone]] = 0
				battery_charging[bc_nz_indicies[bc_gone]+1] = 0
				battery_charging[bc_nz_indicies[0]] = 0


			unmet_demand_df = pd.DataFrame(unmet_demand_sf, index = dates_hourly)
			battery_charging_df = pd.DataFrame(battery_charging, index = dates_hourly)
			battery_discharging_df = pd.DataFrame(battery_discharging, index = dates_hourly)

			solar_power = CF_solar_df[dates_of_interest[0]:dates_of_interest[-1]] * solar_cap
			wind_power = CF_wind_df[dates_of_interest[0]:dates_of_interest[-1]] * wind_cap
			unmet_power = unmet_demand_df[dates_of_interest[0]:dates_of_interest[-1]]
			demand_power = demand_df[dates_of_interest[0]:dates_of_interest[-1]]
			battery_discharging_power = battery_discharging_df[dates_of_interest[0]:dates_of_interest[-1]]
			battery_charging_power = battery_charging_df[dates_of_interest[0]:dates_of_interest[-1]]

			solar_power = solar_power.squeeze().values
			wind_power = wind_power.squeeze().values
			unmet_power = unmet_power.squeeze().values
			demand_power = demand_power.squeeze().values
			battery_discharging_power = battery_discharging_power.squeeze().values
			battery_charging_power = battery_charging_power.squeeze().values

			curtail_indicies = np.where(solar_power + wind_power > demand_power)
			curtailed_solar = np.zeros(dates_of_interest.size)
			curtailed_wind = np.zeros(dates_of_interest.size)

			for index in curtail_indicies[0]:
				
				curtail = solar_power[index] + wind_power[index] - demand_power[index]
				
				if curtail / 2 > solar_power[index]:
					curtailed_solar[index] = solar_power[index] - battery_charging_power[index] / 2
					curtailed_wind[index] = curtail - solar_power[index] - battery_charging_power[index] / 2
					solar_power[index] = 0
					wind_power[index] = wind_power[index] - curtailed_wind[index] \
						- battery_charging_power[index] / 2

				elif curtail / 2 > wind_power[index]:
					curtailed_wind[index] = wind_power[index] - battery_charging_power[index] / 2
					curtailed_solar[index] = curtail - wind_power[index] - battery_charging_power[index] / 2
					wind_power[index] = 0
					solar_power[index] = solar_power[index] - curtailed_solar[index] \
						- battery_charging_power[index] / 2

				else:
					curtailed_wind[index] = (curtail - battery_charging_power[index]) / 2
					curtailed_solar[index] = (curtail - battery_charging_power[index]) / 2
					wind_power[index] = wind_power[index] - curtailed_wind[index] - battery_charging_power[index] / 2
					solar_power[index] = solar_power[index] - curtailed_solar[index] - battery_charging_power[index] / 2


			solar_power_df = pd.DataFrame(solar_power, index = dates_of_interest)
			wind_power_df = pd.DataFrame(wind_power, index = dates_of_interest)
			unmet_power_df = pd.DataFrame(unmet_power, index = dates_of_interest)
			demand_power_df = pd.DataFrame(demand_power, index = dates_of_interest)
			battery_discharging_power_df = pd.DataFrame(battery_discharging_power, index = dates_of_interest)
			battery_charging_power_df = pd.DataFrame(battery_charging_power, index = dates_of_interest)

			time_shift = -7

			Y = np.zeros((solar_power.size, 5))
			Y[:, 0] = solar_power_df.shift(time_shift).squeeze() / 10**9
			Y[:, 1] = wind_power_df.shift(time_shift).squeeze() / 10**9
			Y[:, 2] = battery_discharging_power_df.shift(time_shift).squeeze() / 10**9
			Y[:, 3] = unmet_power_df.shift(time_shift).squeeze() / 10**9
			Y[:, 4] = battery_charging_power_df.shift(time_shift).squeeze() / 10**9

			demand_power_df = demand_power_df.shift(time_shift)

			colors = ['yellow', 'green', 'orange', 'red', 'blue']

			plt.stackplot(dates_of_interest, Y.T, colors = colors)
			plt.plot(dates_of_interest, demand_power_df / 10**9, color = 'black')
			plt.xticks(rotation = 'vertical', fontsize = 14)
			plt.ylim(0,1000)
			plt.ylabel('Power (GW)', fontsize = 16)
			plt.yticks(fontsize = 14)
			plt.tight_layout()

			# plt.show()

			plt.savefig('{}/Stacked_power_overbuild-{}_storagesize-{}hours_SF-{}_{}.png'
				.format(path_figure, overbuild[ob], batsize[bs]*24, SF[0], region), format = 'png', dpi=1000)
			plt.close()


if __name__ == '__main__':
	stacked_power_plot()








