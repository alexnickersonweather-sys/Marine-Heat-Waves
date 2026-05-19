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

import pandas as pd
import time

s = time.time()

stat_all = pd.read_csv('Docs/List_Redux_ERDDAP.txt',
                        header=0, sep="|", index_col=False)
for stat in ["Reg","Type","Abr","Org","Name"]:
    stat_all[stat] = stat_all[stat].str.strip()
    
front_IOOS = "https://erddap.sensors.ioos.us/erddap/tabledap/"
nc_var1 = "?time,latitude,longitude,z,sea_water_temperature,sea_water_temperature_qc_agg"
nc_var2 = "?time,latitude,longitude,z,sea_water_temperature"

for i, stat in stat_all.iterrows():
    a_link = front_IOOS + stat["Reg"] + ".nc"
    
    # if the folder doesn't exist, create it!
    if stat["Type"] == "FACT":
        stat_all.loc[i,"Reg"] = stat_all.loc[i,"Reg"].replace("org_secoora_","")
        
        # these if statements are all for stations with errors in their file 
        # names that break from the network's naming conventions
        if "CMAST Array" in stat["Name"] and "cmast" not in stat["Reg"]:
            stat_all.loc[i,"Reg"] = "cmast_" + stat_all.loc[i,"Reg"]
        elif "FLKEYS Array" in stat["Name"] and "flkeys" not in stat["Reg"]:
            stat_all.loc[i,"Reg"] = "flkeys_" + stat_all.loc[i,"Reg"]
        elif "HBOI Array" in stat["Name"] and "hboi" not in stat["Reg"]:
            stat_all.loc[i,"Reg"] = "hboi_" + stat_all.loc[i,"Reg"]
        elif "KSC Array" in stat["Name"] and "ksc" not in stat["Reg"]:
            stat_all.loc[i,"Reg"] = "ksc_" + stat_all.loc[i,"Reg"]
        elif "SCARE Array" in stat["Name"] and "scare" not in stat["Reg"]:
            stat_all.loc[i,"Reg"] = "scare_" + stat_all.loc[i,"Reg"]

# sort the data before saving it
stat_all = stat_all.sort_values(by=["Type","Abr","Reg"]).reset_index(drop=True)
stat_all.to_csv('Docs/List_Download_ERDDAP.txt',index=False,sep="|")
    
print("List generation completed.")

e = time.time()
print(str(e-s) + " seconds")
