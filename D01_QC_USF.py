# Purpose: Convert USF data into same format as FACT, NDBC, and SWT data.
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

stat_all = stat_all.loc[stat_all["Type"] == "USF",:]

nsa = 2
nsd = 3
q_lo = 0.003
q_hi = 0.997

head = "Data/USF/"
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
                            "sea_water_temperature": "wt_new", 
                            "sea_water_temperature_qc_agg": "wt_flag"})
    
    # cull any NaN's from the data
    Pt = ~np.isnan(df["wt_new"])
    df = df.loc[Pt,:].set_index('time')
    
    df["wt_info"] = np.full(np.shape(df["wt_new"]),"Not tested",dtype='O')
    df.loc[df["wt_flag"] == 1,"wt_info"] = "Passed"
    df.loc[df["wt_flag"] == 2,"wt_info"] = "Untested"
    df.loc[df["wt_flag"] >= 3,"wt_info"] = "Failed"
    df.loc[df["wt_flag"] == 9,"wt_info"] = "Missing or not measured"
    
    # set the index and convert to an xarray
    ds = df.to_xarray()
    
    # define the long variable names
    ds.attrs["long_name"] = [
        "longitude",
        "latitude",
        "water temperature",
        "water temperature QARTOD flag",
        "water temperature QARTOD failure reason"
    ]
    
    # assign the units
    ds.attrs["units"] = [
        "degrees north",
        "degrees east",
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
