# subdaily

[Inputs](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.subdaily_cl.html).

This code applies models that improve the initial RH values. **THE NEW RH VALUES ARE 
NOT WRITTEN TO COLUMN 3!**  Please look at 
the file to look at the column number with the new results.

Whle this code is meant to be used AFTER you have chosen a good analysis strategy, you can 
apply new azimuth and Quality Control constraints on the commandline, i.e. <code>-azim1, -azim2, -ampl</code>.
This can be helpful when you are trying to identify the source of persistent outliers.

Please keep in mind that the spline fit is **not truth**. We use it to provide one of our model corrections. 
We also report how well the individual RH values fit this spline, but this is not true precision.  It is only representative of 
precision if the tides look like splines.

## Section I

The section summarizes the RH data previously computed using <code>gnssir</code>, i.e. 
which constellations where used, how do the RH data look compared to various quality 
control parameters).  It also removes gross 
outliers by looking a very crude daily standard deviation (i.e. with 2.5 sigma, which you 
can control on the commandline). The main results are visual.


<img src="../_static/sc02_Figure1.png" width="600">

Allows you see which constellations are contributing to your solution

<img src="../_static/sc02_Figure2.png" width="600">

RH plotted with respect to time for three color-coded metrics: frequency, amplitude, and peak2noise.

<img src="../_static/sc02_Figure3.png" width="600">

RH plotted with respect to azimuth.

<img src="../_static/sc02_Figure4.png" width="600">

Bottom panel is the final RH series with gross outliers removed. These data are written to a new file.


## Section II

The primary goal of this section is to 
apply the [RHdot correction](https://www.kristinelarson.net/wp-content/uploads/2015/10/LarsonIEEE_2013.pdf)
It also tries to do a better job of removing outliers by using a spline fit. If the spline fit
is not very good (which you control with -knots), then it will throw out too many points (or too few).
Right now it uses three sigma. You can override this using -spline_outlier1 in meters.
If your spline looks like it is too loose or too tight, please try different knots.
Keep in mind that splines don't like data outages.

After RH dot is applied, it makes a new spline and then calculates how well the different frequencies
agree with this. It computes and applies a frequency dependent offset with respect to GPS L1.  
This final version also removes three sigma outliers - though again, you can use -spline_outlier2 to set
that to a better value for your data set.

If you have your own concatenated file of results you can set -txtfile_section1 to that filename.
Similarly, if you want to skip section 1 and go right to section 2, you can set -txtfile_section2 to your filename.

These figures are created and summarize the steps being taken

<img src="../_static/sc02_Figure5.png" width="600">

Initial spline fit to RH data - three sigma outliers removed.

<img src="../_static/sc02_Figure6.png" width="600">

Surface velocity derived from the spline fit and the corresponding RHdot correction (in meters)

<img src="../_static/sc02_Figure7.png" width="600">

Final result: 

- RHdot correction applied
- Interfrequency bias (IF) removed
- Three sigma outliers removed
- New spline fit
- Spline fit written out at set intervals


## RHdot Correction

There are lots of ways to apply the RHdot correction - I am only providing a simple one at this point.  
The RHdot correction requires you know :

- the average of the tangent of the elevation angle during an arc 
- edot, the elevation angle rate of change with respect to time 
- RHdot, the RH rate of change with respect to time  

The first two are (fairly) trivial to compute and are included in the results file in column 13 as the edotF. 
This edot factor has units of rad/(rad/hour), or hours. So if you 
know RHdot in units of meters/hour, you can get the correction by simple multiplication. 

Computing RHdot is the trickiest part of calculating the RHdot correction.
And multiple papers have been written about it. If you have a 
well-observed site (lots of arcs and minimal gaps), you can use the RH 
data themselves to estimate a smooth model for RH (via cubic splines) and 
then just back out RHdot. This is what is done in <code>subdaily</code> 

If you have a site with a large RHdot correction, you should be cautious of removing too many
outliers in the first section of this code as this is really signal, not noise. You can set the outlier criterion 
with <code>-spline_outlier1 </code>. 

There are other ways to compute the RHdot correction:

- computing tidal coefficients, and then iterating using the forward predictions of the tidal fit (as in Larson et al. 2013b)
- estimating RHdot effect simultaneously with tidal coefficient (as done in Larson et al. 2017). 
- low-order tidal fit (Lofgren et al 2014)
- direct inversion of the SNR data (Strandberg et al 2016 , Purnell et al. 2021)
- estimate a rate and an acceleration term (Tabibi et al 2020)


## Miscellaneous

Here is an example of a site (TNPP) where the RHdot correction is important (I apologize for color choice here. The 
current code uses more color-blindness-friendly colors):

<img src="../_static/tnpp_rhdot2.png" width="600">

After removing the RHdot effect and frequency biases, the RMS with respect to the spline improves from 0.244 to 0.1 meters.

<img src="../_static/tnpp_final.png" width="600">


If you want to do your own quality control, you can simply cat the files in your results area. As an example, after you have 
run <code>gnssir</code> for a station called sc02 in the year 2021:

<code>cat $REFL_CODE/2021/results/sc02/*.txt >sc02.txt</code>

I think you can then send this file to the code using <code>-txtfile_part2</code>
