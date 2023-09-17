# makes comparison plot for niwot ridge GPS-IR use case for snow accumulation
# in situ data: pole 16 in saddle data set
# RH is reflector height in meters
# author: kristine larson
# march 19, 2021
import numpy as np
import datetime
import matplotlib.pyplot as plt
import sys

hires = True

# in situ data for Niwot Ridge LTER
# https://portal.edirepository.org/nis/mapbrowse?scope=knb-lter-nwt&identifier=34
# this is the file we need.
insitufile = 'saddsnow.dw.data.csv'
# save the date, pole#, and snow depth columns (cm)
insitu= np.loadtxt(insitufile,skiprows=1,delimiter=',',dtype='str',usecols=(3,2,4))
# pick out pole 16, which is closest to nwot GPS site
ij = insitu[:,1] == '16'
insitu = insitu[ij,:]

date = insitu[:,0] # date string
sval= insitu[:,2] # snow depth as string

# arrays for the in insitu answers
obst = np.empty(shape=[0, 1])
snow = np.empty(shape=[0,1])
for i in range(0,len(insitu)):
    y=int(date[i][0:4])
    m=int(date[i][5:7])
    d=int(date[i][8:10])
    s = float(sval[i])/100
    obst= np.append(obst, datetime.datetime(year=y, month=m, day=d))
    snow = np.append(snow,s)

# read in the daily average RH file
gpsfile = 'nwot_dailyRH.txt'
gps = np.loadtxt(gpsfile,comments='%')

# going to use august and mid-september to determine "no snow level"
# for other sites, you might be able to use all of september ...
# doy 213 through doy 258 
# RH is stored in column 2, doy is in column 1
ii = (gps[:,1] >= 213) & (gps[:,1] <= 258)
noSnowRH = np.mean(gps[ii,2])
print('No snow RH value: ', '{0:7.3f}'.format( noSnowRH),'(m)' )

# make a datetime array for plotting the gps results
gobst = np.empty(shape=[0, 1])
for i in range(0,len(gps)):
    gobst = np.append(gobst, datetime.datetime(year=int(gps[i,0]), month=int(gps[i,4]), day=int(gps[i,5])))

snowAccum = noSnowRH - gps[:,2]

plt.figure()
plt.plot(gobst, snowAccum, 'b.',label='GPS-IR')
plt.plot(obst,snow,'ro',label='Manual - Pole16',markersize=6)
plt.legend(loc="upper left")
plt.title('Snow Depth, Niwot Ridge LTER Saddle')
plt.xlabel('Years')
plt.ylabel('meters')
plt.grid()
left = datetime.datetime(year=2009, month=9, day = 1)
right = datetime.datetime(year=2015, month=5, day = 1)
plt.xlim((left, right))
plt.ylim((-0.05, 3.25))

if hires:
    plot_path = 'nwot_usecase.eps'
else:
    plot_path = 'nwot_usecase.png'

print('writing file to ', plot_path)
plt.savefig(plot_path)
plt.show()
# GPS receiver failed in spring 2015

