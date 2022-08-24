### Soil Moisture

<img src=https://www.kristinelarson.net/wp-content/uploads/2015/10/famousFigure.png width=500>

This soil moisture code is based on many years of experiments and model development by Eric Small, Clara Chew, John Braun, Kristine Larson, Kristine Larson, and Felipe Nievinski. We cannot possibly describe all that work here - but we do attempt to give you some context to why 
we have taken various steps.  Please look to the soil moisture publications at my website [for additional details](https://www.kristinelarson.net/publications/).

Some cautionary notes:

- This algorithm only uses GPS satellites. This is because we take advantage of the repeating GPS 
ground track. There is no reason you can't use other GNSS satellites to measure soil moisture - 
but this code won't do it for you.  

- Will your site be a good soil moisture site?  This is almost entirely based on how flat your site is.
Flat is good. You can use a DEM, if you have it, or a photograph.  

- This algorithm is currently only recommended and validated for the L2C signal. It is **your responsbility** to make sure that 
your files have L2C data in them. While this is trivial with the RINEX 3 format, it can be very challenging to 
find L2C data in some older datasets and at some archives (e.g. UNAVCO). 

- For many PBO sites (but by no means all), you can find L2C data in the 
high-rate RINEX 2.11 streams at UNAVCO. However, you don't need the high-rate data for estimating soil
moisture, so I recommend you decimate to 15 seconds when you translate the RINEX file into the SNR format.

- I have generally found that people using Septentrio receivers archive the L2C data in their RINEX 2.11 files.

- We have had good success using L1 data for water level, vegetation, and snow measurements. We found them
to be unreliable for PBO H2O and never used them. We have tested our algorithms with newer receivers and still
find the data to be lacking. We do not recommend you use this soil moisture code with L1 data

- The PBO H2O algorithm was successfully validated for choke ring antennas. We will do our best 
to test more antennas as time allows. 


### 1. Analyze the reflection characteristics of your site

Our soil moisture algorithm depends on initial reflector height values derived from 
the [traditional reflector height method](gnssir.md). We need to use the average of the snow-free RH values
for a given year. When this method was demonstrated for a large network in the western US, 
[PBO H2O](https://www.kristinelarson.net/wp-content/uploads/2015/12/Larson-2016-WIRES_Water.pdf), we 
were also estimating snow depth on a daily basis. This allowed us to easily identify and remove snow-contaminated values from
our soil moisture estimates. **We are no longer running the PBO H2O network.** The goal of this module is to provide a 
way for you to measure soil moisture, but you must take responsibility for evaluating whether your site 
has snow effects. For the time being we are testing the code where it does not snow or it does not snow very often. 
Regardless, you need to take these initial steps:

- [Generate the SNR files](rinex2snr.md) For the sample case given below you can use the "special" archive.

- [Take a quick look at the data](quickLook.md)

- [Estimate reflector heights](gnssir.md)


### 2. Estimate Phase 

For reasons described by Clara Chew in her [first paper](https://www.kristinelarson.net/wp-content/uploads/2015/10/Chew_etal_Proof.pdf), 
we use phase instead of RH or amplitude to derive soil moisture. We need to 
know which satellites to use. You should use <code>vwc_input</code> to pick the best satellite tracks. 
The default will be to use rising and setting L2C satellites arcs. This is the signal we used for PBO H2O and we 
have [extensively validated its results](https://www.kristinelarson.net/wp-content/uploads/2015/12/SmallLarson_etal2016.pdf). 
The code also requires that you pick the year that you think has the most L2C satellites (by definition this will be the latest year).

This creates a file that will go in <code>$REFL_CODE/input/ssss_phaseRH.txt</code> where ssss is your station name.
If you want to remove certain azimuths, just delete or comment out those azimuths (use a %).

You then need to estimate the phase for the years in question. I will just use 2016 through 2018 for station p038:

<code>phase p038 2016 1 -doy_end 366 -year_end 2018 </code>


### 3. Estimate VWC

First stage is to give you "raw" phase results for the four geographic regions (northwest, northeast, etc)

 <br />
<img src="p038_Figure_1.png" width="700">
 <br />

If you have previously run the code it will attempt to warn you about bad satellite tracks.
You can iterate to see if removing the satellite track improved things.
You are also shown a daily average of the phase data. 

 <br />
<img src="p038_Figure_2.png" width="600">
 <br />

Second stage is to model and remove the vegetation effects:

As described by Clara Chew in her follow up publications, vegetation will have a significant impact on the phase results 
and that effect must be removed to achieve accurate soil moisture estimates. We follow a 
multi-stage process:

- change units from phase (degrees) to VWC  

- model and remove the vegetation effect from the spectral amplitudes 

- "level" the data using soil texture profiles for your site.

- do not allow nonsense soil moisture values (e.g. negative soil moisture is not allowed)

Currently we level the VWC data to 5% but we will allow that to vary by site in future versions as that value should depend on 
the soil texture at the site.

<img src="p038_Figure_3.png" width="600">
 <br />

Final stage - put it all together:

<img src="p038_Figure_4.png" width="600">

Can you measure soil moisture more often than once per day? Of course you can. We routinely
measured it twice/day at PBO H2O when there were less than 10 satellites. Now that there are 24 L2C 
transmitting satellites, it would be straightforward to estimate VWC four times/day. 

Kristine M. Larson
August 23, 2022
