# Purpose: Narrows stations down to those within a select region
#
# Date of Version 01: Mar. 04, 2026
# 
# Author 01: Alexander K. Nickerson
#

import pandas as pd

# loop through EREDDAP servers
for SI in ["IOOS","SECOORA"]:
    # file to open
    stat_all = pd.read_csv(("Docs/List_All_" + SI + ".csv"),
                            header=0,index_col=False,delimiter=",",
                            low_memory=False)
    
    # select specific columns
    stat_all = stat_all[["datasetID","maxLongitude","minLongitude","maxLatitude","minLatitude","institution","title"]]
    stat_all = stat_all.drop(0)
    
    # get latitudes and longitudes of each station.  The reason for min & max
    # values is because the ERDDAP includes non-stationary stations
    wbc_row = stat_all["minLongitude"].astype(float)
    ebc_row = stat_all["maxLongitude"].astype(float)
    nbc_row = stat_all["minLatitude"].astype(float)
    sbc_row = stat_all["maxLatitude"].astype(float)
    
    # set a region only of interest to SECOORA and CariCOOS
    condW = wbc_row > -99.0
    condE = ebc_row < -45.0
    condN = nbc_row < +36.5
    condS = sbc_row > +11.0
    
    Pt = (condW & condE & condN & condS &
          (wbc_row == ebc_row) & (nbc_row == sbc_row)
    )
    
    # get subset of stations
    stat_reg = stat_all.loc[Pt].copy().reset_index()
    stat_reg = stat_reg[["datasetID","minLongitude","minLatitude","institution","title"]]
    stat_reg.columns = ["Reg","Lon","Lat","Org","Name"]
    
    # prepare the data for saving to output file
    stat_reg["Reg"] = stat_reg["Reg"].str.rjust(40) + " "
    stat_reg["Lon"] = stat_reg["Lon"].astype(float).map("{:+9.3f}".format) + " "
    stat_reg["Lat"] = stat_reg["Lat"].astype(float).map("{:+9.3f}".format) + " "
    stat_reg["Org"] = " " + stat_reg["Org"].str.replace("\"","").str.ljust(125) + " "
    stat_reg["Name"] = " " + stat_reg["Name"]
    
    stat_reg.to_csv('Docs/List_Region_' + SI + '.txt',
                    index=False,sep="|")
     