import numpy as np
from glob import glob
import itertools


lats = range(0,361,90)
lats[-1] += 1
lons = range(0,577,192)

for (xs, xe), (ys, ye) in itertools.product(zip(lats[0:-1],lats[1::]),zip(lons[0:-1],lons[1::])):

	wind_speed = np.load('/lustre/data/mshaner/merra2/uv50m/all_years_grided/windspeed_{}-{}_{}-{}.npy'.format(xs, xe-1, ys, ye-1))

	u_ci = 3 # cut in speed in m/s
	u_r = 15 # rated speed in m/s
	u_co = 25 # cut out speed in m/s

	CF_wind = np.zeros(wind_speed.shape)

	CF_wind[wind_speed < u_ci] = 0
	CF_wind[(u_ci <= wind_speed) & (wind_speed < u_r)] = wind_speed[(u_ci <= wind_speed) & (wind_speed < u_r)]**3/u_r**3
	CF_wind[(u_r <= wind_speed) & (wind_speed <= u_co)] = 1


	np.save('/lustre/data/mshaner/merra2/uv50m/all_years_grided/windCF_uci-{}_ur-{}_uco-{}_{}-{}_{}-{}'.format(u_ci, u_r, u_co, xs, xe, ys, ye), CF_wind)
