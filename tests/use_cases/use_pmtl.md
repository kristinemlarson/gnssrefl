### St Lawrence River

<p align=center>
<img src="https://webapp.geod.nrcan.gc.ca/cacs/PMTL_MONU.jpg" width="500"/>
</p>

To the best of our knowledge, we are now longer allowed access to the high-rate data streams
needed to do reflectometry at this site. NRCAN has stated that they are working to allow access 
to these data. If you would like to make further inquiries, please contact NRCAN.

**Station Name:**  pmtl

**Location:** Port de Montreal, Montreal, Canada

**Archive:**  [NRCAN](https://www.nrcan.gc.ca/home)

**Ellipsoidal Coordinates:**

- Latitude: 45.557

- Longitude: -73.520

- Height: 54.073 m

[Station Page at Natural Resources Canada](https://webapp.geod.nrcan.gc.ca/geod/data-donnees/station/report-rapport.php?id=M0722900)

[Station Page at Nevada Geodetic Laboratory](http://geodesy.unr.edu/NGLStationPages/stations/PMTL.sta)

[Google Map Link](https://goo.gl/maps/FoJ68HDT2KZ6KnZc7)


### Data Summary

Station PMTL is located on the Viterra Montreal Terminal building on the St Lawrence River in Montreal, Canada. It is operated by the Montreal Port Authority.

GPS L1 and Glonass L1 and L2 can be used for this site. Since the site is more than 60 meters above the water, you need to use high-rate GNSS data. Because of the way that NRCAN stores these data, you need to install <code>teqc</code>.

Note the [ellipsoidal height and geoid corrected height](https://gnss-reflections.org/geoid?station=pmtl). To pick an azimuth and elevation mask, try the [reflection zone webapp](https://gnss-reflections.org/rzones) with station name pmtl, varying elevation angles, and different azimuth limits. Here is one effort:

<P align=center>
<img src="pmtl_rzone.png" width="500" />
</P>

### quickLook

Make a SNR file for multi-GNSS and high-rate:

<code>rinex2snr pmtl 2020 330 -archive nrcan -rate high -orb gnss</code>


<code>quickLook pmtl 2020 330 -h1 40 -h2 90 -e1 5 -e2 12</code>

<img src="pmtl-first-try.png" width="600"/>

I have annotated this <code>quickLook</code> periodogram to point out that there is an outlier in the SW region. 
You can also see that the NW region is useless, which is what we should expect. 
Windowing down the reflector region and using day of year 270:

<img src=pmtl-lsp-75-85.png width=600>

The QC plot gives the azimuth windows - and help on setting the required amplitude and peak to noise ratio.
Retrievals are not returned near 90 degrees because of the satellite inclination and the way the azimuth regions are defined in <code>quickLook</code>. It does not mean there are obstructions in that direction.

<img src=pmtl-qc-75-85.png width=600>


### Analyze the Data

Set up analysis instructions, using a smaller RH region: 

<code>make_json_input pmtl 45.5571 -73.5204 54.073 -h1 75 -h2 85 -e1 5 -e2 12 -allfreq True -peak2noise 3 -ampl 7</code>

Hand-edit the json to remove GPS L2C, GPS L5, and Galileo data, and to set your azimuth region. [Sample json](pmtl.json)

Make the SNR files (this takes a long long time):

<code>rinex2snr pmtl 2020 270 -doy_end 300 -archive nrcan -rate high -orb gnss</code>

This is also slow - though not as slow as translating RINEX files and computing orbits:

<code>gnssir pmtl 2020 270 -doy_end 300</code>

One way to make the gnssir code run faster would be to loosen up the RH precision.  Since you 
are using daily averages, it is not necessary to use the default of 5 mm.  10 mm would suffice.
This needs to be hand-edited in the json file.

Now compute daily averages:

<code>daily_avg pmtl 2020 0.25 50 -txtfile pmtl-rh.txt </code>

All tracks:

<img src=pmtl-all.png width=600>

The daily average:

<img src=pmtl_RH.png width=600>

[Daily average RH file](pmtl-rh.txt)

### Accuracy

The Canadian Hydrographic Service within Fisheries and Ocean Canada operates tide gauges along the St Lawrence 
River, the closest of which is Montreal Jetee #1 (station 15520), about 1 km south of the GNSS site. 
Tide data can be [downloaded](https://www.isdm-gdsi.gc.ca/isdm-gdsi/twl-mne/inventory-inventaire/interval-intervalle-eng.asp?user=isdm-gdsi&region=PAC&tst=1&no=15520). Use the daily mean water level and UTC when submitting a request and download the resulting csv file. 

For this use case, the tidal data have already been [downloaded](pmtl.csv). 
Given that there is quite drastic water level changes within a day, it is entirely
plausible that the correlation will improve if using the subdaily RH and hourly tide gauge data.

<img src=pmtl-compare-time.png width=600>

<img src=pmtl-correlation.png width=600>


[Code for comparison](pmtl_usecase.py)


