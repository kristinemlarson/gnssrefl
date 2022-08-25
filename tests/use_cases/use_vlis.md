### Vlissingen

<p align="center">
<img src="VLIS.jpeg" width="500"><BR>
</P>

**Station Name:** vlsi 

**Location:** Vlissingen, the Netherlands

**Archive:** SONEL, BKG, BEV


[Station Page at Nevada Geodetic Laboratory](http://geodesy.unr.edu/NGLStationPages/stations/VLIS.sta)


### Take a Quick Look at the Site Reflection Zones

This lovely site is currently tracking multiple GNSS constellations.  
It is always a good idea to get an idea of the azimuthal range for sea level reflections.
And you will want to find out its height above sea level for a "reality check."

[Type VLIS into the station name and first use the defaults.](http://gnss-reflections.org/rzones)
Try different azimuth constraints. I recommend only using 5-15 degree elevation angles.

### Take a Quick Look at the Data

Begin by making an SNR file. 

<code>rinex2snr tgho 2020 300 -orb gnss -archive nz</code>

<code>quickLook tgho 2020 300 -e1 5 -e2 15</code>

<img src="tgho-default.png" width="600">

The clutter near the monument produces noise at the small RH values.  A better result 
can be found if those values are eliminated by setting h1 to 2. We also extend h2 to 8.

<code>quickLook tgho 2020 300 -e1 5 -e2 15 -h1 2 -h2 8</code>

<img src="tgho-better.png" width="600">

Now try looking at the periodogram for L2:

<code>quickLook tgho 2020 300 -e1 5 -e2 15 -h1 2 -h2 8 -fr 2</code>

<img src="tgho-l2.png" width="600"/>

### Analyze the Reflections 

Use <code>make_json_input</code> to set up the analysis parameters. I am going to constrain both
the RH values and the elevation angles. I am not familiar with this station, so I am more or less
turning off the amplitude constraint (to 1) and using only peak2noise for QC.  

<code>make_json_input vlis 0 0 0 -h1 5 -h2 15 -e1 5 -e2 15 -peak2noise 3 -ampl 1 -allfreq T</code>
 
The loThe azimuth mask has to be set by hand, so edit the file accordingly

Glonass signals (frequencies 101 and 102) were added and GPS L2/L5 were removed.[Sample json](tgho.json)

Then make SNR files for ~six months:

<code>rinex2snr tgho 2020 130 -archive nz -doy_end 319 -orb gnss</code>

The output SNR files are stored in $REFL_CODE/2020/snr/tgho.

Now run <code>gnssir</code> for these same dates:

<code>gnssir tgho 2020 130 -doy_end 319 </code>

To look at daily averages, use the utility <code>daily_avg</code>. The median filter is set to allow values within 0.25 meters of the 
median, and the minimum number of tracks required to calculate the average is set to 50 tracks.  


