# Puerto Penasco, Sonora, Mexico

**Updated June 4, 2023 for gnssir_input**

[Warning](warning.md)

## metadata

**Station Name:** tnpp

[Station Page at UNAVCO](https://www.unavco.org/instrumentation/networks/status/nota/overview/TNPP)

<p align=center>
<img src="https://www.unavco.org/data/gps-gnss/lib/images/station_images/TNPP.jpg" width=500>
</p>

**Archive:** [UNAVCO](http://www.unavco.org)

**Ellipsoidal Coordinates:**

- Latitude: 31.33552

- Longitude: -113.63164

- Height: 27.640 m

- Height above sea level: 62.766 m 


This is a high-rate site. There are multi-GNSS data including L2C starting on 
2021 Oct 27. I will look at a small dataset from late 2021.  


Use the reflection zone app to think about [RH and azimuth constraints](https://gnss-reflections.org/rzones)


### Make SNR Files

Let's start with one file. We are using the high-rate (1 second) data but are decimating it to 2 seconds to make the code run faster.
(my result plots below use the 1 second datastream, but you won't be able to tell the difference):

<code>rinex2snr tnpp 2021 301 -archive unavco -rate high -dec 2 -orb gnss</code>

To get started :

<code>quickLook tnpp 2021 301 -fr 20 -e1 5 -e2 10 -h1 50 -h2 70 </code>  

<img src=../_static/tnpp_1.png width=600>

The periodograms show the tides in the southwest quadrant. That is further demonstrated in the summary plot:

<img src=../_static/tnpp_2.png width=600>

Set your analysis strategy (with some variations):

<code>gnssir_input tnpp  -e1 5 -e2 12 -h1 55 -h2 70  -ampl 0 -azlist2 180 270 -fr_list 1 20 5 101 102 201 205</code>

Now go back and make more SNR files:

<code>rinex2snr tnpp 2021 301 -archive unavco -rate high -dec 2 -orb gnss -doy_end 316</code>

Estimate RH :

<code>gnssir tnpp 2021 301 -doy_end 316 </code>

Look at the sea level results for multiple weeks:

<code>subdaily tnpp 2021</code>

Number of measurements for each constellation:

<img src=../_static/subdaily_tnpp_3.png width=600>

Azimuth vs. constellation, amplitude, and peak2noise:

<img src=../_static/subdaily_tnpp_2.png width=600>

Initial RH values:

<img src=../_static/subdaily_npp_1.png width=600>

Estimating and applying the RH dot correction improves RH 
precision ([Larson et al., 2013](https://www.kristinelarson.net/wp-content/uploads/2015/10/LarsonIEEE_2013.pdf)).

<img src=../_static/tnpp_rhdot_2.png width=600>

**PLEASE PAY ATTENTION - the corrected RH values are not written to column 3!**

Final series with antenna frequency biases removed compared to a spline fit:

<img src=../_static/tnpp_rhdot_3.png width=600>

The final precision for this site is 0.1 meters
**PLEASE PAY ATTENTION - the corrected RH values are not written to column 3!**

Updated Kristine Larson 2022 December 6

