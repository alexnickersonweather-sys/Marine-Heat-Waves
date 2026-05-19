# Purpose: Create a simple bar chart showing the number of stations
#
# Date of Version 01: Oct. 15, 2025
#
# Author 01: Alexander Nickerson
#

import numpy as np
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
# end if    

# my personal preferences for font
plt.rcParams["font.family"] = "serif"
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['font.size'] = 12

fig, ax = plt.subplots()
plt.draw()

# y-axis labels
ax.set_ylabel(r'Count')

# x-axis limits and tick marks
ax.set_xlim(0,+5)
ax.set_xticks(np.arange(0.5,4.0,step=1))
ax.set_xticklabels(["FACT","NDBC","SWT","USF"])
    
# y-axis limits and tick markcs
ax.set_ylim(0,670)
ax.set_yticks(np.arange(0,601,step=100))
ax.yaxis.set_minor_locator(MultipleLocator(25))
    
# plot title
ax.set_title("Number of Stations")

# loop through types of stations
for i, t in enumerate(["FACT","NDBC","SWT","USF"]):
    # get the station counts
    n_type = len(stat_all.loc[stat_all["Type"] == t,:])

    # set the x ranges for the bars to be plotted
    x_type = [0.25 + i,0.75 + i,0.75 + i,0.25 + i,0.25 + i]

    # set the y ranges for the bars to be plotted
    y_type = [-20,-20,n_type,n_type,-20]

    # plot the bars (really rectangles)
    ax.fill(x_type, y_type, "r")

    # print the counts for each collection
    ax.text(0.5 + i,n_type+15,n_type,ha='center')

# save the figure
file2save = folder + "Counts_All.png"
fig.savefig(file2save, dpi=300)
