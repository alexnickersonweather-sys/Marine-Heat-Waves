# Purpose: Reduce NDBC stations down to only those from moored buoys in the 
#          SECOORA, GCOOS, and CariCOOS regions
#
# Date of Version 01: Jun. 25, 2025
# 
# Author 01: Alexander Nickerson
#
# Version 02 uses station names to simplify the process.
#

import pickle
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import urllib
    
stat_all = pd.read_csv('Docs/List_All_NDBC.txt',
                        header=None, sep=";", index_col=False)
stat_all.columns = ["Reg","Org"]
stat_all = stat_all.sort_values(by='Reg').reset_index(drop=True)
    
# open the dict of organizational shorthands
with open('Docs/Dict_Orgs.pkl', 'rb') as f:
    dict_org = pickle.load(f)
    
# Index(['Reg', 'Type', 'Abr', 'Lon', 'Lat', 'Org', 'Name']
    
# strip the strings of the buoy ID's and create empty series for Lat & Lon
stat_all["Reg"] = stat_all["Reg"].str.strip()
stat_all["Type"] = np.full(np.size(stat_all["Reg"]),fill_value="NDBC")
stat_all["Abr"] = stat_all["Org"].str.strip().map(dict_org)
stat_all["Lon"] = np.full(np.size(stat_all["Reg"]),fill_value=np.nan)
stat_all["Lat"] = np.full(np.size(stat_all["Reg"]),fill_value=np.nan)
stat_all["Name"] = np.full(np.size(stat_all["Reg"]),fill_value="")

# put in same order as other stations
stat_all = stat_all[["Reg","Type","Abr","Lon","Lat","Org","Name"]]

# find the abbreviations from the dict created & eliminated ID's not included
stat_all = stat_all.loc[stat_all["Abr"].notna() == True].reset_index(drop=True)

# These are the station conditions to reduce the data set
# Stations "41###" are in the Atlantic, and stations "42###" are in the Gulf
C1 = ((~stat_all["Reg"].str.strip().str.startswith('41')) & 
      (~stat_all["Reg"].str.strip().str.startswith('42')))

# stations without data, possibly a result of errors in saving the data
C2 = ((stat_all["Reg"].str.strip() == "41060") |
      (stat_all["Reg"].str.strip() == "41061") |
      (stat_all["Reg"].str.strip() == "42008") |
      (stat_all["Reg"].str.strip() == "42065") |
      (stat_all["Reg"].str.strip() == "42080") |
      (stat_all["Reg"].str.strip() == "42087"))

# stations with letters in the name
C3 = pd.to_numeric(stat_all["Reg"], errors='coerce').isna()

# remove stations from certain organizations
C4 = ((stat_all["Org"].str.contains('AOML')) | 
      (stat_all["Abr"].str.contains('CaroCOOPS')) | 
      (stat_all["Org"].str.contains('COMPS')))
Pt = (C1 | C2 | C3 | C4)

# eliminated the unwanted points
stat_all = stat_all.loc[Pt == False].reset_index(drop=True)

print("Stations parsed for NDBC.")

front = "https://www.ndbc.noaa.gov/station_page.php?station="

# loop to get the latitude and longitude
for i, stat in stat_all.iterrows():
    page_to_read = front + stat["Reg"]
    
    # open the station page
    opened_page = urllib.request.urlopen(page_to_read)
    page_read = BeautifulSoup(opened_page.read(),'lxml')

    # the station kinds are buried under the <h2> tag
    link = page_read.find_all('link', rel="alternate")
    cord = link[-1].get('href')
    cord = cord.split("?")
    
    # extract the coordinates
    lat_lon = cord[1].split("&")
    y = lat_lon[0].split("=")[1]
    x = lat_lon[1].split("=")[1]

    if y == '':
        continue
    
    # assign the latitude
    if y[-1] == "N":
        stat_all.loc[i,"Lat"] = float(y[:-1])
    else:
        stat_all.loc[i,"Lat"] = -1*float(y[:-1])
        
    # assign the longitude
    if x[-1] == "W":
        stat_all.loc[i,"Lon"] = -1*float(x[:-1])
    else:
        stat_all.loc[i,"Lon"] = float(x[:-1])
        
    print("Parsed station " + stat["Reg"])
    
# remove these non-moored stations
stat_all = stat_all.loc[stat_all["Lat"].notna() == True].reset_index(drop=True)
stat_all = stat_all.sort_values(by='Abr').reset_index(drop=True)
        
print("Station coordinates extracted successfully.")

# prepare the columns and write them to a CSV file
stat_all["Reg"] = stat_all["Reg"].str.rjust(40) + " "
stat_all["Type"] = " " + stat_all["Type"].str.ljust(5)
stat_all["Abr"] = " " + stat_all["Abr"].str.ljust(17)
stat_all["Lon"] = stat_all["Lon"].map("{:+9.3f}".format) + " "
stat_all["Lat"] = stat_all["Lat"].map("{:+9.3f}".format) + " "
stat_all["Org"] = " " + stat_all["Org"].str.replace("\"","").str.ljust(125)
stat_all["Name"] = " " + stat_all["Name"]

stat_all.to_csv('Docs/List_Redux_NDBC.txt',index=False,sep="|")