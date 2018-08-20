import numpy as np
import pandas as pd
import sys

secs = 60

df = pd.read_hdf(sys.argv[1])
#pr = df.altitude_barometer
pr = (df.raw_pressure_1 + df.raw_pressure_2 + df.raw_pressure_3 + df.raw_pressure_4)/4.
alts = pr.resample('%ds' % secs).mean().astype(np.float32)
lats = df.lat_gps.resample('%ds' % secs).mean().astype(np.float32)
lons = df.long_gps.resample('%ds' % secs).mean().astype(np.float32)
latlons = np.zeros((len(alts), 2))
latlons[:,0] = lats
latlons[:,1] = lons 
np.save('../proc/latlons.npy', latlons)
np.save('../proc/times.npy', alts.index.astype(np.uint64)//(10**9))

t0 = alts.index.astype(np.int64)[0] // 10**9

f = open("../proc/inp.bin", "wb")
f.write(np.uint32(secs).tobytes())
f.write(np.uint32(t0).tobytes())
f.write(np.uint32(len(alts.values)).tobytes())
f.write(alts.values.tobytes())
assert alts.values.dtype == np.float32
f.close()

print('done')