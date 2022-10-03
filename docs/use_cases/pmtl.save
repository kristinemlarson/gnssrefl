### St Lawrence River

Station pmtl is operated by the Montreal Port Authority. The data are archived at NRCAN. 

Because I need to use high-rate data at this site, you need to have installed **teqc**.
See the [main documentation for more information](https://github.com/kristinemlarson/gnssrefl).
I also urge you to install the **gnssSNR** Fortran code, as it is MUCH faster 
than my python-only RINEX reader/orbit interpolator.

GPS L1, Glonass L1 and L2 can be used at this site. Tracking L2C, L5, Galileo, and Beidou signals 
would significantly improve the site.

Look at the [NRCAN Site Description for pmtl](https://webapp.geod.nrcan.gc.ca/geod/data-donnees/station/report-rapport.php?id=M0722900)

<img src="https://webapp.geod.nrcan.gc.ca/cacs/PMTL_MONU.jpg" width="500" />

The GNSS antenna is on the roof of grain terminal. Also 
note the ellipsoidal height (and geoid corrected height),
[also provided at my geoid site](https://gnss-reflections.org/geoid?station=pmtl)

**Picking a mask:** 

For reflections, you want to know the height above the water.
This is easy for an ocean site - but a little trickier here. To start out, concentrate on the 
geographic mask appropriate for its location using my [reflection zone webapp](https://gnss-reflections.org/rzones).

<img src="pmtl_rzone.png" width="500" />

Make a SNR file using the -orb gps+glo, -archive nrcan, and -rate high options.
Warning: downloading a high-rate GNSS file can take a while ... 

- *rinex2snr pmtl 2020 330 -archive nrcan -rate high -orb gps+glo*


Run **quickLook** - but given the height of pmtl, you are going to need to change the RH values. If you aren't
sure how that should go, start out with a broad RH region:

- *quickLook pmtl 2020 330 -h1 40 -h2 90 -e1 5 -e2 12*

<img src="pmtl-first-try.png" width="500"/>

I have annotated this **quickLook** periodogram to point out that there is an outlier in the SW region. 
You can also see that the NW region is useless, which is what we should expect.
You can try looking at a few more frequencies (such as Glonass) and using a more restricted RH region.

For a final analysis, you need to use **gnssir**. First you set up a json of instructions using
**make_json_input**:  

- *make_json_input pmtl 45.5571 -73.5204 54.073 -h1 70 -h2 90 -e1 5 -e2 12 -allfreq True*

You will need to hand-edit the json to remove GPS L2C, GPS L5, and Galileo data, and 
to set your azimuth region and amplitudes. [Here is my json that you can compare to](pmtl.json).
Note: I do not consider this to be the "final" mask. For a busy region 
like a harbor, you would want to examine multiple days and weeks of data before 
making final decisions. To run the **gnssir** code, you really only need to provide the station name,
the year, and doy.  The rest of the inputs are in that json.

- *gnssir pmtl 2020 330*

If you want to see some plots of different frequencies (they will not be like the quadrants you saw before):

- *gnssir pmtl 2020 330 -plt True*

This is L1. The top plot is all the SNR data used in the periodograms. The plot below is the RH periodograms all on 
top of each other. Different colors are different satellites.

<img src="pmtl_l1.png" width="500" />

These are the results for Glonass L1

<img src="pmtl_l101.png" width="500" />

The RH results for a single day are written to $REFL_CODE/2020/results/pmtl/330.txt
Once you are happy with how you have set your station mask (elevation and azimuth angles) 
and quality control metrics, you can analyze as much data as you like. This command would do all the data
between day of year 300 and day of year 330 (assuming you had previously run **rinex2snr** for the same time period):

- *gnssir pmtl 2020 300 -doy_end 330*

At this site you would most likely convert the results to a daily average using **daily_avg**.

There is a tide gauge near this site. Please see NRCAN for more information.
I downloaded this plot. You can see the expected height of the river on November 25, 2020, the day
I used as an example. The St Lawrence River height is just where you would expect, given the difference between
the RH analysis and the orthometric height of the GNSS antenna.

<img src="montreal.png" width="500">
