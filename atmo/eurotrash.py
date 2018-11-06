from datetime import datetime as dt 
from datetime import timedelta
import pygrib as gb
import numpy as np 
import matplotlib.pyplot as plt
import math
from urllib.request import urlretrieve
import os
import pickle
import pandas as pd

def fetchWindData(start,end,db='gfs_anl_1deg'):
    raise ValueError("lol good luck son")

def procWindData(src,db='euro_fc',overwrite=False):
    dstpath = "../ignored/proc/"+ db + "/"
    srcpath = "../ignored/raw/" + db + "/"
    if not os.path.exists(dstpath):
        os.makedirs(dstpath)

    grb = gb.open(srcpath+src)
    lats,lons = grb.select(shortName="u",typeOfLevel='isobaricInhPa',level=250)[0].latlons() #arbitrary data, doing this for latlons
    lats = lats[:,0]
    lons = lons[0,:]
    levels = getGRIBlevels(grb)
    print(list(levels))
    grb = gb.open(srcpath+src)
    headertext = genWindHeader(db,lons,lats,levels)
    headerfile = dstpath + db + ".h"
    with open(headerfile,"w") as f:
        f.write(headertext)
    last = np.inf 
    lst = []
    arr = None
    for x in grb:
        if x.level < last:
            """print(x)
            print(dir(x))
            for k in dir(x):
                if not k.startswith("_"): print(k, getattr(x,k))
            print(x.has_key("fcst time"))
            print(x.stepRange)"""
            if arr is not None:
                arr.flatten().tofile(dstpath+str(tgt)+'.bin')
            date = x.validDate + timedelta(hours = int(x.stepRange))
            tgt = int((date-dt(1970,1,1)).total_seconds())
            i = 0.
            print("NEW FILE", tgt)
            arr = np.zeros((lats.size, lons.size, levels.size, 2), dtype=np.int16)
        j = 0 if x.shortName == "u" else 1
        arr[:,:,int(i),j] = x.values*100
        #print(x.level, x.shortName, int(i), j)
        i += 0.5
        last = x.level
    exit()
    lats,lons = grb.select(shortName="u",typeOfLevel='isobaricInhPa',level=250)[0].latlons() #arbitrary data, doing this for latlons
    levels = getGRIBlevels(grb)
    for k,file in enumerate(files):
        outpath = dstpath + '%d.bin' % (times[k]-dt(1970,1,1)).total_seconds()
        ss = times[k].strftime("%s") == "1529002800"
        print("ss", ss)
        if not ss: continue
        if os.path.exists(outpath) and not overwrite:
            print("Local file "+outpath+" found, skipping (%d / %d)" % (k+1, len(files)))
        else:    
            #print("Saving to",outpath+"...",end='',flush=True)
            #print("hmm", lats, lons)
            data = np.zeros((lats.size,lons.size,levels.size,2),dtype=np.int16)
            path = srcpath+file
            grb = gb.open(path)
            i = 0.
            for row in grb:
                if row.shortName == 'u' or row.shortName == 'v':
                    if row['typeOfLevel'] == 'isobaricInhPa' and row.level >= levels[0] and row.level <= levels[-1]:
                        j = 0 if row.name.startswith('U') else 1
                        print(row.shortName, row.level, int(row.values[95,584]*100))
                        data[:,:,int(i),j] = row.values*100
                        i += 0.5
            data.flatten().tofile(outpath)
            print("   done (%d / %d)" % (k+1, len(files)))

def getGRIBlevels(grib,shortname='v'):
    """ returns array of all levels in a GRIB file """
    levels = []
    for message in grib:
        if message.shortName == shortname:
            if message.typeOfLevel == "isobaricInhPa":
                levels.append(message.level)
    levels = np.unique(levels)
    return levels

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

#procWindData("63fc.grib",db="euro_fc",overwrite=not False)
#procWindData("fc67.grib",db="euro_fc",overwrite=not False)