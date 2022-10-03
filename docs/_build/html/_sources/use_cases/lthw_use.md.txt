### Lower Thwaites Glacier

Station lthw is operated by UNAVCO. The data are archived at UNAVCO.

<img src="http://gnss-reflections.org/static/images/LTHW.jpg" width="500"/>

**Coordinates:**
Use the [UNAVCO DAI](https://www.unavco.org/data/gps-gnss/data-access-methods/dai2/app/dai2.html#4Char=LTHW;scope=Station;sampleRate=both;4CharMod=contains) if you like. Or you can try the [Nevada Reno site](http://geodesy.unr.edu/NGLStationPages/stations/LTHW.sta).
The coordinates do not have to be super precise (within 100 meters is fine)

Unfortunately the operators of this site set an elevation mask of 7 degrees. You need to 
acknowledge this when you set the data anlaysis
parameters, i.e. set e1 to 7, because otherwise the lack of low elevation data will be 
interpreted as low data quality.

To my knowledge the receiver only tracks L1, and it does not track L2C or L5. 
For that reason, only L1 data should be used. The reflector height changes 
significantly with time and the site must be dug out of the snow
and reset fairly regularly. You can see this effect in the vertical position data compiled 
by [Nevada Reno](http://geodesy.unr.edu/NGLStationPages/stations/LTHW.sta).

<img src="LTHW_UNR.png" width=500/>

Don't pay attention to the red "model" as Nevada Reno is using a default model
that is more relevant for crustal deformation than a glacier. The important 
data are in blue, and there are clear breaks 
that are correlated with when they changed the height of the antenna. We will 
focus on the period after January 1, 2018. Go ahead and make SNR files for the whole year.

*rinex2snr lthw 2018 1 -doy_end 365 -archive unavco*

Then take a look at January 1 in 2018:

*quickLook lthw 2018 1 -e1 7*

<img src="lthw-day1-2018.png" width="500"/>

This is a bit of a mess really. If there are significant peaks, they are really 
close to the cutoff for the method (at 0.5 meters).  Now look a week later:

*quickLook lthw 2018 9 -e1 7*

<img src="lthw-day9-2018.png" width="500"/>
This is *much* better and clearly shows that a field crew reset the antenna to a little 
less than 5 meters sometime between day 1 and day 9.
If you like you can compare this to the first day of 2020 (if you make the SNR file):

<img src="lthw-day1-2020.png" width=500/>

Now the peaks in the RH periodograms are ~2.2 meters - so that means ~2.5 meters of surface change 
from 2018 to 2020.

Now let's run **gnssir**. First we need to make json input,

*make_json_input lthw -76.458  -107.782 1011.0 -e1 7 -e2 25 -peak2noise 3.2*

Handedit the json file so that only L1 is used.  

Analyze the data for 2018 from day 1 to day 365:

*gnssir lthw 2018 1 -doy_end 365 -screenstats False*

Then compute daily averages requiring 50 satellite tracks and using a median filter of 0.25 meters:

*daily_avg lthw 0.25 50*

<img src="lthw-req50.png" width="500"/>

You can tighten required number of tracks if you want:

*daily_avg lthw 0.25 40*

<img src="lthw-req40.png" width="500"/>


