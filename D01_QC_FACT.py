# Purpose: run quality control on FACT data
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

stat_all = stat_all.loc[stat_all["Type"] == "FACT",:]

nsa = 2
nsd = 3
q_lo = 0.003
q_hi = 0.997

head = "Data/FACT/"
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
    ds.close()
    
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
    
    # if there's no temperature measurement
    is_nan = np.isnan(df["wt_new"])
    df.loc[is_nan,"wt_flag"] = 9
    df.loc[is_nan,"wt_info"] = "Missing or not measured"
    
    # if there's no time
    is_nat = np.isnat(df["time"])
    df = df.loc[~is_nat]
    df = df.reset_index(drop=True)
    
    # find timestamps ending in :01 seconds instead of :00
    t1 = pd.to_datetime(df["time"])
    min01 = np.array(t1.dt.minute)
    sec01 = np.array(t1.dt.second)
    
    # many measurements are only off by one second; this fixes that
    df.loc[sec01 ==  1,"time"] = df.loc[sec01 ==  1,"time"] - np.timedelta64(1,'s')
    df.loc[sec01 == 59,"time"] = df.loc[sec01 == 59,"time"] + np.timedelta64(1,'s')
    
    # stations with unusual but erroneous timestamps
    if stat["Reg"] == "btsnp_mb_in":
        df.loc[sec01 == 19,"time"] = np.datetime64('2019-01-08T18:30:00')
        
    if stat["Reg"] == "scan_np_out_s_shoal":
        Pt = (df.index == '2020-04-18T00:18:26')
        df = df.loc[~Pt]
        
    if stat["Reg"] == "scdnrdfp_sc_gpd_rkm_1" or stat["Reg"] == 'teq_dart3':
        Pt = (np.append(np.nan,np.diff(df.index).astype(int)) == 0)
        df = df.loc[~Pt]
        
    if stat["Reg"] == "teq_gghe":
        Pt = (min01 != 0)
        df.loc[Pt,"time"] = df.loc[Pt,"time"] + np.timedelta64(13,'m')
    
    # find interruptions in the data series
    # the nature of the instrument means it is logging data even when not in
    # the water, which can result in erroneuous beginning and ending points
    dt = np.append(np.diff(df["time"]),np.timedelta64(3600*24,'s'))
    gap = np.where(dt > np.timedelta64(3600*24,'s'))
    df.loc[gap[0],    "wt_flag"] = 6
    df.loc[gap[0] + 1,"wt_flag"] = 7
    
    # Author 01 likes to expand time series to begin at the first time step of
    # Jan. 01 of the first year and end at the last time step of Dec. 31 of the
    # last year.  This leads to easier computation of climatologies.
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
    
    # set time stamps without data as missing
    qc_find = np.isnan(df["wt_old"]) & np.isnan(df["lat"])
    df.loc[qc_find,("wt_new")] = np.nan
    df.loc[qc_find,"wt_flag"] = 9
    df.loc[qc_find,"wt_info"] = "Missing or not measured"
    
    wt_range = np.logical_or(df["wt_new"] > 40,
                             df["wt_new"] <  0)
    df.loc[wt_range,"wt_new"] = np.nan
    df.loc[wt_range,"wt_flag"] = 4
    df.loc[wt_range,"wt_info"] = "Gross Range: Outside span"
    
    # eliminate several points at startup
    # some groups seem to have a longer time between startup and placement
    if (stat["Abr"] == "SEZARC"):
        ns, ne, nf, nr =  10,  20,  20,  10
    elif (stat["Abr"] == "FAB-HBOI" or
          stat["Abr"] == "Field-School" or
          stat["Abr"] == "NOAA-NCCOS" or
          stat["Abr"] == "SCDNR"):
        ns, ne, nf, nr =  20,  20,  20,  20
    elif (stat["Abr"] == "FAU") and "hboi" in stat["Reg"]:
        ns, ne, nf, nr = 100, 100, 100, 100
    elif (stat["Abr"] == "NASA"):
        ns, ne, nf, nr =  25,  25,  25,  15
    else:
        ns, ne, nf, nr =   5,   5,   5,   5
        
    if (stat["Reg"] == "flkeys_lka05"):
        ne = 50
    elif (stat["Reg"] == "flkeys_lka19a"):
        nr = 45
    elif (stat["Reg"] == "gacra_bnos09" or
        stat["Reg"] == "gacra_bnos10"):
        ns = 26  
    elif (stat["Reg"] == "gaicfs_005"):
        ns =  41
    elif (stat["Reg"] == "gaicfs_007"):
        ns =  75
    
    # necessary for using index-based methods
    df = df.reset_index()
    df = df.rename(columns={"index": "time"})
    
    # find the initial points and set to 4 due to instrument bootup, which
    # often occurs before the FACT receiver is placed in the water
    qc_log = np.where(~np.isnan(df["wt_new"]))
    
    df.loc[qc_log[0][0:ns],"wt_new"] = np.nan
    df.loc[qc_log[0][0:ns],"wt_flag"] = 4
    df.loc[qc_log[0][0:ns],"wt_info"] = "Activation"
    df.loc[qc_log[0][-ne:],"wt_new"] = np.nan
    df.loc[qc_log[0][-ne:],"wt_flag"] = 4
    df.loc[qc_log[0][-ne:],"wt_info"] = "Deactivation"
    
    qc6 = np.where(df["wt_flag"] == 6)
    qc7 = np.where(df["wt_flag"] == 7)
    
    for q in qc6[0]:
        P1 = q - nf
        P2 = q + 1
        df.loc[P1:P2,"wt_new"] = np.nan
        df.loc[P1:P2,"wt_flag"] = 4
        df.loc[P1:P2,"wt_info"] = "Deactivation"
    for q in qc7[0]:
        P1 = q
        P2 = q + nr
        df.loc[P1:P2,"wt_new"] = np.nan
        df.loc[P1:P2,"wt_flag"] = 4
        df.loc[P1:P2,"wt_info"] = "Activation"
        
    # this makes it possible to use the pd.dt commands
    df = df.set_index(["time"])
    tb_pd = df.index
    
    if stat["Reg"] == "fsbbaya_kybc":
        P1 = np.logical_and(df.index >= "2023-02-07T20:00:00",
                            df.index <  "2024-02-01T00:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Removed?"
        
    if (stat["Abr"] == "FAU"):
        P1 = np.logical_and(df.index >= "2018-03-20T15:00:00",
                            df.index <  "2018-03-22T00:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Removed?"
    
    if stat["Abr"] == "Field-School":
        P1 = np.logical_and(df.index >= "2022-06-26T00:00:00",
                            df.index <  "2022-07-15T00:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Replacement?"
        
    if (stat["Reg"][0:7] == "fscapea"):
        P1 = np.logical_and(df.index >= "2024-06-03T00:00:00",
                            df.index <  "2024-06-07T00:00:00")
        P2 = np.logical_and(df.index >= "2024-10-15T00:00:00",
                            df.index <  "2024-10-16T12:00:00")
        P3 = np.logical_and(df.index >= "2025-02-26T12:00:00",
                            df.index <  "2025-02-27T18:00:00")
        Pt = (P1 | P2 | P3) & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
            
    if (stat["Reg"] == "tbhoga_hrsl" or
        stat["Reg"] == "tbhoga_circle"):
        P1 = np.logical_and(df.index >= "2023-02-24T19:00:00",
                            df.index <  "2023-04-25T13:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
        
    if (stat["Reg"] == "tbhoga_ms"):
        P1 = np.logical_and(df.index >= "2022-03-04T20:00:00",
                            df.index <  "2022-03-22T13:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
        
    if (stat["Reg"] == "teq_4mir" or stat["Reg"] == "teq_aking" or
        stat["Reg"] == "teq_dolo" or stat["Reg"] == "teq_intdr" or
        stat["Reg"] == "teq_moody" or stat["Reg"] == "teq_oplr" or
        stat["Reg"] == "teq_pwrn" or stat["Reg"] == "teq_tyrf"):
        P1 = df.index <  "2019-06-27T00:00:00"
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Activation"
        
        P1 = df.index >  "2021-10-21T00:00:00"
        Pt = P1 & ~np.isnan(df["wt_new"])
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Deactivation"
        
    if (stat["Reg"] == "teq_evca"):
        P1 = np.logical_and(df.index >= "2018-06-04T00:00:00",
                            df.index <  "2018-06-29T00:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
        
    if (stat["Reg"] == "teq_fpcc"):
        P1 = np.logical_and(df.index >= "2018-04-04T12:00:00",
                            df.index <= "2018-04-04T19:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
        
    if (stat["Reg"] == "teq_pcbr"):
        P1 = np.logical_and(df.index >= "2010-12-01T00:00:00",
                            df.index <= "2011-06-01T00:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
            
    if (stat["Reg"] == "gacra_bnos07"):
        P1 = np.logical_and(df.index >= "2022-03-09T18:00:00",
                            df.index <  "2022-05-07T00:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Removed?"
        
    if (stat["Reg"] == "grnms_fs15"):
        P1 = np.logical_and(df.index >= "2019-10-01T00:00:00",
                            df.index <  "2019-11-01T00:00:00")
        P2 = df["wt_new"] < 25
        Pt = P1 & P2 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
        
    if (stat["Reg"] == "grnms_surtas05in"):
        P1 = np.logical_and(df.index >= "2019-09-22T22:00:00",
                            df.index <  "2019-10-17T18:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
        
    if (stat["Reg"] == "grnms_surtasstn20"):
        P1 = np.logical_and(df.index >= "2019-09-22T22:00:00",
                            df.index <  "2019-09-29T01:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
        
    if (stat["Reg"] == "scan_bp_out_n"):
        P1 = np.logical_and(df.index >= "2023-08-08T18:00:00",
                            df.index <  "2024-07-03T12:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
        
    if (stat["Reg"] == "scan_lb_out_n"):
        P1 = np.logical_and(df.index >= "2017-03-01T00:00:00",
                            df.index <  "2017-04-01T00:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
        
    if (stat["Reg"] == "scan_vin_out_s"):
        P1 = np.logical_and(df.index >= "2024-04-01T00:00:00",
                            df.index <  "2025-04-01T00:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Replacement?"
        
    if (stat["Reg"] == "scan_skc_500"):
        P1 = np.logical_and(df.index >= "2022-10-27T20:00:00",
                            df.index <  "2023-03-01T00:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
        
    if (stat["Reg"] == "scare_chs_green_01"):
        P1 = np.logical_and(df.index >= "2022-04-01T00:00:00",
                            df.index <  "2022-10-01T00:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
        
    if (stat["Reg"] == "scdnrdfp_sc_edisto_r_1" or
        stat["Reg"] == "scdnrdfp_sc_edisto_r_4"):
        P1 = np.logical_and(df.index >= "2024-06-25T00:00:00",
                            df.index <  "2024-08-01T00:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
        
    if (stat["Reg"] == "scdnrdfp_sc_edisto_r_16"):
        P1 = np.logical_and(df.index >= "2024-08-07T00:00:00",
                            df.index <  "2024-09-01T00:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
        
    if (stat["Reg"] == "scdnrdfp_sc_gpd_rkm_7"):
        P1 = np.logical_and(df.index >= "2023-08-01T00:00:00",
                            df.index <  "2023-10-20T12:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
        
    if (stat["Reg"] == "scdnrdfp_sc_savannah_1"):
        P1 = np.logical_and(df.index >= "2024-12-29T00:00:00",
                            df.index <  "2025-01-12T00:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
        
    if (stat["Reg"] == "scdnrdfp_sc_savannah_11"):
        P1 = np.logical_and(df.index >= "2023-12-30T07:00:00",
                            df.index <  "2024-01-08T02:00:00")
        Pt = P1 & ~np.isnan(df["wt_new"])
        
        df.loc[Pt,"wt_new"] = np.nan
        df.loc[Pt,"wt_flag"] = 4
        df.loc[Pt,"wt_info"] = "Instrument Failure"
     
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
    
    # any remaining 2's survived QC -> turn them into 1's
    Pt = (df["wt_flag"] == 2)
    df.loc[Pt,"wt_flag"] = 1
    df.loc[Pt,"wt_info"] = "Passed"
    
    # set the index and convert to an xarra
    ds = df.to_xarray()
    
    # define the long variable names
    ds.attrs["long_name"] = [
        "longitude",
        "latitude",
        "depth",
        "water temperature (original)",
        "water temperature (QC'd')",
        "water temperature QARTOD flag",
        "water temperature QARTOD failure reason"
    ]
    
    # assign the units
    ds.attrs["units"] = [
        "degrees north",
        "degrees east",
        "meters",
        "degrees C",
        "degrees C",
        "QARTOD flag",
        "QARTOD flag reason"
    ]
    s
    # save the dataset
    ncf = f_new + stat["Reg"] + ".nc"
    ds.to_netcdf(path=ncf, mode="w")
    
    e = time.time()
    print("Successfully saved " + str(stat["Reg"]) + 
          " at " + str(round((e - s), 3)), "seconds")
