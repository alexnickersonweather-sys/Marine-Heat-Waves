# Purpose: Create dicts to go with the different organizations to simplify
#          saving the data from the IOOS & SECOORA ERDDAP servers and from
#          the NDBC server
#
# Date of Version 01: May  22, 2025
# 
# Author 01: Alexander Nickerson
#

import pickle

# assign short IDs to each of the station owners so that the data can be
# used as a unit or to compare different station owners
dict_abb = {'Biscayne National Park': 'Biscayne-NP',
            'Bonefish and Tarpon Trust (BTT)': 'BTT',
            'Caribbean Integrated Coastal Ocean Observing System (CarICoos)': 'CariCOOS',
            'Caribbean Coastal Ocean Observing System (CARICOOS)': 'CariCOOS',
            'CaroCOOPS': 'CaroCOOPS',
            'Conrad Blutcher Institute': 'CBI',
            'Conrad Blucher Institute (CBI) for Surveying and Science, Texas A&M University-Corpus Christi': 'CBI',
            'Neal Pettigrew': 'CariCOOS',
            'DIMAR Colombia - CCCP': 'DIMAR',
            'Dauphin Island Sea Lab': 'DISL',
            'Duke University': 'Duke',
            'East Coast Biologists, Inc': 'EC-Biologists',
            'Everglades National Park': 'Everglades-NP',
            'Field School': 'Field-School',
            'Florida Atlantic University (FAU)': 'FAU',
            'Florida Atlantic University Harbor Branch Oceanographic Institute (FAU HBOI)': 'FAB-HBOI',
            'Florida Department of Environmental Protection (FLDEP)': 'FL-DEP',
            'Florida Fish and Wildlife Conservation Commission Fish and Wildlife Research Institute (FWCC-FWRI)': 'FWCC-FWRI',
            'Florida Fish and Wildlife Conservation Commission Fish and Wildlife Research Institute (FWCC-FWRI) Marathon Keys Laboratory': 'FWCC-FWRI-MKL',
            'The Water School at Florida Gulf Coast University (FGCU)': 'FGCU-WS',
            'Florida Institute Of Technology (FIT)': 'FIT',
            'Florida International University (FIU)': 'FIU',
            'Georgia Aquarium': 'Georgia-Aquarium',
            'Georgia Department Of Natural Resources (GADNR)': 'GADNR',
            'Gulf Coastal Ocean Observing System': 'GCOOS',
            'Integrated Coral Observing Network (ICON)': 'ICON',
            'Long Bay Observation System': 'LBOS',
            'Louisiana Universities Marine Consortium': 'LUMCON',
            'Meteo France': 'MF',
            'Marine Megafauna Foundation (MMF)': 'MMF',
            'Mote Marine Laboratory': 'MML',
            'National Aeronautics and Space Administration (NASA)': 'NASA',
            'NSF Ocean Observatories Initiative': 'NSF-OOI',
            'Ocean Observatories Initiative (OOI)': 'NSF-OOI',
            'New College of Florida (NCF)': 'NCF',
            'North Carolina State University (NCSU)': 'NCSU',
            'Northeastern Regional Association of Coastal and Ocean Observing Systems (NERACOOS)': 'NERACOOS',
            'NOAA Atlantic Oceanographic and Meteorological Laboratory (NOAA AOML)': 'NOAA-AOML',
            'NOAA Center for Operational Oceanographic Products and Services (CO-OPS)': 'NOAA-COOPS',
            'NOAA National Centers for Coastal Ocean Science (NCCOS)': 'NOAA-NCCOS',
            'NOAA National Data Buoy Center (NDBC)': 'NOAA-NDBC',
            'National Data Buoy Center': 'NOAA-NDBC',
            'NOAA National Estuarine Research Reserve System (NERRS)': 'NOAA-NERRS',
            'Prediction and Research Moored Array in the Atlantic': 'NOAA-PIRATA',
            'NOAA Pacific Marine Environmental Lab (PMEL)': 'NOAA-PMEL',
            'Sanibel-Captiva Conservation Foundation': 'SCCF',
            'South Carolina Department of Natural Resources (SCDNR)': 'SCDNR',
            'SCRIPPS': 'SCRIPPS',
            'South-East Zoo Alliance for Reproduction and Conservation (SEZARC)': 'SEZARC',
            'TABS': 'TABS',
            'Texas Automated Buoy System': 'TABS',
            'Tampa Bay Land/Ocean Biogeochemical Observatory': 'TB-LOBO',
            'The Tampa Bay Physical Oceanographic Real-Time System': 'TB-PORTS',
            'Greater Tampa Bay Marine Advisory Council-PORTS': 'TB-PORTS',
            'Coastal Data Information Program, SIO/UCSD': 'UCSD-CDIP',
            'Coastal Data Information Program (CDIP)': 'UCSD-CDIP',
            'University of Florida Whitney Laboratory for Marine Bioscience (UF)': 'UF-WLMB',
            'University of Georgia (UGA)': 'UGA',
            'University of Georgia Skidaway Institute of Oceanography': 'UGA-SIO',
            'UMaine/Physical Oceanography Group': 'UMaine-POG',
            'University of North Carolina': 'UNC-CH',
            'University of North Carolina at Chapel Hill (UNC-CH)': 'UNC-CH',
            'University of North Carolina Coastal Studies Institute (UNC-CSI)': 'UNC-CSI',
            'ModMon Project, University of North Carolina': 'UNC-ModMon',
            'University of North Carolina Wilmington Center for Marine Science (UNCW-CMS)': 'UNCW-CMS',
            'UNCW - Coastal Ocean Research and Monitoring Program (CORMP)': 'UNCW-CORMP',
            'CORMP': 'UNCW-CORMP',
            'U.S. Army Corps of Engineers (USACE)': 'USACE',
            'U.S. Army Corps of Engineers': 'USACE',
            'Marine Sensory and Neurobiology Lab at University of South Carolina Beaufort': 'USCB-MSNL',
            'University of South Florida Coastal Ocean Monitoring and Prediction System (COMPS)': 'USF-COMPS',
            'University of South Florida Tampa Bay Estuary Program (TBEP)': 'USF-TBEP',
            'USGS Coastal and Marine Geology Program (USGS-CMGP)': 'USGS-CMGP',
            'USGS National Water Information System (NWIS)': 'USGS-NWIS',
            'University of Southern Mississippi': 'USM',
            'Woods Hole Oceanographic Institution': 'WHOI',
            'Woods Hole Oceanographic Institution (WHOI)': 'WHOI'}

# pickle allows you to save the dict as a Python dict object
with open('Docs/Dict_Orgs.pkl', 'wb') as f:
    pickle.dump(dict_abb, f)
