## snowdepth

In order to estimate snow depth, you should first run <code>daily_avg</code>.
This utility changes these average reflector height values to snow depth using the procedures
used in PBO H2O. The assumptions are:

- you set the "no snow" or "bare soil" values using data from the fall (in the northern hemisphere)
- negative snow depth is not allowed!
- snow depth < 0.05 is set to zero as these small values are close to the resolution of the method.
- we do not estimate snow depth after June 30. This is purely a practical constraint as most 
of the GNSS sites where we tested the method did not have snow cover then. 

The current required inputs are :

- station name
- water year

You have two choices. The default model calculates an azimuth specific bare soil reflector height every 
20 degrees in azimuth and removes that as the bare soil value for that azimuth range.  The "simple" algorithm simply treats
them all the same (this was the first version released).  So if you were measuring RH from 90 to 270 degrees, 
the simple version would average all the bare soil values together.  This would be perfectly fine if a site 
is fairly horizontal. It would be perfectly fine to add more inputs (like setting 
azimuth ranges to smaller or larger azimuth increments). I will leave that
to the community to make as a PR.

Optional inputs include:

- set the y-axis limits for snow depth (minS, maxS) 
- set the "bare soil" dates(-bare_date1, bare_date2). The defaults are September 1-September 30 
from the fall. The format is year, numerical month, numerical day: 2020-09-01.
- set longer to True for time series to span August 1 through June 30. Otherwise you see October 1-June 30.
- set plt to False if you do not want the plot sent to the screen

The error bars are **over-estimates** and based on the standard deviation of the 
reflector heights used in the daily average. These include terrain errors as well 
as snow depth errors.

There is a SWE module that is currently written in matlab. If you are willing to port it to
python, we would be happy to add it to this respository. Please contact us directly.

PBO H2O snow depth products were based on L2C data. This utility allows multi-GNSS retrievals.
For further reading, [search for the word snow on this page](https://www.kristinelarson.net/publications/).

You might be interested to compare your GNSS-IR results with 
SNODAS or [SNOTEL](https://data.nal.usda.gov/dataset/snowpack-telemetry-network-snotel).
**However**, there are no SNOTEL data that will agree with GNSS-IR because they do not 
have the same footprint. Furthermore, the two sensors are rarely close enough to 
each other or in the same treecover. SNODAS is a **model** - and for that reason alone 
you should never expect it to agree with GNSS-IR.

There are certainly other ways you can convert reflector heights to snow depth. And 
some of the L1 reflector height retrievals from some receivers are extremely problematic.  
When you see large gaps at PBO sites in winter this is most likely because the site was 
not designed to operate when snow covers the solar panels. In other cases the GPS receiver failed and was 
not repaired until the following spring. GPS/GNSS instruments can of course operate throughout the winter - but it does 
require that that be a design goal. 
