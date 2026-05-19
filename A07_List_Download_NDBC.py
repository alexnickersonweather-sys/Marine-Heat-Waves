# Purpose: Combine the lists into one
#
# Date of Version 01: May  23, 2025
#
# Author 01: Alexander Nickerson
#

import os
import pandas as pd
    
# open the text file, name the columns, and sort
stat_all = pd.read_csv('Docs/List_Redux_NDBC.txt',
                        header=0, sep="|", index_col=False)

stat_all = stat_all.sort_values(by=['Org','Reg']).reset_index(drop=True)

stat_full = stat_all["Reg"].astype(str) + "_" + stat_all["Abr"].str.strip()

# get the list of files
folder = "Data/NOAA-NDBC/L00D/"
file_all = sorted([f for f in os.listdir(folder)])

# check for stations that actually downloaded data and keep those only
is_down = stat_full.isin(file_all)
stat_all = stat_all.loc[is_down == True]

# prepare the columns and write them to a CSV file
stat_all["Reg"] = stat_all["Reg"].astype(str).str.rjust(40) + " "
stat_all["Type"] = stat_all["Type"].str.ljust(5)
stat_all["Abr"] = stat_all["Abr"].str.ljust(17)
stat_all["Lon"] = stat_all["Lon"].map("{:+9.3f}".format) + " "
stat_all["Lat"] = stat_all["Lat"].map("{:+9.3f}".format) + " "
stat_all["Org"] = stat_all["Org"].str.replace("\"","").str.ljust(125)
stat_all["Name"] = stat_all["Name"]

stat_all.to_csv('Docs/List_Download_NDBC.txt',index=False,sep="|")
