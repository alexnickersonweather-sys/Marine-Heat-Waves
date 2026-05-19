# Purpose: List NDBC stations from the NDBC website
#
# Date of Version 01: Apr. 03, 2025
#
# Author 01: Alexander Nickerson
#

import urllib.request
from time import time
from bs4 import BeautifulSoup

s = time()

# establish the url
page_to_read = 'https://www.ndbc.noaa.gov/to_station.shtml'

# open the page
opened_page = urllib.request.urlopen(page_to_read)
page_read = BeautifulSoup(opened_page.read(),'lxml')

# the station kinds are buried under the <h2> tag
stat_all = page_read.find_all(['h2','a'])
head_all = page_read.find_all('h2')
href_all = page_read.find_all('a', href=True)

stat_reg = []
stat_org = []

# loop through all hyperlinks
for stat in stat_all:
    # some necessary workarounds due to how the page is coded
    if stat.name == 'h2':
        org = stat.contents[0]
        org = org.replace(' Stations','')
    
    # get the links to the individual station pages
    if stat.name == 'a':
        link = stat.get('href')
        
        # some pages are dead
        if link == None:
            continue
        
        # if itn's not dead, then collect the link
        if ("station_page.php?" in link):
            link_split = link.split("=")
            stat_org.append(org)
            stat_reg.append(link_split[1])
        
print('Finished all stations.')

# save the list of stations to a text file.
with open('Docs/List_All_NDBC.txt', 'w') as f:
    for i in range(0,len(stat_reg)):
        f.write("%8s" % stat_reg[i] + "; " + 
                "%s\n" % stat_org[i])
            
e = time() - s

print(f"Links generated in {e:6.3f} seconds")
