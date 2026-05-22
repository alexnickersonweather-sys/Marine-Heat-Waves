# Title: Read Me for SECOORA and ERDDAP data acquisition
# Date of Version 01: May  15, 2025
# Date of Version 02: Jan. 28, 2026
#
# Author 01: Alexander Nickerson
# Author 02: Alexander Nickerson
#
# I apologize for the crudeness of this ReadMe file, which serves to help users
# who wish to download water temperature data from the respective SECOORA and
# IOOS ERDDAP servers.  This is a many-layered and complicated process, and I
# hope this guide makes the process much easier.  I use Python via the Anaconda
# environment and Spyder as the GUI for developing the code.
#
# Codes are listed in order that they are meant to be run.  Some codes do the
# same tasks but on the respective SECOORA and IOOS servers, so these will be
# listed side-by-side as "(SECOORA/IOOS)_List_Function_Name.py"
#
# Note: the master CSV files from the ERDDAP servers can be acquired thusly
#       http://erddap.sensors.ioos.us/erddap/tabledap/allDatasets.csv
#       http://erddap.secoora.org/erddap/tabledap/allDatasets.csv
#
# Phase A: these codes relate to the acquisition of the data
#
# A01_List_All_NDBC.py
# Purpose: Get the list of all stations on the NDBC website.
# Files Made: Docs/List_All_NDBC.txt
#
# A02_List_Region_ERDDAP.py
# Purpose: Get a list of all stations from the IOOS & SECOORA ERDDAP servers.
# Files Used: Docs/List_All_(IOOS/SECOORA).csv
# Files Made: Docs/List_Region_(IOOS/SECOORA)_ERDDAP.txt
#
# A03_List_Temperature_ERDDAP.py
# Purpose: Get a list of all stations from the IOOS & SECOORA ERDDAP servers
#          if sea_water_temperature is a measured variable within the chosen
#          subset of waters
# Files Used: Docs/List_Region_(IOOS/SECOORA).py
# Files Made: Docs/List_Temperature_(IOOS/SECOORA).py
#
# A04_Dict_Org.py
# Purpose: Make a dictionary of abbreviations for all station owners.
# Files Made: Docs/Dict_Orgs.pkl
#
# A05_List_Redux_(ERDDAP/NOAA).py
# Purpose: Reduces the list of NDBC stations to the desired datasets
# Files Used: Docs/List_Temperature_(IOOS/SECOORA/NOAA).txt
# Files Made: Docs/List_Redux_(ERDDAP/NOAA).txt
#
# IMPORTANT NOTE 1: In succeeding codes, [Reg] refers to the file names that
#                   contain the data for each of the stations.
#
# IMPORANT NOTE 2: One UNCW-CORMP station is classified as "USF" because it is
#                  the only one station downloaded by this function library that
#                  has observations at more than one depth.
#
# A06_Download_ERDDAP.py
# Purpose: Download the ERDDAP data from the IOOS server since it has all of
#          the data in one location.
# Files Used: Docs/List_Redux_ERDDAP.txt
# Files Made: Data/(FACT/SWT/USF)/L00N/[Reg].nc
#
# A06_Download_NOAA.py
# Purpose: Download the NOAA data from the NDBC website.
# Files Used: Docs/List_Redux_NOAA.txt
# Files Made: Data/NDBC/L00D/[Reg]_YYYY.dat
#
# A07_List_Download_(ERDDAP/NOAA).py
# Purpose: Download data for the LBOS/SST/SWT from the IOOS ERDDAP server and
#          save it to folders based on organizations from the dictionaries that
#          were defined in Code #05.  Folders are created as necessary.
# Files Used: Docs/List_Redux_(ERDDAP/NOAA).txt
# Files Made: Docs/List_Download_(ERDDAP/NOAA).txt
#
# A08_List_Download_Combo.py
# Purpose: Combines the two downloaded lists into one.
# Files Used: Docs/List_Download_(ERDDAP/NOAA).txt
# Files Made: Docs/List_Download_All.txt
#
# Phase B: these codes convert NDBC text files into netCDF files
#
# B01_Convert_NDBC_NC.py
# Purpose: Merge the annual text files for the NDBC stations into a single
#          large netCDF file with all of the data.
# Files Used: Docs/List_Download_All.txt
#             Data/NDBC/L00D/[Reg]_YYYY.dat
# Files Made: Data/NDBC/L00N/[Reg].nc
#
# At this point, it's important to discuss the formats of the files that have
#    been downloaded from ERDDAP and from the NDBC.  The ERDDAP and NDBC files
#    have different formats, and later codes in Phase D will merge these.  This
#    is because of the NDBC files having various issues (explained in code B01)
#    that necessitate a two-phase QC, whereas the files downloaded from ERDDAP
#    only need a one-phase QC, performed entirely in Phase D.
#
# Phase C: these codes make plots of water temperatures as downloaded from
#          their respective servers.  This allows for identification of files
#          where quality control was done by the provider.
#
# C01_Plot_L00.py
# Purpose: Plot the provided water temperatures and their QC flags
# Files Used: Docs/List_Download_All.txt
#             Data/(FACT/NDBC/SWT)/L00D/[Reg].nc
# Functions : C01_Plot.py
# Files Made: Figs/Data/(FACT/NDBC/SWT)_L00N/[Reg].png
#
# C02_Counts_All.py
# Purpose: Plot a bar chart with number of stations in each collection
# Files Used: Docs/List_Download_All.txt
# Files Made: Figs/Statistics/Counts_All.png
#
# C02_Counts_Owner.py
# Purpose: Plot bar charts counting how many stations each owner possesses
# Files Used: Docs/List_Download_All.txt
# Files Made: Figs/Statistics/Counts_Owner_(thresh).png
# "thresh" is the threshold of the minimum number of stations that the owners
# must have in order to be included on the bar chart.  Choose your threshold.
#
# C03_Locations.py
# Purpose: Make maps showing all stations or stations by type, on a static map.
# Files Used: Docs/List_Download_All.txt
# Files Made: Figs/Statistics/Locations_(All/FACT/NDBC/SWT/USF).png
# Functions : C03_Map.py
#
# C04_Depths_(All/Type).py
# Purpose: Make bar charts showing the depths of all stations or by type.
# Files Used: Docs/List_Download_All.txt
# Files Made: Figs/Statistics/Locations_All.png
#
# Phase D: These codes perform quality control on the datasets.
#          USF data is already QC'd before being pushed to ERDDAP.
#          FACT data needs a two-phase QC to utilize adjacent stations.
#
# D01_QC_(FACT/NDBC/SWT/USF).py
# Purpose: perform quality control on the datasets.
# Files Used: Docs/List_Download_All.txt
#             Data/(FACT/NDBC/SWT)/L00N/[Reg].nc
# Files Made: Data/(FACT/NDBC/SWT)/QC/[Reg].nc
#
# D02_QC_FACT2.py
# Purpose: perform phase-2 QC on the FACT data
# Files Used: Two pairs of files created in D01_QC_FACT.py
# Files Made: New pairs of files
#
# D03_Plot_QC.py
# Purpose: Plot the provided water temperatures and their QC flags
# Files Used: Docs/List_Download_All.txt
#             Data/(FACT/NDBC/SWT)/QC/[Reg].nc
# Functions : C01_Plot.py
# Files Made: Figs/Data/(FACT/NDBC/SWT)_L00N/[Reg].png
#
# Phase E: These codes perform compute hourly, daily, monthly, and annual
#          means that are then used in plots.
#
# E01_Climo.py
# Purpose: Compute hourly, daily, monthly, and annual means.  This is where the
#          various codes are finally streamlined to use the same code.
# Files Used: Docs/List_Download_All.txt
#             Data/(FACT/NDBC/SWT/USF)/QC/[Reg].nc
# Files Made: Data/(FACT/NDBC/SWT/USF)/Climo/[Reg]_(Hour/Day/Month/Year).nc
#             Docs/List_Climo_All.txt
#
# E02_Climo_List_Redux.py
# Purpose: Reduces the list to only the stations with at least 3 years of data.
# Files Used: Docs/List_Climo_All.txt
# Files Made: Docs/List_Climo_Redux.txt
#
# E03_Climo_Plot.py
# Purpose: Plot the climatologies for each of the stations.  As always, there is
#          a separate code dedicated to the USF dedicated due to the layers.
# Files Used: Docs/List_Climo_Redux.txt
#             Data/(FACT/NDBC/SWT/USF)/Climo/[Reg]_(Hour/Day/Month/Year).nc
# Files Made: Figs/Data/(FACT/NDBC/SWT/USF)_Climo/[Reg].png
#
# E04_Climo_Map.py
# Purpose: Make an interactive map using Folium/Leaflet.  The map is color-coded
#          with the different kinds of stations having their own symbols.
# Files Used: Docs/List_Climo_All.txt
# Files Made: Figs/Maps/Locations_Climo.html
#
# E05_Climo_Counts.py
# Purpose: Make simple bar charts of the lengths of the data series based on the
#          number of years containing data and the number of years for which
#          annual means were computed.
# Files Used: Docs/List_Climo_All.txt
# Files Made: Figs/Statistics/Climo_Years.png
#             Figs/Statistics/Climo_Length.png
#
# Phase F: These codes compute trends based on monthly and annual mean data.
#
# F01_Trends_(Month/Year).py
# Purpose: Compute sea temperature trends.  For the monthly mean data, the trend
#          is performed by first assuming sinusoidal annual variation.  This is
#          acceptable, but annual means are better when there is uneven
#          seasonal variability (e.g in subtropical and tropical regions).  Once
#          again, a separate code is necessary for USF data
# Files Used: Docs/List_Climo_All.txt
#             Data/(FACT/NDBC/SWT/USF)/Climo/[Reg]_(Month/Year).nc
# Functions : trend_compute.py
#           : matreg.py (called within trend_compute.py)
# Files Made: Stats/Trends_(Month/Year).txt
#
# F02_Trends_Barchart.py
# Purpose: Make barcharts in different bins to count the stations exhibiting
#          trends of varying magnitudes
# Files Used: Stats/Trends_(Month/Year).txt
# Files Made: Figs/Statistics/Count_Trends_(Month/Year).png
#
# Phase G: These are the codes you'd been hoping to use when you started using
#          this library!  Phase G contains the codes to identify Marine Heat
#          Waves (MHWs) in accordance with the Hobday et al. (2016) study.
#
# G01_MHW.py
# Purpose: Compute MHWs using the code developed by E.C.J. Oliver and plot the
#          results to figures that will be saved.
# Files Used: Stats/Trends_Month.txt
#             Data/(FACT/NDBC/SWT/USF)/Climo/[Reg]_Day.nc
#             Data/(FACT/NDBC/SWT/USF)/Climo/[Reg]_Month.nc
# Files Made: Figs/MHW_Possible/(FACT/NDBC/SWT)_[Reg].png
#
