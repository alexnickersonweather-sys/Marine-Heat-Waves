# Purpose: Make plots of the raw FACT data
#
# Date of Version 01: Aug. 07, 2025
#
# Author 01: Alexander Nickerson
#

import numpy as np
import pandas as pd
import xarray as xr
import os
import time
import C01_Plot as c01p
import matplotlib.pyplot as plt

s = time.time()

# get the list of stations and strip the whitespace from the strings
stat_all = pd.read_csv('Docs/List_Download_All.txt',
                        header=0, sep="|", index_col=False)

for stat in stat_all.columns:
    if stat_all[stat].dtype == 'object':
        stat_all[stat] = stat_all[stat].str.strip()

# loop through three types
# USF data has a different format and cannot be plotted in this manner
for t in ["FACT","NDBC","SWT"]:
    # take subset of data
    stat_type = stat_all.loc[stat_all["Type"] == t,:]
    
    folder = "Figs/Data/" + t + "_L00N/"
    
    # create the folder only if necessary
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    # set the plot window
    fig, ax = c01p.plot_L00N()
    
    # loop through FACT stations
    for i, stat in stat_type.iterrows():
        # extract data from netCDF files
        file2open = "Data/" + t + "/L00N/" + stat["Reg"] + ".nc"
        
        # open the dataframe
        ds = xr.open_dataset(file2open)
        df = ds.to_dataframe()
        ds.close()
       
        # get the timestamps and prepare the plot window based on range of data
        T_min = df["time"].iat[ 0].to_datetime64().astype('datetime64[Y]')
        T_max = df["time"].iat[-1].to_datetime64().astype('datetime64[Y]') + np.timedelta64(1,'Y')
        
        # adjust the axis windows based on time span
        for i in range(0,2):
            ax[i].set_xlim(T_min,T_max)
            plt.setp(ax[i].get_xticklabels(), fontsize=12, rotation=90)
        
        # mask the water temperature
        wt = np.ma.MaskedArray(df["sea_water_temperature"])
        wt.mask = df["sea_water_temperature_qc_agg"] > 2
    
        # plot the raw data and the QC'd data
        ax[1].plot(df["time"],df["sea_water_temperature_qc_agg"],'ko',markersize=0.5,mfc='k')
        ax[0].plot(df["time"],df["sea_water_temperature"],'ko',markersize=0.5,mfc='k')
        ax[0].plot(df["time"],wt,'ro',markersize=0.5,mfc='r')
        
        # create the name for the saved figure
        file2save = folder + stat["Abr"] + "_" + stat["Reg"] + ".png"
        
        fig.suptitle(stat["Abr"] + "\n" + stat["Name"])
    
        # save the figure
        fig.savefig(file2save, dpi=300)
        
        # remove the title
        fig.suptitle("")
        
        # remove the lines for easy looping
        for i in range(0,2):
            for line in ax[i].lines:
                line.remove()
            
# close the figure
plt.close()

# print time to run code
e = time.time()
print("Time taken: ", round((e - s), 3), "seconds")