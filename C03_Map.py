# Purpose: Create and return the figure and axis for a simple map
#
# Date of Version 01: May  15, 2026
#
# Author 01: Alexander Nickerson
#

import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

def map_c03(x_min,y_min,x_max,y_max):

    # my personal preferences for font
    plt.rcParams["font.family"] = "serif"
    plt.rcParams['font.serif'] = ['Times New Roman']
    plt.rcParams['font.size'] = 12
    
    # create a figure window
    fig, ax = plt.subplots(figsize=(10, 6))
    plt.draw()
    
    # my preferred color for maps
    ax.set_facecolor((176/255,224/255,230/255))
    
    # axis labels
    ax.set_xlabel(r'Longitude ($^\circ$W)')
    ax.set_ylabel(r'Latitude ($^\circ$N)')
    
    # x-tick labels and limits
    ax.set_xticks(np.arange(-360,+361,step=10))
    ax.xaxis.set_minor_locator(MultipleLocator(1))
    ax.set_xticklabels(abs(np.arange(-360,+361,step=10)))
    ax.set_xlim(x_min,x_max)
        
    # y-tick labels and limits
    ax.set_yticks(np.arange(-90,+91,step=5))
    ax.yaxis.set_minor_locator(MultipleLocator(1))
    ax.set_yticklabels(np.arange(-90,+91,step=5))
    ax.set_ylim(y_min,y_max)
    
    # plot world map
    world = gpd.read_file(
        "https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_admin_0_countries.geojson"
    )
    world.plot(ax=ax, color=[0.7,0.7,0.7], edgecolor='black')  # You can change 'skyblue' to any color
    
    return fig, ax
