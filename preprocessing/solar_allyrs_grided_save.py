from glob import glob
import itertools
import netCDF4 as nc
import numpy as np 

data_name = 'swgdn'
path = '/lustre/data/mshaner/merra2/{}/all_yrs_grided'.format(data_name)

fnames = sorted(glob('{}/*270*.nc'.format(path)))

for f in fnames:

  data = nc.Dataset(f)['SWGDN'][:]

  fn1 = f.split('/')[-1].split('_')[1]
  fn2 = f.split('/')[-1].split('_')[2]

  np.save('{}/swgdn_{}_{}'.format(path, fn1, fn2), data)
