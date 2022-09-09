### TGGO

**Station Name:** tggo  or TGGO00DEU

**Location:** Elbe River, Germany

**Archives:** [BFG](https://www.bafg.de/EN/Home/homepage_en_node.html) 

[Station Page at NGL](http://geodesy.unr.edu/NGLStationPages/stations/TGGO.sta)

<p align=center>
<img src=TGGO.JPG width=600</img>
</p>

TGGO is a station in 
the [BfG-GNSS Monitoring Network](https://fig.net/resources/proceedings/fig_proceedings/fig2021/papers/ts05.4/TS05.4_esch_11010.pdf). It is located in the Elbe River. It is colocated with a tradtional 
tide gauge. It has excellent visibilty of the water.  

### Reflection Zones for TGGO

[Type tggo into the station name for our reflection zone web site.](http://gnss-reflections.org/rzones)
Generally for water, I recommend using up to 15 degree elevation angles.
Note that the height of the GNSS antenna above sea level is returned on the right hand side.
We will compare that value with the estimated reflector height.
[It does look like there might be some kind of pier that we should avoid](http://gnss-reflections.org/rzones?station=tggo&lat=0.0&lon=0.0&height=0.0&msl=msl&RH=2&freq=1&nyquist=0&srate=30&eang=1&azim1=-90&azim2=180&system=gps)

### Make a SNR file 

Because the GNSS station is ~12 meters above the water, we are too close to the L1 Nyquist 
for a receiver that is sampling at 30 seconds.  I recommend using the 15 second files that BFG started 
producing in summer 2022. Using <code>rinex2snr</code>, make the following choices:

- station tggo00deu (the longer station name will tell the code to find RINEX 3 instead of RINEX 2.11)
- archive bfg
- orb gnss (you can also use rapid after mid-2021)
- samplerate 15

<code>rinex2snr tggo00deu 2022 234 -archive bfg -orb rapid -samplerate 15</code>

You will need a password for the BFG archive which is available upon request.
While you can also find TGGO data at SONEL, it will likely be the 30 second data which is not 
as useful as the 15 second data.

### First evaluation of the data for TGGO

I am going to use year 2022 and day of year 234 and frequency 20 (which means L2C). I will 
further restrict elevation angles to 5-15. In order to see the water, you need to set the reflector height
limits to include the vertical distance to the water with the optional parameters h1 and h2.

<code>quickLook tggo 2022 234 -fr 20 -e1 5 -e2 15 -h1 6 -h2 20</code>

The first plot shows periodograms in the four geographic coordinates. 

<img src=tggo_ql1.png width=600>

These are summarized below.  

<img src=tggo_ql2.png width=600>

The "blue" retrievals here show that the GNSS antenna is indeed ~12 meters above the water. The variation 
in reflector height (as seen in the periodograms and in this summary with respect to azimuth) are the tides.  
I've outlined in red the azimuth region that shows consistently rejected retrievals.  This corresponds to 
where we saw the pier in the photograph.  

### Analyze the data

Go back and make SNR files for a longer time period:

<code>rinex2snr tggo00deu 2022 226 -doy_end 240 -archive bfg -orb rapid -samplerate 15</code>

Since tggo is included in our global database, you can simply use 0,0,0 for the *a priori* station coordinates:
I am using a slightly smaller reflector height zone.

<code>make_json_input tggo 0 0 0 -h1 6 -h2 20 -e1 5 -e2 15 -h1 6 -h2 18 -allfreq T</code>

Edit the json file (location is printed to the screen) and remove the azimuth region in
the red box above.

Now estimate reflector heights for these same dates: 

<code>gnssir tggo 2022 226 -doy_end 240 </code>

To put those results all together:

<code>subdaily tggo 2022</code>

Multiple figures come to the screen. The first will summarize how much each
constellation contributes. Because of restrictions for this particular receiver, the Galileo 
signals are degraded for reflections. When a new receiver is installed, the Galileo 
retrievals will significantly improve.

<img src=tggo_1.png width=600>

The reflector heights are then plotted as a function of constellation (GPS, Glonass, Galileo), azimuth, and 
amplitude of the periodogram. These can be useful if you are trying to assess whether your azimuth mask 
is working.

<img src=tggo_2.png width=800>

Time series with large outliers removed.

<img src=tggo_3.png width=600>
 
Additional corrections can be made using the <code>rhdot T</code> setting. I will add 
more information here when I get a chance.

Kristine M. Larson September 9, 2022
