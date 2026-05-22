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
from datetime import date
import marineheatwaves as mhw
import time
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MultipleLocator
from math import floor

s = time.time()
# get the list of stations and strip the whitespace from the strings
stat_all = pd.read_csv('Docs/List_Climo_All.txt',
                        header=0, sep="|", index_col=False)

for stat in stat_all.columns:
    if stat_all[stat].dtype == 'object':
        stat_all[stat] = stat_all[stat].str.strip()

folder = "Figs/MHW_Possible/"

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
sx = 0.81
gy = 0.17
ty = 0.08
dy = 0.02
    
g = 10     # year threshhold for means
y = 20     # year threshhold for data
mg = 12*g  # year threshhold for means in months
my = 12*y  # year threshhold for means in months

cb = '#1A1AFF'
cg = '#1FFF35'
cr = '#FF311F'

# loop through stations
for i, stat in stat_all.iterrows():
    # data files to open
    file_daily = "Data/" + stat["Type"] + "/Climo/" + stat["Reg"].strip() + "_Day.nc"
    file_month = "Data/" + stat["Type"] + "/Climo/" + stat["Reg"].strip() + "_Month.nc"
    
    # open the daily data
    daily_ds = xr.open_dataset(file_daily)
    daily_df = daily_ds.to_dataframe()
    daily_df = daily_df.reset_index()
    daily_ds.close()
    
    # open the monthly data
    month_ds = xr.open_dataset(file_month)
    month_df = month_ds.to_dataframe()
    month_df = month_df.reset_index()
    month_ds.close()
    
    # get the number of depths
    col = daily_df.columns[3:]
    
    # remove columns that have less than 10 years of data
    for c in col:
        if sum(~np.isnan(month_df[c])) < mg:
            daily_df = daily_df.drop(columns=c)
            month_df = month_df.drop(columns=c)
        
    # check if any columns remain before proceeding
    if len(daily_df.columns) < 4:
        continue
    else:
        col = daily_df.columns[3:]    
    
    # get the number of depths
    nd = len(col) 
    
    # this factor helps to ensure the y-axis label is centered
    n_lb = floor(nd/2)
    
    # compute the height of the windows to be based on the number of depths    
    sy = (1 - gy - ty - (nd-1)*dy)/nd
        
    # create the plot window
    fig = plt.figure(1)
    plt.draw()
    
    axs = []

    # the date_ord must be forcibly reset because it retains its value
    # and thereby breaks the mhw.detect() function.
    # Likewise, climatologyPeriod has to be forcibly reset because otherwise
    # python retains the value from the prior instance and considers the value
    # to be defined already
    date_ord = None
    date_np = daily_df["time"].dt.date.to_numpy()
    date_ord = np.fromiter((d.toordinal() for d in date_np), dtype=np.int64)
    clim_per = [date.fromordinal(date_ord[0]).year,
                date.fromordinal(date_ord[-1]).year]
    
    # set the grid with the desired subplots
    for n in range(0,nd):
        # get the depth
        txt = col[n]
        
        # position window
        py = gy + (nd-n-1)*(sy+dy)
        
        ax = fig.add_axes([px,py,sx,sy])
        # ax = fig.add_subplot(gs[P1:P2,:])
    
        # x-axis ticks
        ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1)))
        ax.xaxis.set_minor_locator(mdates.MonthLocator())
            
        ax.xaxis.set_major_formatter(
            mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
        
        # y-axis limits and ticks
        ax.set_ylim(0,40)
        ax.set_yticks(np.arange(0,40,step=10))
        ax.yaxis.set_minor_locator(MultipleLocator(1))
        ax.tick_params(top=True, right=True, bottom=True, left=True)
        
        # turn on the grid
        ax.grid()
        
        # x-axis tick labels
        plt.setp(ax.get_xticklabels(), fontsize=12, rotation=90)
        
        # set the a-axis range
        T_min = np.datetime64('1997-01-01T00:00:00').astype('datetime64[Y]')
        T_max = np.datetime64('2025-01-01T00:00:00').astype('datetime64[Y]')
        # T_min = daily_df["time"].astype('datetime64[Y]')
        # T_max = daily_df["time"].astype('datetime64[Y]') + np.timedelta64(1,'Y')
        dt = (T_max - T_min).astype('timedelta64[s]') 
        
        # the range of the axis labels depends on the length of the time series
        if dt < np.timedelta64(3600*24*30*6,'s'):
            ax.xaxis.set_major_locator(mdates.DayLocator(1))
            ax.xaxis.set_minor_locator(mdates.DayLocator())
        else:
            ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1)))
            ax.xaxis.set_minor_locator(mdates.MonthLocator())
        
        # x-tick labels aren't needed except on the bottom window
        if n < (nd-1):
            ax.set_xticklabels([])
    
        # set the x-axis limits
        ax.set_xlim(T_min,T_max)
        plt.setp(ax.get_xticklabels(), fontsize=12, rotation=90)
        
        # plot the raw data and the QC'd data
        ax.plot(daily_df["time"],daily_df[txt],'ko',markersize=0.5,mfc='k')
    
        # plot the depth label
        T0 = ax.text( np.datetime64('2025-07-01T00:00:00').astype('datetime64[M]'),
                  20, txt)
        
        # number of years of data
        ng = sum(~np.isnan(month_df[txt]))
        
        # length of time series
        ny = len(month_df[txt])
        if ng < mg:# and ny >= my:
            continue
        if ny < my:# and ny >= my:
            continue
        
        # this helps ensure the dataframe isn't overwritten by the MHW function
        tmp = daily_df[txt].to_numpy().copy()
        
        # find the MHWs
        mhw_all, clim_WR = mhw.detect(date_ord,tmp,climatologyPeriod=clim_per,pctile=90,windowHalfWidth=5)
        mhw_all = pd.DataFrame.from_dict(mhw_all)

        rectangle = []
        
       # loop through all MHW events
        for d, m in mhw_all.iterrows():
            PX = (daily_df.loc[m["index_start"],"time"],
                  daily_df.loc[m["index_end"],"time"],
                  daily_df.loc[m["index_end"],"time"],
                  daily_df.loc[m["index_start"],"time"],
                  daily_df.loc[m["index_start"],"time"])
            PY = (-100,-100,100,100,-100)
            MC = m["category"]
            
            # plot if it's moderate, strong, or severe
            if MC == "Moderate":
                rectangle.append(ax.fill(PX,PY,facecolor=cb,edgecolor=None))
            elif MC == "Strong":
                rectangle.append(ax.fill(PX,PY,facecolor=cg,edgecolor=None))
            elif MC == "Severe":
                rectangle.append(ax.fill(PX,PY,facecolor=cr,edgecolor=None))
      
        axs.append(ax)
    
    # if nothing was plotted, continue
    if len(axs) == 0:
        continue
        
    # if there were plots, now it's worth the effort to plot the axis labels
    axs[0].set_xlabel(r'Date')
    axs[n_lb].set_ylabel(r'Temperature ($^{\circ}$C)')
    
    # position the y-axis label accordingly
    if nd % 2 == 0:
        axs[n_lb].yaxis.set_label_coords(-0.07,-0.1)
    else:
        axs[n_lb].yaxis.set_label_coords(-0.07,+0.5)
    
    # create the name for the saved figure
    if stat["Abr"] == "USF-COMPS":
        file2save = folder + stat["Type"] + "_" + stat["Reg"][0:3].upper() + ".png"
    else:
        file2save = folder + stat["Type"] + "_" + stat["Reg"] + ".png"

    if stat["Abr"] == "USF-COMPS":
        fig.suptitle(stat["Abr"] + " " + stat["Name"][0:3])
    else:
        fig.suptitle(stat["Abr"] + " " + stat["Name"])

    # save the figure
    fig.savefig(file2save, dpi=300)
    
    # close the figure to save memory
    plt.close(1)
    
# end for


e = time.time()
print("Time taken: ", round((e - s), 3), "seconds")
