# Purpose: Combine the two lists into one
#
# Date of Version 01: Mar. 04, 2026
#
# Author 01: Alexander Nickerson
#

import pandas as pd
    
# open the text files
stat_N = pd.read_csv('Docs/List_Download_NDBC.txt',
                        header=0, sep="|", index_col=False)
stat_E = pd.read_csv('Docs/List_Download_ERDDAP.txt',
                        header=0, sep="|", index_col=False)

# combine the station listings and sort them
stat_all = pd.concat([stat_N, stat_E], ignore_index=True)
stat_all = stat_all.sort_values(by=["Type","Abr","Reg"]).reset_index(drop=True)

# prepare the columns and write them to a CSV file
stat_all["Reg"] = stat_all["Reg"].astype(str).str.rjust(40) + " "
stat_all["Type"] = " " +stat_all["Type"].str.ljust(5)
stat_all["Abr"] = " " +stat_all["Abr"].str.ljust(17)
stat_all["Lon"] = stat_all["Lon"].map("{:+9.3f}".format) + " "
stat_all["Lat"] = stat_all["Lat"].map("{:+9.3f}".format) + " "
stat_all["Org"] = " " + stat_all["Org"].str.replace("\"","").str.ljust(125)
stat_all["Name"] = " " +stat_all["Name"]

stat_all.to_csv('Docs/List_Download_All.txt',index=False,sep="|")
