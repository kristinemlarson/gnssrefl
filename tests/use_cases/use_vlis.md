### Vlissingen

<p align="center">
<img src="VLIS.jpeg" width="500"><BR>
</P>

**Station Name:** vlsi  or VLSI00NLD

**Location:** Vlissingen, the Netherlands

**Archive:** SONEL, BKG, BEV

[Station Page at NGL](http://geodesy.unr.edu/NGLStationPages/stations/VLIS.sta)

[EUREF Page](https://epncb.oma.be/_networkdata/siteinfo4onestation.php?station=VLIS00NLD)

### Take a Quick Look at the Site Reflection Zones

The EUREF page has a lot of information about the GNSS site here. It is currently tracking multiple GNSS constellations.  
If you are going to try and measure water levels, it is a good idea to find out whether 
the "reflection zones" are on water. And which azimuths provide that.
[Type VLIS into the station name and first use the defaults at this web site.](http://gnss-reflections.org/rzones)
Try different azimuth constraints. I recommend only using 5-15 degree elevation angles.
Note that the height of hte antenna above sea level is provided by the web app.

Another you can do is try to get an idea of what the tidal range will be.  Follow the link to see how big they are:

[IOC Tide Gauge Site](http://www.ioc-sealevelmonitoring.org/station.php?code=vlis)


While I won't discuss it here 
(please read [Roesler and Larson, 2018](https://link.springer.com/article/10.1007/s10291-018-0744-8) for details about 
the Nyquist for GNSS-IR), it is an issue at VLIS. The easiest data to find are the 30 second data
deposited by geodesists at various global archives. This sample rate would be fine for an antenna 8 meters above the water. But at VLIS - with 
the known tidal range - we are really too close to the L1 Nyquist to use 30 second data. You can use the 30 second data for L2, but
you are basically throwing away half your data if ignore L1 and only use L2 and L5. 

So what *can* you do? The good news is that this site reliably reports high-rate GNSS data. 
The bad news is that the sample rate is 1 second. And you do not need 1 second data for this site; 15 
second data would be fine. If you retain the 1 second data, all the <code>gnssrefl</code> programs will be pretty slow.

To get you started, I have made some RINEX files for you. They are 
available in this [tar file.](https://morefunwithgps.com/public_html/vlis_2022.tar)
After downloading, <code>tar -xvf vlis_tar.2022</code>. There should be 14 gzipped files in RINEX 2.11 format.
Instead of using <code>gnssrefl</code> I am going to show you how to use the web app. Open a browser and 
type in <code>gnss-reflections.org</code>. You will be using the RINEX upload option which is in the center.

You should pick one of the RINEX files I've given you.  Pick the L1L2CL5 frequency option, and set the 
elevation angles to range from 5 to 15.  Set the Reflector Heights to vary from 5 to 19 meters. 
I am going to set my azimuth range to 70 to 180 and the amplitude to 2 (which is essentially turning it off).
The quality control metric is the peak2noise ratio - and it is nominally set to 3. That is ok for now.
Hit submit and wait ~5-10 seconds for results. 


### Make SNR files

To make your own 15 second multi-GNSS VLIS files with <code>rinex2snr</code> you need to :

- station vlis00nld (the longer station name will tell the code to find RINEX 3 instead of RINEX 2.11)
- rate high
- dec 15
- archive BKG
- orb of gnss

### Take a Quick Look at the Data

Begin by making an SNR file. 

<code>rinex2snr vlis00nld 2020 153 -rate high -dec 15 -orb gnss -archive bkg</code>

and relying on the peak2noise parameter for quality control
turning off the amplitude constraint (to 1) and using only peak2noise for QC.  

<code>make_json_input vlis 0 0 0 -h1 5 -h2 15 -e1 5 -e2 20 -peak2noise 3 -ampl 1 -allfreq T</code>

Edit the json file and change the azimuth ranges 0-90 70-90 and  delete the western azimuths. Be careful
when editing the file so that the commas and such are in the right places.

Now run <code>gnssir</code> for these same dates:

<code>gnssir vlis 2022 130 -doy_end 153 </code>



