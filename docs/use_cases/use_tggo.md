### Grauerort-Reede

**Station Name:** tggo  or TGGO00DEU

**Location:** Elbe River, Germany

**Archives:** [BFG](https://www.bafg.de/EN/Home/homepage_en_node.html) 

[Station Page at NGL](http://geodesy.unr.edu/NGLStationPages/stations/TGGO.sta)

<p align=center>
<img src=../_static/TGGO.JPG width=600</img>
</p>

TGGO is a station in 
the [BfG-GNSS Monitoring Network](https://fig.net/resources/proceedings/fig_proceedings/fig2021/papers/ts05.4/TS05.4_esch_11010.pdf). 
It is located in the Elbe River. It is colocated with a tradtional 
tide gauge. It has excellent visibility of the water.  

### Reflection Zones for TGGO

[Type tggo into the station name for our reflection zone web site.](http://gnss-reflections.org/rzones)
Generally for water, I recommend using up to 15 degree elevation angles.
Note that the height of the GNSS antenna above sea level is returned on the right hand side.
We will compare that value with the estimated reflector height.
[It does look like there might be some kind of pier that we should avoid](http://gnss-reflections.org/rzones?station=tggo&lat=0.0&lon=0.0&height=0.0&msl=msl&RH=2&freq=1&nyquist=0&srate=30&eang=1&azim1=-90&azim2=180&system=gps)

### Make a SNR file 

Because the GNSS station is ~12 meters above the water, we are too close to the L1 Nyquist 
for a receiver that is sampling at 30 seconds.  I recommend using the 15 second files that BFG started 
producing in summer 2022. Make the following choices:

- station tggo00deu (the longer station name will tell the code to find RINEX 3 instead of RINEX 2.11)
- archive bfg
- orb rapid (you can also use gnss if you prefer)
- samplerate 15

<code>rinex2snr tggo00deu 2022 234 -archive bfg -orb rapid -samplerate 15</code>

You will need a password for the BFG archive. This is available upon request by sending an e-mail to gnss@bafg.de.
You will only need to enter the password once as <code>gnssrefl</code> will save it to your local system.
While you can also find TGGO data at SONEL, it will likely be the 30 second data which is not as useful as the 15 second data.

### First evaluation of the data for TGGO

I am going to use year 2022 and day of year 234 and frequency 20 (which means L2C). I will 
further restrict elevation angles to 5-15. In order to see the water, you need to set the reflector height
limits to include the vertical distance to the water with the optional parameters h1 and h2.

<code>quickLook tggo 2022 234 -fr 20 -e1 5 -e2 15 -h1 6 -h2 20</code>

The first plot shows periodograms in the four geographic coordinates. 

<img src=../_static/tggo_ql1.png width=600>

These are summarized below.  

<img src=../_static/tggo_ql2.png width=600>

All three plots are with respect to azimuth in degrees. On the top plot, the "blue" retrievals show that the GNSS antenna is indeed ~12 meters above the water. The variation in reflector height (with respect to azimuth) are the tides. I've outlined in red the azimuth region that shows consistently rejected retrievals. This roughly corresponds to where we saw the pier in the photograph.  

### Analyze the data

Go back and make SNR files for a longer time period:

<code>rinex2snr tggo00deu 2022 226 -doy_end 240 -archive bfg -orb rapid -samplerate 15</code>

The next step is to write down your analyis strategy using <code>make_json_input</code>. Since tggo is 
included in our global database, you can simply use 0,0,0 for the required *a priori* station coordinates:
I am using a slightly smaller reflector height zone than I used with <code>quickLook</code>.

<code>make_json_input tggo 0 0 0 -h1 6 -h2 20 -e1 5 -e2 15 -h1 6 -h2 18 -allfreq T -azlist 30 90 90 180 270 330 </code>

Now estimate reflector heights for these same dates: 

<code>gnssir tggo 2022 226 -doy_end 240 </code>

To put those results all together:

<code>subdaily tggo 2022</code>

Multiple figures come to the screen. The first will summarize how much each
constellation contributes. Because of restrictions for this particular receiver type, the Galileo 
signals are degraded for reflections. When a new receiver is installed, the Galileo 
retrievals will significantly improve.

<img src=../_static/tggo_1.png width=600>

The reflector heights are then plotted as a function of constellation (GPS, Glonass, Galileo), azimuth, and 
amplitude of the reflector height periodogram. These can be useful if you are trying to assess whether your azimuth mask 
is working.

<img src=../_static/tggo_2.png width=800>

Time series with large outliers removed.

<img src=../_static/tggo_3.png width=600>
 
Additional corrections can be made using the <code>rhdot T</code> setting. In order to 
compute the RHdot correction, we use a spline fit to our initial RH estimates. And then
we will use the numpy algorithms to estimate RHdot anywhere from that:  

<img src=../_static/tggo_rhdot3.png width=600>

The outliers in the RHdot correction plot above are disturbingly large. If you look at the file with
the corrections in it (the name of the file is sent to the screen), and simply look 
at which satellites have the largest outliers, you find that they have a 
delT (length of the arc) of more than 60 minutes, whereas the vast 
majority of the arcs are less than 30 minutes. Such a long arc is 
perfectly fine for computing snow depth or lake heights - significant 
subdaily behavior is not expected. For tides where tidal rates are 
significant, the gnssrefl code is not going to be able to use a simple fit to find the RH dot
correction. The best thing to do is to change the delT parameter in the json file to ignore these 
long arcs. The default was 75; I changed mine to 35 minutes and 
reran <code>gnssir</code> and then <code>subdaily</code>.
You can see now that those RHdot outliers are gone:

<img src=../_static/tggo_delT_fixed.png width=600>

The statistics for the fits are then printed to the screen. In this case, without 
the RHdot correction, the standard deviation of each RH value is 27.3 cm.
WIth the RHdot correction it is 21.5 cm, so a significant improvement. Note that
this is relative to the spline fit (i.e. it is not accuracy) and without correcting for phase center offsets.

<img src=../_static/tggo_new.png width=600>

**Please note that the new RH values are being written to a new column!  Please look into the file.**


The code will then remove interfrequency biases and recompute a spline:

<img src=../_static/tggo_delT_fixed2.png width=600>

**Please note that the IF corrected RH values are being written to a new column!  Please look into the file.**

Overall this is a very good reflections site - but it is hampered by the lack of Galileo observations.
When this current receiver is upgraded to a newer model, I expect to see much better results.
If someone would like to provide "truth" data, I could add a comparison.

Kristine M. Larson November 21, 2022

[Current status for station at WSV](https://www.pegelonline.wsv.de/gast/stammdaten?pegelnr=5970020)

[Another view](https://www.pegelonline.wsv.de/webservices/zeitreihe/visualisierung?parameter=WASSERSTAND%20ROHDATEN&pegelnummer=5970026&ansicht=einzeln)
