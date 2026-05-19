# Purpose: Download NDBC station data from the NDBC website
#
# Date of Version 01: ???? ??, 201?
# Date of Version 02: Apr. 03, 2025
#
# Author 01: Alexander Nickerson
# Author 02: Alexander Nickerson
#
# Version 02 collects all data from all NDBC stations by examining the full
#            list of stations and recursively parsing through them all
#

import os
import pandas as pd
import numpy as np
import itertools
    
# open the list of NDBC stations

stat_all = pd.read_csv('Docs/List_Download_All.txt',
                        header=0, sep="|", index_col=False)

# formatting is nice for easily scanning the text files, but the extra
# white space needs to be removed
for stat in stat_all.columns:
    if stat_all[stat].dtype == 'object':
        stat_all[stat] = stat_all[stat].str.strip()

# reduce to only NDBC stations
stat_all = stat_all.loc[stat_all["Type"] == "NDBC",:]

# the folder to save the netCDF files
f_new = "Data/NDBC/L00N/"

# create the folder only if necessary
if not os.path.exists(f_new):
    os.makedirs(f_new) 

# loop through all hyperlinks
for i, stat in stat_all.iterrows():
    yr = []
    mo = []
    dy = []
    hr = []
    mn = []
    wt = []
    
    # folder of files to open
    f_old = "Data/NDBC/L00D/" + str(stat["Reg"]) + "_" + stat["Abr"].strip()
    
    # get list of files
    file_all = [f for f in os.listdir(f_old)]
    file_all = sorted(file_all)
    
    # loop through files
    for file in file_all:
        # file to open
        fto = f_old + "/" + file
        
        # skip if the file is empty
        if os.path.getsize(fto) == 0 or 'Store' in file:
            continue
        
        # get the year from the file name
        year = int(file[-8:-4])
        
        # format of the text files varies by year
        if year <= 2006:
            skip = None
        else:
            skip = [1]
        
        # open the text file as a dataframe
        df = pd.read_csv(fto,sep=' +',skiprows=skip,engine='python')
        
        # if there's no data in the file, skip it
        if df.empty:
            print("No data for " + str(stat["Reg"]) + " in year " + str(year))
            continue
        
        # date format varies by year
        if year <= 1998:
            yr = yr + df['YY'].tolist()
        elif year >= 1999 and year <= 2006:
            yr = yr + df['YYYY'].tolist()
        else:
            yr = yr + df['#YY'].tolist()
            
        mo = mo + df['MM'].tolist()
        dy = dy + df['DD'].tolist()
        hr = hr + df['hh'].tolist()
        
        if year >= 2005:
            mn = mn + df['mm'].tolist()
        else:
            mn = mn + [0]*len(df)
            
        wt = wt + df['WTMP'].tolist()
        del(df)
    
    # there are no second stamps, but they're needed for datetime formats
    sc = list(itertools.repeat(0, len(yr)))
    
    date = pd.DataFrame({'year': yr,
                         'month': mo,
                         'day': dy,
                         'hour': hr,
                         'minute': mn,
                         'second': sc})
    
    # get the time stamps in a conventional format
    date["year"] = pd.to_numeric(date["year"],errors='coerce')
    date["month"] = pd.to_numeric(date["month"],errors='coerce')
    date["day"] = pd.to_numeric(date["day"],errors='coerce')
    date['hour'] = pd.to_numeric(date['hour'], errors='coerce')
    date["minute"] = pd.to_numeric(date["minute"],errors='coerce')
    date["second"] = pd.to_numeric(date["second"],errors='coerce')
    
    # some files have 2-digit years (e.g. "99" instead of "1999")
    pt = (date["year"] < 1900)
    yr_old = date["year"][pt == True]
    yr_new = yr_old + 1900
    
    date.loc[pt == True,"year"] = yr_new
    
    # put the timestamp in ISO-8601, the same format ERDDAP uses
    ts = pd.to_datetime(date,format='ISO8601').astype('datetime64[s]')
        
    # get the water temperature
    wtmp = pd.DataFrame({'WTMP': wt})    
    wtmp['WTMP'] = pd.to_numeric(wtmp['WTMP'], errors='coerce') 
    
    # create dataframes for data, QC, and reason for QC
    dict_new = {'time': ts,
                'latitude': stat["Lat"]*np.ones(np.shape(ts),
                                      dtype="float64"),
                'longitude': stat["Lon"]*np.ones(np.shape(ts),
                                      dtype="float64"),
                'z': -1.5*np.ones(np.shape(ts),
                                      dtype="float64"),
                'wt_old': wtmp["WTMP"],
                'wt_new': wtmp["WTMP"],
                'wt_flag': 2*np.ones(np.shape(ts),
                                        dtype="int8"),
                'wt_info': np.full(np.shape(ts), 
                                        "Not tested",
                                        dtype='O')}
    
    df_new = pd.DataFrame(data=dict_new)
    df_new = df_new.sort_values(by='time')
    
    # remove points where the minute isn't 00 and the temp is 999.0 because
    # it most likely means the instrument wasn't designed to record at these
    # times, although other measurements are recorded
    is_min = (date['minute'] != 0)
    is_999 = (df_new['wt_new'] > 100)
    is_bad = (is_min & is_999)
    
    # 999.9 degrees is the NDBC format for missing data in their text files
    df_new.loc[is_999 == True,'wt_new'] = np.nan
    df_new.loc[is_999 == True,'wt_flag'] = 4
    df_new.loc[is_999 == True,'wt_info'] = "Instrument Failure (999.0 deg C)"
    
    # measurements between hours are often post-facto interpolations and not 
    # real measurements or often indicate instrumentation failure
    df_new = df_new.loc[~is_bad]
    
    # set the index and convert to an xarray
    df_new = df_new.set_index(['time'])
    ds_new = df_new.to_xarray()
    
    # define the long variable names
    ds_new.attrs["long_name"] = [
        "longitude",
        "latitude",
        "depth",
        "water temperature",
        "water temperature (QC)",
        "water temperature QARTOD flag",
        "water temperature QARTOD failure reason"]
    
    # assign the units
    ds_new.attrs["units"] = [
        "degrees north",
        "degrees east",
        "m below surface",
        "degrees C",
        "degrees C",
        "QARTOD flag",
        "QARTOD flag reason"]
    
    # save the dataset
    ncf = f_new + str(stat["Reg"]) + ".nc"
    ds_new.to_netcdf(path=ncf, mode="w")
    
    del(ds_new)
    del(df_new)
    
    print("Successfully saved station " + str(stat["Reg"]))
        
print('Finished all stations.');
