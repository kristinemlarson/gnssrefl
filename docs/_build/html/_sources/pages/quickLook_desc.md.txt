# Quick Description of the quickLook Code 

<code>quickLook</code> is meant to give you a visual assessment of the reflection characteristics 
of your GNSS site. It is **not** meant for routine analysis of your data - instead it is 
meant to give you a better understanding of how to choose settings for that routine analysis, which 
is done in <code>gnssir</code>.

<code>quickLook</code> takes all the SNR data at a site and splits it into four geographic 
quadrants (northwest, northeast, southwest, southeast). Within those quadrants, it identifies rising
and setting arcs for one GNSS transmitter frequency and uses a periodogram to estimate the dominant Reflector Height (RH) 
in meters.

Two plots are returned. One is a summary periodogram plot. This allows you to see for yourself the periodograms
that will be used to retrieve RH.  Each  color here represents a different satellite. Defaults were used, so the periodograms
were limited to the region 0.5 to 6 meters. The GPS L1 frequency is the default. (This site has good L1 SNR data at this time - in previous 
years it was a different receiver with poor data quality).

<p align=center>
<img src="../use_cases/p041-l1.png" width=600>
</p>

The y-axis is the spectral amplitude in converted SNR units (volts/volts).  If you see a strong peak in the periodogram,
that means you will have a good estimate of the RH for that satellite arc. The data represented in gray are "failed" periodograms. 

The second plot returned is a summary for various quality control metrics. 

* the top plot is the color coded RH retrieval color: blue for good and gray for bad.  What you are looking for are RH that 
are consistent with your site.  In this case the antenna is above level ground - and it is ~2 meters tall.  Even the failed RH 
retrievals in general are consistent at this site. 


* the middle plot is the "peak to noise ratio" which is defined as peak spectral amplitude divided by the average 
spectral value over a defined noise region.  In <code>quickLook</code> this will be the same region you used for your RH estimate.
So here the noise region would be 0.5 to 6 meters.  The peak to noise ratio of 3 seems to work - but also seems that one 
could increase it a bit. However, this value is surface dependent. If you happen to check the peak to noise ratio on a day at peak 
vegetation growth, you might be fooled into thinking the site did not work. Similarly, a windy day on a lake will produce lower peak to 
noise ratios than a day without wind. I generally use 3.5 for snow, 3.2 for lakes, and 2.7 for tides.

* the bottom plot is the spectral amplitude for the RH peak. This will depend -again - on the surface type. Different surfaces (water, ice, snow, bare soil) reflect 
signals differently. It also reflects how smooth the surface is and which elevation angle limits were used.

<p align=center>
<img src="../use_cases/p041_l1_qc.png" width=600>
</p>

**Common Questions:**

Why are spectral amplitudes bigger when lower elevation angles (5-15) are used? Because the GNSS antenna does a relatively poor job 
of rejecting reflections there.  When you start to include higher elevation angles (> 20), the reflection oscillations are still there,
but they are much smaller.

Is there something magical about a peak to noise ratio of 3? No. In fact we used a peak to noise ratio of 4 for most of PBO H2O. 

Does a "gray" failed periodogram mean there is an obstruction of some kind on the ground? No. It can also mean that the satellite arc
is too small. The code also tries ot make sure that you have a long enough data series to retrieve a reliable spectral peak. So some arcs
have too little data - sometimes because the arc crosses your azimuth boundaries.

[Additional discussion of the GNSS-IR method, with example periodogram links.](https://gnss-reflections.org/overview)
