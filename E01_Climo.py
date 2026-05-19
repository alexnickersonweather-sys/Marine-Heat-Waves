    # Purpose: Make climatologies of the QC'd data
#
# Date of Version 01: Dec. 18, 2025
#
# Author 01: Alexander Nickerson
#

import numpy as np
import pandas as pd
import xarray as xr
import os
import time

s = time.time()

def np_nan_mean(a):
    return np.nan if np.all(a!=a) else np.nanmean(a)

stat_all = pd.read_csv('Docs/List_Download_All.txt',
                        header=0, sep="|", index_col=False)

for stat in stat_all.columns:
    if stat_all[stat].dtype == 'object':
        stat_all[stat] = stat_all[stat].str.strip()

# stat_all = stat_all.loc[stat_all["Type"] == "USF",:].reset_index(drop=True)

stat_all["N_Yr"] = np.zeros(np.shape(stat_all["Lat"]),dtype="int64")
stat_all["N_Mn"] = np.zeros(np.shape(stat_all["Lat"]),dtype="int64")

for t in ["USF","FACT","NDBC","SWT","USF"]:
    stat_own = stat_all.loc[stat_all["Type"] == t,:].reset_index(drop=True)
    
    # folder path information
    head = "Data/" + t + "/"
    f_old = head + "QC/"
    f_new = head + "Climo/"
    
    # create the folder only if necessary
    if not os.path.exists(f_new):
        os.makedirs(f_new) 
        
    # loop through stations
    for i, stat in stat_own.iterrows():
        # extract data from netCDF files
        file2open = f_old + stat["Reg"] + ".nc"
        
        # open the file
        ds = xr.open_dataset(file2open)
        df = ds.to_dataframe()
        ds.close()
        
        # get first and last years of dataset
        Y1 = np.datetime_as_string(np.array(df.index[ 0]).astype('datetime64[Y]'))
        Y2 = np.datetime_as_string(np.array(df.index[-1]).astype('datetime64[Y]'))
        
        # by making the final time step be the next year, the process is made much
        # easier by usin np.arange() to generate the common time array
        index_full = pd.date_range(
            start = np.datetime64(Y1 + '-01-01T00:00:00'),
            end   = np.datetime64(Y2 + '-12-31T23:00:00'),
            freq='h'
        )
        
        # get timestamps as both index and a numpy array
        ts = np.array(index_full)
        
        wt_hour = pd.DataFrame()
        wt_days = pd.DataFrame()
        wt_mons = pd.DataFrame()
        wt_year = pd.DataFrame()
        
        # get 
        wt_hour["time"] = np.unique(ts.astype('datetime64[h]'))
        wt_days["time"] = np.unique(ts.astype('datetime64[D]'))
        wt_mons["time"] = np.unique(ts.astype('datetime64[M]'))
        wt_year["time"] = np.unique(ts.astype('datetime64[Y]'))
        
        wt_hour["lat"] = np.ones(np.shape(wt_hour["time"]))*df.iloc[0]["lat"]
        wt_days["lat"] = np.ones(np.shape(wt_days["time"]))*df.iloc[0]["lat"]
        wt_mons["lat"] = np.ones(np.shape(wt_mons["time"]))*df.iloc[0]["lat"]
        wt_year["lat"] = np.ones(np.shape(wt_year["time"]))*df.iloc[0]["lat"]
        
        wt_hour["lon"] = np.ones(np.shape(wt_hour["time"]))*df.iloc[0]["lon"]
        wt_days["lon"] = np.ones(np.shape(wt_days["time"]))*df.iloc[0]["lon"]
        wt_mons["lon"] = np.ones(np.shape(wt_mons["time"]))*df.iloc[0]["lon"]
        wt_year["lon"] = np.ones(np.shape(wt_year["time"]))*df.iloc[0]["lon"]
        
        wt_hour = wt_hour.set_index(["time"])
        wt_days = wt_days.set_index(["time"])
        wt_mons = wt_mons.set_index(["time"])
        wt_year = wt_year.set_index(["time"])
        
        # get the unique depths
        dep = np.flip(np.unique(df["z"]))
        dep = dep[~np.isnan(dep)]
        
        # loop through the depths
        for n in dep:
            nd = abs(n.astype(int))
            txt = ("D" + f"{nd:03d}")
            
            wt_hour[txt] = np.zeros(np.shape(wt_hour.index),dtype="float64")
            wt_days[txt] = np.zeros(np.shape(wt_days.index),dtype="float64")
            wt_mons[txt] = np.zeros(np.shape(wt_mons.index),dtype="float64")
            wt_year[txt] = np.zeros(np.shape(wt_year.index),dtype="float64")
            
            wt_time = df.loc[df["z"] == n,:]
            
            # this expands the time series to include the hours without measurements
            index_new = wt_time.index.union(index_full)
            wt_time = wt_time.reindex(index_new)
            wt_time = wt_time.sort_index()
            
            # grouper makes it easy to compute the climatologies
            g = wt_time.groupby(pd.Grouper(freq="h"))
            group = g["wt_new"].agg(
                median="median",
                n_total="size",
                n_valid="count"
            )
            wt_hour[txt] = group["median"].where(group["n_valid"] >= 1)
            
            g = wt_hour.groupby(pd.Grouper(freq="D"))
            group = g[txt].agg(
                mean="mean",
                n_total="size",
                n_valid="count"
            )
            group["n_nan"] = group["n_total"] - group["n_valid"]
            wt_days[txt] = group["mean"].where(group["n_nan"] <= 18)
            
            g = wt_days.groupby(pd.Grouper(freq="MS"))
            group = g[txt].agg(
                mean="mean",
                n_total="size",
                n_valid="count"
            )
            group["n_nan"] = group["n_total"] - group["n_valid"]
            wt_mons[txt] = group["mean"].where(group["n_nan"] <= 7)
            
            g = wt_mons.groupby(pd.Grouper(freq="YS"))
            group = g[txt].agg(
                mean="mean",
                n_total="size",
                n_valid="count"
            )
            group["n_nan"] = group["n_total"] - group["n_valid"]
            wt_year[txt] = group["mean"].where(group["n_nan"] <= 2)     
        
        ds_hour = wt_hour.to_xarray()
        ds_days = wt_days.to_xarray()
        ds_mons = wt_mons.to_xarray()
        ds_year = wt_year.to_xarray()
        
        names = ["latitude", "longitude","water temperature"]
        units = ["degrees north","degrees east","degrees C"]
        
        # define the long variable names and assign the units
        ds_hour.attrs["long_name"] = names
        ds_days.attrs["long_name"] = names
        ds_mons.attrs["long_name"] = names
        ds_year.attrs["long_name"] = names
        ds_hour.attrs["units"] = units
        ds_days.attrs["units"] = units
        ds_mons.attrs["units"] = units
        ds_year.attrs["units"] = units
            
        # file to save
        file_front = f_new + str(stat["Reg"]) 
        
        # save the dataset
        ncf_hour = (file_front + "_Hour.nc")
        ncf_days = (file_front + "_Day.nc")
        ncf_mons = (file_front + "_Month.nc")
        ncf_year = (file_front + "_Year.nc")
        
        ds_hour.to_netcdf(path=ncf_hour, mode="w")
        ds_days.to_netcdf(path=ncf_days, mode="w")
        ds_mons.to_netcdf(path=ncf_mons, mode="w")
        ds_year.to_netcdf(path=ncf_year, mode="w")
        
        # because there are multiple depths at which data are collected, only the
        # most shallow depth is used for determining the length of the time series
        cy = wt_year.columns
        stat_all.loc[i,"N_Yr"] = len(wt_year[cy[2]])
        stat_all.loc[i,"N_Mn"] = sum(~np.isnan(wt_year[cy[2]]))

e = time.time()
print("Successfully processed all at " + str(round((e - s), 3)) + " seconds")

stat_A = stat_all.copy()

# prepare the columns and write them to a CSV file
stat_A["Reg"] = stat_A["Reg"].str.rjust(40) + " "
stat_A["Type"] = " " + stat_A["Type"].str.ljust(5)
stat_A["Abr"] = " " + stat_A["Abr"].str.ljust(17)
stat_A["Lon"] = stat_A["Lon"].map("{:+9.3f}".format) + " "
stat_A["Lat"] = stat_A["Lat"].map("{:+9.3f}".format) + " "
stat_A["Org"] = " " + stat_A["Org"].str.replace("\"","").str.ljust(125)
stat_A["Name"] = " " + stat_A["Name"].replace("\"","").str.ljust(140)
stat_A["N_Yr"] = " " + stat_A["N_Yr"].map("{:2d}".format) + " "
stat_A["N_Mn"] = " " + stat_A["N_Mn"].map("{:2d}".format)

stat_A.to_csv('Docs/List_Climo_All.txt',index=False,sep="|")
