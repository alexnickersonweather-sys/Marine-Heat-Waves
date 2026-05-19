# Purpose: Download other SST data
#
# Date of Version 01: May  23, 2025
#
# Author 01: Alexander Nickerson
#
# Please note the formats of the ERDDAP links below and compare them to this
# link to a manual data request:
# https://erddap.sensors.ioos.us/erddap/tabledap/org_secoora_btsnp_br_1.html
#
# https://erddap.sensors.ioos.us/
# erddap/tabledap/
# org_secoora_btsnp_br_1.nc
# ?time,sea_water_temperature,sea_water_temperature_qc_agg,z
# &time>=2019-03-27T14:00:00Z
# &time<=2024-01-31T17:00:00Z
#
# Note: All stations on the SECOORA ERDDAP server are found on the IOOS ERDDAP
#       server as well.  Since the stations are in lists, it is just as fast to
#       use the IOOS ERDDAP as it is to use the SECOORA ERDDAP

import urllib.request
import pandas as pd
import time
import os

s = time.time()

stat_all = pd.read_csv('Docs/List_Redux_ERDDAP.txt',
                        header=0, sep="|", index_col=False)
for stat in ["Reg","Type","Abr","Org","Name"]:
    stat_all[stat] = stat_all[stat].str.strip()
    
front_IOOS = "https://erddap.sensors.ioos.us/erddap/tabledap/"
nc_var1 = "?time,latitude,longitude,z,sea_water_temperature,sea_water_temperature_qc_agg"
nc_var2 = "?time,latitude,longitude,z,sea_water_temperature"

# adjust this line as needed due to stops in your workflow
for i, stat in stat_all.iterrows():
    a_link = front_IOOS + stat["Reg"] + ".nc"
    folder = "Data/" + stat["Type"] + "/L00N/"
    
    # create the folder only if necessary
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    # some of the FACT files have errrs in their file name
    if stat["Type"] == "FACT":
        stat_save = stat["Reg"].replace("org_secoora_","")
        
        # these if statements are all for stations with errors in their file 
        # names that break from the network's naming conventions
        if "CMAST Array" in stat["Name"] and "cmast" not in stat["Reg"]:
            stat_save = "cmast_" + stat_save
        elif "FLKEYS Array" in stat["Name"] and "flkeys" not in stat["Reg"]:
            stat_save = "flkeys_" + stat_save
        elif "HBOI Array" in stat["Name"] and "hboi" not in stat["Reg"]:
            stat_save = "hboi_" + stat_save
        elif "KSC Array" in stat["Name"] and "ksc" not in stat["Reg"]:
            stat_save = "ksc_" + stat_save
        elif "SCARE Array" in stat["Name"] and "scare" not in stat["Reg"]:
            stat_save = "scare_" + stat_save
        
        file_save = folder + "/" + stat_save + ".nc"
    else:
        file_save = folder + "/" + stat["Reg"] + ".nc"
    
    # download the data and save it to the folder and file
    try:
        link_download = a_link + nc_var1
        urllib.request.urlretrieve(link_download,file_save)
    except:
        link_download = a_link + nc_var2
        urllib.request.urlretrieve(link_download,file_save)
    
    print("Downloaded " + stat["Reg"])
    
print("Download completed.")

e = time.time()
print(str(e-s) + " seconds")
