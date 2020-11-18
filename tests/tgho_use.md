# Lake Taupo

Station tgho is operated by GNS in New Zealand.  It is on Lake Taupo.

<img src="http://gnss-reflections.org/static/images/TGHO.jpg"/>

The receiver does not track L2C and it is not clear to me that L5 data are available. However, Glonass L1 and L2 are 
tracked, which is a good thing. It uses a geodetic sampling rate - 30 sec - which is not great but acceptable for this 
reflector height, which appears to be ~ 4 meters.

Let's make a SNR file and take a quick look at the spectral characteristics. Because of all the 
clutter at the site and the dielectric constant of water, I am going to emphasize the lower elevation angles.

*rinex2snr tgho 2020 300 -archive nz*

*quickLook tgho 2020 300 -e1 5 -e2 15*

<img src="tgho-default.png" width="500"/>

There is a lot of clutter at the small RH values.  So try again, windowing:

*quickLook tgho 2020 300 -e1 5 -e2 15 -h1 2 -h2 8*

<img src="tgho-better.png" width="500"/>

Why don't I like L2 data?

<img src="tgho-l2.png" width="500"/>

Now make a SNR file that includes both GPS and Glonass:

*rinex2snr tgho 2020 303 -archive nz -orb gps+glo*

Look at the Glonass L1 results. Very nice.

*quickLook tgho 2020 303 -e1 5 -e2 15 -fr 101 -h1 2 -h2 8*

<img src="tgho-glonass-l1.png" width="500"/>


You need to set an azimuth mask at this site. I will rely on the work of
Lucas Holden at RMIT. Currently this needs to be done by hand-editing the json.
So, first make the standard json, but with some changes to reflector height, peak2noise 
and elevation angle settings:

*make_json_input tgho -38.8130   175.9960  385.990 -h1 2 -h2 8 -e1 5 -e2 15 -peak2noise 3.2*

Hand edit to only look at L1, Glonass L1 (freq 101) and Glonass L2 (freq 102) and 
include an azimuth mask. [Sample json here](tgho.json).
Note that I increased the required amplitude to 9 for all frequencies. 

Now let's run a longer dataset for this site to see what Lake Taupo is up to,
say 5/9/2020 through 11/14/2020. Use **ymd** to find the day of year for these dates.
Make sure you ask for the NZ archive and the correct orbits:

*rinex2snr tgho 2020 130 -archive nz -doy_end 319 -orb gps+glo*

Then analyze the data:

*gnssir tgho 2020 130 -doy_end 319 -screenstats False*

Of course if you want some screenstats, you can leave that part out.

Remember, the RH results are in $REFL_CODE/2020/results/tgho. Since this is a lake, you can 
use **daily_avg** to give you a daily value. I used this command:

*daily_avg tgho 0.25 50*

<img src="tgho-six-months.png" width="500"/>


