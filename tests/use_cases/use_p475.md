### P475

This use case is not finished.  

**Station Name:** 	p475

**Location:** San Diego, CA, USA

**Archive:** [UNAVCO](http://www.unavco.org)


[Station Page at UNAVCO](https://www.unavco.org/instrumentation/networks/status/nota/overview/P475)

<p align="center">
<img src="p038.png" width="500"/>
</P>
 
P475 was a PBO site. Soil moisture can be extracted, but it is a challenging case.  
To access L2C from the original dataset, 1-Hz data must be downloaded and decimated. To avoid 
having to do this, we will only use data from the Septentrio receiver. We will look at the years 2020 and 2021.

#### Step 1: GNSS-IR


<code>rinex2snr p475 2020 1 -doy_end 366 -archive unavco -year_end 2021</code>

The analysis parameters are set up with <code>make_json_input</code>. While ordinarily you need to input 
the station latitude, longitude, and ellipsoidal height for this code, if the station is in the <code>gnssrefl</code> database, you can 
put zero values there instead. We only need the L2C data, so have set the parameter accordingly.

<code>make_json_input p475 0 0 0 -l2c true</code>

Now we run <code>gnssir</code>. This will be needed for estimate *a priori* reflector heights for the soil moisture code.

<code>gnssir p038 2017 1 -doy_end 365 </code>


#### Step 2: Soil Moisture

[Please read the soil moisture user manual.](../../docs/README_vwc.md) It is very short and has a lot of tips that will save you time.

We need a list of satellite tracks to use:

<code>vwc_input p475 2020</code>

Now we estimate the phase for each satellite track on each day in 2020 and 2021:

<code>phase p475 2017 1 -doy_end 366 -year_end 2021</code>

Finally, convert the phase to volumetric water content:

<code>vwc p475 2020 -year_end 2021</code>

Phase results plotted in geographic coordinates:



Kristine M. Larson September 14, 2022
