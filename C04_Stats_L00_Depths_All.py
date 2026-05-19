# Purpose: Create a simple bar chart showing the depths at each station
#
# Date of Version 01: Nov. 03, 2025
#
# Author 01: Alexander Nickerson
#

import numpy as np
import xarray as xr
import pandas as pd
import os
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

# get the list of stations and strip the whitespace from the strings
stat_all = pd.read_csv('Docs/List_Download_All.txt',
                        header=0, sep="|", index_col=False)

for stat in stat_all.columns:
    if stat_all[stat].dtype == 'object':
        stat_all[stat] = stat_all[stat].str.strip()
        
folder = "Figs/Statistics/"

# create the folder only if necessary
if not os.path.exists(folder):
    os.makedirs(folder)

depth = []

# no USF due to the multiple depths of measurement
for t in ["FACT","NDBC","SWT"]:
    # get subset of stations
    stat_own = stat_all.loc[stat_all["Type"] == t,:]
    
    for i, stat in stat_own.iterrows():
        # extract data from netCDF files
        file2open = "Data/" + t + "/L00N/" + stat["Reg"].strip() + ".nc"
    
        ds = xr.open_dataset(file2open)
        df = ds.to_dataframe()
        df = df.reset_index()
        ds.close()
        
        z = np.nanmean(df["z"])
        depth.append(z)
    
# my personal preferences for font
plt.rcParams["font.family"] = "serif"
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['font.size'] = 12

# generate the figure window
fig, ax = plt.subplots()
plt.draw()

# axis labels; rotate the x-axis labels 90 degrees
ax.set_ylabel(r'Count')

# x-axis limits and ticks
ax.set_xlim(0,160)
ax.set_xticks(np.arange(0,160.5,step=10))
ax.xaxis.set_minor_locator(MultipleLocator(5))
ax.set_xticklabels(np.arange(0,160.5,step=10),rotation=90)

# y-axis limits and ticks
ax.set_ylim(0,700)
ax.set_yticks(np.arange(0,701,step=100))
ax.yaxis.set_minor_locator(MultipleLocator(50))
ax.set_yticklabels(np.arange(0,701,step=100))

# plot title
ax.set_title("Number of Stations by Depth")

# plot the data
ax.hist(-np.array(depth), bins=np.arange(-10,160.5,step=5))
plt.show()

# save the figure
file2save = folder + "Counts_Depth_All.png"
fig.savefig(file2save,bbox_inches='tight',dpi=300)
