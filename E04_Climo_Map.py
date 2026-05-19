# Purpose: Make an interactive map with the stations and their lenghts
#
# Date of Version 01: Mar. 26, 2026
#
# Author 01: Alexander Nickerson
#

import folium
import branca
import os
import pandas as pd

# open station lists
stat_all = pd.read_csv('Docs/List_Climo_All.txt',
                        header=0, sep="|", index_col=False)

form = {"FACT": 'home',
        "NDBC": 'info-sign',
        "SWT":  'cloud',
        "USF":  'bell'}

# UserWarning: color argument of Icon should be one of: 
    # {'lightblue', 'lightgreen', 'cadetblue', 'gray', 'purple', 'green', 
    # 'darkpurple', 'lightgray', 'black', 'red', 'pink', 'darkred', 'white', 
    # 'darkblue', 'blue', 'beige', 'darkgreen', 'lightred', 'orange'}.

m = folium.Map(location=(+27.6000, -82.6000),zoom_start=7, tiles='CartoDB positron')

folder = "Figs/Maps/"

# create the folder only if necessary
if not os.path.exists(folder):
    os.makedirs(folder)
# end if    

# loop through all stations and plot the color based on the length of the
# station record and the symbol based on the collection
for s, stat in stat_all.iterrows():
    if stat["N_Yr"] >= 30:
        folium.Marker(
            location=[stat["Lat"], stat["Lon"]],
            tooltip=("Years: " + str(stat["N_Yr"]) + "\n"
                     "Means: " + str(stat["N_Mn"])),
            popup=(stat["Abr"] + ": " + stat["Name"] + " " + stat["Reg"]),
            icon=folium.Icon( color="green",icon=form[stat["Type"].strip()] ),
        ).add_to(m)
    elif (stat["N_Yr"] <  30 and stat["N_Yr"] >= 20):
        folium.Marker(
            location=[stat["Lat"], stat["Lon"]],
            tooltip=("Years: " + str(stat["N_Yr"]) + "\n"
                     "Means: " + str(stat["N_Mn"])),
            popup=(stat["Abr"] + ": " + stat["Name"] + " " + stat["Reg"]),
            icon=folium.Icon( color="blue",icon=form[stat["Type"].strip()] ),
        ).add_to(m)
    elif (stat["N_Yr"] <  20 and stat["N_Yr"] >= 10):
        folium.Marker(
            location=[stat["Lat"], stat["Lon"]],
            tooltip=("Years: " + str(stat["N_Yr"]) + "\n"
                     "Means: " + str(stat["N_Mn"])),
            popup=(stat["Abr"] + ": " + stat["Name"] + " " + stat["Reg"]),
            icon=folium.Icon( color="purple",icon=form[stat["Type"].strip()] ),
        ).add_to(m)
    elif (stat["N_Yr"] <  10 and stat["N_Yr"] >= 3):
        folium.Marker(
            location=[stat["Lat"], stat["Lon"]],
            tooltip=("Years: " + str(stat["N_Yr"]) + "\n"
                     "Means: " + str(stat["N_Mn"])),
            popup=(stat["Abr"] + ": " + stat["Name"] + " " + stat["Reg"]),
            icon=folium.Icon( color="orange",icon=form[stat["Type"].strip()] ),
        ).add_to(m)
    else:
        folium.Marker(
            location=[stat["Lat"], stat["Lon"]],
            tooltip=("Years: " + str(stat["N_Yr"]) + "\n"
                     "Means: " + str(stat["N_Mn"])),
            popup=(stat["Abr"] + ": " + stat["Name"] + " " + stat["Reg"]),
            icon=folium.Icon( color="red",icon=form[stat["Type"].strip()] ),
        ).add_to(m)

# Unfortunately, it's hard to match the folium colors exactly for the legend
legend_html = """
{% macro html(this, kwargs) %}
<div style="
    position: fixed;
    bottom: 50px;
    left: 50px;
    width: 250px;
    height: 150px;
    z-index:9999;
    font-size:14px;
    ">
    <p><a style="color:#2AAD27;font-size:150%;margin-left:20px;">◼</a>&emsp;>30 years</p>
    <p><a style="color:#38AADD;font-size:150%;margin-left:20px;">◼</a>&emsp; 20-30 years</p>
    <p><a style="color:#9B59B6;font-size:150%;margin-left:20px;">◼</a>&emsp; 10-20 years</p>
    <p><a style="color:#FFA500;font-size:150%;margin-left:20px;">◼</a>&emsp;  3-10 years</p>
    <p><a style="color:#D63E2A;font-size:150%;margin-left:20px;">◼</a>&emsp; <3 years</p>
</div>
{% endmacro %}
"""

legend = branca.element.MacroElement()
legend._template = branca.element.Template(legend_html)

m.get_root().add_child(legend)

m.save((folder + "/Years.html"))
