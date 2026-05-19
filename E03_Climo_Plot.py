# Purpose: Make plots of the QC'd FACT data
#
# Date of Version 01: Nov. 05, 2025
#
# Author 01: Alexander Nickerson
#

import numpy as np
import pandas as pd
import xarray as xr
import os
from math import floor
import time
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MultipleLocator

s = time.time()

stat_all = pd.read_csv('Docs/List_Climo_Redux.txt',
                        header=0, sep="|", index_col=False)

for stat in stat_all.columns:
    if stat_all[stat].dtype == 'object':
        stat_all[stat] = stat_all[stat].str.strip()

stat_all = stat_all.loc[stat_all["Type"] == "USF",:].reset_index(drop=True)

folder = "Figs/Data/USF_Climo"

# create the folder only if necessary
if not os.path.exists(folder):
    os.makedirs(folder)
# end if

# my personal preferences for font
plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman"]
plt.rcParams["font.size"] = 12

# plotting in this matter works better due to the varying numbers of windows
px = 0.10
sx = 0.85
gy = 0.17
ty = 0.08
dy = 0.02

# loop through stations
for t in ["USF","FACT","NDBC","SWT","USF"]:
    stat_own = stat_all.loc[stat_all["Type"] == t,:].reset_index(drop=True)
    
    # folder path information
    f_old = "Data/" + t + "/Climo/"
    f_new = "Figs/Data/" + t + "_Climo/"
    
    # create the folder only if necessary
    if not os.path.exists(f_new):
        os.makedirs(f_new) 
        
    # loop through stations
    for i, stat in stat_own.iterrows():
        # extract data from netCdf_hour files
        file_hour = f_old + stat["Reg"] + "_Hour.nc"
        file_days = f_old + stat["Reg"] + "_Day.nc"
        file_mons = f_old + stat["Reg"] + "_Month.nc"
        file_year = f_old + stat["Reg"] + "_Year.nc"
        
        # open the data files
        ds_hour = xr.open_dataset(file_hour)
        ds_days = xr.open_dataset(file_days)
        ds_mons = xr.open_dataset(file_mons)
        ds_year = xr.open_dataset(file_year)
    
        df_hour = ds_hour.to_dataframe()
        df_days = ds_days.to_dataframe()
        df_mons = ds_mons.to_dataframe()
        df_year = ds_year.to_dataframe()
        
        ds_hour.close()
        ds_days.close()
        ds_mons.close()
        ds_year.close()
        stop
        # get the number of depths
        col = df_year.columns[2:]
        nd = len(col) 
        n_lb = floor(nd/2)
        
        # adjust the size of the windows based on the number needed
        sy = (1 - gy - ty - (nd-1)*dy)/nd
            
        # create the plot window
        fig = plt.figure()
        plt.draw()
        
        axs = []
        
        # set the grid with the desired subplots
        for n in range(0,nd):
            # get the depth
            txt = col[n]
            
            # set the position for the window
            py = gy + n*(sy+dy)
            
            ax = fig.add_axes([px,py,sx,sy])
            
            # x-axis limits and ticks
            ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1)))
            ax.xaxis.set_minor_locator(mdates.MonthLocator())
            
            ax.xaxis.set_major_formatter(
                mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
        
            # y-axis limits and ticks
            ax.set_ylim(+8,+36)
            
            ax.set_yticks(np.arange(10,40,step=10))
            ax.yaxis.set_minor_locator(MultipleLocator(1))
            
            # plot basic gridlines
            ax.grid()
            
            # plot the tick labels
            plt.setp(ax.get_xticklabels(), fontsize=12, rotation=90)
            
            # some prefer to plot with specific time ranges; others like fixed
            # T_min = np.datetime64('1997-01-01T00:00:00').astype('datetime64[Y]')
            # T_max = np.datetime64('2025-01-01T00:00:00').astype('datetime64[Y]')
            T_min = df_hour.index[ 0].to_datetime64().astype('datetime64[Y]')
            T_max = df_hour.index[-1].to_datetime64().astype('datetime64[Y]') + np.timedelta64(1,'Y')
            
            # get span of times for determining x-axis tick spacing
            dt = (T_max - T_min).astype('timedelta64[s]') 
            
            if dt < np.timedelta64(3600*24*30*6,'s'):
                ax.xaxis.set_major_locator(mdates.DayLocator(1))
                ax.xaxis.set_minor_locator(mdates.DayLocator())
            else:
                ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1)))
                ax.xaxis.set_minor_locator(mdates.MonthLocator())
                
            # no x-axis labels on windows except the bottom one
            if n > 0:
                ax.set_xticklabels([])
            
            # set the plot range
            ax.set_xlim(T_min,T_max)
            plt.setp(ax.get_xticklabels(), fontsize=12, rotation=90)
        
            # plot the raw data and the QC'd data
            ax.plot(df_hour.index,df_hour[txt],'ko',markersize=0.5,mfc='k')
            ax.plot(df_days.index,df_days[txt],'ro',markersize=0.5,mfc='r')
            ax.plot(df_mons.index,df_mons[txt],'bs',markersize=3.0,mfc='b')
            ax.plot(df_year.index,df_year[txt],'ys',markersize=6.0,mfc='y')
            
            axs.append(ax)
            
        # axis labels
        axs[0].set_xlabel(r'Date')
        axs[n_lb].set_ylabel(r'Temperature ($^{\circ}$C)')
        
        # adjust axis location to be centered
        if nd % 2 == 0:
            axs[n_lb].yaxis.set_label_coords(-0.07,-0.1)
        else:
            axs[n_lb].yaxis.set_label_coords(-0.07,+0.5)
        
        # create the name for the saved figure
        if stat["Abr"] == "USF-COMPS":
            file2save = f_new + stat["Reg"][0:3] + ".png"
        else:
            file2save = f_new + stat["Reg"] + ".png"
    
        if stat["Abr"] == "USF-COMPS":
            fig.suptitle(stat["Abr"] + " " + stat["Name"][0:3])
        else:
            fig.suptitle(stat["Abr"] + " " + stat["Name"])
        
        # save the figure
        fig.savefig(file2save, dpi=300)
    stop
# end for

plt.close()

e = time.time()
print("Time taken: ", round((e - s), 3), "seconds")
