# Purpose: compute the trend and associated statistics
#
# Date of Version 01: Jan. 07, 2026
#
# Author 01: Alexander Nickerson
#
from matreg import matreg
import numpy as np
from scipy.stats import t

def trend(X,Y,TS):
    # Trend3 finds the slope, y-intercept, and 95%
    # confidence interval for data without gaps in it and with a known
    # number of cycles/year.
    #   X:  X-axis data
    #   Y:  Y-axis data
    #  Be:  number of cycles per year
    # TS1:  temporal unit and method of regression as follows
    #       'm' is months with a sine/cosine term for annual signal
    #       'y' is years
    # nBad: number of interpolated points, which subtracts from DoF

    # X = time; Y = sst1; clearvars -except X Y

    # make vertical arrays
    X = np.asarray(X).reshape(-1, 1)
    Y = np.asarray(Y).reshape(-1, 1)

    # array must have at least three years of data
    if TS == 'y':
        NM = 3
    elif TS == 'm':
        NM = 36
    else:
        raise ValueError("Enter a valid value for TS1: 'y' or 'm'")

    # if data meets minimum count
    if np.sum(~np.isnan(Y)) >= NM:
        if TS == 'y':
            # do regression for annual data, get the number of points, and
            # compute the DoF based upon Be
            _, Y_DT, Xb, _, _ = matreg(X, Y, X[0])
            DOF = sum(~np.isnan(Y)) - 2

        elif TS == 'm':
            # do regression for monthly data, get the number of points, and
            # compute the DoF based upon Be
            _, Y_DT, Xb, _, _ = matreg(X, Y, X[0],[1])
            DOF = sum(~np.isnan(Y)) - 2

        # extract slope and Y-intercept
        slope = Xb[1]
        Yint  = Xb[0]

        # demean the data
        X_DM = X - np.nanmean(X)

        # if there are positive degrees of freedom, compute other values
        if DOF > 0:
            # Standard Error
            std_err = np.sqrt(
                np.nansum(Y_DT**2) / (DOF * np.nansum(X_DM**2))
            )
            T95  = t.ppf(0.975, DOF)
            CI95 = T95 * std_err
        else:
            DOF  = 0
            T95  = np.inf
            CI95 = np.inf
    else:
        slope = np.nan
        Yint  = np.nan
        DOF   = np.nan
        T95   = np.nan
        CI95  = np.nan

    return slope, Yint, DOF, T95, CI95
