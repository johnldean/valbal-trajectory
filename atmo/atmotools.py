from datetime import datetime as dt 
from datetime import timedelta
import pandas as pd
import pygrib as gb
import numpy as np 
import matplotlib.pyplot as plt
import math
from urllib.request import urlretrieve
import os
import pickle

def fetchWindData(start,end,db='gfs_anl_0deg5'):
	""" Fetch data from gfs database for times inbetween start and end
	"""
	if db == 'gfs_anl_1deg':
		remote="https://nomads.ncdc.noaa.gov/data/gfsanl/"
		local="../ignored/raw/gfs_anl_1deg/"
		fstartname = "gfsanl_3_"
	if db == 'gfs_anl_0deg5':
		remote="https://nomads.ncdc.noaa.gov/data/gfsanl/"
		local="../ignored/raw/gfs_anl_0deg5/"
		fstartname = "gfsanl_4_"
	if db == "euro_fc":
		raise ValueWarning("lol good luck son, this data is not easy to get")
		return 
	if not os.path.exists(local):
		os.makedirs(local)
	if not type(start) == type("boop"):
		start -= timedelta(hours=1)
		start = "%04d-%02d-%02d_%02d"%(start.year,start.month,start.day,start.hour)
		end = "%04d-%02d-%02d_%02d"%(end.year,end.month,end.day,end.hour)		
	print(start)
	t = dt.strptime(start,"%Y-%m-%d_%H");
	t = t.replace(hour=math.floor(t.hour/6)*6,minute=0,second=0)
	end_t = dt.strptime(end,"%Y-%m-%d_%H") + timedelta(1/4);
	start = "%04d-%02d-%02d_%02d"%(t.year,t.month,t.day,t.hour)
	end = "%04d-%02d-%02d_%02d"%(end_t.year,end_t.month,end_t.day,end_t.hour)
	print("Downloading files")
	filelist = []
	times = []
	while t < end_t:
		datestr = "%04d%02d%02d" % (t.year, t.month, t.day) 
		dpath = "%04d%02d/"% (t.year, t.month) + datestr + "/"
		fpath = fstartname + datestr + "_%02d00"%t.hour
		for i in [0,3]:
			fulfpath = fpath + "_00%d"%i + ".grb2"
			path = dpath + fulfpath;
			if os.path.exists(local+fulfpath):
				print("Local file "+local+fulfpath+" found, skipping")
			else:	
				print("Fetching from",remote+path+"...",end='',flush=True)
				urlretrieve(remote+path,local+fulfpath)
				print("   done")
			filelist.append(fulfpath)
			times.append(t + i*timedelta(1/24))
		t +=  timedelta(1/4)
	return filelist,times,start,end

def procWindData(start,end,db='gfs_anl_0deg5',overwrite=False):
	dstpath = "../ignored/proc/" + db + "/"
	srcpath = "../ignored/raw/" + db + "/"
	ret = fetchWindData(start,end,db)
	times = ret[1]
	files = ret[0]
	if not os.path.exists(dstpath):
		os.makedirs(dstpath)

	grb = gb.open(srcpath+files[0])
	lats,lons = grb.select(shortName="u",typeOfLevel='isobaricInhPa',level=250)[0].latlons() #arbitrary data, doing this for latlons
	lats = lats[:,0]
	lons = lons[0,:]
	levels = getGRIBlevels(grb)
	headertext = genWindHeader(db,lons,lats,levels)
	headerfile = dstpath + db + ".h"
	procfiles=[]
	with open(headerfile,"w") as f:
		f.write(headertext)
	keys = {"lons":lons, "lats":lats, "levels": levels, "alts": p2a(levels)}
	pickle.dump(keys,open(dstpath + "keys.pickle",'wb'))
	for k,file in enumerate(files):
		outpath = dstpath + '%d.bin' % (times[k]-dt(1970,1,1)).total_seconds()
		#print(times[k]) 
		#exit()
		procfiles.append(outpath)
		if os.path.exists(outpath) and not overwrite:
			print("Local file "+outpath+" found, skipping (%d / %d)" % (k+1, len(files)))
		else:	
			print("Saving to",outpath+"...",end='',flush=True)
			data = np.zeros((lats.size,lons.size,levels.size,2),dtype=np.int16)
			path = srcpath+file
			grb = gb.open(path)
			i = 0.
			for row in grb:
				if row.shortName == 'u' or row.shortName == 'v':
					if row['typeOfLevel'] == 'isobaricInhPa' and row.level >= levels[0] and row.level <= levels[-1]:
						j = 0 if row.name.startswith('U') else 1
						data[:,:,int(i),j] = row.values*100
						i += 0.5
			data.flatten().tofile(outpath)
			print("   done (%d / %d)" % (k+1, len(files)))
	return procfiles,times



def genWindHeader(dataset,lons,lats,levels):
	filetext = "#ifndef __%s__ \n\r" % dataset
	filetext += "#define __%s__ \n\r \n\r" % dataset
	filetext += "/* \n\r"
	filetext += " * This header is auto-generated by atmotools.py. \n\r"
	filetext += " * For the dataset '%s'. \n\r" % dataset
	filetext += " */ \n\r \n\r"
	filetext += "typedef short wind_t; // Type used to store wind data on disk, in cm/s. \n\r \n\r"
	filetext += "/* wind grid paramters */ \n\r"
	filetext += "const float LON_MIN = %f;\n\r" % lons[0]
	filetext += "const float LON_MAX = %f;\n\r" % lons[-1]
	filetext += "const float LON_D = %f;\n\r" % (lons[1] - lons[0])
	filetext += "const int NUM_LONS = %d;\n\r" % lons.size
	filetext += "const float LAT_MIN = %f;\n\r" % lats[0]
	filetext += "const float LAT_MAX = %f;\n\r" % lats[-1]
	filetext += "const float LAT_D = %f;\n\r" % (lats[1] - lats[0])
	filetext += "const int NUM_LATS = %d;\n\r" % lats.size
	filetext += "const float LEVELS[] = {" + ",".join(map(str,levels*100)) + "}; \n\r"
	filetext += "const int NUM_LEVELS = sizeof(LEVELS)/sizeof(LEVELS[0]); \n\r"
	filetext += "const int NUM_VARIABLES = 2; \n\r \n\r"
	filetext += "#endif \n\r"
	return filetext;



def makeWindArray(start,end,overwrite=False,altitude_range=[10000,20000],name_modifier=''):
	""" gets data and returns in a mulitdimentional array of format:
		[lon,lat,alt,time,pred,vaules]
	"""
	files,times,start,end = fetchGFSAnalysisData(start,end)
	local="../ignored/GFS-anl-0deg5/"
	filepath = "../ignored/GFS_anl_0deg5_objs/" + start + "_to_" +end + name_modifier+ ".pickle"
	filepath2 = "../ignored/GFS_anl_0deg5_objs/" + start + "_to_" +end + name_modifier+".npy"
	if os.path.exists(filepath) and not overwrite: print("File " +filepath+ " already exists, skipping") ; return filepath,filepath2
	windobj = {}
	grb = gb.open(local+files[0])
	lat,lon = grb.select(shortName="u",typeOfLevel='isobaricInhPa',level=250)[0].latlons() #arbitrary data, doing this for latlons
	windobj["lats"] = lat[:,0] 
	nlats = lat[:,0].size
	windobj["lons"] = lon[0,:]
	nlons = lon[0,:].size
	windobj["values"] = ["u","v"]
	nvalues = 2;
	levels = getGRIBlevels(grb,windobj["values"][0])
	alts = p2a(levels)
	idxs = np.where(np.logical_and(altitude_range[0]<=alts,alts<=altitude_range[1]))
	levels = levels[idxs]
	alts = alts[idxs]
	windobj["levels"] = levels
	windobj["alts"] = alts
	nalts = alts.size
	timeshr = np.unique([(t - times[0]).seconds/3600 + (t - times[0]).days*24 for t in times])
	ntimes = timeshr.size
	windobj["times"] = timeshr
	windobj["start_time"] = times[0]
	tdelatshr = np.array([0.0,3.0,6.0]);
	windobj["tdeltas"] = tdelatshr;
	ntdeltas = 3;
	data = np.zeros((nlons,nlats,nalts,ntimes,ntdeltas,nvalues))
	dtind = 0
	tind = 0
	print("Starting to build array. This may take a while :(")
	total = nvalues*ntdeltas*ntimes
	ctr = 0
	for i in range(len(files)):
		path = local+files[i]
		grb = gb.open(path)
		for valind,val in enumerate(windobj["values"]): #this could be sped up by a factor of 2 if u selected both vals are once. But then have to be sure they are returned in the correct order
			dat = grb.select(shortName=val,typeOfLevel='isobaricInhPa',level=levels)
			data[:,:,:,tind,dtind,valind] = np.array(list(map(lambda x : x.values,dat))).T
			ctr+=1
			print("%d/%d"%(ctr,total))
		dtind += 1
		if dtind == 3 : tind += 1; dtind=0
	print("done")
	print("Saving to ",filepath)
	pickle.dump(windobj,open(filepath,'wb'))
	print("Saving to ",filepath2)
	np.save(filepath2,data)
	return filepath,filepath2

def getGRIBlevels(grib,shortname='v',altitude_range = [0,20000]):
	""" retruns array of all levels in a GRIB file
	"""
	levels = []
	for message in grib:
		if message.shortName == shortname:
			if message.typeOfLevel == "isobaricInhPa":
				levels.append(message.level)
	levels = np.unique(levels)
	alts = p2a(levels)
	idxs = np.where(np.logical_and(altitude_range[0]<=alts,alts<=altitude_range[1]))
	levels = levels[idxs]
	return levels

def p2a(x):
	""" Presure to altitude hectopascals to meters 
	"""
	return (1-(x/1013.25)**0.190284)*145366.45*0.3048

def getKeysForBin(filepath):
	keypath = "/".join(filepath.split("/")[:-1])+"/keys.pickle"
	return pickle.load(open(keypath,'rb'))

def getArrayFromBin(filepath,keys):
	return np.fromfile(filepath,dtype=np.int16).reshape(keys["lats"].size,keys["lons"].size,keys["levels"].size,2)

'''
df = pd.read_hdf('../../valbal-controller/ssi67-analysis/ssi67.h5')
print(df.long_gps.values[1000])
print(df.lat_gps.values[1000])
print(df.index[0])
procWindData(df.index[0],df.index[-1] + timedelta(2),db="gfs_anl_0deg5",overwrite=False)
'''

#procWindData("2018-09-05_00","2018-09-21_00",db="gfs_anl_0deg5",overwrite=False)
