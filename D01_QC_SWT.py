# Purpose: run quality control on SWT data
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

stat_all = stat_all.loc[stat_all["Type"] == "SWT",:]

nsa = 2
nsd = 3
q_lo = 0.003
q_hi = 0.997

head = "Data/SWT/"
f_old = head + "L00N/"
f_new = head + "QC/"

# create the folder only if necessary
if not os.path.exists(f_new):
    os.makedirs(f_new) 

# loop through stations
for i, stat in stat_all.iterrows():
    # extract data from netCDF files
    file2open = f_old + stat["Reg"] + ".nc"
    if stat["Reg"] != "mooring-ob27m-onslow-bay-nc":
        continue
    
    # open the data file
    ds = xr.open_dataset(file2open,mask_and_scale=True)
    df = ds.to_dataframe()
    df = df.reset_index()
    ds.close()
    stop
    # rename columns for standarization across datasets and create new
    # columns as necessary for quality control
    df = df.rename(columns={"longitude": "lon",
                            "latitude": "lat",
                            "sea_water_temperature": "wt_old"}) 
    df["wt_new"] = df["wt_old"]
    
    # some stations already have a QC flag variable, although most
    # station owners did not perform any QC
    if "sea_water_temperature_qc_agg" in df.columns:
        df = df.rename(columns={"sea_water_temperature_qc_agg": "wt_flag"})
    else:
        df["wt_flag"] = 2*np.ones(np.shape(df["wt_old"]),dtype="float64")
    
    df["wt_info"] = np.full(np.shape(df["wt_old"]),"Not tested",dtype='O')
    df["time"] = df["time"].astype('datetime64[s]')
    
    # if there's no temperature measurement
    is_nan = np.isnan(df["wt_new"])
    df.loc[is_nan,"wt_flag"] = 9
    df.loc[is_nan,"wt_info"] = "Missing or not measured"
    
    # if there's no time
    is_nat = np.isnat(df["time"])
    df = df.loc[~is_nat]
    
    # find timestamps ending in :01 seconds instead of :00
    t1 = pd.to_datetime(df["time"])
    min01 = np.array(t1.dt.minute)
    sec01 = np.array(t1.dt.second)

    # Author 01 likes to expand time series to begin at the first time step of
    # Jan. 01 of the first year and end at the last time step of Dec. 31 of the
    # last year.  This leads to easier computation of climatologies.
    T1 = np.datetime_as_string(np.array(df["time"].iloc[ 0]).astype('datetime64[s]'))
    Y1 = np.datetime_as_string(np.array(df["time"].iloc[ 0]).astype('datetime64[Y]'))
    Y2 = np.datetime_as_string(np.array(df["time"].iloc[-1]).astype('datetime64[Y]'))
    
    # eliminate duplicates
    is_dup = df['time'].duplicated('last')        
    df = df[~is_dup]
    
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
    qc_find = np.isnan(df["wt_new"]) & np.isnan(df["lat"])
    df.loc[qc_find,("wt_new")] = np.nan
    df.loc[qc_find,"wt_flag"] = 9
    df.loc[qc_find,"wt_info"] = "Missing or not measured"
    
    wt_range = np.logical_or(df["wt_new"] > 40,
                             df["wt_new"] <  0)
    df.loc[wt_range,"wt_new"] = np.nan
    df.loc[wt_range,"wt_flag"] = 4
    df.loc[wt_range,"wt_info"] = "Gross Range: Outside span"
    
    # manual QC work
    if stat["Reg"] == "gov-nps-ever-gkyf1": 
        P1 = (df.index >= "2020-10-16T17:00:00")
        P2 = (df.index <  "2022-11-01T00:00:00")  
        Pt = (P1 & P2) & ~np.isnan(df["wt_new"])    
      
        df.loc[Pt,"wt_new"] = np.nan     
        df.loc[Pt,"wt_new"] = df.loc[Pt,"wt_new"] - 5
        df.loc[Pt,"wt_info"] = "Temperature shifted by 5 degrees"
    
    if stat["Abr"] == "UNC":
        Pt = (df["wt_new"] < 5) & ~np.isnan(df["wt_new"])
          
        df.loc[Pt,"wt_new"] = np.nan     
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
    
    if stat["Abr"] == "WHOI":
        P1 = (df.index >= "2021-11-01T00:00:00")
        P2 = (df.index <  "2021-12-01T00:00:00")
        P3 = (df["wt_new"] < 27)
        Pt = (P1 & P2 & P3) & ~np.isnan(df["wt_new"])
          
        df.loc[Pt,"wt_new"] = np.nan     
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Seasonal Norm"
        
        P1 = (df.index >= "2022-10-01T00:00:00")
        P2 = (df.index <  "2022-11-01T00:00:00")  
        Pt = (P1 & P2) & ~np.isnan(df["wt_new"])
          
        df.loc[Pt,"wt_new"] = np.nan     
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
    
    if "nps-ever" in stat["Reg"]:
        P1 = tb_pd.month > 2
        P2 = df["wt_new"] < 5
        P3 = tb_pd.month >= 10
        P4 = df["wt_new"] > 35
        P5 = tb_pd.month < 3
        P6 = df["wt_new"] > 30  
        
        Pt = ((P1 & P2) | (P3 & P4) | (P5 & P6)) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Seasonal Norm"
        
    if stat["Reg"] == "gov-nps-ever-bskf1": 
        P1 = (df.index >= "2019-01-01T00:00:00")
        P2 = (df.index <  "2025-01-01T00:00:00")  
        
        Pt = (P1 & P2) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Random point 4 years after last measurement"
        
    if stat["Reg"] == "gov-nps-ever-canf1": 
        Pt = (df.index <  "2003-01-01T00:00:00")  
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Random point 2 years before first measurement"
        
    if stat["Reg"] == "gov-ndbc-41052":
        P1 = np.logical_and(df.index >= "2020-08-01T00:00:00",
                            df.index <  "2020-09-01T00:00:00")
        P2 = np.logical_and(df.index >= "2021-03-01T00:00:00",
                            df.index <  "2021-03-15T00:00:00")
        Pt = (P1 | P2) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
    if stat["Reg"] == "gov-ndbc-41053":
        P1 = np.logical_and(df.index >= "2017-09-01T00:00:00",
                            df.index <  "2017-10-01T00:00:00")
        P2 = np.logical_and(df.index >= "2019-08-01T00:00:00",
                            df.index <  "2019-08-15T00:00:00")
        P3 = np.logical_and(df.index >= "2021-05-16T00:00:00",
                            df.index <  "2021-06-01T00:00:00")
        P4 = np.logical_and(df.index >= "2022-09-01T00:00:00",
                            df.index <  "2022-10-01T00:00:00")
        Pt = (P1 | P2 | P3 | P4) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
    if stat["Reg"] == "gov-ndbc-41056":
        P1 = np.logical_and(df.index >= "2021-05-16T00:00:00",
                            df.index <  "2021-06-01T00:00:00") 
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
    if stat["Reg"] == "gov-ndbc-42085":
        Pt = np.logical_and(df.index >= "2022-08-16T00:00:00",
                            df.index <  "2022-09-01T00:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
    if stat["Reg"] == "ism-secoora-wmo_41025":
        Pt = np.logical_and(df.index >= "2022-05-08T12:00:00",
                            df.index <  "2022-05-17T15:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
        P1 = np.logical_and(df.index >= "2021-01-01T00:00:00",
                            df.index <  "2024-01-01T00:00:00")
        P2 = df["wt_new"] < 17
        Pt = (P1 & P2) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Seasonal Norm"
            
    if stat["Abr"] == "FAU":
        P1 = np.logical_or(df["wt_new"] < 10,df["wt_new"] > 35)
        P2 = np.logical_or(tb_pd.month <= 2,tb_pd.month >= 11)
        P3 = df["wt_new"] > 30
        P4 = np.logical_and(tb_pd.month >= 5,tb_pd.month <= 8)
        P5 = df["wt_new"] < 20
        P6 = tb_pd.month < 3
        P7 = df["wt_new"] > 30  
        Pt = P1 | (P2 & P3) | (P4 & P5) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Seasonal Norm"
    
    if stat["Reg"] == "gulf-star-marina":
        P1 = (df.index >= "2024-01-01T00:00:00")
        P2 = (df.index <  "2025-01-01T00:00:00")  
        P3 = df["wt_new"] < 15
        
        Pt = P1 & P2 & P3 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Seasonal Norm"   
    
    if stat["Reg"] == "vester-field-station":
        P1 = (df.index >= "2025-03-01T00:00:00")
        P2 = (df.index <  "2025-04-01T00:00:00")  
        P3 = df["wt_new"] < 15
        P4 = (df.index >= "2025-06-01T00:00:00")
        P5 = (df.index <  "2025-07-01T00:00:00")  
        P6 = df["wt_new"] < 26
        
        Pt = ((P1 & P2 & P3) | (P4 & P5 & P6)) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Seasonal Norm"          
    
    if stat["Reg"] == "indian-river-lagoon-banana-river":
        P1 = (df.index >= "2023-03-01T00:00:00")
        P2 = (df.index <  "2023-03-10T00:00:00")
        P3 = df["wt_new"] < 23.5
        P4 = (df.index >= "2023-12-01T00:00:00")
        P5 = (df.index <  "2024-01-01T00:00:00")
        P6 = df["wt_new"] > 23.5
        Pt = ((P1 & P2 & P3) | (P4 & P5 & P6)) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Spike: Multiple Points"
    
    if stat["Abr"] == "FL-DEP":
        P1 = np.logical_and(tb_pd.month >= 5,tb_pd.month <= 10)
        P2 = df["wt_new"] < 19
        P3 = ~np.logical_and(tb_pd.month >= 5,tb_pd.month <= 10)
        P4 = df["wt_new"] < 10
        P5 = np.logical_or(np.logical_and(df.index >= "2011-09-01T00:00:00",
                                          df.index <  "2012-01-01T00:00:00"),
                            np.logical_and(df.index >= "2014-09-15T00:00:00",
                                          df.index <  "2015-01-01T00:00:00"))
        P6 = df["wt_new"] > 30
        P7 = np.logical_and(df.index >= "2018-06-01T00:00:00",
                            df.index <  "2018-08-01T00:00:00")
        P8 = df["wt_new"] < 22
        Pt = ((P1 & P2) | (P3 & P4) | (P5 & P6) | (P7 & P8)) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Seasonal Norm"
    
    if stat["Abr"] == "FGCU-WS":
        P1 = np.logical_and(tb_pd.month >= 7,tb_pd.month <= 8)
        P2 = df["wt_new"] < 27
        Pt = (P1 & P2) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Seasonal Norm"
    
    if stat["Abr"] == "ICON":
        P1 = np.logical_and(df.index >= "2017-10-01T00:00:00",
                            df.index <  "2018-11-01T00:00:00")
        P2 = df["wt_new"] < 28
        Pt = (P1 & P2) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Seasonal Norm"
        
    if stat["Reg"] == "gov-ndbc-mhpa1":
        P1 = np.logical_and(df.index >= "2019-12-15T00:00:00",
                            df.index <  "2020-03-01T00:00:00")    
        Pt = P1 &  ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
    if stat["Reg"] == "noaa_nos_co_ops_8651370":
        P1 = np.logical_and(df.index >= "2021-10-01T00:00:00",
                            df.index <  "2021-10-22T00:00:00")   
        P2 = np.logical_and(df.index >= "2024-01-01T00:00:00",
                            df.index <  "2024-03-01T00:00:00")  
        Pt = (P1 | P2) &  ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
    if stat["Reg"] == "noaa_nos_co_ops_8658163":
        P1 = np.logical_and(df.index >= "2004-01-01T00:00:00",
                            df.index <  "2005-12-01T00:00:00") 
        P2 = np.logical_and(df.index >= "2006-06-01T00:00:00",
                            df.index <  "2006-06-30T00:00:00")   
        Pt = (P1 | P2) &  ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
    if stat["Reg"] == "noaa_nos_co_ops_8670870":
        P1 = np.logical_and(df.index >= "2022-12-01T00:00:00",
                            df.index <  "2023-01-01T00:00:00") 
        Pt = (P1) &  ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
    if stat["Reg"] == "noaa_nos_co_ops_8721604":
        P1 = np.logical_and(df.index >= "2024-10-15T00:00:00",
                            df.index <  "2024-11-01T00:00:00") 
        Pt = (P1) &  ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
    if stat["Reg"] == "noaa_nos_co_ops_8722670":
        P1 = np.logical_and(df.index >= "2022-01-16T00:00:00",
                            df.index <  "2022-02-04T00:00:00") 
        Pt = (P1) &  ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
    if stat["Reg"] == "noaa_nos_co_ops_8726674":
        P1 = np.logical_and(df.index >= "2022-12-16T00:00:00",
                            df.index <  "2023-01-01T00:00:00") 
        Pt = (P1) &  ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
    if stat["Reg"] == "noaa_nos_co_ops_8736897":
        P1 = np.logical_and(df.index >= "2018-05-14T00:00:00",
                            df.index <  "2018-05-28T00:00:00") 
        Pt = (P1) &  ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
    if stat["Reg"] == "noaa_nos_co_ops_8741533":
        P1 = np.logical_and(df.index >= "2016-01-16T00:00:00",
                            df.index <  "2016-02-15T00:00:00") 
        Pt = (P1) &  ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
    if stat["Reg"] == "noaa_nos_co_ops_8767961":
        P1 = np.logical_and(df.index >= "2019-09-16T00:00:00",
                            df.index <  "2020-03-15T00:00:00") 
        Pt = (P1) &  ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
    if stat["Reg"] == "noaa_nos_co_ops_8770733":
        P1 = np.logical_and(df.index >= "2016-06-01T00:00:00",
                            df.index <  "2016-06-20T00:00:00") 
        Pt = (P1) &  ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
    if stat["Reg"] == "noaa_nos_co_ops_8779749":
        P1 = np.logical_and(df.index >= "2017-08-15T00:00:00",
                            df.index <  "2017-09-01T00:00:00") 
        P2 = np.logical_and(df.index >= "2022-10-01T00:00:00",
                            df.index <  "2023-04-01T00:00:00")   
        Pt = (P1 | P2) &  ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
    if stat["Reg"] == "noaa_nos_co_ops_9751381":
        P1 = np.logical_and(tb_pd.month <= 4,tb_pd.year <= 2025)
        P2 = df["wt_new"] > 30 
        Pt = (P1 & P2) &  ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Seasonal Range"
        
    if stat["Reg"] == "gov_ornl_cdiac_graysrf_81w_31n":
        P1 = (tb_pd.year == 2012)
        P2 = df["wt_new"] > 17.5
        Pt = (P1 & P2) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
    if stat["Reg"] == "gov_ornl_cdiac_coastalms_88w_30n":
        P1 = df["wt_new"] < 10
        Pt = (P1) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Seasonal Range"
    
    if stat["Abr"] == "TABS":
        P1 = np.logical_or(df["wt_new"] < 8,df["wt_new"] > 33)
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Regional Range"
        
        P2 = np.logical_and(tb_pd.month >= 2,tb_pd.month <= 12)
        P3 = df["wt_new"] < 10
        P4 = np.logical_and(tb_pd.month >= 5,tb_pd.month <= 9)
        P5 = df["wt_new"] < 20
        P6 = tb_pd.month <= 3
        P7 = df["wt_new"] > 25
        P8 = ~P4
        P9 = df["wt_new"] > 27
        Pt = ((P2 & P3) | (P4 & P5) | (P6 & P7)) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Seasonal Norm"         
    
    if stat["Reg"] == "tabs_historic_tabs_d":
        P1 = (df.index >= "2019-08-11T00:00:00")
        P2 = (df.index <  "2019-10-25T00:00:00")
        Pt = (P1 & P2) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"  
    
    if stat["Reg"] == "tabs_historic_tabs_f":
        P1 = (df.index >= "2016-01-01T00:00:00")
        P2 = (df.index <  "2016-02-01T00:00:00")
        Pt = (P1 & P2) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
    
    if stat["Reg"] == "tabs_historic_tabs_k":
        P1 = (df.index >= "2016-01-01T00:00:00")
        P2 = (df.index <  "2016-08-08T00:00:00")
        P3 = (df.index >= "2018-04-16T00:00:00")
        P4 = (df.index <  "2018-12-01T00:00:00")
        P5 = (df.index >= "2017-12-14T00:00:00")
        P6 = (df.index <  "2017-12-21T00:00:00")
        Pt = ((P1 & P2) | (P3 & P4) | (P5 & P6)) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
        Pt = (df["wt_new"] < 15)
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Regional Range"
    
    if stat["Reg"] == "tabs_historic_tabs_n":
        P1 = (df.index >= "2016-08-23T00:00:00")
        P2 = (df.index <  "2016-08-25T00:00:00")
        Pt = (P1 & P2) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
    
    if stat["Reg"] == "tabs_historic_tabs_v":
        P1 = (df.index >= "2018-12-16T00:00:00")
        P2 = (df.index <  "2018-12-18T00:00:00")
        P3 = (df.index >= "2019-04-23T00:00:00")
        P4 = (df.index <  "2019-05-01T00:00:00")
        Pt = ((P1 & P2) | (P3 & P4)) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
        P5 = np.logical_or(df["wt_new"] > 32,df["wt_new"] < 19)
        Pt = P5 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Seasonal Norm"
    
    if stat["Abr"] == "TB-LOBO":
        P1 = np.logical_and(tb_pd.month >= 7,tb_pd.month <= 8)
        P2 = df["wt_new"] < 28.5
        P3 = (df.index >= "2018-06-01T00:00:00")
        P4 = (df.index <  "2018-11-10T00:00:00")
        P5 = df["wt_new"] < 22
        Pt = ((P1 & P2) | (P3 & P4 & P5)) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Seasonal Norm"
        
    if stat["Abr"] == "UNC-CH":
        Pt = df["wt_new"] < 5
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Seasonal Norm"
       
    if stat["Abr"] == "UNC-CSI":
        P1 = (df.index >= "2022-12-01T00:00:00")
        P2 = (df.index <  "2022-12-31T00:00:00")
        P3 = df["wt_new"] < 10
        Pt = (P1 & P2 & P3)  & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Spike: Multiple Points"
        
    if stat["Abr"] == "UNCW-CORMP":
        P1 = np.logical_and(tb_pd.month >= 6,tb_pd.month <= 9)
        P2 = df["wt_new"] < 20
        P3 = np.logical_and(tb_pd.month >= 7,tb_pd.month <= 8)
        P4 = df["wt_new"] < 25
        P5 = np.logical_and(tb_pd.month >= 1,tb_pd.month <= 2)
        P6 = np.logical_or(df["wt_new"] > 20,df["wt_new"] < 2)
        P7 = df["wt_new"] > 35
        Pt = ((P1 & P2) | (P3 & P4) | (P5 & P6) | (P7)) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Seasonal Norm"
        
    if stat["Reg"] == "41070-pncwave-ponce-de-leon-inle":
        P1 = np.logical_and(df.index >= "2023-09-15T00:00:00",
                            df.index <  "2023-10-05T00:00:00")
        Pt = P1  & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
    if stat["Reg"] == "mooring-ob27m-onslow-bay-nc":
        P1 = np.logical_and(df.index >= "2019-12-06T12:00:00",
                            df.index <  "2019-12-06T18:00:00")
        P2 = df["wt_new"] < 15
        Pt = (P1 & P2) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
    if stat["Reg"] == "org_cormp_cap2":
        P1 = np.logical_and(df.index >= "2022-01-01T00:00:00",
                            df.index <  "2023-01-05T00:00:00")
        P2 = df["wt_new"] < 10

        P3 = np.logical_or(
                np.logical_and(df.index >= "2008-12-20T08:00:00",
                               df.index <  "2009-01-01T00:00:00"),
                np.logical_and(df.index >= "2012-02-01T00:00:00",
                               df.index <  "2012-03-29T12:00:00")
        )
        P4 = np.logical_or(
                np.logical_and(df.index >= "2012-02-01T00:00:00",
                               df.index <  "2012-03-29T12:00:00"),
                np.logical_and(df.index >= "2014-12-25T00:00:00",
                               df.index <  "2015-03-29T00:00:00")
        )
        P5 = np.logical_and(df.index >= "2018-01-12T16:00:00",
                            df.index <  "2018-01-15T00:00:00")
         
        P6 = df["wt_new"] < 5
        P7 = np.logical_and(df.index >= "2012-01-07T00:00:00",
                            df.index <  "2012-02-01T00:00:00")
        P8 = df["wt_new"] > 15
        Pt = ((P1 & P2) | (P3 | P4 | P5 | P6) | (P7 & P8)) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
    if stat["Reg"] == "org_cormp_frp2":
        P1 = tb_pd.month > 1
        P2 = np.logical_or(df["wt_new"] < 10,
                           df["wt_new"] > 33.5  )
        Pt = (P1 & P2) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatatology: Outside Seasonal Norm"
        
    if stat["Reg"] == "org_cormp_ilm2":
        P1 = np.logical_or(df["wt_new"] < 6,
                           df["wt_new"] > 32  )
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Local Range"
        
        P2 = np.logical_and(df.index >= "2011-01-01T00:00:00",
                            df.index <  "2011-01-15T00:00:00")
        P3 = np.logical_and(df.index >= "2018-04-28T00:00:00",
                            df.index <  "2018-05-01T00:00:00")
        P4 = np.logical_and(df.index >= "2025-01-01T00:00:00",
                            df.index <  "2025-01-17T00:00:00")
        Pt = (P2 | P3 | P4) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
    if stat["Reg"] == "org_cormp_ilm3":
        P1 = np.logical_and(df.index >= "2005-12-26T20:00:00",
                            df.index <  "2006-03-01T00:00:00")
        P2 = np.logical_and(df.index >= "2013-11-01T00:00:00",
                            df.index <  "2014-06-01T00:00:00")
        P3 = np.logical_and(df.index >= "2005-12-17T00:00:00",
                            df.index <  "2006-01-01T00:00:00")
        P4 = (df["wt_new"] > 18)
        Pt = (P1 | P2 | (P3 & P4)) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
        P7 = (df["wt_new"] < 12)
        P8 = tb_pd.month >= 3
        
        P9 = (df["wt_new"] < 9)
        Pt = ((P7 & P8) | P9) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Local Range"
        
    if stat["Reg"] == "org_cormp_lej3":
        P7 = (df["wt_new"] < 15)
        P8 = tb_pd.month >= 5
        
        P9 = (df["wt_new"] < 10)
        Pt = ((P7 & P8) | P9) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Local Range"
        
    if stat["Reg"] == "org_cormp_sun2":
        P1 = (df["wt_new"] < 10)
        P2 = tb_pd.year == 2012
        P3 = (df["wt_new"] > 15)
        P4 = np.logical_and(tb_pd.year == 2013,tb_pd.month <= 3)
        P5 = (df["wt_new"] < 10)
        P6 = np.logical_and(tb_pd.year == 2014,tb_pd.month >= 3)
        Pt = ((P1 & P2) | (P3 & P4) | (P5 & P6)) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
        P9 = (df["wt_new"] < 5)
        Pt = (P9) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Seasonal Range"
        
    if stat["Reg"] == "sun2wave-sunset-nearshore-wave":
        P1 = np.logical_and(df.index >= "2024-12-01T00:00:00",
                            df.index <  "2025-01-01T00:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
       
    if stat["Abr"] == "USM":
        P1 = tb_pd.month == 1
        P2 = df["wt_new"] > 23
        Pt = (P1 & P2) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Climatology: Outside Seasonal Norm"
    
    if stat["Reg"] == "station-14m-may-river-sc-bottom-":
        P1 = np.logical_and(df.index >= "2025-05-01T00:00:00",
                            df.index <  "2025-10-01T00:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
    if stat["Reg"] == "station-cc4-chechessee-creek-sc-":
        P1 = np.logical_and(df.index >= "2022-07-20T11:30:00",
                            df.index <  "2022-07-21T10:15:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
    if stat["Reg"] == "station-cr1-colleton-river-sc-bo":
        P1 = np.logical_and(df.index >= "2022-04-01T00:00:00",
                            df.index <  "2022-05-01T00:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan   
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrumentation Failure"
        
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
    
    # set time as index for using "rolling" functions
    df["time"] = pd.to_datetime(df.index)
    df = df.set_index('time')
    
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
        
    if (stat["Reg"] == "noaa_nos_co_ops_8722956" or 
        stat["Reg"] == "noaa_nos_co_ops_8740166"):
        Pt = ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 3
        df.loc[Pt,"wt_info"] = "Possibly air temperature"
    
    # any remaining 2's survived QC -> turn them into 1's
    Pt = (df["wt_flag"] == 2)
    df.loc[Pt,"wt_flag"] = 1
    df.loc[Pt,"wt_info"] = "Passed"
    df = df.drop("row",axis=1)
    
    # set the index and convert to an xarra
    ds = df.to_xarray()
    
    # define the long variable names
    ds.attrs["long_name"] = [
        "longitude",
        "latitude",
        "water temperature (original)",
        "water temperature (QC'd')",
        "water temperature QARTOD flag",
        "water temperature QARTOD failure reason"
    ]
    
    # assign the units
    ds.attrs["units"] = [
        "degrees north",
        "degrees east",
        "degrees C",
        "degrees C",
        "QARTOD flag",
        "QARTOD flag reason"
    ]
    
    # save the dataset
    ncf = f_new + stat["Reg"] + ".nc"
    ds.to_netcdf(path=ncf, mode="w")
    
    e = time.time()
    print("Successfully saved " + str(stat["Reg"]) + 
          " at " + str(round((e - s), 3)), "seconds")
