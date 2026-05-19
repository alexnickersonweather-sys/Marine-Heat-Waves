# Purpose: Get list of all IOOS stations with water temperature
# 
# Date of Version 01: Apr. 10, 2025
# 
# Author 01: Alexander Nickerson
# 
# There are several ways to approach this, but using "if... continue" causes
# fewer levels of indentation.  
#
# This code somewhat foolishly assumes that all pages will be found without
# any exception flags being thrown.
# 
# There are five page types into which the certain station data are embedded.
#
# 1: https://erddap.sensors.ioos.us/erddap/tabledap/org_cormp_sun2.html
# 2: https://erddap.sensors.ioos.us/erddap/tabledap/org_cormp_sun2.graph
# 3: https://erddap.sensors.ioos.us/erddap/metadata/fgdc/xml/org_cormp_sun2_fgdc.xml
# 4: https://erddap.sensors.ioos.us/erddap/metadata/iso19115/xml/org_cormp_sun2_iso19115.xml
# 5: https://erddap.sensors.ioos.us/erddap/info/org_cormp_sun2/index.html
# 
# This code is written to use option 3 because it is approximately 9 minutes
# faster than option 1.
#

import requests
import numpy as np
import pandas as pd
from time import time
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

s = time()

# URL for ERDDAP
link = {"IOOS": "https://erddap.sensors.ioos.us/erddap/search/advanced.html",
        "SECOORA": "https://erddap.secoora.org/erddap/search/advanced.html"}

# loop through ERDDAPs
for SI in ["IOOS", "SECOORA"]:
    stat_swt = []
    stat_sst = []
    
    # open list of stations and get into format
    stat_all = pd.read_csv('Docs/List_Region_' + SI + '.txt',
                            index_col=False, sep="|")
    stat_all["Reg"] = stat_all["Reg"].str.strip()
    stat_all["Type"] = np.full(np.size(stat_all["Reg"]),"NA")
    stat_all = stat_all[["Reg","Type","Lon","Lat","Org","Name"]]
    
    ####### SWT
    # parallel processing helps significantly reduce runtime
    # using more than 20 workers risks getting blocked
    with ThreadPoolExecutor(max_workers=20) as executor:
        # url parameters after "?" 
        params = {
            "page": '1',
            "itemsPerPage": 50000, 
            "variableName":"sea_water_temperature",
            "maxLon": -99.0,
            "minLon": -45.0,
            "maxLat":  36.5,
            "minLat":  11.0,
        }
        
        # raise the request for the webpage
        r = requests.get(link[SI], params=params, timeout=10)
        r.raise_for_status()
        
        # get the text from the page
        soup = BeautifulSoup(r.text, "lxml")
        
        # get the stations from the list
        for a in soup.select("a[href$='.html']"):
            href = a["href"]
            
            # work to get only the station link
            if (
                "tabledap" in href and
                "page=" not in href and 
                "documentation" not in href and 
                "allDatasets" not in href
            ):
                stat = href.rsplit("/", 1)[-1][:-5]
                
                # find station in master list of stations
                # and assign the station type
                if (np.any(stat_all["Reg"].str.match(stat))):
                    pg = stat_all["Reg"].str.match(stat)
                    stat_all.loc[pg,"Type"] = "SWT"
    
    ####### SST
    # I commented this portion because "sea_surface_temperature" is used
    #       nearly exclusively by GCOOS
    # # parallel processing helps significantly reduce runtime
    # # using more than 20 workers risks getting blocked
    # with ThreadPoolExecutor(max_workers=20) as executor:
    #     # url parameters after "?" 
    #     params = {
    #         "page": '1',
    #         "itemsPerPage": 50000, 
    #         "variableName":"sea_surface_temperature"
    #     }
        
    #     # raise the request for the webpage
    #     r = requests.get(link[SI], params=params, timeout=10)
    #     r.raise_for_status()
        
    #     # get the text from the page
    #     soup = BeautifulSoup(r.text, "lxml")
        
    #     # get the stations from the list
    #     for a in soup.select("a[href$='.html']"):
    #         href = a["href"]
            
    #         # work to get only the station link
    #         if (
    #             "tabledap" in href and
    #             "page=" not in href and 
    #             "documentation" not in href and 
    #             "allDatasets" not in href
    #         ):
    #             stat = href.rsplit("/", 1)[-1][:-5]
                
    #             # find station in master list of stations
    #             if (np.any(stat_all["Reg"].str.match(stat))):
    #                 pg = stat_all["Reg"].str.match(stat)
    #                 stat_all.loc[pg,"Type"] = "SST"
    
    # identify retained stations and elimanted others
    good = stat_all["Type"] != "NA"
    stat_ws = stat_all.loc[good].copy()
    
    # format data and save it.
    stat_ws["Reg"] = stat_ws["Reg"].str.rjust(40) + " "
    stat_ws["Lon"] = stat_ws["Lon"].astype(float).map("{:+9.3f}".format) + " "
    stat_ws["Lat"] = stat_ws["Lat"].astype(float).map("{:+9.3f}".format) + " "
    stat_ws["Org"] = " " + stat_ws["Org"].str.replace("\"","").str.ljust(125) + " "
    stat_ws["Name"] = " " + stat_ws["Name"]
    
    stat_ws.to_csv('Docs/List_Temperature_' + SI + '.txt',
                   index=False,sep="|")
        
e = time() - s

print(f"Lists generated in {e:6.3f} seconds")
    