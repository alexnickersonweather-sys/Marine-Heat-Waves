# Purpose: Combine the two lists into one
#
# Date of Version 01: Mar. 04, 2026
#
# Author 01: Alexander Nickerson
#

import pandas as pd
    
# open the text file, name the columns, and sort
stat_A = pd.read_csv('Docs/List_Climo_All.txt',
                        header=0, sep="|", index_col=False,dtype=object)

# convert important variable to integer
stat_A["N_Mn"] = stat_A["N_Mn"].astype(int)

# collect subset of array
stat_R = stat_A.loc[stat_A["N_Mn"] >= 3,:].copy()

# return column to string
stat_R["N_Mn"] = " " + stat_R["N_Mn"].map("{:2d}".format)

# save data
stat_R.to_csv('Docs/List_Climo_Redux.txt',index=False,sep="|")
