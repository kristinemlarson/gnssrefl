# daily_avg<a name="module5"></a>

<code>daily_avg</code> is a utility for people interested 
in daily averaged reflector heights, such as are used for measuring 
snow accumulation or water levels in lakes/rivers. *It is not to be used for tides!*
The goal is to make a valid daily average - for this reason, we have two required inputs 
for quality control. 

- The first is called a *median filter* value. This input helps remove
large outliers. For each day, a median RH is found. Then all values larger than the 
*median filter* value from the median RH are thrown out. 

- The second required input to <code>daily_avg</code> sets a limit for how 
many satellite arcs are considered sufficient to create a trustworth daily average. 
If you had 5 arcs, for example, you probably would not want to compare that 
with another day where 100 arcs were available. The number of tracks required 
varies a lot depending on the azimuth mask and the number of frequencies available.
If you are not sure what values to use at your GNSS site, run it once with very minimal constraints.
The code provides some feedback plots that will let you pick better values.

Here is an example from one of our use cases where there are a few large outliers.  
I have set the median filter value to 2 meters and the required number of tracks to 12:

<code> daily_avg mchn 2 12 </code>

You can easily see the outliers. 

<p align=center>
<img width=500 src=../_static/mchn-A.png>
</p>

Next I have rerun the code with a better median filter constraint of 0.25 meters:

<code> daily_avg mchn 0.25 12 </code>

<p align=center>
<img width=500 src=../_static/mchn-B.png>
</p>

A daily average plot is also made and a text file of the outputs is created.

<p align=center>
<img width=500 src=../_static/mchn-C.png>
</p>

