import numpy as np 
import pandas as pd

def main():
	# import demand data files, all values are in MW

	path = '/lustre/data/mshaner/merra2/EIA_demand_files'

	jul_dec_2015 = pd.read_excel('{}/EIA930_BALANCE_2015_Jul_Dec_modified.xlsx'.format(path), index_col = 0)
	jan_jul_2016 = pd.read_excel('{}/EIA930_BALANCE_2016_Jan_Jul_modified.xlsx'.format(path), index_col = 0)
	jul_jul_2016 = pd.read_excel('{}/EIA930_BALANCE_2016_Jul_Jul_modified.xlsx'.format(path), index_col = 0)

	# groupby and sum data files

	gb_2015 = jul_dec_2015.groupby(lambda x: (x.month, x.day, x.hour))
	gb_2016 = jan_jul_2016.groupby(lambda x: (x.month, x.day, x.hour))
	gb_2016_jul = jul_jul_2016.groupby(lambda x: (x.month, x.day, x.hour))

	sum_2015 = gb_2015.sum()
	sum_2016 = gb_2016.sum()
	sum_2016_jul = gb_2016_jul.sum()


	# modify datasets so correct chronological order

	sum_2015 = sum_2015.dropna()
	sum_2015 = sum_2015.sort_index()

	sum_2016 = sum_2016.dropna()
	sum_2016 = sum_2016.sort_index()

	sum_2016_jul = sum_2016_jul.dropna()
	sum_2016_jul = sum_2016_jul.sort_index()

	# modify 2015 dataset so jan 2016 dates are at end

	for i in range(9):
		holder = sum_2015.iloc[0]
		sum_2015 = sum_2015.ix[1:]
		sum_2015 = sum_2015.append(holder)

	# make date ranges for each dataset

	dates_2015 = pd.date_range('2015-07-01 05:00:00', '2016-1-1 08:00:00', freq='H')
	dates_2016 = pd.date_range('2016-01-01 06:00:00', '2016-7-1 07:00:00', freq='H')
	dates_2016_jul = pd.date_range('2016-07-01 05:00:00', '2016-7-18 07:00:00', freq='H')

	# make dataframes and combine them

	columns = ['VAL_D', 'VAL_DF', 'VAL_NG', 'VAL_TI']

	df_2015 = pd.DataFrame(sum_2015.values, index = dates_2015, columns = columns)
	df_2016 = pd.DataFrame(sum_2016.values, index = dates_2016, columns = columns)
	df_2016_jul = pd.DataFrame(sum_2016_jul.values, index = dates_2016_jul, columns = columns)

	df_combo = df_2015.add(df_2016, fill_value = 0)
	df_combo = df_combo.add(df_2016_jul, fill_value = 0)

	# cut data so it is represents exactly one year.  3 24 hour periods into dataset was chosen because
	# the overlap between the first entry and last entry are relatively good...there isn't a large jump
	# in demand between the 2015 and 2016 connection in july

	one_year_w_leap = df_combo.iloc[2+24*3:8784+2+24*3]
	one_year_w_leap = one_year_w_leap.groupby(lambda x: (x.month, x.day, x.hour))
	one_year_w_leap = one_year_w_leap.sum() # doesn't actually sum anything, just allows you to collect data values

	# create year without leap, leap day is 1416:1439
	one_year_no_leap = one_year_w_leap.ix[:1416]
	one_year_no_leap = one_year_no_leap.add(one_year_w_leap.ix[1440:], fill_value = 0)

	# create 36 year string of demand

	conus_demand = []
	leaps = [1980, 1984, 1988, 1992, 1996, 2000, 2004, 2008, 2012]

	for year in np.arange(1980, 2016):

		if year in leaps:

			conus_demand.append(one_year_w_leap['VAL_D'].values)

		else:

			conus_demand.append(one_year_no_leap['VAL_D'].values)

	conus_demand = [f for list in conus_demand for f in list]
	conus_demand_np = np.array(conus_demand)

	np.save('{}/conus_real_demand'.format(path), conus_demand_np)


if __name__ == '__main__':
	main()



