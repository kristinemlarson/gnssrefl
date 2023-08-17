# Michipicoten, Lake Superior 


Updated December 11, 2022

## metadata

**Station Name:** 	mchn

**Location:** Michipicoten Harbor, Ontario, Canada

**Archive:**  [SOPAC](http://sopac-csrc.ucsd.edu/index.php/sopac/) 

**Ellipsoidal Coordinates:**

- Latitude: 47.961

- Longitude: -84.901

- Height: 152.019 m

[Station Page at Natural Resources Canada](https://webapp.geod.nrcan.gc.ca/geod/data-donnees/station/report-rapport.php?id=M093001)

[Station Page at Nevada Geodetic Laboratory](http://geodesy.unr.edu/NGLStationPages/stations/MCHN.sta)

[Google Maps Link](https://goo.gl/maps/mU5GbsvMsLfe5buQ7) 

<p align=center>
<img src="../_static/mchn_monu-cors.png" width="500"/>
</P>

### Data Summary

Station mchn is operated by [NRCAN](https://www.nrcan.gc.ca/home).
The station overlooks Lake Superior in a favorable location for measuring seasonal water levels.
This site only tracks legacy GPS signals. 

More information on mchn can be obtained 
from the [GNSS-IR Web App](https://gnss-reflections.org/api?example=mchn),
where mchn is one of the test cases. 

For GNSS reflectometry, you need to set an azimuth and elevation angle mask.
The azimuths are chosen to ensure that the reflected signals reflect off the surface of interest.
[Here is a good start on an elevation and azimuth angle mask](https://gnss-reflections.org/rzones?station=mchn&msl=on&RH=7&eang=2&azim1=80&azim2=180). 


### Reproduce the Web App

**Make SNR File** 

If you know where the data are stored (i.e. sopac), it is better (faster) to set that flag.
Since the receiver only tracks GPS signals, there is no need to specify gnss orbits.

<code>rinex2snr mchn 2019 205 -archive sopac</code>

**Take a Quick Look at the Data**

Examine the spectral characteristics of the SNR data for the default settings
[(For details on quickLook output.)](../pages/quickLook.md):

<code>quickLook mchn 2019 205</code>

<img src="../_static/mchn-example.png" width="600">

Why does this not look like the results from the web app? Look closely at the station photo and the x-axis 
of the periodograms, then change the range of reflector heights at the command line for **quickLook**:

<code>quickLook mchn 2019 205 -h1 2 -h2 8</code>

<img src="../_static/qc-mchn-1.png" width="600">

Also look at the QC metrics:

<img src="../_static/qc-mchn-2.png" width="600">

The water is ~6.5 meters below the antenna. You can see from the top plot that the good retrievals (in blue) 
very clearly show you which azimuths are acceptable and which are not.  The middle plot shows the peak to noise 
ratio, which we would like to at least exceed 3. And here again, the bad retrievals are always below this level.
The amplitudes in the bottom plot indicate that 8 is an acceptable minimal value.

### Analyze the Data

The data from 2013 will be analyzed here as a test case.  Begin by generating the SNR files:

<code>rinex2snr mchn 2013 1 -archive sopac -doy_end 365 </code>

The resulting SNR files are stored in $REFL_CODE/2013/snr/mchn.  

Analysis parameters are set up with <code>gnssir_input</code> using the default receiver location:

<code>gnssir_input mchn  -h1 3 -h2 10 -e1 5 -e2 25 -l1 T -peak2noise 3 -ampl 8 -azlist2 80 180</code>

Although it is possible to get good reflections beyond an azimuth of 180 degrees, the 
photographs suggest barriers are present in that region.  

Now that the analysis parameters are set, run <code>gnssir</code> to save the reflector height (RH) output for each day in 2013.

<code>gnssir mchn 2013 1 -doy_end 365 </code>

The daily output files are stored in $REFL_CODE/2013/results/mchn. [Here is an example output for a single day.](195.txt) 
Plots of SNR data can be seen with the -plt option.

<code>gnssir mchn 2013 195  -plt True </code>

<img src="../_static/mchn-g-l1.png" width="500">

For a lake, it is appropriate to use the daily average. Our utility for computing a daily average requires a value
for the median filter and a minimum number of tracks.  If the median value is set to the be large (2 meters), you can see 
large outliers: 

<code>daily_avg mchn 2 10</code>

<img src="../_static/mchn_1.png" width="500">

A more reasonable result is obtained with a 0.25-meter median filter and the 12-track requirement. If you want to save 
the daily averages to a specific file, use the -txtfile option. Otherwise it will use a default location (which is printed to the screen)

<code>daily_avg mchn 0.25 12 -txtfile mchn-dailyavg.txt</code>

<img src="../_static/mchn_3.png" width="500">

[Sample daily average RH file.](mchn-dailyavg.txt)

The number of tracks required will depend on the site. Here the azimuth is restricted because  of the location of the antenna.
Please note that these reflections are from ice in the winter and water during the summer. Surface 
bias corrections (ice, snow) will be implemented in the software in the future. Until then, please take 
this into account when interpreting the results.

There is a [tide gauge](https://tides.gc.ca/eng/Station/Month?sid=10750) at this site. The data can be 
downloaded from [this link](http://www.isdm-gdsi.gc.ca/isdm-gdsi/twl-mne/inventory-inventaire/interval-intervalle-eng.asp?user=isdm-gdsi&region=CA&tst=1&no=10750). 
Please select the daily mean water level, as there are restrictions on hourly data (more information is available on the download page). 
We have downloaded [the 2013 data](10750-01-JAN-2013_slev.csv).

The water levels measured by the traditional tide gauge and GNSS-IR are shown here:

<img src="../_static/mchn-timeseries-tide-rh.png" width="600">

The linear regression between the two series gives a slope m=-1.03. The rms of the 
residuals is very good, 0.025 m.  

<img src="../_static/mchn-linreg.png" width="600">

The [python script](plotmchn.py) used to generate these plots is provided.

### Reference

DFO (2021). Institute of Ocean Sciences Data Archive. Ocean Sciences Division. Department of Fisheries and Oceans 
Canada. http://www.pac.dfo-mpo.gc.ca/science/oceans/data-donnees/index-eng.html. Data obtained on 2021-01-28.

