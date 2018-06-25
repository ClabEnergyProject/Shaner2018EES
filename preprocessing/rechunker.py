from glob import glob
import multiprocessing
import os 
import subprocess
import time

def rechunk(fname):
  out_parts = os.path.basename(fname).split('.')
  out_fname = out_parts[0] + "_rc.nc"
  out_path = "/".join([os.path.dirname(fname), out_fname])
  sys_call = 'nccopy -m 14000 -c "TIME_EOSGRID/1035,XDim_EOSGRID/29,YDim_EOSGRID/35" %s %s' % (fname, out_path)
  print "Processing %s" % sys_call
  subprocess.call(sys_call, shell=True)

def main(par=1):
  
  dirname = "/lustre/data/mshaner/wind_data"
  pattern = "U50M_V50M_*.nc" 
  fnames = glob("/".join([dirname, pattern]))
  print fnames
  if par == 1:
    p = multiprocessing.Pool(5)
    p.map(func=rechunk, iterable=fnames, chunksize=1)
    time.sleep(1)
  else: 
    rechunk(fnames[0])
    
  
 
if __name__ == main():
  main()
