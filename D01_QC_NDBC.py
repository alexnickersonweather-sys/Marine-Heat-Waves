# Purpose: run quality control on NDBC data
#
# Date of Version 01: Nov. 03, 2025
#
# Author 01: Alexander Nickerson
#

import numpy as np
import pandas as pd
import xarray as xr
import os
import time

s = time.time()

stat_all = pd.read_csv('Docs/List_Download_All.txt',
                        header=0, sep="|", index_col=False)

for stat in stat_all.columns:
    if stat_all[stat].dtype == 'object':
        stat_all[stat] = stat_all[stat].str.strip()

stat_all = stat_all.loc[stat_all["Type"] == "NDBC",:]

nsa = 2
nsd = 3
q_lo = 0.003
q_hi = 0.997

head = "Data/NDBC/"
f_old = head + "L00N/"
f_new = head + "QC/"

# create the folder only if necessary
if not os.path.exists(f_new):
    os.makedirs(f_new) 
    
# loop through stations
for i, stat in stat_all.iterrows():
    # extract data from netCDF files
    file2open = f_old + stat["Reg"] + ".nc"
    
    # open the data file
    ds = xr.open_dataset(file2open,mask_and_scale=True)
    df = ds.to_dataframe()
    df = df.reset_index()
    ds.close()
    
    # rename columns for standarization across datasets and create new
    # columns as necessary for quality control
    df = df.rename(columns={"longitude": "lon",
                            "latitude": "lat"}) 
    
    # eliminate duplicates
    is_dup = df['time'].duplicated('last')        
    df = df[~is_dup]
        
    # having times available as UTC time stamps can often be helpful
    ta = np.array(df["time"]).astype('datetime64[s]')
    
    if (stat["Reg"] == 41007):
        is_dup = df["time"].duplicated('last')
        df.loc[is_dup, "time"] = (df.loc[is_dup, "time"] +
                                      np.timedelta64(30,'m'))
        
    # this finds the values that ought to be masked
    is_nat = np.isnat(df["time"])
    df = df.loc[~is_nat]
    
    # if there's no temperature measurement
    is_nan = np.isnan(df["wt_old"])
    df.loc[is_nan,"wt_new"] = np.nan
    df.loc[is_nan,"wt_flag"] = 9
    df.loc[is_nan,"wt_info"] = "No temperature measurement"
    
    # Author 01 likes to expand time series to begin at the first time step of
    # Jan. 01 of the first year and end at the last time step of Dec. 31 of the
    # last year.  This leads to easier computation of climatologies.
    T1 = np.datetime_as_string(np.array(df["time"].iloc[ 0]).astype('datetime64[s]'))
    Y1 = np.datetime_as_string(np.array(df["time"].iloc[ 0]).astype('datetime64[Y]'))
    Y2 = np.datetime_as_string(np.array(df["time"].iloc[-1]).astype('datetime64[Y]'))
    
    # by making the final time step be the next year, the process is made much
    # easier by usin np.arange() to generate the common time array
    df = df.set_index(["time"])
    index_full = pd.date_range(
        start = np.datetime64(Y1 + '-01-01T00:00:00'),
        end   = np.datetime64(Y2 + '-12-31T23:00:00'),
        freq='h'
    )
    # this expands the time series to include the hours without measurements
    index_new = df.index.union(index_full)
    df = df.reindex(index_new)
    df = df.sort_index()
    
    # this makes it possible to use the pd.dt commands
    tb_pd = df.index
    
    # set time stamps without data as missing
    qc_find = np.isnan(df["wt_old"]) & np.isnan(df["lat"])
    df.loc[qc_find,"wt_new"] = np.nan
    df.loc[qc_find,"wt_flag"] = 9
    df.loc[qc_find,"wt_info"] = "Missing or not measured"
    
    wt_range = np.logical_or(df["wt_new"] > 40,
                             df["wt_new"] <  0)
    df.loc[wt_range,"wt_new"] = np.nan
    df.loc[wt_range,"wt_flag"] = 4
    df.loc[wt_range,"wt_info"] = "Gross Range: Outside span"
    
    if stat["Abr"] == "CariCOOS": 
        P1 = df["wt_new"] < 25
        Pt = (P1 & ~np.isnan(df["wt_new"]))
    
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Local Range"
    
    # manual QC work
    if stat["Reg"] == 41053: 
        P1 = np.logical_or(
                np.logical_and(df.index >= "2013-05-04T12:00:00",
                               df.index <  "2013-05-04T18:00:00"),  
                np.logical_and(df.index >= "2021-05-15T00:00:00",
                               df.index <= "2021-05-28T00:00:00"))
        Pt = (P1 & ~np.isnan(df["wt_new"]))
    
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
    
    # manual QC work
    if stat["Reg"] == 41056: 
        P1 = np.logical_and(df.index >= "2021-05-14T00:00:00",
                            df.index <  "2021-05-25T17:00:00")
        Pt = (P1 & ~np.isnan(df["wt_new"]))
    
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
    
    # manual QC work
    if stat["Reg"] == 42085: 
        P1 = np.logical_and(df.index >= "2022-08-18T00:00:00",
                            df.index <  "2022-08-20T15:00:00")
        Pt = (P1 & ~np.isnan(df["wt_new"]))
    
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
    
    # manual QC work
    if stat["Reg"] == 41002: 
        P1 = tb_pd.year == 2010
        Pt = (P1 & ~np.isnan(df["wt_new"]))
    
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
    
    # manual QC work
    if stat["Reg"] == 41008: 
        P1 = np.logical_and(df.index >= "2013-01-01T00:00:00",
                            df.index <  "2013-01-24T00:00:00")
        Pt = (P1 & ~np.isnan(df["wt_new"]))
    
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
    
    # manual QC work
    if stat["Reg"] == 41012: 
        P1 = np.logical_and(df.index >= "2003-11-12T12:00:00",
                            df.index <  "2003-12-01T00:00:00")
        Pt = (P1 & ~np.isnan(df["wt_new"]))
    
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
        
    if stat["Reg"] == 41036: 
        P1 = np.logical_or(
                np.logical_and(df.index >= "2010-01-01T00:00:00",
                               df.index <  "2010-02-01T00:00:00"),  
                np.logical_and(df.index >= "2015-01-01T00:00:00",
                               df.index <= "2015-02-01T00:00:00"))
        Pt = (P1 & ~np.isnan(df["wt_new"]))
    
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
    
    # manual QC work
    if stat["Reg"] == 41040: 
        P1 = np.logical_and(df.index >= "2006-11-23T21:00:00",
                            df.index <  "2006-12-01T00:00:00")
        Pt = (P1 & ~np.isnan(df["wt_new"]))
    
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
    
    # manual QC work
    if stat["Reg"] == 42003: 
        P1 = np.logical_and(df.index >= "2014-06-05T00:00:00",
                            df.index <  "2014-10-16T00:00:00")
        Pt = (P1 & ~np.isnan(df["wt_new"]))
    
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
    
    # manual QC work
    if stat["Reg"] == 41193: 
        P1 = np.logical_and(df.index >= "2009-01-14T12:00:00",
                            df.index <  "2009-01-16T00:00:00")  
        Pt = (P1 & ~np.isnan(df["wt_new"]))
    
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
        
    if stat["Reg"] == 42089: 
        P1 = np.logical_or(
                np.logical_and(df.index >= "2014-10-15T13:00:00",
                               df.index <  "2014-10-16T00:00:00"),  
                np.logical_and(df.index >= "2015-10-11T00:00:00",
                               df.index <  "2015-10-15T00:00:00"))
        Pt = (P1 & ~np.isnan(df["wt_new"]))
    
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
        
    if stat["Reg"] == 41112: 
        P1 = np.logical_and(tb_pd.year == 2012,
                            tb_pd.month == 9)  
        P2 = df["wt_new"] > 29
        Pt = ((P1 & P2) & ~np.isnan(df["wt_new"]))
    
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Suspect Data"
        
    if stat["Abr"] == "TABS": 
        P1 = df["wt_new"] > 33
        Pt = (P1 & ~np.isnan(df["wt_new"]))
    
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Local Range"
        
    if stat["Reg"] == 42043: 
        P1 = np.logical_or(
                np.logical_and(df.index >= "2010-08-21T00:00:00",
                               df.index <  "2010-08-22T13:00:00"),  
                np.logical_and(df.index >= "2011-08-26T05:00:00",
                               df.index <  "2011-08-30T14:00:00"))
        Pt = (P1 & ~np.isnan(df["wt_new"]))
    
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
        
    if stat["Reg"] == 42044: 
        P1 = np.logical_and(df.index >= "2011-08-27T18:00:00",
                            df.index <  "2011-08-29T14:00:00")
        Pt = (P1 & ~np.isnan(df["wt_new"]))
    
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
        
    if stat["Reg"] == 42045: 
        P1 = np.logical_or(
                np.logical_and(df.index >= "2008-10-09T00:00:00",
                               df.index <  "2008-10-10T17:30:00"),  
                np.logical_and(df.index >= "2014-03-11T00:00:00",
                               df.index <= "2014-03-12T00:00:00"))
        P2 = np.logical_or(
                np.logical_and(df.index >= "2018-04-09T00:00:00",
                               df.index <  "2018-08-12T02:00:00"),  
                np.logical_and(df.index >= "2018-11-28T00:00:00",
                               df.index <= "2018-11-29T00:00:00"))
        Pt = ((P1 | P2) & ~np.isnan(df["wt_new"]))
    
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
        
    if stat["Reg"] == 42046: 
        P1 = np.logical_and(tb_pd.year <= 2010,
                            df["wt_new"] < 18.5)
        P2 = np.logical_and(df.index >= "2009-08-12T15:30:00",
                            df.index <  "2009-08-13T13:00:00")
        Pt = ((P1 | P2) & ~np.isnan(df["wt_new"]))
    
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
        
    if stat["Reg"] == 42047: 
        P1 = np.logical_or(
                np.logical_and(df.index >= "2010-08-19T12:30:00",
                               df.index <  "2010-09-01T00:00:00"),  
                np.logical_and(df.index >= "2013-01-09T03:00:00",
                               df.index <= "2013-01-10T05:00:00"))
        P2 = np.logical_and(tb_pd.year == 2018,
                            df["wt_new"] < 20)
        Pt = ((P1 | P2) & ~np.isnan(df["wt_new"]))
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
        
        P3 = np.logical_and(tb_pd.year == 2012,
                            df["wt_new"] > 30)
        Pt = (P3 & ~np.isnan(df["wt_new"]))
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Local Range"     
    
    # look for spikes
    wt = np.array(df["wt_new"])
    wt_mean = np.array(0.5*(wt[0:-2] + wt[2:]))
    pt_mean = np.append(np.append(np.nan,wt_mean),np.nan)
    
    spike = abs(pt_mean - df["wt_new"])
    
    diff_lo = (spike > 3)
    diff_hi = (spike > 8)
    
    df.loc[diff_lo,"wt_new"] = np.nan
    df.loc[diff_hi,"wt_new"] = np.nan
    df.loc[diff_lo,"wt_flag"] = 3
    df.loc[diff_hi,"wt_flag"] = 4
    df.loc[diff_lo,"wt_info"] = "Spike: Low single Point"
    df.loc[diff_hi,"wt_info"] = "Spike: High single Point"
    
    # daily cycle analysis
    roll_lo = df['wt_new'].rolling('25h').quantile(q_lo)
    roll_hi = df['wt_new'].rolling('25h').quantile(q_hi)
    roll_med = df['wt_new'].rolling('25h').median()
    roll_std = df['wt_new'].rolling('25h').std()
    
    Pt = np.logical_or(np.logical_and(df['wt_new'] > roll_med + (nsa + nsd*roll_std),
                                      df['wt_new'] > roll_hi),
                       np.logical_and(df['wt_new'] < roll_med - (nsa + nsd*roll_std),
                                      df['wt_new'] < roll_lo))
    df.loc[Pt,"wt_new"] = np.nan
    df.loc[Pt,"wt_flag"] = 3
    df.loc[Pt,"wt_info"] = "Outside 25 hour variation limit"
        
    # monthly data analysis
    roll_lo = df['wt_new'].rolling('720h').quantile(q_lo)
    roll_hi = df['wt_new'].rolling('720h').quantile(q_hi)
    roll_med = df['wt_new'].rolling('720h').median()
    roll_std = df['wt_new'].rolling('720h').std()
    
    Pt = np.logical_or(np.logical_and(df['wt_new'] > roll_med + (nsa + nsd*roll_std),
                                      df['wt_new'] > roll_hi),
                        np.logical_and(df['wt_new'] < roll_med - (nsa + nsd*roll_std),
                                      df['wt_new'] < roll_lo))    
    df.loc[Pt,"wt_new"] = np.nan
    df.loc[Pt,"wt_flag"] = 3
    df.loc[Pt,"wt_info"] = "Outside 30 day variation limit"
        
    # check for spotty data
    roll_cnt_c = df['wt_new'].rolling('720h', center=True).count()
    P1 = roll_cnt_c <= 5
    P2 = df['wt_flag'] == 2
    Pt = P1 & P2
    df.loc[Pt,"wt_new"] = np.nan
    df.loc[Pt,"wt_flag"] = 4
    df.loc[Pt,"wt_info"] = "Instrumentation Failure"
      
    # do a month-by-month check through the time series for local outliers
    for m in range(1,13):
        for y in range(np.min(tb_pd.year),np.max(tb_pd.year)):
            Pt_YM = np.logical_and(tb_pd.year == y,tb_pd.month == m)
            Pt_Qc = df["wt_flag"] == 2
            Pt_Kp = Pt_YM & Pt_Qc
            
            if np.size(np.where(Pt_Kp)) == 0:
                continue
                
            move_lo = df['wt_new'][Pt_Kp].quantile(q_lo)
            move_hi = df['wt_new'][Pt_Kp].quantile(q_hi)
            move_med = df['wt_new'][Pt_Kp].median(skipna=True)
            move_std = df['wt_new'][Pt_Kp].std(skipna=True)
                               
            P1 = np.logical_or(np.logical_and(df['wt_new'] > move_med + (nsa + nsd*move_std),
                                              df['wt_new'] > move_hi),
                               np.logical_and(df['wt_new'] < move_med - (nsa + nsd*move_std),
                                              df['wt_new'] < move_lo))
            Pt = P1 & Pt_Kp
            df.loc[Pt,"wt_new"] = np.nan
            df.loc[Pt,"wt_flag"] = 3
            df.loc[Pt,"wt_info"] = "Outside 30 day variation limit"
            
        Pt_Mo = tb_pd.month == m
        Pt_Qc = df["wt_flag"] == 2
        Pt_Kp = Pt_Mo & Pt_Qc
        
        if np.size(np.where(Pt_Kp)) == 0:
            continue
            
        move_lo = df['wt_new'][Pt_Kp].quantile(q_lo)
        move_hi = df['wt_new'][Pt_Kp].quantile(q_hi)
        move_med = df['wt_new'][Pt_Kp].median(skipna=True)
        move_std = df['wt_new'][Pt_Kp].std(skipna=True)
        
        P1 = np.logical_or(np.logical_and(df['wt_new'] > move_med + (nsa + nsd*move_std),
                                          df['wt_new'] > move_hi),
                           np.logical_and(df['wt_new'] < move_med - (nsa + nsd*move_std),
                                          df['wt_new'] < move_lo))
        Pt = P1 & Pt_Kp
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Outside seasonal range"
        
    if stat["Reg"] == 41053: 
        P1 = np.logical_and(df.index >= "2017-09-19T12:00:00",
                            df.index <  "2017-09-23T00:00:00")  
        Pt = (P1 & ~np.isnan(df["wt_new"]))
    
        df.loc[Pt,"wt_flag"] = 1
        df.loc[Pt,"wt_info"] = "Passed"
    
    # any remaining 2's survived QC -> turn them into 1's
    Pt = (df["wt_flag"] == 2)
    df.loc[Pt,"wt_flag"] = 1
    df.loc[Pt,"wt_info"] = "Passed"
    
    # set the index and convert to an xarray
    ds = df.to_xarray()
    
    # define the long variable names
    ds.attrs["long_name"] = [
        "latitude",
        "longitude",
        "depth",
        "water temperature (original)",
        "water temperature (QC'd')",
        "water temperature QARTOD flag",
        "water temperature QARTOD failure reason"
    ]
    
    # assign the units
    ds.attrs["units"] = [
        "degrees east",
        "degrees north",
        "degrees C",
        "degrees C",
        "m below surface",
        "QARTOD flag",
        "QARTOD flag reason"
    ]
    
    # save the dataset
    ncf = f_new + stat["Reg"] + ".nc"
    ds.to_netcdf(path=ncf, mode="w")
    
    e = time.time()
    print("Successfully saved " + str(stat["Reg"]) + 
          " at " + str(round((e - s), 3)), "seconds")
