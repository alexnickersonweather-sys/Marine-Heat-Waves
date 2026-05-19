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

# get station owners
owners = stat_all["Abr"]

# count unique station owners
owner, count = np.unique(owners, return_counts=True)

# choose your own thresholds
ct_lim = [10,50]

# loop to create two different plots based on each chosen threshold
for c in ct_lim:
    limits = (count > c)
    ownerL = owner[limits == True]
    countL = count[limits == True]
    
    # my personal preferences for font
    plt.rcParams["font.family"] = "serif"
    plt.rcParams['font.serif'] = ['Times New Roman']
    plt.rcParams['font.size'] = 12
    
    # create the figure window
    fig, ax = plt.subplots()
    plt.draw()
    
    # y-axis label
    ax.set_ylabel(r'Count')
    
    # x-axis limits and tick marks
    ax.set_xlim(0,len(ownerL))
    ax.set_xticks(np.arange(0.5,len(ownerL),step=1))
    ax.set_xticklabels(ownerL,rotation=90)
        
    # y-axis limits and tick marks
    ax.set_ylim(0,150)
    ax.set_yticks(np.arange(0,151,step=25))
    ax.yaxis.set_minor_locator(MultipleLocator(5))
    ax.set_yticklabels(np.arange(0,151,step=25))
       
    # plot title
    ax.set_title("Number of Stations by Owner")
    
    # plot owner counts
    for i, x in enumerate(countL):
        x_box = [i+0.25,i+0.75,i+0.75,i+0.25,i+0.25]
        y_box = [-20,-20,countL[i],countL[i],-20]
        ax.fill(x_box, y_box, "r")
    
    # save the figure
    file2save = folder + "Counts_Owner_" + str(c) + ".png"
    fig.savefig(file2save,bbox_inches='tight',dpi=300)
