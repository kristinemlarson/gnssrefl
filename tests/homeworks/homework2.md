# [2021 gnssrefl short course](https://www.unavco.org/event/2021-gnss-interferometric-reflectometry/)


## Homework 2

**Due date:** This homework is to be completed **before** the short course given on October 21. You need to make
sure the software has been properly installed and you have successfully completed the "homework 0" assignment.

**Purpose:** Learn how to measure snow depth levels with gnssrefl using GNSS data 


**Station:**
We will be using station **gls1**.
gls1 was installed at [Dye2](http://greenlandtoday.com/dye-2-a-relic-from-a-not-so-distant-past/?lang=en) on the Greenland Ice Sheet in 2011. 
The antenna is mounted on a long pole; approximately 3.5-meter of the pole was above the ice at the time of installation. 
The receiver at the site only consistently tracks legacy GPS signals. This means none of the 
enhanced GPS signals (L2C and L5) are available. A detailed discussion of the monument and 
data from the station can be found in [Larson, MacFerrin, and Nylen (2020)](https://tc.copernicus.org/articles/14/1985/2020/tc-14-1985-2020.pdf). 
The latest position time series for gls1 can be retrieved 
from the [Nevada Geodetic Laboratory](http://geodesy.unr.edu/gps_timeseries/tenv3/IGS14/GLS1.tenv3). 

As gls1 is on an ice sheet and the ice surface is relatively smooth in all directions, it 
is unlikely that a complicated azimuth mask will be required.

gls1 was originally installed with an elevation mask of 7 degrees, which is suboptimal for reflections research.
Even though the mask was later removed, we will use 7 degrees as the minimum elevation angle for all our analysis.
Similarly, even though the site managers later changed to enable L2C tracking, to ensure that 
a consistent dataset is being used, we will only use L1 data.

Run the cell below (starts with %%html) to view the gnss-reflections webapp. Use the geoid tab in the 
webapp to get an idea of its surroundings. You can enter the station coordinates by hand if 
you know them, but since gls1 is part of a public archive known to geodesists, coordinates have been stored in the 
webapp. Just type in gls1 for the station name. Make a note of the station latitude, 
longitude, and ellipsoidal height that is returned by the webapp because you will need it later. 




**Using gnssrefl**

Our ultimate goal in this use case is to analyze one year of data. We have chosen the year 2012 
because there was a large melt event on the ice sheet. In order to set the proper quality control parameters, we will use 
<code>quickLook</code> for one day. First we need to translate one day of RINEX data using rinex2snr. We will use day of year 100:

We need to pick up a RINEX file and strip out the SNR data.  We use the <code>rinex2snr</code> for this purpose. 
The only required inputs are the station name (ross), the year (2012) and day of year (100) (note: to convert from year and day of year to year, 
month, day and vice versa, try the modules <code>ydoy</code> and 
<code>ymd</code>). 

By default <code>rinex2snr</code> tries to find the RINEX data for you by looking at a few 
key archives.  However, if you know where the data are, it will be faster to specify it.
In this case they are available from both unavco and sopac. Try the <code>archive</code> option.

Once you have successfully created a SNR file, run <code>quickLook</code>.

There are two ways to view the quicklook plots in the jupyter notebook version:

* The first way is to set the parameter pltscreen to True (`pltscreen=True`). This will print out the plots that the gnssrefl code makes.

* The second way is to make the plot ourselves so we can better view these plots. In that case we set `pltscreen=False` - which is also the default. Both options are provided in the cells below.

The quicklook plots consist of two graphical representations of the data. The first is 
periodograms for the four geographic quadrants (northwest, northeast, and so on). 
You are looking for nice clean (and colorful) peaks. Color means they have 
passed Quality Control (QC). Gray lines are satellite tracks that failed QC. The second plot summarizes the 
RH retrievals and how the QC metrics look compared to 
the defaults. In this case the x-axis is azimuth in degrees.
[For more details on quicklook output](https://github.com/kristinemlarson/gnssrefl/blob/master/docs/quickLook_desc.md).



Looking at the metrics plots, the top plot we see that the retrieved reflector heights are consistent at all azimuths.
Retrievals for azimuths between ~340 degrees and ~40 degrees are consistently marked as not having met quality 
control settings. From the center plot we can see that a peak2noise QC metric of 3 is reasonable. 
Similarly, the amplitudes (bottom plot) are generally larger than 10, so 8 is an acceptable minimum value.


Use whichever quicklook plotting method to compare the above to its level when the 
site was installed in the year 2011 in the cell provided below (run rinex2snr and then quicklook similar to what was shown above).


Now, lets make SNR files for the whole year 2012: We will use the 'weekly' 
parameter that will make just one day of the week over the period we give it. This is in the interest 
of saving time. It should take ~5 minutes to complete.

We will next analyze a year of L1 GPS reflection data from this site. We will use the default minimum and maximum 
reflector height values (0.5 and 6 meters). But for the reasons previously stated, we will 
set a minimum elevation angle of 7 degrees. We also specify that we only want to use the L1 data and set peak2noise and a mimimum
amplitude for the periodograms. We use the utility make_json_input to set and store these analysis settings:

Now we are going to hand edit the azimuths to between 40 and 330 degrees.


file['azval'] = [40,90,90,180,180,270,270,330]

    
Now that you have SNR files and json inputs, you can go ahead and estimate reflector heights for the year 2012:

*note that it will be normal to see 'Could not read the first SNR file:' results - this is because we used 
the weekly setting when downloading the snr files. We are setting gnssir to run for 
every day of the year but if the snr file doesn't exist, it will continue on - in this case we only have one snr file per week.

Now, we can use the daily_avg tool to compute a daily average reflector height. A median filter is set to 0.25 meters 
and 30 individual tracks are required in order to recover a daily average:



This will create a daily file that contains the daily averages. Let's plot them:


```python
filepath = f'{refl_code_loc}/Files/{station}-dailyavg.txt'

# I have provided  a function that will read the file for you.
data = check_parameters.read_allrh_file(filepath)
df = pd.DataFrame(data, index=None, columns=['dates', 'rh'])
df.head()
```


```python
plt.figure(figsize=(8,8))
g = sns.scatterplot(x='dates', y='rh', data=df, legend=False)
# here we flip the axis so its low reflector height (higher snow) to higher reflector height (lower snow)
g.set_ylim(3.6,2.3)
g.set_ylabel('Reflector Height (m)');
```

The data in this plot show you long-term accumulation as well as relatively small snow accumulation events. The overall plot is dominated by the large melt event in the summer.

