# Purpose: Create a simple map showing where the stations are found.
#
# Date of Version 01: Oct. 16, 2025
#
# Author 01: Alexander Nickerson
#

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import os
import C03_Map as cm

# get the list of stations and strip the whitespace from the strings
stat_all = pd.read_csv('Docs/List_Download_All.txt',
                        header=0, sep="|", index_col=False)

for stat in stat_all.columns:
    if stat_all[stat].dtype == 'object':
        stat_all[stat] = stat_all[stat].str.strip()

folder = "Figs/Maps/"

# create the folder only if necessary
if not os.path.exists(folder):
    os.makedirs(folder)
# end if    

fig, ax = cm.map_C03(np.floor( np.min(stat_all["Lon"]) ),
                     np.ceil(  np.max(stat_all["Lon"]) ),
                     np.floor( np.min(stat_all["Lat"]) ),
                     np.ceil(  np.max(stat_all["Lat"]) ))
    
ax.set_title("Locations of All Stations")

# plot world map
world = gpd.read_file(
    "https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_admin_0_countries.geojson"
)
world.plot(ax=ax, color=[0.7,0.7,0.7], edgecolor='black')  # You can change 'skyblue' to any color

ax.plot(stat_all["Lon"],stat_all["Lat"],'ro',markersize=1,mfc='r')
    
plt.tight_layout()

# save the figure
file2save = folder + "Locations_All.png"
fig.savefig(file2save, dpi=300)

for line in ax.lines:
    line.remove()

for t in ["FACT","NDBC","SWT","USF"]:
    stat_own = stat_all.loc[stat_all["Type"] == t,:]

    fig, ax = cm.map_C03(np.floor( np.min(stat_own["Lon"]) ),
                         np.ceil(  np.max(stat_own["Lon"]) ),
                         np.floor( np.min(stat_own["Lat"]) ),
                         np.ceil(  np.max(stat_own["Lat"]) ))

    ax.plot(stat_own["Lon"],stat_own["Lat"],'ro',markersize=1,mfc='r')
        
    plt.tight_layout()

    # save the figure
    file2save = folder + "Locations_" + t + ".png"
    fig.savefig(file2save, dpi=300)

    for line in ax.lines:
        line.remove()
