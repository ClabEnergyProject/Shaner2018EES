
from numba import jit
import numpy as np
# import pandas as pd


#common function that calculates wind capacity factor given windspeeds
@jit
def windcf_calc(wind_speed): # calculate wind capacity factor
	
	u_ci = 3 # cut in speed in m/s
	u_r = 15 # rated speed in m/s
	u_co = 25 # cut out speed in m/s


	CF_wind = np.zeros(wind_speed.shape) # initialize array
	CF_wind[wind_speed < u_ci] = 0 # for all wind speed values less than cut in speed no power is produced (CF=0)
	CF_wind[(u_ci <= wind_speed) & (wind_speed < u_r)] = wind_speed[(u_ci <= wind_speed) & (wind_speed < u_r)]**3/u_r**3 # for all wind speed values between cut in and rated speeds the CF goes by u cubed
	CF_wind[(u_r <= wind_speed) & (wind_speed <= u_co)] = 1 # for all wind speed values above the rated speed CF = 1

	return CF_wind

# common function that calculates the wind and solar capacities
def capacity_calc(CF_wind, CF_solar, SF, pwr_avg, hours_in_period):

	wind_capacity = np.zeros(SF.size)
	solar_capacity = np.zeros(SF.size)

	counter = 0
	for sf in SF:
		wind_capacity[counter] = ((1-sf) * pwr_avg * hours_in_period) / CF_wind.sum()
		solar_capacity[counter] = sf * pwr_avg * hours_in_period / CF_solar.sum()

		counter += 1

	return wind_capacity, solar_capacity


# common function that takes in CF_wind, CF_solar data and user specified values and 
# calculates the capacities and reliabilities for each case
def reliability_calc(CF_wind, wind_capacity, CF_solar, solar_capacity, demand, batsize, SF, hours_in_period):

	solarfrac = range(SF.size)

	# initialize arrays for collection reliabilities
	binary_reliability = np.zeros((SF.size, hours_in_period)) # will collect hours unable to met demand at each time step
	binary_reliability_sum = np.zeros(SF.size) # holder for biniary reliability over all time for a given SF
	power_reliability = np.zeros((SF.size, hours_in_period)) # will collect amount of power unable to be delivered at each time step
	power_reliability_sum = np.zeros(SF.size) # holder for reliability of power for all time for a given SF
	battery_state = np.zeros((SF.size, hours_in_period + 1)) # initialize array; need +1 because first entry is initial state

	for sf in solarfrac: # loop through all solar fractions
		
		# supply - demand at each time step                            
		power = (np.squeeze(solar_capacity[sf]) * np.squeeze(CF_solar) + \
				np.squeeze(wind_capacity[sf]) * np.squeeze(CF_wind)) - demand

		for time in range(0,hours_in_period): # loop through all times
			
			bs_next_state = battery_state[sf, time] + power[time] # starting point for next battery state; will be bounded by empty and full battery below

			#discharging
			if power[time] < 0:

				if bs_next_state < 0: # if some power demand cannot be met, i.e. energy stored in battery isn't enough
					binary_reliability[sf, time] = 1 # record that hour as unreliabile
					power_reliability[sf, time] = np.absolute(bs_next_state) # add amount of power that cannot be delivered to running sum
					# next battery state is 0, which is the default

				else: # if enough energy left in battery to meet demand
					battery_state[sf, time+1] = bs_next_state # next battery state is current state minus discharged amount

			#charging
			else:

				battery_state[sf, time+1] = min(bs_next_state, batsize) # either something less than full or full
			
		# now go back through battery state using last battery state to reloop through years until the values don't change...stable solution reached
		time = 0
		num_iters = 0
		for anything in range(0,hours_in_period * 10): # the potential to loop through the battery state many times

			# calculate the potential next battery state
			if time != 0: 
				possible_next_bs_state = battery_state[sf, time] + power[time]

			else: # use end state of battery as initial state instead of original initial state, this will be true least often so put as else statement
				possible_next_bs_state = battery_state[sf, -1] + power[time]
			
			# determine what poential next battery state is given battery size bounds of full or empty
			if power[time] < 0:

				if possible_next_bs_state < 0: # if some power demand cannot be met, i.e. energy stored in battery isn't enough
					binary_reliability[sf, time] = 1 # record that hour as unreliabile
					power_reliability[sf, time] = np.absolute(possible_next_bs_state) # add amount of power that cannot be delivered to running sum
				else:
					binary_reliability[sf, time] = 0 # record that hour as reliable...may have been unreliable in previous run
					power_reliability[sf, time] = 0 # record that hour as reliable...may have been unreliable in previous run


				possible_next_bs_state = max(possible_next_bs_state, 0)

			else:
				possible_next_bs_state = min(possible_next_bs_state, batsize)

			# if steady solution reached break out of loop, otherwise give battery state new value and go next time step
			if battery_state[sf, time+1] == possible_next_bs_state:
				break

			else:
				battery_state[sf, time+1] = possible_next_bs_state
				time += 1

				if time >= hours_in_period: # if end of battery state reached, start over
					time = 0

			num_iters += 1 #count number of iterations just to see how far this has to go before steady solution is achieved

		# calculate fraction of power able to be delivered since recorded values are power unable to be delivered
	binary_reliability_sum = 1 - binary_reliability.sum(axis=1) / hours_in_period
	power_reliability_sum = 1 - power_reliability.sum(axis=1) / (demand.sum())

	# return results
	return binary_reliability, binary_reliability_sum, power_reliability, power_reliability_sum, battery_state
