### Soil Moisture

Our soil moisture code is based on many years of experiments, models, and publications
by Eric Small, Clara Chew, John Braun, Kristine Larson, Valery Zavorotny, and Felipe Nievinski.
We cannot possibly describe all that work here - but attempt to give some context to why 
decisions are made as they are.  Please look for the publications [here](https://www.kristinelarson.net/publications/).


Will your site be a good soil moisture site?  This is almost entirely based on how flat your site is.
Flat is good. You can use a DEM, if you have it, or a photograph.  


### 1. Analyze the reflection characteristics of your site

Our soil moisture algorithm depends on initial reflector height values derived from 
the [traditional reflector height method](gnssir.md). We need to use the average of the snow-free RH values
for a given year. When this method was demonstrated for a large network in the wesetern US (PBO H2O), we 
were also estimating snow depth. This allowed us to easily identify and remove snow-contaminated values from
our soil moisture estimates. **We are no longer running the PBO H2O network** and thus this code will first
be tested on sites where it does not snow or does not snow very often. You need to take these initial steps:

- [Generate the SNR files](rinex2snr.md)

- [Take a quick look at the data](quickLook.md)

- [Estimate reflector heights](gnssir.md)


### 2. Estimate Phase 

For reasons described by Clara Chew in her [first paper](https://www.kristinelarson.net/wp-content/uploads/2015/10/Chew_etal_Proof.pdf), 
we use phase instead of RH or amplitude to derive soil moisture. We need to know which satellites to use. You should 
use <code>vwc_input</code> to pick the satellite tracks. 
The default will be to use L2C signals which is what was used by PBO H2O. 
The code will ask that you pick the year that you think has the most L2C satellites (usually the latest year).

This creates a file that will go in $REFL_CODE/input/ssss_phaseRH.txt where ssss is your station name.
If you want to remove certain azimuths, just delete or comment out those azimuths (use a %).

Estimate the phase for the years 2017 through 2020 for station ssss:

<code>phase ssss 2017 1 -doy_end 365 -year_end 2020 </code>

This will produce color plots for the four geographic regions (northwest, northeast, etc):


 <br />
<img src="../tests/use_cases/p038_azim.png" width="600">
 <br />

If you have previously run the code it will attempt to warn you about bad satellite tracks.
The main output of this code is a daily average of the phase data. 

Can you measure phase (and thus soil moisture) more often than once per day? Of course you can. We routinely
measured it twice/day with a limited constellation. Now that L2C has 24 satellites, it would be straightforward 
to estimate it four times/day. By also using the L1 signal, one could perhaps push that temporal resolution even further.


### 3. Estimate VWC

As described by Clara Chew in her follow up publications, vegetation can have a significant impact on the phase results 
and must be modeled.  We follow a multi-stage process - we change units from phase (degrees) to VWC, 
we model and remove the vegetation effect, and then we "level" the data using soil texture profiles for your site.
Currently we set the minimum soil moisture value to 5%.

<img src="../tests/use_cases/p038_smc_models.png" width="600">
 <br />

Final Result:

<img src="../tests/use_cases/p038_vwc.png" width="600">


