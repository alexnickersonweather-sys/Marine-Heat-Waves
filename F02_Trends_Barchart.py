# Purpose: Create a simple bar chart showing the depths at each station
#
# Date of Version 01: Nov. 03, 2025
#
# Author 01: Alexander Nickerson
#

import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.ticker import MultipleLocator

t = "Year"

# open station lists
stat_A = pd.read_csv(('Stats/Trends_' + t + '.txt'),
                        header=0, sep="|", index_col=False)

folder = "Figs/Statistics/"
    
# my personal preferences for font
plt.rcParams["font.family"] = "serif"
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['font.size'] = 12

for i in range(10,31,10):
    Pt_A = ((stat_A["N_Mn"] >= i) & (stat_A["N_Mn"] < i + 10))
    sA = stat_A.loc[Pt_A,:].reset_index(drop=True)
    
    # create the folder only if necessary
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    fig, ax = plt.subplots()
    plt.draw()
    
    # axis labels; rotate the x-axis labels 90 degrees
    ax.set_ylabel(r'Count')
    
    # x-axis limits and ticks
    ax.set_xlim(-0.3,1.5)
    ax.set_xticks(np.arange(-0.3,1.51,step=0.05))
    ax.xaxis.set_minor_locator(MultipleLocator(5))
    ax.set_xticklabels(np.arange(-0.3,1.51,step=0.05),rotation=90)
    ax.xaxis.set_major_formatter(mtick.FormatStrFormatter('%.2f'))
        
    # y-axis limits and titles
    ax.set_ylim(0,26)
    ax.set_yticks(np.arange(0,26,step=5))
    ax.yaxis.set_minor_locator(MultipleLocator(1))
    ax.set_yticklabels(np.arange(0,26,step=5))
      
    # plot title
    ax.set_title(r'Number of Stations by Trend ($^{\circ}$C/dec)')
    
    # make bars
    ax.hist(np.array(sA["Trend"]*10), bins=np.arange(-0.3,1.5,step=0.05))
    
    # save file
    file2save = folder + "Counts_Trends_" + t + str(i) + ".png"
    fig.savefig(file2save,bbox_inches='tight',dpi=300)
