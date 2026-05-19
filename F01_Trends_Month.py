# Purpose: Create a simple bar chart showing the number of stations
#
# Date of Version 01: Oct. 15, 2025
#
# Author 01: Alexander Nickerson
#

import os
import numpy as np
import pandas as pd
import xarray as xr
from trend_compute import trend

# get the list of stations and strip the whitespace from the strings
stat_all = pd.read_csv("Docs/List_Climo_All.txt",
                       header=0, delimiter="|")

for stat in stat_all.columns:
    if stat_all[stat].dtype == 'object':
        stat_all[stat] = stat_all[stat].str.strip()
        
# remove USF stations since they need their own dedicated code

# create empty dataframe to hold the results
num_rows = len(stat_all)

trends = pd.DataFrame()

g = 10    # year threshhold for means
y = 10    # year threshhold for data
mg = 12*g # year threshhold for means in years
my = 12*y # year threshhold for means in years

for i, stat in stat_all.iterrows():
    file = "Data/" + stat["Type"].strip() + "/Climo/" + stat["Reg"].strip() + '_Month.nc'
    
    # open the data file
    ds = xr.open_dataset(file)
    df = ds.to_dataframe()
    df = df.reset_index()
    ds.close()
    
    # get the depths
    dep = df.columns[3:]
    
    # remove columns that have less than 10 years of data
    for d in dep:
        if sum(~np.isnan(df[d])) < mg:
            df = df.drop(columns=d)
        
    # check if any columns remain before proceeding
    if len(df.columns) < 4:
        continue
    else:
        dep = df.columns[3:]    
    
    # get the number of depths
    nd = len(dep) 
    
    for d in dep:
        # get time stamps in format appropriate for computing trends
        yr = df["time"].dt.year + (df["time"].dt.month-1)/12
        
        # number of years of data
        ng = sum(~np.isnan(df[d]))
        
        # length of time series
        ny = len(df[d])
        
        # compute trends and y-intercepts
        # but only compute the trend errors if there is at least 10 years of means
        if ng >= mg and ny >= my:
            slope, yint, dof, t95, ci95 = trend(yr,df[d],"m")
        elif ng < mg and ny >= my:
            slope, yint, _, _, _ = trend(yr,df[d],"m")
            dof = np.nan
            t95 = np.nan
            ci95 = np.nan
        else:
            continue
        
        new_row = pd.DataFrame({'Reg': stat["Reg"],
                                'Type': stat["Type"],
                                'Abr': stat["Abr"],
                                'Lon': stat["Lon"],
                                'Lat': stat["Lat"],
                                'Org': stat["Org"],
                                'Name': stat["Name"],
                                'N_Yr': stat["N_Yr"],
                                'N_Mn': stat["N_Mn"],
                                'Depth': d,
                                'Trend': slope,
                                'Y_Int': yint,
                                'DoF': dof,
                                'T_95': t95,
                                'CI_95': ci95})
        trends = pd.concat([trends,new_row], ignore_index=True)

# prepare the folder for saving the data
fold_save = "Stats"
if not os.path.exists(fold_save):
    os.makedirs(fold_save)
    
# prepare the columns and write them to a CSV file
trends["Reg"] = trends["Reg"].str.rjust(40) + " "
trends["Type"] = " " + trends["Type"].str.ljust(5)
trends["Abr"] = " " + trends["Abr"].str.ljust(17)
trends["Lon"] = trends["Lon"].map("{:+9.3f}".format) + " "
trends["Lat"] = trends["Lat"].map("{:+9.3f}".format) + " "
trends["Org"] = " " + trends["Org"].str.replace("\"","").str.ljust(125)
trends["Name"] = " " + trends["Name"].str.replace("\"","").str.ljust(120)
trends["N_Yr"] = " " + trends["N_Yr"].map("{:2d}".format) + " "
trends["N_Mn"] = " " + trends["N_Mn"].map("{:2d}".format) + " "
trends["Depth"] = " " + trends["Depth"].str.ljust(4)
trends["Trend"] = " " + trends["Trend"].map("{:+9.3f}".format) + " "
trends["Y_Int"] = " " + trends["Y_Int"].map("{:+9.3f}".format) + " "
trends["DoF"] = " " + trends["DoF"].map("{:5.0f}".format) + " "
trends["T_95"] = " " + trends["T_95"].map("{:9.3f}".format) + " "
trends["CI_95"] = " " + trends["CI_95"].map("{:9.3f}".format)

trends.to_csv('Stats/Trends_Month.txt',index=False,sep="|")
