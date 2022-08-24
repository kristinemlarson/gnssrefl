### P038

**Station Name:** 	p038

**Location:** Portales, NM, USA

**Archive:** [UNAVCO](http://www.unavco.org)

**Ellipsoidal Coordinates:**

- Latitude: 34.14726 degrees

- Longitude: -103.40734 degrees

- Height: 1212.982 meters

[Station Page at UNAVCO](https://www.unavco.org/instrumentation/networks/status/nota/overview/P038)

[Google Maps Link](https://www.google.com/maps/place/34%C2%B008'50.1%22N+103%C2%B024'26.4%22W/@34.14725,-103.4073333,17z/data=!3m1!4b1!4m5!3m4!1s0x0:0x64e449f205085274!8m2!3d34.14725!4d-103.4073333) 

<p align=""center>
<img src="p038.png" width="500"/>
</P>
 
### Analyze the Data
P038 was a PBO site. The data from 2017 will be analyzed here as a test case.  
We fist start by analyzing the data using the GNSS-IR process. 
Then we will use the results gathered to run the soil moisture code.

#### Step 1: GNSS-IR
Begin by generating the SNR files. Although typically PBO sites do not have L2C 
data in their low-rate RINEX files, UNAVCO is providing these data in the "special" archive section
so that people can test out this code.

<code>rinex2snr p038 2017 1 -doy_end 365 -archive special</code>


Analysis parameters are set up with <code>make_json_input</code>. While ordinarily you need to input 
the station latitude, longitude, and ellipsoidal height, if the station is in the <code>gnssrefl</code> database, you can 
put zero values there instead.

<code>make_json_input p038 0 0 0 -l2c true</code>

The json file is saved at $REFL_CODE/input/p038.json

Now run <code>gnssir</code> to save the reflector height (RH) output for each day in 2017.

<code>gnssir p038 2017 1 -doy_end 365 </code>

The daily output files are stored in $REFL_CODE/2017/results/p038

#### Step 2: Soil Moisture

[Please read the soil moisture user manual.](../../docs/README_vwc.md).  It is very short and has a lot of tips that will save you time.

We need a list of satellite tracks to use:

<code>vwc_input p038 2017</code>

This creates a file that goes in $REFL_CODE/input/p038_phaseRH.

Now estimate the phase:

<code>phase p038 2017 1 -doy_end 365</code>

Finally, convert the phase to volumetric water content:

<code>vwc p038 2017</code>


 <br />
<img src="p038_azim.png" width="600">
 <br />
<img src="p038_daily_phase.png" width="500">
 <br />
<img src="p038_phase_vwc_result.png" width="600">
 <br />
<img src="p038_vol_soil_moisture.png" width="600">


