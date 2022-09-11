
<p align=center>
<img src="https://morefunwithgps.com/public_html/gnssrefl-images-sm.jpg" width=600 />
</p>

### gnssrefl

**github version: 1.1.5** [![PyPI Version](https://img.shields.io/pypi/v/gnssrefl.svg)](https://pypi.python.org/pypi/gnssrefl) [![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.5601495.svg)](http://dx.doi.org/10.5281/zenodo.5601495)

**WARNING: All access to UNAVCO data will end October 1, 2022 unless [you sign up for an account there](https://www.unavco.org/data/gps-gnss/file-server/file-server-access-examples.html)**

**WARNING: CDDIS has changed their high-rate directory protocol. This means some of our download codes now fail.
If someone wants to provide a pull request that addresses this issue, I would be happy to implement it.  I 
am not willing to write such code myself.**

### Table of Contents

1. [Installation](https://github.com/kristinemlarson/gnssrefl/blob/master/docs/README_install.md)
2. Understanding the Code
    1. [rinex2snr: translating GNSS Data (RINEX, NMEA)](https://github.com/kristinemlarson/gnssrefl/blob/master/docs/rinex2snr.md)
    2. [quickLook: assessing a GNSS site using SNR files](https://github.com/kristinemlarson/gnssrefl/blob/master/docs/quickLook.md)
    3. [gnssir: estimating reflector heights from SNR data](https://github.com/kristinemlarson/gnssrefl/blob/master/docs/gnssir.md)
3. Products:
    1. [daily_avg: daily average reflector heights](https://github.com/kristinemlarson/gnssrefl/blob/master/docs/README_dailyavg.md)
    2. [subdaily: LSP quality control and RHdot for reflector height estimates](https://github.com/kristinemlarson/gnssrefl/blob/master/docs/README_subdaily.md)
    3. [invsnr: SNR inversion for subdaily reflector height estimates](https://github.com/kristinemlarson/gnssrefl/blob/master/docs/README_invsnr.md)
    4. [vwc: soil moisture module](https://github.com/kristinemlarson/gnssrefl/blob/master/docs/README_vwc.md)
4. [Examples](https://github.com/kristinemlarson/gnssrefl/blob/master/tests/first_drivethru.md)
5. [Utilities](#helper)
6. [News/Bugs/Future Work](https://github.com/kristinemlarson/gnssrefl/blob/master/docs/news.md)
7. [Publications](https://kristinelarson.net/publications)
8. [How can you help this project? How can you ask for help?](#weneedhelp)

<HR> 

### Understanding <a name="understanding"></a>

**gnssrefl** is an open source/python version of my GNSS interferometric reflectometry (GNSS-IR) code. 

*If you would like to try out reflectometry without installing the code*

I recommend you use [this web app](https://gnss-reflections.org). It 
can show you representative results with minimal constraints. It should provide 
results in less than 10 seconds.

*If you prefer Matlab*

I had a [working matlab version on github](https://github.com/kristinemlarson/gnssIR_matlab_v3), 
but I will not be updating it. You will very likely have to make changes to accommodate the recent
change in security protocols at CDDIS.

*Goals*

The goal of the gnssrefl python repository is to help you compute (and evaluate) GNSS-based
reflectometry parameters using geodetic data. This method is often
called GNSS-IR, or GNSS Interferometric Reflectometry. There are three main modules:

* [**rinex2snr**](docs/rinex2snr.md) translates RINEX files into SNR files needed for analysis.

* [**gnssir**](docs/gnssir.md) computes reflector heights (RH) from SNR files.

* [**quickLook**](quickLook.md) gives you a quick (visual) assessment of a file without dealing
with the details associated with **gnssir**. It is not meant to be used for routine analysis.
It also helps you pick an appropriate azimtuh mask and quality control settings.

There are also various [utilities](#helper) you might find to be useful.
If you are unsure about why various restrictions are being applied, it is really useful 
to read [Roesler and Larson (2018)](https://link.springer.com/article/10.1007/s10291-018-0744-8) 
or similar. You can also watch some background videos 
on GNSS-IR at [youtube](https://www.youtube.com/channel/UCC1NW5oS7liG7C8NBK148Bg).

*Philosophy*

In geodesy, you don't really need to know much about what you are doing to 
calculate a reasonably precise position from GPS data. That's just the way it is.
(Note: that is also thanks to the hard work of the geodesists that wrote the 
computer codes). For GPS/GNSS reflections, you need to know a little bit more - like what are you
trying to do? Are you trying to measure water levels? Then you need to know where the water
is! (with respect to your antenna, i.e. which azimuths are good and which are bad). 
Another application of this code is to measure snow accumulation. If you 
have a bunch of obstructions near your antenna, 
you are responsible for knowing not to use that region. If your antenna is 10 meters 
above the reflection area, and the software default only computes answers up to 6 meters,
the code will not tell you anything useful. It is up to you to know what is best for the site and 
modify the inputs accordingly. 
I encourage you to get to know your site. If it belongs to you, look at 
photographs. If you can't find photographs, use Google Earth.  You can also try using
my [google maps web app interface](https://gnss-reflections.org/geoid?station=smm3).

*Overview*

To summarize, direct (blue) and reflected (red) GNSS signals interfere and create
an interference pattern that can be observed in GNSS Signal to Noise Ratio (SNR) data as a satellite rises or sets. 
The frequency of this interference pattern is directly related to the height of the GNSS antenna phase
center above the reflecting surface, or reflector height RH (purple). *The primary goal of this software 
is to measure RH.* This parameter is directly related to changes in snow height and water levels below
a GNSS antenna. This is why GNSS-IR can be used as a snow sensor and tide gauge. GNSS-IR can also be 
used to measure soil moisture, but the code to estimate soil moisture is not as strongly related to RH as
snow and water. We will be posting the code you need to measure soil moisture later in the year.

<p align=center>
<img src="https://gnss-reflections.org/static/images/overview.png" width="500" />
</p>

This code is meant to be used with Signal to Noise Ratio (SNR) data. This is a SNR sample for a site in the 
the northern hemisphere (Colorado) and a single GPS satellite. The SNR data are plotted with respect to time - however,
we have also highlighted in red the data where elevation angles are less than 25 degrees. These are the data used in 
GNSS Interferomertric Reflectometry GNSS-IR. You can also see that there is an overall smooth polynomial signature
in the SNR data. This represents the dual effects of the satellite power transmission level and the antenna 
gain pattern. We aren't interested in that so we will be removing it with a low order polynomial (and 
we will convert to linear units on y-axis). 

<p align=center>
<img src="https://raw.githubusercontent.com/kristinemlarson/gnssrefl/master/docs/p041-snr.png" width="600"/>
</p>

After that polynomial is removed, we will concentrate on the *rising* 
and *setting* satellite arcs. That is the red parts on the left and right.  

Below you can see those next two steps. On the top is the "straightened" SNR data. Instead of time,
it is plotted with respect to sine of the elevation angle. It was shown a long time ago by Penina 
Axelrad that the frequency extracted from these data is representative of the reflector height.
Here a periodogram was used to extract this frequency, and that is shown below, with the x-axis 
units changed to reflector height. In a nutshell, that is what this code does. It figures out the 
rising and setting satellite arcs in all the azimuth regions you have said are acceptable. It does a 
simple analysis (removes the polynomial, changes units) and uses a periodogram to look at the 
frequency content of the data. You only want to report RH when you think the peak on the periodogram is 
significant. There are many ways to do this - we only use two quality control metrics:

* is the peak larger than a user-defined value  (amplitude of the dominant peak in your periodogram)

* is the peak divided by a "noise" metric larger than a user-defined value. The code calls this the peak2noise.

<p align=center>
<img src="https://raw.githubusercontent.com/kristinemlarson/gnssrefl/master/tests/for_the_web.png" width="600"/>
</p>

The Colorado SNR example is for a fairly planar field where the RH for the rising and setting arc 
should be very close to the same name. What does the SNR data look like for a more extreme case? 
Shown below is the SNR data for [Peterson Bay](https://gnss-reflections.org/static/images/PBAY.jpg), where the rising arc (at low tide) has a very different
frequency than during the setting arc (high tide). This gives you an idea of how the code can be 
used to measure tides. 

<p align=center>
<img src="https://raw.githubusercontent.com/kristinemlarson/gnssrefl/master/docs/pbay-snr.png" width="600"/>
</p>

A couple common sense issues: one is that since you define the noise region, if you make it really large, that 
will artificially make the peak2noise ratio larger. I have generally used a region of 6-8 meters for this 
calculation. So in the figure above the region was for 0-6 meters. The amplitude can be tricky because 
some receivers report low SNR values, which then leads to lower amplitudes. The default amplitude values are 
for the most commonly used signals in GNSS-IR (L1, L2C, L5, Glonass, Galileo, Beidou). The L2P data
used by geodesists are generally not useable for reasons to be discussed later.

Even though we analyze the data as a function of sine of elevation angle, each satellite arc
is associated with a specific time period. The code keeps track of that and reports it in the final answers.
It also keeps track of the average azimuth for each rising and setting satellite arc that passes quality 
control tests.

What do these satellite reflection zones look like? Below are 
photographs and [reflection zone maps](https://gnss-reflections.org/rzones) for two standard GNSS-IR sites, 
one in the northern hemisphere and one in the southern hemisphere.

<p align=center>
<table align=center>
<TR>
<TH>Mitchell, Queensland, Australia</TH>
<TH>Portales, New Mexico, USA</TH>
</TR>
<TR>
<TD><img src=http://gnss-reflections.org/static/images/MCHL.jpg width=300></TD>

<TD><img src=http://gnss-reflections.org/static/images/P038.jpg width=300></TD>
</TR>
<TR>
<TD><img src=https://raw.githubusercontent.com/kristinemlarson/gnssrefl/master/tests/use_cases/mchl_google.jpg width=300</TD>
<TD><img src=https://raw.githubusercontent.com/kristinemlarson/gnssrefl/master/tests/use_cases/p038_google.jpg width=300></TD>
</TR>
</table>
</p>
Each one of the yellow/blue/red/green/cyan clusters represents the reflection zone
for a single rising or setting GPS satellite arc. The colors represent different elevation angles - 
so yellow is lowest (5 degrees), blue (10 degrees) and so on. The missing satellite signals in the north
(for Portales New Mexico) and south (for Mitchell, Australia) are the result of the GPS satellite 
inclination angle and the station latitudes. The length of the ellipses depends on the height of the 
antenna above the surface - so a height of 2 meters gives an ellipse that is smaller than one 
that is 10 meters. In this case we used 2 meters for both sites - and these are pretty 
simple GNSS-IR sites. The surfaces below the GPS antennas are fairly smooth soil and that 
will generate coherent reflections. In general, you can use all azimuths at these sites.  
<P>
<P>
Now let's look at a more complex case, station <code>ross</code> on Lake Superior. Here the goal 
is to measure water level. The map image (panel A) makes it clear
that unlike Mitchell and Portales, we cannot use all azimuths to measure the lake. To understand our reflection 
zones, we need to know the approximate lake level. That is a bit tricky to know, but the 
photograph (panel B) suggests it is more than the 2 meters we used at Portales - 
but not too tall. We will try 4 meters and then check later to make sure that was a good assumption.  
</P>

<p align=center>
<table align=center>
<TR>
<TD>A. <img src=https://raw.githubusercontent.com/kristinemlarson/gnssrefl/master/tests/use_cases/ross-google.jpg width=300> <BR>
Map view of station ROSS </TD>
<TD>B. <img src=https://gnss-reflections.org/static/images/ROSS.jpg width=300> <BR>
Photograph of station ROSS</TD>
</TD>
</TR>
<Tr>
<TD>C. <img src=https://raw.githubusercontent.com/kristinemlarson/gnssrefl/master/tests/use_cases/ross-first.jpg width=300><BR>
Reflection zones for GPS satellites at elevation <BR>angles of 5-25 degrees 
for a reflector height of <BR>4 meters.</TD> 
<TD>D. <img src=https://raw.githubusercontent.com/kristinemlarson/gnssrefl/master/tests/use_cases/ross-second.jpg width=300><BR>
Reflection zones for GPS satellites at elevation <BR>angles of 5-15 degrees 
for a reflector height of <BR>4 meters.  </TD>
</Tr>
</table>
</p>

Again using the reflection zone web app, we can plot up the appropriate reflection zones for various options.
Since <code>ross</code> has been around a long time, [http://gnss-reflections.org](https://gnss-reflections.org) has its coordinates in a 
database. You can just plug in <code>ross</code> for the station name and leave 
latitude/longitude/height blank. You *do* need to plug in a RH of 4 since mean 
sea level would not be an appropriate reflector height value for this 
case. Start out with an azimuth range of 90 to 180 degrees.
Using 5-25 degree elevation angles (panel C) looks like it won't quite work - and going all the way to 180 degrees
in azimuth also looks it will be problematic. Panel D shows a smaller elevation angle range (5-15) and cuts 
off azimuths at 160. These choices appear to be better than those from Panel C.  
It is also worth noting that the GPS antenna has been attached to a pier - 
and *boats dock at piers*. You might very well see outliers at this site when a boat is docked at the pier.

Once you have the code set up, it is important that you check the quality of data. This will also 
allow you to check on your assumptions, such as the appropriate azimuth and elevation angle 
mask and reflector height range. This is one of the reasons <code>quickLook</code> was developed. 

<HR>

### Utilities <a name="helper"></a>

<code>download_rinex</code> can be useful if you want to 
download RINEX v2.11 or 3 files (using the version flag) without using 
the reflection-specific codes. As with <code>rinex2snr</code>, the default archive is 
to check unavco, sopac, and sonel in that order. For other archives, you must specify their name.
For a listing of supported archives, please see the documentation for [rinex2snr](docs/rinex2snr.md).

Sample calls:

- <CODE>download_rinex p041 2020 6 1</CODE> downloads the RINEX 2.11 data from June 1, 2020

- <CODE>download_rinex p041 2020 150 0</CODE> downloads the data from day of year 150 in 2020

- <CODE>download_rinex p041 2020 150 0 -archive sopac</CODE> downloads the data from sopac archive on day of year 150 in 2020

- <CODE>download_rinex onsa00swe 2020 150 0 -archive cddis</CODE> downloads the RINEX 3 data 
from the cddis archive on day of year 150 in 2020

<code>download_orbits</code> downloads orbit files and stores them in $ORBITS. The list of orbits 
we support changes regularly. Please see the [rinex2snr documentation](docs/rinex2snr.md).

<code>ymd</code> translates year,month,day to day of year

<code>ydoy</code> translates year,day of year to month and day

<code>llh2xyz</code> translates latitude (deg), longitude (deg), and ellipsoidal ht (m) to X, Y, Z (m)

<code>xyz2llh</code> translates Cartesian coordinates (meters) to latitude (deg), longitude (deg), ellipsoidal height (m)

<code>gpsweek</code> translates year, month, day into GPS week, day of week (0-6) 
   
<code>download_unr</code> downloads ENV time series for GPS sites from the Nevada Reno website (IGS14), so ITRF 2014. Input is 
four character station name. Lowercase.

<code>download_tides</code> downloads up to a month of NOAA tide 
gauge data given a station number (7 characters), and begin/end dates, e.g. 
20150601 would be June 1, 2015. The NOAA API works perfectly well for this,
but this utility writes out a file with only columns of 
numbers (or csv if you prefer). To implement the latter, use csv as the ending 
of your output filename.
This can also be called as <code>download_noaa</code>; there is an optional plot produced with -plt T.

<code>download_psmsl</code> downloads sealevel files from the 
[Permanent Service for Mean Sea Level](https://www.psmsl.org/data/gnssir/map.php). 
Input is the station name. Ouput can be plain txt of csv. To implement the 
latter, use csv as the ending of your output filename. Optional plot to the screen if -plt is set to T.

<code>download_ioc</code> downloads up to a month of tide gauge records from the 
[IOC website](http://www.ioc-sealevelmonitoring.org/). Requires beginning and 
ending date (yyyymmdd format) and is limited by the IOC to 30 days. Optional output filename allowed. 
If the output file ends in csv, it writes a csv file instead of plain text.
You can pick the sensor type or you will get all of them. 
There is an optional plot produced with -plt T.

<code>query_unr</code> returns latitude, longitude, and ellipsoidal height and Cartesian position 
for stations that were in the Nevada Reno database as of October 2021. Coordinates are now more precise 
than they were originally (UNR used to provide four decimal points in lat/long). 

<code>check_rinex</code> returns simple information from the file header, such as receiver
and antenna type, receiver coordinates, and whether SNR data are in the file. RINEX 2.11 only

<code>prn2gps</code> will try to tell you which PRN numbers are associated with which SVN (or GPS) numbers 
for a given day, as in <code>prn2gps 2021-01-01</code>. 
It uses the public [JPL](https://sideshow.jpl.nasa.gov/pub/gipsy_products/gipsy_params/PRN_GPS.gz) translation file, so if that file
is no good, the translation will also be no good.  

<HR>

### GNSS-IR Community <a name="weneedhelp"></a>

**We need help to maintain and improve this code. How can you help?**

- Archives are *constantly* changing their file transfer protocols. If you 
find one in <code>gnssrefl</code> that doesn't work anymore,
please fix it and let us know. Please test that it 
works for both older and newer data.

- If you would like to add an archive, please do so. Use the existing code in gps.py as a starting point. 

- We need better models for GNSS-IR far more than we need more journal articles finding that the 
method works. And we need these models to be in python. 

- I would like to add a significant wave height calculation to this code. If you have such code that 
works on fitting the spectrum computed with detrended SNR data, please consider contributing it.

- If you have a better refraction correction than we are using, please provide it to us as a function in python.

- Write up a new [use case](https://github.com/kristinemlarson/gnssrefl/blob/master/tests/first_drivethru.md).

- Investigate surface related biases for polar tide gauge calculations (ice vs water).

- I have ported NOCtide.m and will add it here when I get a chance.

**How to get help with your gnssrefl questions?**

If you are new to the software, you should consider watching the 
[videos about GNSS-IR](https://www.youtube.com/playlist?list=PL9KIPkLxL-c_d-NlNsaoGgScWqSxxUB5n)

Before you ask for help - a few things to ask yourself:

Are you running the current software?

- gnssrefl command line  <code>git pull </code>

- gnssrefl docker command line  <code>docker pull unavdocker/gnssrefl</code>

- gnssrefl jupyter notebook  <code>git pull</code>

- gnssrefl jupyter notebook docker <code>docker pull unavdocker/gnssrefl_jupyter</code>

You are encouraged to submit your concerns as an issue to 
the [github repository](https://github.com/kristinemlarson/gnssrefl). If you are unfamiliar 
with github, you can also email Kelly (enloe@unavco.org ) about Jupyter 
NoteBooks or Tim (dittmann@unavco.org) for commandline/docker issues.

Please

- include the exact command or section of code you were running that prompted your question.

- Include details such as the error message or behavior you are getting. 
Please copy and paste (this is preferred over a screenshot) the error string. 
If the string is long - please post the error string in a thread response to your question.

- Please include the operating system of your computer.

*Please wait - We are confirming whether this information is correct.*
Would you like to join our <code>gnssrefl</code> users email list?
Send an email to gnss-ir-request@postal.unavco.org and put the word
subscribe (or unsubscribe to leave) in your email subject.


<HR>

**Acknowledgements**  

- [Radon Rosborough](https://github.com/raxod502) helped with 
python/packaging questions and improved our docker distribution. 
- [Naoya Kadota](https://github.com/naoyakadota) added the GSI data archive. 
- Joakim Strandberg provided python RINEX translators. 
- Johannes Boehm provided source code for the refraction correction. 
- At UNAVCO, Kelly Enloe made Jupyter notebooks and Tim Dittmann made docker builds. 
- Makan Karegar added the NMEA capability.
- Dave Purnell provided his inversion code, which is now running in the <code>invsnr</code> capability.  
- Carolyn Roesler helped with the original Matlab codes.
- Felipe Nievinski and Simon Williams have provided significant advice for this project.
- Clara Chew and Eric Small developed the soil moisture algorithm; I ported it to python with Kelly's help.

Kristine M. Larson

[https://kristinelarson.net](https://kristinelarson.net)


GNSS-IR was developed with funding from NSF (ATM 0740515, EAR 0948957, AGS 0935725, EAR 1144221, AGS 1449554) and 
NASA (NNX12AK21G and NNX13AF43G). <code>gnssrefl</code> was developed with support from NASA (80NSSC20K1731).

This documentation was updated on September 10, 2022
<HR>


**File structure for station abcd in the year YYYY (last two characters YY), doy DDD:**

- REFL_CODE/input/abcd.json - instructions for gnssir analysis, refraction files

- REFL_CODE/YYYY/snr/abcd/abcdDDD0.YY.snr66  - SNR files 

- REFL_CODE/YYYY/results/abcd/DDD.txt  Lomb Scargle analysis 

- REFL_CODE/YYYY/phase/abcd/DDD.txt  phase analysis 

- REFL_CODE/Files/ - various output files and plots will be placed here

- ORBITS/YYYY/nav/autoDDD0.YYn - GPS broadcast orbit file 

- ORBITS/YYYY/sp3/ - sp3 files of orbits - these use names from the archives.

RINEX files are not stored by this code. In fact, quite the opposite. If they are being translated, 
they are deleted. Do not keep your only copy of RINEX files in your default directory.


