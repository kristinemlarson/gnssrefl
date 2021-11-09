## Homework 2 Solution

*Make SNR file for gls1, 2012, doy 100*

<code>rinex2snr gls1 2012 100 -archive unavco </code>

<code>quickLook gls1 2012 100</code>

This makes two plots.  

<img src=hw2_period.png width=500/>
<P>
<img src=hw2_summary.png width=500/>


*Looking at the QC metrics plots created by <code>quickLook</code>, do you have some ideas on how to change the azimuth mask angles?*

I've circled the areas that consistently produce unsuccessful retrievals.  Note that the default peak2noise is 3 in <code>quickLook</code>.

Now make SNR files for gls1 for the all of 2012. 

<code>rinex2snr gls1 2012 1 -archive unavco -doy_end 366 -weekly True</code>

*We will next analyze a year of L1 GPS reflection data from gls1. We will use the default minimum and maximum 
reflector height values (0.5 and 6 meters). But for the reasons previously stated, you will want to 
set a minimum elevation angle of 7 degrees. We also specify that we only want to use the L1 data.*

If you cannot remember the coordinates of gls1, you can try:

<code>query_unr gls1</code>

Note: this code was recently updated to include more precision for coordinates. This precision is not needed for make_json_input.
Although it is not required, I am going to override the dfeaults for peak2noise and reqamp to mimic what is used by quickLook.

<code>make_json_input gls1 66.479391272 -46.310152753 2148.5783167 -l1 True -e1 7 -peak2noise 3 -ampl 8 </code>

*Hand-edit the azimuths in the json file to:*

```
"azval": [ 40, 90, 90, 180, 180, 270, 270, 330 ],
```

[Here is my json file](gls1.json)
    
*Now that you have SNR files and json inputs, you can go ahead and estimate reflector heights for the year 2012 using <code>gnssir</code>.
Note that it is normal to see 'Could not read the first SNR file:' because we only created SNR files once a week.*

<code>gnssir gls1 2012 1 -doy_end 366</code>

*Now you can use the <code>daily_avg</code> tool to compute a daily average reflector height for gls1. 
Try setting the median filter to 0.25 meters and individual tracks to 30.*

<code>daily_avg gls1 0.25 30</code>

Produces three plots and a daily average file.  My plots have every day of 2012 in them whereas yours will only have one point per week.

This is all the individual RH:

<img src=gls1-av.png width=500/>

This is the daily average after outliers have been removed:

<img src=gls1-av2.png width=500/>

This lets you know how many arcs went into each day's average:

<img src=gls1-av3.png width=500/>

*Note that RH is plotted on the y-axis with RH decreasing rather than increasing. Why do you think we did that?*

Most people are interested in snow accumulation, so reversing the y-axis accommodates that.

[Here is my RH result for 2012.](gls1_dailyRH.txt)

