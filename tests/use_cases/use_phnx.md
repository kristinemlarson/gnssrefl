### Phoenix, Antarctica

<P align=center>
<img src="https://gnss-reflections.org/static/images/PHNX.jpg" width="500">
</p>

**Station Name:**  phnx

**Location:**  Phoenix, Antarctica

**Archive:**  [UNAVCO](http://www.unavco.org)


[Station Page at UNAVCO](https://www.unavco.org/instrumentation/networks/status/nota/overview/phnx)

[Station Page at Nevada Geodetic Laboratory](http://geodesy.unr.edu/NGLStationPages/stations/PHNX.sta)



### Take a Look at the Data

First make a SNR file.

<code>rinex2snr lorg 2021 1</code>

Use <code>quickLook</code> to produce a periodogram similar to the one in the web app [(For details on quickLook output)](../../docs/quickLook_desc.md). quickLook is set to use the L1 frequency by default:

<code>quickLook lorg 2021 1</code>

<img src="lorg-ql-l1.png" width="600">
 
Compare the periodograms for other frequencies: L2C and L5. They should be similar 
to the L1 periodogram, except that there will be fewer satellite traces because only GPS satellites launched after 2005 
broadcast L2C and only satellites after 2010 broadcast L5.

### Analyze the Data

Now prepare to analyze the data using <code>gnssir</code>.  First you need to create a set of analysis instructions. 
The default settings only need the station name, latitude, longitude, and ellipsoidal height. Originally the software
required you to input the coordinates. If you know that the Nevada Reno group has the site in its database, you can 
avoid that step, i.e.

<code>make_json_input phnx 0 0 0 -query_unr True</code>

The json output will be stored in $REFL_CODE/input/phnx.json. [Here is a sample json file.](phnx.json)

Next make some snr files for a time span of about eight months. Restrict the search 
to the UNAVCO archive to make the 
code run faster (otherwise it will check three other archives as well). The resulting SNR files 
will be stored in $REFL_CODE/2019/snr/lorg. 

<code>rinex2snr lorg 2019 1 -doy_end 233 -archive unavco</code>

Run <code>gnssir</code> for all the SNR files:

<code>gnssir lorg 2019 1 -doy_end 233</code>

The default does not send any plots to the screen. If you do want to see them, set <code>-plt True</code>:
