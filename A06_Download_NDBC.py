# Purpose: Download NDBC station data from the NDBC website
#
# Date of Version 01: ???? ??, 201?
# Date of Version 02: Apr. 03, 2025
#
# Author 01: Alexander Nickerson
# Author 02: Alexander Nickerson
#
# Version 02 collects all data from all NDBC stations by examining the full
#            list of stations and recursively parsing through them all
#

import requests
import pandas as pd
import os
    
stat_all = pd.read_csv('Docs/List_Redux_NDBC.txt',
                        header=None, sep=";", index_col=False)
stat_all.columns = ["Buoy","Lat","Lon","Owner"]
stat_all["Buoy"] = stat_all["Buoy"].astype(str)
stat_all["Owner"] = stat_all["Owner"].str.strip()

# loop through all hyperlinks
for i, stat in stat_all.iterrows():
    # loop through the years of data, and this method ensures all years from 
    # all stations are included, albeit at the cost of time
    for yr in range(1970,2025):
        # full NDBC link
        url = ("https://www.ndbc.noaa.gov/view_text_file.php?filename=" +
               stat["Buoy"] + "h" + str(yr) + 
               ".txt.gz&dir=data/historical/stdmet/")
        
        # make the web request
        req  = requests.get(url);
        
        # code 200 means requests found a real page with data
        if (req.status_code != 200):        
            continue
        
        # folder to save the data must be created if it doesn't exist
        folder_path = ("Data/NDBC/L00D/" + stat["Buoy"])
        
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        # this puts the text in a python friendly format
        filename = (folder_path + "/" + stat["Buoy"] + '_' + str(yr) + ".dat")
        
        # save the data
        f = open(filename, "w")
        data = req.content.decode("utf-8");
        data = data.replace('\r\n', '\n');
        f.write(data);
        
    print("Finished station " + stat["Buoy"])
        
print('Finished all stations.');
