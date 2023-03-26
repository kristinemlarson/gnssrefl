## Utilities for Downloding Tide Data

### download_noaa

downloads up to a year of NOAA tide gauge data given a station number (7 characters), 
and begin/end dates, e.g. 20150601 would be June 1, 2015. 

The NOAA API works perfectly well for this, but this utility writes out a file with 
only columns of numbers (or csv if you prefer). To implement the latter, use csv as the 
ending of your output filename. An optional plot is produced with -plt T.

### download_psmsl 

downloads GNSS-IR based sealevel files from the Permanent Service 
for Mean Sea Level. 

Input is the station name. Output can be plain txt or csv. To 
implement the latter, use csv as the ending of your output filename. 
Optional plot to the screen if -plt is set to T.

### download_ioc 

downloads up to a year of tide gauge records from the IOC website. 
It requires beginning and ending date (yyyymmdd format). Although limited by the IOC to 30 days, the code
will download up to a year of data. 

Optional output filename allowed. If the output file ends 
in csv, it writes a csv file instead of plain text. You can pick the 
sensor type or you will get all of them. 

There is an optional plot produced with -plt T.


### download_wsv 

downloads the last fifteen days of data from the German water level agency
(WSV). Requires the station name.

Optional output filename allowed. plt comes to the screen, but can be turned off with -plt F

