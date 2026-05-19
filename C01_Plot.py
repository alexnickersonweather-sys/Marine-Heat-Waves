# Purpose: Make plots of the QC'd FACT data
#
# Date of Version 01: Nov. 05, 2025
#
# Author 01: Alexander Nickerson
#

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MultipleLocator

def plot_L00N():
    # my personal preferences for font
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["font.serif"] = ["Times New Roman"]
    plt.rcParams["font.size"] = 12
    
    # my personal preferences for font
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["font.serif"] = ["Times New Roman"]
    plt.rcParams["font.size"] = 12
    
    px = 0.10
    sx = 0.85
    gy = 0.17
    ty = 0.13
    dy = 0.02
    y1 = 0.45
        
    # create the plot window
    fig = plt.figure()
    plt.draw()
    ax = []
    
    # create the temperature plot window
    py = gy
    ax.append(fig.add_axes([px,py,sx,y1]))
    
    # create the QC plot window
    py = gy + dy + y1
    y2 = 1 - py - ty
    ax.append(fig.add_axes([px,py,sx,y2]))
    
    ax[0].set_xlabel(r'Date')
    ax[0].set_ylabel(r'Water Temperature ($^{\circ}$C)')
    ax[1].set_ylabel(r'QC Flag')
    
    ax[0].set_ylim(-2,+40)
    ax[1].set_ylim(0,+10)
    
    for i in range(0,2):
        ax[i].xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1)))
        ax[i].xaxis.set_minor_locator(mdates.MonthLocator())
        
    ax[0].xaxis.set_major_formatter(
        mdates.ConciseDateFormatter(ax[0].xaxis.get_major_locator()))
    ax[0].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    
    ax[0].set_yticks(np.arange(0,40,step=5))
    ax[0].set_yticklabels(np.arange(0,40,step=5))
    ax[0].yaxis.set_minor_locator(MultipleLocator(1))
    ax[1].set_yticks(np.arange(0,10,step=3))
    ax[1].yaxis.set_minor_locator(MultipleLocator(1))
    
    for i in range(0,2):
        ax[i].grid()
        plt.setp(ax[i].get_xticklabels(), fontsize=12, rotation=90)
    
    ax[1].set_xticklabels([])

    return fig, ax
