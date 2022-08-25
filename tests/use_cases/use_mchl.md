### MCHL

**Station Name:** 	mchl (mchl00aus)

**Location:** Walhallow, Queensland, Austalia

**Ellipsoidal Coordinates:**

- Latitude: -26.359 degrees

- Longitude: 148.145 degrees

- Height: 534.591 meters

[Station Page at Nevada Geodetic Laboratory](http://geodesy.unr.edu/NGLStationPages/stations/MCHL.sta)

[Google Maps Link](https://www.google.com/maps/place/26%C2%B021'32.4%22S+148%C2%B008'42.0%22E/@-26.359,148.145,11z/data=!4m5!3m4!1s0x0:0x9200f9ebb23ec5b1!8m2!3d-26.359!4d148.145?hl=en) 

<p align=center>
<img src=MCHL.jpeg>
</p>
 
Read the [soil moisture instructions](../../docs/README_vwc.md)!

#### Step 1: GNSS-IR
Begin by generating the SNR files.
To be sure we can get the L2C data, we will use the RINEX 3 files.
These require the longer station name (mchl00aus) and are available at either cddis or ga.
Choose the one that is less slow for you.

<code>rinex2snr mchl00aus 2017 1 -doy_end 365 -year_end 2018 -archive cddis </code>

Use <code>quickLook</code> with the l2c frequency to give a look to the data quality.
Then set up your parameters with <code>make_json_input</code>

<code>make_json_input mchl 0 0 0 -l2c true</code>

Modify the azimuths in the json if you feel that is needed.

Now run the <code>gnssir</code> each day in 2017 and 2018:

<code>gnssir mchl 2017 1 -doy_end 365 -year_end 2018</code>

#### Step 2: Soil Moisture

<code>vwc_input mchl 2018</code>

This creates a file that will go in $REFL_CODE/input/mchl_phaseRH.txt

This file can be hand edited if you find out later one arc is not working.  
To comment lines out you use %. 

Run phase for the entire year of 2017:

<code>phase mchl 2017 1 -doy_end 365 -year_end 2018</code>

The results will be one file per day requested. The location of the output is printed to the screen.

Finally, the <code>vwc</code> module compiles all the data in the requested years and generates volumetric water content.

<code>vwc mchl 2017 -year_end 2018</code>


Raw phases in geographic quadrants
 <br />
<img src="mchl_1.png" width="600">
 <br />
Daily phase averages
 <br />
<img src="mchl_2.png" width="500">
 <br />
Modeling Results
 <br />

<img src="mchl_3.png" width="600">
 <br />
 Final VWC:
 <br>
<img src="mchl_4.png" width="600">


