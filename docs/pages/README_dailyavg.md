# daily_avg<a name="module5"></a>

Updated August 10, 2023 by Kristine Larson

<code>daily_avg</code> is a utility for people interested 
in daily averaged reflector heights, such as are used for measuring 
snow accumulation or water levels in lakes/rivers. *It is not to be used for tides!*
There are two required inputs for quality control. 

- The first is called a *median filter* value. This input helps remove
large outliers. For each day, a median RH is found. Then all values larger than the 
*median filter* value from the median RH are thrown out. 

- The second required input *ReqTracks* sets a limit for how 
many satellite arcs are considered sufficient to create a trustworth daily average. 
If you had 5 arcs, for example, you probably would not want to compare that 
with another day where 100 arcs were available. The number of tracks required 
varies a lot depending on the azimuth mask and the number of frequencies available.
If you are not sure what values to use at your GNSS site, run it once with very minimal constraints.
The code provides some feedback plots that will let you pick better values.

Notes: 

- the computed daily average value should be associated with 12:00 UTC, not midnight.   

- If you are interested in looking at subdaily variations of reflector height, you should
be using subdaily.

- No frequency biases are removed in this module. This is done in subdaily.


The outputs:

- completely raw RH that have been concatenated into a single file.  

- all RH that meet the QC criteria

- daily average RH that meet the QC criteria

The locations of the files and various plots are printed to the screen. 


I illustrate the steps you might take with station MCHN. The antenna is very close to the water, so that is good.  
But the receiver itself is operated suboptimally and only L1 GPS data can be used here.
This severely limits the number of tracks that can be used. 

I start out with almost no QC (outliers with 2 meters of the median value, only 5 satellite arcs required per day):

<code> daily_avg mchn 2 5 </code>

<p align=center>
<img width=500 src=../_static/mchn_01.png>

<img width=500 src=../_static/mchn_02.png>

<img width=500 src=../_static/mchn_03.png>
</p>


You can easily see the outliers - and that you need to use something more 
useful than 2 meters for the median filter.  I will use 0.25 meters instead.  I am also going to 
change the required tracks to 10 :

<p align=center>
<img width=500 src=../_static/mchn_05.png>
<img width=500 src=../_static/mchn_06.png>
</p>


There is also an optional plot_limits setting so you can see how close the variation of
the measurements is with respect to your choices. I will also tighten the median filter a bit:

<code> daily_avg mchn 0.20 10 -plot_limits T </code>

You can see that at least visually, this makes no change in the daily averages and suggests one could
make it even smaller.  

<p align=center>
<img width=500 src=../_static/mchn_07.png>
<img width=500 src=../_static/mchn_08.png>
</p>


I hope this module is helpful for you. If it is not, there is certainly nothing 
wrong with doing your own QC using another software tool such as Matlab.

There is a [use case for this site](https://gnssrefl.readthedocs.io/en/latest/use_cases/use_mchn.html) that was 
done a very long time ago. But in general I think it is consistent with what is shown here.
