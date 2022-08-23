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
The data from 2017 will be analyzed here as a test case.  
We fist start by analyzing the data using the GNSS-IR process. 
Then we will use the results gathered to run the soil moisture code.

#### Step 1: GNSS-IR
Begin by generating the SNR files:
Use the highrate option and decimate to 15 seconds - this is required to get the L2C data.

<code>rinex2snr p038 2017 1 -doy-end 365 -rate high -dec 15</code>

The resulting SNR files are stored in $REFL_CODE/2017/snr/p038.

Analysis parameters are set up with <code>make_json_input</code>

<code>make_json_input p038 34.14726 -103.40734 1212.982 -l2c true</code>

The json file is saved at $REFL_CODE/input/p038.json

Now run <code>gnssir</code> to save the reflector height (RH) output for each day in 2017 and set the frequency to l2c.

<code>gnssir p038 2017 1 -doy_end 365 -fr 20</code>

The daily output files are stored in $REFL_CODE/2017/results/p038

#### Step 2: Soil Moisture

For this python version we can come up with a good reflector height (RH) value for each satellite in each quadrant by using the RH values you will have estimated.
And we will define "good arcs" by successful RH estimates.
Run **apriori** for the year of 2017:

<code>apriori p038 2017</code>

This creates a file that will go in $REFL_CODE/input/p038_phaseRH.
For each GPS satellite (column 3), a RH (meters) is given in column 2. The azimuth is column 4, 
number of retrievals in column 5, and then the azimuths in the last two columns.
This file can be hand edited if you find out later one arc is not working.  
To comment lines out you use %. [This is what the file should look like.](p038_phaseRH.txt)

The phase analysis code - **quickphase** - will use that file to restrict the number of satellite arcs that are used.
Run quickphase for the entire year of 2017:

<code>quickphase p038 2017 1 -doy_end 365</code>

The results of quickphase will be one file per day requested, saved as doy.txt (ex: 365.txt).
In this case, one file for every day of the year 2017. These results will be saved in the directory $REFL_CODE/2017/phase/p038.

Finally, we can run soil moisture code which is called **plotphase**.

<code>plotphase p038 2017</code>

plotphase will produce some QC type plots, daily phase, phase w/ vegetation correction, vwc, and soil moisture plots. 
all plots are saved in the directory $REFL_CODE/Files as p038_az_phase.png, p038_daily_phase.png,
p038_phase_vwc_result.png, and p038_vol_soil_moisture.png

The daily phase results go to $REFL_CODE/Files/p038_phase.txt. [Example](p038_phase.txt)
Then it converts those to VWC using the Clara Chew derived algorithms.
The output goes in the same place as phase: $REFL_CODE/Files/p038_vwc.txt. [Example](p038_vwc.txt)
 <br />
<img src="p038_azim.png" width="600">
 <br />
<img src="p038_daily_phase.png" width="500">
 <br />
<img src="p038_phase_vwc_result.png" width="600">
 <br />
<img src="p038_vol_soil_moisture.png" width="600">


