## Steenbras Dam, Lower

Station Name: sbas

Latitude: -34.18704704

Longitude: 18.84986166

Ellipsoidal Height(m): 403.342

Network: TRIGNET

Archive: UNAVCO (use the special option)

<img src=https://gnss-reflections.org/static/images/SBAS.jpg width=500>

I am pretty sure that this site is now tracking Glonass, but the files currently available 
from UNAVCO are GPS only. So for now that is the use case we will discuss.

### Reflection Zones 

Use the reflection zone web app to think about which azimuths and elevation angles ot use.
Note the photograph!  **You are not 6 meters from the water.**

### Evaluate the Data

<code>quickLook sbas 2020 1 -e1 5 -e2 10 -h1 20 -h2 35 -azim1 0 -azim2 90 </code>

<img src=sbas-quicklook2.png width=600 />

### Estimate Lake Level

Make the SNR files:

<code>rinex2snr sbas 2020 1 -doy_end 366 -archive special</code>

Save your analysis strategy:

<code>make_json_input sbas 0 0 0 -e1 5 -e2 12 -h1 15 -h2 35 -peak2noise 3</code>

Edit the file to restrict azimuths to 0-80 degrees.

Estimate reflector height :

<code>gnssir sbas 2021 1 -doy_end 366</code>

If you use -plt T on that command 

<img src=sbas-l1.png width=600/>	

<img src=sbas-l2.png width=600 />

Compute a daily average:

<code>daily_avg sbas 0.25 10</code>

Number of available values per day:

<img src=sbas_4.png width=600 />

<img src=sbas_2.png width=600 />

Compare with in situ data:

sbas_use.md




https://www.dws.gov.za/Hydrology/Weekly/ProvinceWeek.aspx?region=WC


https://www.dws.gov.za/Hydrology/Verified/HyData.aspx?Station=G4R001100.00&DataType=Point&StartDT=2020-01-01&EndDT=2020-12-31&SiteType=RES
