import general_reliability_functions as grf
import geopandas as gpd
import numpy as np
import netCDF4 as nc
import pandas as pd
import shapely as spy

# import shapefile
path = '/lustre/data/mshaner/merra2/country_mask_files/NERC_regions'
sf = gpd.GeoDataFrame.from_file('{}/eGRID2012 Subregions_pri.shp'.format(path))

#0    None  (POLYGON ((-64.7618972959018 17.68467547603631...
#1    AKGD  (POLYGON ((-151.6496154661473 59.1198254461873...
# 2    AKMS  (POLYGON ((-179.1075436434378 51.3011990656535...
# 3    AZNM  (POLYGON ((-115.6084700257172 33.2262163500522...
# 4    CAMX  (POLYGON ((-117.2122172498818 32.7734472836062...
# 5    ERCT  (POLYGON ((-97.19963729550715 26.0002172790583...
# 6    FRCC  (POLYGON ((-81.96339182448357 24.5210972971987...
# 7    HIMS  (POLYGON ((-155.9085609250116 19.1811436466020...
# 8    HIOA  (POLYGON ((-157.7154954419322 21.2914399784873...
# 9    MROE  (POLYGON ((-90.85919454273095 43.3691181977416...
# 10   MROW  (POLYGON ((-91.35037184172641 40.7251800092851...
# 11   NEWE  (POLYGON ((-73.62286090796471 40.9837036471760...
# 12   NWPP  (POLYGON ((-108.1366390793909 35.3888827230132...
# 13   NYCW  (POLYGON ((-74.20240999345211 40.5795554704399...
# 14   NYLI  (POLYGON ((-73.72961365255108 40.5963690798683...
# 15   NYUP  (POLYGON ((-76.94667909216631 43.2589400159802...
# 16   RFCE  (POLYGON ((-76.0795563416017 37.03398543549812...
# 17   RFCM  (POLYGON ((-83.43621093131406 41.7430327202138...
# 18   RFCW  (POLYGON ((-82.3901372472782 36.84461092642321...
# 19   RMPA  (POLYGON ((-111.8257472519902 33.4717890726196...
# 20   SPNO  (POLYGON ((-94.49497636480298 36.6170481738557...
# 21   SPSO  (POLYGON ((-91.33069725406914 29.4268218419641...
# 22   SRMV  (POLYGON ((-89.4136945232374 28.92072818575706...
# 23   SRMW  (POLYGON ((-89.2764200177368 41.6123463614092,...
# 24   SRSO  (POLYGON ((-85.49054456552005 29.9821054354902...
# 25   SRTV  (POLYGON ((-90.03447365579531 35.1900563678291...
# 26   SRVC  (POLYGON ((-80.88025908162993 32.0779100215915...

#join polygon subregions to form NERC region

#obtain and combined all polygons for the region of interest
wecc = gpd.GeoDataFrame([sf.iloc[3], sf.iloc[4], sf.iloc[12], sf.iloc[19]])
wecc_uu = wecc.unary_union

#extract areas of each polygon 
areas = []
for i in range(len(wecc_uu)):
	areas.append(wecc_uu[i].area)

#find index of entry with maximum area.  This corresponds to the major region and is orders of
#magnitude larger than the others.  Take that region
areas = np.array(areas)
wecc_maxindex = np.argmax(areas)
wecc_dict = {'Region': 'WECC', 'geometry': wecc_uu[wecc_maxindex]}
wecc_series = gpd.GeoSeries(wecc_dict)


######

mro = gpd.GeoDataFrame([sf.iloc[9], sf.iloc[10]])
mro_uu = mro.unary_union

areas = []
for i in range(len(mro_uu)):
	areas.append(mro_uu[i].area)

areas = np.array(areas)
mro_maxindex = np.argmax(areas)
mro_dict = {'Region': 'MRO', 'geometry': mro_uu[mro_maxindex]}
mro_series = gpd.GeoSeries(mro_dict)

######

spp = gpd.GeoDataFrame([sf.iloc[20], sf.iloc[21]])
spp_uu = spp.unary_union

areas = []
for i in range(len(spp_uu)):
	areas.append(spp_uu[i].area)

areas = np.array(areas)
spp_maxindex = np.argmax(areas)
spp_dict = {'Region': 'SPP', 'geometry': spp_uu[spp_maxindex]}
spp_series = gpd.GeoSeries(spp_dict)

######

tre = gpd.GeoDataFrame(sf.iloc[5])
tre_uu = tre.values[1][0]

areas = []
for i in range(len(tre_uu)):
	areas.append(tre_uu[i].area)

areas = np.array(areas)
tre_maxindex = np.argmax(areas)
tre_dict = {'Region': 'TRE', 'geometry': tre_uu[tre_maxindex]}
tre_series = gpd.GeoSeries(tre_dict)

######

serc = gpd.GeoDataFrame([sf.iloc[22], sf.iloc[23], sf.iloc[24], sf.iloc[25], sf.iloc[26]])
serc_uu = serc.unary_union

areas = []
for i in range(len(serc_uu)):
	areas.append(serc_uu[i].area)

areas = np.array(areas)
serc_maxindex = np.argmax(areas)
serc_dict = {'Region': 'SERC', 'geometry': serc_uu[serc_maxindex]}
serc_series = gpd.GeoSeries(serc_dict)

######

rfc = gpd.GeoDataFrame([sf.iloc[16], sf.iloc[17], sf.iloc[18]])
rfc_uu = rfc.unary_union

areas = []
for i in range(len(rfc_uu)):
	areas.append(rfc_uu[i].area)

areas = np.array(areas)
rfc_maxindex = np.argmax(areas)
rfc_dict = {'Region': 'RFC', 'geometry': rfc_uu[rfc_maxindex]}
rfc_series = gpd.GeoSeries(rfc_dict)

######

frcc = gpd.GeoDataFrame(sf.iloc[6])
frcc_uu = frcc.values[1][0]

areas = []
for i in range(len(frcc_uu)):
	areas.append(frcc_uu[i].area)

areas = np.array(areas)
frcc_maxindex = np.argmax(areas)
frcc_dict = {'Region': 'FRCC', 'geometry': frcc_uu[frcc_maxindex]}
frcc_series = gpd.GeoSeries(frcc_dict)

######

npcc = gpd.GeoDataFrame([sf.iloc[11], sf.iloc[13], sf.iloc[14], sf.iloc[15]])
npcc_uu = npcc.unary_union

areas = []
for i in range(len(npcc_uu)):
	areas.append(npcc_uu[i].area)

areas = np.array(areas)
npcc_maxindex = np.argmax(areas)
npcc_dict = {'Region': 'NPCC', 'geometry': npcc_uu[npcc_maxindex]}
npcc_series = gpd.GeoSeries(npcc_dict)


# make GeoDataFrame from everything and save

NERC_regions = gpd.GeoDataFrame([wecc_series, mro_series, spp_series, tre_series, serc_series, 
	rfc_series, frcc_series, npcc_series])

for n in range(len(NERC_regions)):
	geom = NERC_regions.geometry[n]
	NERC_regions.geometry[n] = spy.geometry.Polygon(geom.exterior)


NERC_regions.to_file('{}/NERC_regions.shp'.format(path))

