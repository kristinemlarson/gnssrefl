### Test the code on a longer dataset from the Ross Ice Shelf 

Now we will look at a station called lorg. This site is on the Ross Ice Shelf, Antarctica. The data are archived at UNAVCO.  

Get some coordinates for the site, either lat,long,ht or XYZ. 
Use the [UNAVCO DAI](https://www.unavco.org/data/gps-gnss/data-access-methods/dai2/app/dai2.html#4Char=LORG;scope=Station;sampleRate=both;4CharMod=contains) if you like. Or you can try the [Nevada Reno site](http://geodesy.unr.edu/NGLStationPages/stations/LORG.sta).
The coordinates do not have to be super precise (within 100 meters is fine).

**Exercise for the reader:** It is always nice to have a photograph of site. Try to
get a photograph of lorg from the UNAVCO website. If you cannot find it at there,
email dmencin@unavco.org and ask him to post it.

lorg is an example station on my webapp. [Please note that the app will be analyzing data in 
real-time, so you need to wait for the answers to "pop" up in the left hand side of the page. It takes 5-10 
seconds](https://gnss-reflections.org/fancy6?example=lorg). You might save the periodogram of results so you have a 
better idea of what the reflection characteristics of the site.

You need to make some snr files. This time we will do eight months or so. 
And we will restrict the search to the unavco archive to make the code run faster (otherwise it will check
four archives). Here I say fortran is False, but of course if you have installed gpsSNR.e, you can 
use it and the exercise will run faster.

*rinex2snr lorg 2019 1 -doy_end 233 -fortran False -archive unavco*

If you want to look at the contents of a SNR file, they are stored in $REFL_CODE/2019/snr/lorg

I recommend that you use **quickLook** for one file. This gives you an idea of the quality of the site.

*quickLook lorg 2019 1*

This will produce a reflection periodogram for the L1 data. 
Compare the periodograms for frequencies 1, 20 (L2C) and 5. It should be simlar to the webapp periodogram except that the peaks in the periodogram
will be in a different place depending on how much snow has accumulated at this site.

Now let's get ready to run **gnssir**. This is the code that saves the RH output.
First you need to make a set of file instructions. If you use defaults, you only
need the station name, lat, lon, and ht. Make this file using **make_json_input**.
The json output will be stored in $REFL_CODE/input/lorg.json.
[Here is a sample.](lorg.json)

Run **gnssir** for all the SNR files you made in the previous section.

*gnssir lorg 2019 1 -doy_end 233*

The code will tell you which satellites it is looking at and give you an overview for 
the estimated reflector heights. You can turn off these statistics in the json (screenstats).
Or from the command line:

*gnssir lorg 2019 1 -doy_end 233 -screenstats False*

The default does not send any plots to the screen - and you definitely do not want to see all those plots 
if you are analyzing 233 days of data. But if you want to look at the plots for a single day, that is an option in the json 
and at the command line:

*gnssir lorg 2019 1 -screenstats False -plt True* 

Unlike **quickLook**, here you get the periodograms for each frequency all together. To see the next frequency, you need to eliminate the current plot, etc.

We can certainly clean these results up by eliminating various azimuths and requiring stronger peaks in the periodograms.
But for now, let's just use defaults.
The reflector height results are stored in $REFL_CODE/2019/results/lorg. You can concatenate 
the daily files and create your own daily average values (which is what is appropriate for this site), or you can 
use **daily_avg**. To avoid using outliers in these daily averages, a median filter is set.  I recommend 
0.25 m and ReqTrack of 50 at this site.

*daily_avg lorg 0.25 50*

The first plot is [all the data](lorg_1.png) (and very colorful). Once you delete it,
the second plot - the daily average - is shown: 

<img src="lorg_2.png" width="500"/>

There are also optional inputs for saving a text file of the daily averages. 
The plot is stored at $REFL_CODE/Files/lorg_RH.png 
This is not yet perfect - as there are some outliers which I have circled in red for you. 
But it is an excellent example of how easy it is to use the default gnssrefl code to estimate snow accumulation in Antarctica.

In this exercise you used L1, L2C, and L5 signals (i.e. only GPS data). Your reflector heights (RH) are telling you 
about snow accumulation changes at lorg. You should notice that when I plot RH, I reverse the y-axis so 
as RH gets smaller, that means the snow layer is increasing.
