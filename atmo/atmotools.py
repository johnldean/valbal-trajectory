from datetime import datetime as dt 
from datetime import timedelta
import pygrib as gb
import numpy as np 
import matplotlib.pyplot as plt
import math
from urllib.request import urlretrieve
import os
import pickle



def fetchGFSAnalysisData(start,end):
	""" Fetch data from gfs database for times inbetween start and end
	"""
	remote="https://nomads.ncdc.noaa.gov/data/gfsanl/"
	local="../ignored/GFS-anl-0deg5/"
	if not type(start) == type("boop"):
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
		fpath = "gfsanl_3_" + datestr + "_%02d00"%t.hour
		for i in [0,3,6]:
			fulfpath = fpath + "_00%d"%i + ".grb2"
			path = dpath + fulfpath;
			if os.path.exists(local+fulfpath):
				print("Local file "+local+fulfpath+" found, skipping")
			else:	
				print("Fetching from",remote+path+"...",end='',flush=True)
				urlretrieve(remote+path,local+fulfpath)
				print("   done")
			filelist.append(fulfpath)
			times.append(t)
		t +=  timedelta(1/4)
	return filelist,times,start,end,

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

def getGRIBlevels(grib,shortname='v'):
	""" retruns array of all levels in a GRIB file
	"""
	levels = []
	for message in grib:
		if message.shortName == shortname:
			if message.typeOfLevel == "isobaricInhPa":
				levels.append(message.level)
	levels = np.unique(levels)
	return levels

def p2a(x):
	""" Presure to altitude hectopascals to meters 
	"""
	return (1-(x/1013.25)**0.190284)*145366.45*0.3048
