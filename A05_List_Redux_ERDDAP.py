# Purpose: Remove stations that are listed on both SECOORA and IOOS
#          as well as FACT stations
#
# Date of Version 01: May  07, 2025
# Date of Version 02: May  16, 2025
# 
# Author 01: Alexander Nickerson
# Author 02: Alexander Nickerson
#
# Version 02 uses station names to simplify the process.
#

import pandas as pd
import numpy as np
import pickle

# URL for ERDDAP
link = {"IOOS": "https://erddap.sensors.ioos.us/erddap/search/advanced.html",
        "SECOORA": "https://erddap.secoora.org/erddap/search/advanced.html"}

# get kust if stations
stat_I = pd.read_csv('Docs/List_Temperature_IOOS.txt',
                      header=0, index_col=False, sep="|")
stat_S = pd.read_csv('Docs/List_Temperature_SECOORA.txt',
                      header=0, index_col=False, sep="|")
    
# open the dict of organizational shorthands
with open('Docs/Dict_Orgs.pkl', 'rb') as f:
    dict_org = pickle.load(f)

# remove trailing spaces
for stat in ["Reg","Org","Name"]:
    stat_I[stat] = stat_I[stat].str.strip()
    stat_S[stat] = stat_S[stat].str.strip()
        
# add new column to dataframe for station abbreviations
stat_I["Abr"] = np.full(np.shape(stat_I["Reg"]),"")
stat_S["Abr"] = np.full(np.shape(stat_S["Reg"]),"")

# search for station names already in the SECOORA station listing and other
#        stations that aren't stationary or have other outstanding issues
# Among other stations removed include those...
#    (1) Belonging to other IOOS members
#    (2) Belonging to USGS
#    (3) Listed more than once
#    (4) Having more complete series on the NDBC website
#    (5) Fixed locations associated with routine research cruise programs
for i, stat in stat_I.iterrows():
    # stations listed on both IOOS and SECOORA
    C1 = stat["Name"] in stat_S["Name"].values
    
    # stations double-listed on IOOS or from other IOOS members
    C2 = ("ism-secoora-wmo" in stat["Reg"] or "ism-gcoos" in stat["Reg"] or 
          "ism-maracoos" in stat["Reg"] or "ism-caricoos" in stat["Reg"] or 
          "ism-secoora-gtbmac" in stat["Reg"] or "ism-secoora-noaa" in stat["Reg"] or 
          "ism-secoora-edu" in stat["Reg"] or  "gov-ndbc" in stat["Reg"] or
          "tabs_" in stat["Reg"] or "water-velocity-wfs" in stat["Reg"])
    
    # freshwater programs and model outputs
    C3 = ("(NWIS)" in stat["Org"] or "(ECMWF)" in stat["Org"] or
          "(USACE)" in stat["Org"] or "ModMon" in stat["Org"] or 
          "Duke" in stat["Org"])
    
    # a long-term dataset that frequently measures air temperature due to tidal
    # cycles, especially during periods of surge associated with hurricanes
    C4 = "Long Bay Observation System" in stat["Org"]
    
    # research cruises that routinely returned to the same locations
    C5 = ("South Florida Program Survey Cruises" in stat["Name"] or
          "Predictions" in stat["Name"])
    
    # USF stations that have multiple listings for real-time and historic data
    C6 = ("(COMPS)" in stat["Org"] and "historic" not in stat["Reg"] and 
          "pinellas" not in stat["Reg"] and stat["Reg"] != "c11" and stat["Reg"] != "c15")
    
    # if any condition is failed, drop it
    if C1 or C2 or C3 or C4 or C5 or C6:
        stat_I = stat_I.drop(i)
        continue
    
    # FACT acoustic receivers located at the bottom of the water column
    if "org_secoora" in stat["Reg"]:
        stat_I.at[i,"Type"] = "FACT"
        
    # these stations are incorrectly listed with GCOOS as their owner
    if "gcoos-cbi" in stat["Reg"]:
        stat_I.at[i,"Org"] = "Conrad Blutcher Institute"
    elif "gcoos-disl" in stat["Reg"]:
        stat_I.at[i,"Org"] = "Dauphin Island Sea Lab"
    elif "gcoos-lumcon" in stat["Reg"]:
        stat_I.at[i,"Org"] = "Louisiana Universities Marine Consortium"
    elif "gcoos-sccf" in stat["Reg"]:
        stat_I.at[i,"Org"] = "Sanibel-Captiva Conservation Foundation"
    elif "USM-R" in stat["Name"]:
        stat_I.at[i,"Org"] = "University of Southern Mississippi"
    elif "Felimon" in stat["Org"]:
        stat_I.at[i,"Org"] = "Gulf Coastal Ocean Observing System"
        
    # add the appropriate abbreviation from the dict
    stat_I.loc[i,"Abr"] = dict_org[stat_I.at[i,"Org"]]
    
    # label the USF stations as a different type from FACT or SWT
    # due to the measurement of multiple depths requiring specialized code
    if stat_I.at[i,"Abr"] == "USF-COMPS":
        stat_I.at[i,"Type"] = "USF"
        
    # I classify this one as "USF" even though it's "UNCW-CORMP" because of the
    # multiple depth layers, a characteristic otherwise unique to USF moorings
    if stat_I.at[i,"Reg"] == "mooring-ob27m-onslow-bay-nc":
        stat_I.at[i,"Type"] = "USF"

print("Stations parsed for IOOS.")
        
# these datasets either have better, more thorough sources, their own code, or
#       difficulties that render them too hard to download
for i, stat in stat_S.iterrows():
    # stations double-listed on IOOS or from other IOOS members
    C2 = ("ism-secoora-wmo" in stat["Reg"] or "ism-gcoos" in stat["Reg"] or 
          "ism-maracoos" in stat["Reg"] or "ism-caricoos" in stat["Reg"] or 
          "ism-secoora-gtbmac" in stat["Reg"] or "ism-secoora-noaa" in stat["Reg"] or 
          "ism-secoora-edu" in stat["Reg"] or  "gov-ndbc" in stat["Reg"] or
          "tabs_" in stat["Reg"] or "water-velocity-wfs" in stat["Reg"])
    
    # freshwater programs and model outputs
    C3 = ("(NWIS)" in stat["Org"] or "(ECMWF)" in stat["Org"] or
          "(USACE)" in stat["Org"] or "ModMon" in stat["Org"] or 
          "Duke" in stat["Org"])  
    
    # a long-term dataset that frequently measures air temperature due to tidal
    # cycles, especially during periods of surge associated with hurricanes
    C4 = "Long Bay Observation System" in stat["Org"]
    
    # research cruises that routinely returned to the same locations
    C5 = ("South Florida Program Survey Cruises" in stat["Name"] or
          "Predictions" in stat["Name"])
    
    # USF stations that have multiple listings for real-time and historic data
    C6 = ("(COMPS)" in stat["Org"] and "historic" not in stat["Reg"] and 
          "pinellas" not in stat["Reg"] and stat["Reg"] != "c11" and stat["Reg"] != "c15")
    
    # if any condition is failed, drop it
    if C2 or C3 or C4 or C5 or C6:
        stat_S = stat_S.drop(i)
        continue
    
    # FACT acoustic receivers located at the bottom of the water column
    if "org_secoora" in stat["Reg"]:
        stat_S.at[i,"Type"] = "FACT"
        
    # add the appropriate abbreviation from the dict
    stat_S.at[i,"Abr"] = dict_org[stat_S.at[i,"Org"]]
    
    # label the USF stations as a different type from FACT or SWT
    # due to the measurement of multiple depths requiring specialized code
    if stat_S.at[i,"Abr"] == "USF-COMPS":
        stat_S.at[i,"Type"] = "USF"
        
    # I classify this one as "USF" even though it's "UNCW-CORMP" because of the
    # multiple depth layers, a characteristic otherwise unique to USF moorings
    if stat_S.at[i,"Reg"] == "mooring-ob27m-onslow-bay-nc":
        stat_S.at[i,"Type"] = "USF"
        
print("Stations parsed for SECOORA.")

# concatenate the dataframes, reorder the columns, and sort by abbreviation
stat_A = pd.concat([stat_I,stat_S],axis=0)
stat_A = stat_A.reset_index()
stat_A = stat_A.loc[:,['Reg', 'Type', 'Abr', 'Lon', 'Lat', 'Org', 'Name']]
stat_A = stat_A.sort_values(by=["Type","Abr"], key=lambda col: col.str.lower())

# shorten the FACT probes to remove superfluous words
for i, stat in stat_A.iterrows():
    stat_A.at[i,"Name"] = stat_A.at[i,"Name"].replace(", Bottom Temperature","")
    if stat["Type"].strip() == "FACT":
        stat_A.at[i,"Name"] = stat_A.at[i,"Name"].replace("Station ","")

# prepare the columns and write them to a CSV file
stat_A["Reg"] = stat_A["Reg"].str.rjust(40) + " "
stat_A["Type"] = " " + stat_A["Type"].str.ljust(5)
stat_A["Abr"] = " " + stat_A["Abr"].str.ljust(17)
stat_A["Lon"] = stat_A["Lon"].map("{:+9.3f}".format) + " "
stat_A["Lat"] = stat_A["Lat"].map("{:+9.3f}".format) + " "
stat_A["Org"] = " " + stat_A["Org"].str.replace("\"","").str.ljust(125)
stat_A["Name"] = " " + stat_A["Name"]

stat_A.to_csv('Docs/List_Redux_ERDDAP.txt',index=False,sep="|")
