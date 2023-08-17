import requests
import os
import datetime
import gnssrefl.gps as g

# downloads data from the Queensland site
# right now it is hardwired for Mornington Island
# restricted to last week, ten minute values
# usage: python gnssrefl/download_qld.py

    
xdir = os.environ['REFL_CODE']

station = 'morningtonA'

outfile = xdir + '/Files/' + station + '.txt'
print('File written to :', outfile)
fout = open(outfile,'w+')


#N = len(data['result']['records'])
NV = 6*24*7 # one week of 10 minute records
urlL = 'https://www.data.qld.gov.au/api/3/action/datastore_search?resource_id=7afe7233-fae0-4024-bc98-3a72f05675bd'
endL = '&q=' + station + '&limit=' + str(NV) 

url = urlL + endL

fout.write("{0:s} \n".format('%' + ' QLD Tide Gauge Station: ' + station ))
fout.write("{0:s} \n".format('% ' + url ))
fout.write("%YYYY MM DD  HH MM SS  Water(m) DOY  MJD     \n")
fout.write("% 1   2  3   4  5  6     7      8     9  \n")


data = requests.get(url).json()
for i in range (0,NV):
    sl = data['result']['records'][i]['Water Level']
    if (sl > -99):
        t = data['result']['records'][i]['DateTime']
        t = t + '+10:00'
        o=datetime.datetime.fromisoformat(t)
        ts = datetime.datetime.utctimetuple(o)
        year = ts.tm_year ; mm  = ts.tm_mon ; dd =  ts.tm_mday
        hh = ts.tm_hour ; minutes = ts.tm_min ; sec = ts.tm_sec; doy = ts.tm_yday
        m, f = g.mjd(year, mm, dd, hh, minutes, sec); mjd = m + f;
        fout.write(" {0:4.0f} {1:2.0f} {2:2.0f} {3:2.0f} {4:2.0f} {5:2.0f} {6:7.3f} {7:3.0f} {8:16.7f} \n".format(year, 
            mm, dd, hh, minutes, sec, sl, doy, mjd))

fout.close()




