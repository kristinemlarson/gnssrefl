### Homework 3  


*Make SNR data. The only required inputs are the station name (ross), the year (2020) and day of year (150)*


<code>rinex2snr ross 2020 150</code> 


*Once you have successfully created a SNR file, run <code>quickLook</code>.*


<code>quickLook ross 2020 150</code> 

<img src=ross_1.png width=500 />

<img src=ross_2.png width=500 />

From these plots, how does the correct *RH* value compare with the one you assumed earlier when you 
were trying out the webapp?  

How about the azimuths?  Go back to the reflection zone webapp and 
make sure you are happy with your azimuth and elevation angle selections.

*Next we need to save our <code>gnssrefl</code> analysis strategy using 
<code>make_json_input</code>.*



* You will need to hand edit the azimuths in the json file. You want
to cut up your azimuth range in 60-90 degree chunks.  So if you wanted to use the region 
for 90-270 degrees, you should say 90-180
and 180-270. You can use smaller chunks, but I generally do not use less than 45 degree azimuth chunks.

*Now run <code>gnssir</code> for the year 2020/doy 150.*


