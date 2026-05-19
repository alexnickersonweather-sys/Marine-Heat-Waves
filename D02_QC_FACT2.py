# Purpose: run special station specific quality control on the data
#
# Date of Version 01: Nov. 03, 2025
#
# Author 01: Alexander Nickerson
#

import numpy as np
import xarray as xr

# these two pairs of files can used to QC one another
file_all = [["SCDNR_scdnrdfp_sc-savannah-12","SCDNR_scdnrdfp_sc-savannah-13"],
            ["MML_scan_ps13","MML_scan_ps12"]]

# loop through station pairs
for file in file_all:
    # files to open
    file1 = "Data/FACT/QC/" + file[0] + ".nc"
    file2 = "Data/FACT/QC/" + file[1] + ".nc"
    
    # open the files
    ds1 = xr.open_dataset(file1,mask_and_scale=True)
    df1 = ds1.to_dataframe()
    ds1.close()
    
    ds2 = xr.open_dataset(file2,mask_and_scale=True)
    df2 = ds2.to_dataframe()
    ds2.close()
    
    # perform side-by-side comparions to identify outliers
    dwt = abs(df1["wt_new"] - (df2["wt_new"] + 0.5))
    if file[0] == "SCDNR_scdnrdfp_sc-savannah-12":
        bad = np.logical_and(dwt > 1.0, df1.index < "2024-08-01T00:00:00")
    elif file[0] == "MML_scan_ps13":
        bad = (dwt > 2.0)
    
    # set flags
    df1.loc[bad,"wt_new"] = np.nan
    df1.loc[bad,"wt_flag"] = 3
    df1.loc[bad,"wt_info"] = "Failed comparison to adjacent station"
        
    # set the index and convert to an xarray
    ds1 = df1.to_xarray()
    
    # define the long variable names
    ds1.attrs["long_name"] = [
        "longitude",
        "latitude",
        "water temperature",
        "water temperature QARTOD flag",
        "water temperature QARTOD failure reason"]
    
    # assign the units
    ds1.attrs["units"] = [
        "degrees north",
        "degrees east",
        "degrees C",
        "QARTOD flag",
        "QARTOD flag reason"]
    
    # save the dataset
    ds1.to_netcdf(path=file1, mode="w")
