### Homework 3 Solution


*Make SNR data. The only required inputs are the station name (ross), the year (2020) and day of year (150)*


<code>rinex2snr ross 2020 150</code> 


*Once you have successfully created a SNR file, run <code>quickLook</code>.*


<code>quickLook ross 2020 150</code> 

<img src=ross_1.png width=500 />

<img src=ross_2.png width=500 />

*From these plots, how does the correct *RH* value compare with the one you assumed earlier when you 
were trying out the webapp?  How about the azimuths?  Go back to the reflection zone webapp and 
make sure you are happy with your azimuth and elevation angle selections.*

Please see the [gnssrefl README](https://github.com/kristinemlarson/gnssrefl) as ross is used an example.

*Next we need to save our <code>gnssrefl</code> analysis strategy*

I shifted the min and max RH to better accommodate the main signal from ~4.5 meters. I also limited 
elevation angles to 5-15 and used the peak2noise from the quickLook (which is 3).

<code>make_json_input ross 48.833729447 -87.519598801 149.8350237 -l1 True -h1 2 -h2 8 -e1 5 -e2 15 -peak2noise 3</code>


[My json was hand edited for the southeast azimuths.](ross.json)

*Now analyze data for the year 2020 using weekly flag*

First you need to make the snr files:

<code>rinex2snr ross 2020 120 -doy_end 290 -weekly True</code> 

<code>gnssir ross 2020 120 -doy_end 290 </code> 

<code>daily_avg ross 0.25 15</code>

Individual RH:
<img src=ross_all.png width=500 />

Daily average:

<img src=ross-dailyavg.png width=500  />

You can compare these retrievals with the NRCAN tide gauge data for Rossport.

