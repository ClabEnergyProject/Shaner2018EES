from glob import glob
import itertools
import netCDF4 as nc
import numpy as np 

data_name = 'uv50m'
path = '/lustre/data/mshaner/merra2/{}/all_years_grided'.format(data_name)

fnames = sorted(glob('{}/*90*.nc'.format(path)))

for f in fnames:

  data = nc.Dataset(f)
  
  windspeed = np.hypot(data['V50M'], data['U50M'])

  fn1 = f.split('/')[-1].split('_')[1]
  fn2 = f.split('/')[-1].split('_')[2]

  np.save('{}/windspeed_{}_{}'.format(path, fn1, fn2), windspeed)
