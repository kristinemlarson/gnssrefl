# this is a python script example for gnssrefl
# this particular example is for mchn. The use
# cases are meant to be used in conjunction with 
# the command line.  
# https://gnssrefl.readthedocs.io/en/latest/use_cases/use_mchn.html
# if you have difficulties with this python script, please 
# look to that or the API documentation 
# https://gnssrefl.readthedocs.io/en/latest/api.html

print('This should be run from the default directory, i.e. gnssrefl should be one folder down.')

# 
# import these gnssrefl libraries
import gnssrefl.make_json_input as mj
import gnssrefl.gnssir as guts
import gnssrefl.rinex2snr as rnx

# standard python libraries
import os
import sys

print('WARNING: I had to compile the fortran on the command line ...')
#    f2py -c -m gnssrefl.gpssnr gnssrefl/gpssnr.f
#    f2py -c -m gnssrefl.gnsssnr gnssrefl/gnsssnr.f
#    f2py -c -m gnssrefl.gnsssnrbigger gnssrefl/gnsssnrbigger.f

# set environment variables 
xdir = os.environ['REFL_CODE']
exedir = os.environ['EXE']

# set to true if they do not exist
make_snr_files = True 

# here i will do just one year
year = 2022
# in case you want to do multiple years, it has to be a list
year_list = [year]

# analyze the first five days of that year
doy_list = [150, 180]

# snr file type - 66 is all e < 30
# snr file type 88 is all data > 5
# 99 is 5-30, but i have abandoned that for the most part
# but then you have to specify snr type for everything downstream
isnr = 66

station = 'mchn'

# refl height limits (m)
h1 = 2.5
h2 = 10

# noise region - meters
nr1 = h1
nr2 = h2

# elev angle limits , deg
e1 = 5
e2 = 15

# lat long ellipsoidal height
# this is only used for refraction.  if station in UNR database, you can set to zero
lat = 0; long = 0; height = 0

# list of frequencies to analyze.  at this site - running a very old receiver with
# poor L2 data, and no modern signals, you only have l1

frlist = [1]

# generic peak amplitude value required. can set to zero if you want to
# just use peak2noise
ampl = 5 

# could be a bit tighter
peak2noise = 3.5

# azimuth min and max. default is four regions as in [0,90,90,180,180,270,270,360]
# in this case we only want the region to the southwest of the dock
azlist = [80, 180 ]

# whether you are testing a new strategy - so results are segregated
extension = ''

##################################################################################
# make SNR files


# default is gps
# since this is an old receiver with limited abilities, you can use nav file
orbtype = 'nav' # gnss or rapid for multi-GNSS

rate = 'low' # for archive directories, high or low
dec_rate = 1 # this is for decimation (seconds).  1 means do nothing
archive = 'sopac' # archive
fortran = False
overwrite = False # if True, you can make new rinex files
translator = 'hybrid'
mk = False # makan option
skipit = 1  # can set to 7 to make a file every week, e.g.

# these must be set - but are only for RINEX 3, which does not exist at this site
samplerate = 30 # 
stream = 'R' # 
bkg = 'IGS'

nolook = False # if you have the properly named rinex files in the locally directory set this to True

strip = False # will remove non SNR obs . useful if someone has a file with more than 25 obstypes


args = {'station': station, 'year_list': year_list, 'doy_list': doy_list, 'isnr': isnr, 'orbtype': orbtype,
        'rate': rate, 'dec_rate': dec_rate, 'archive': archive, 'fortran': fortran, 'nol': nolook,
            'overwrite': overwrite, 'translator': translator, 'srate': samplerate, 'mk': mk,
            'skipit': skipit, 'stream': stream, 'strip': strip, 'bkg': 'IGS'}

if make_snr_files:
    rnx.run_rinex2snr(**args)


##################################################################################
# Make instruction (json) file

delTmax = 75 # arc min length, minutes. for tides you would likely want to tighten this up.
refraction = True 
ediff = 2 # arc must be within ediff degrees of emin/emax

# this is leftover stuff.  it has been supplanted by frlist that was defined earlier
allfreq = False
l2c = False
l1 = True

xyz = False # coordinates are not in xyz


# if json already exists use it.  if not, make one
if len(extension) == 0:
    f = xdir + '/input/' + station + '.json'
else:
    f = xdir + '/input/' + station + '.' + extension + '.json'

if os.path.isfile(f):
    print('found the json')
    lsp = guts.read_json_file(station, extension)
else:
    print('make a json')
    mj.make_json(station, lat, long, height, e1, e2, h1, h2, nr1, nr2, peak2noise, 
            ampl, allfreq, l1, l2c, xyz, refraction, extension, ediff, delTmax, azlist, frlist)
    lsp = guts.read_json_file(station, extension)

print(lsp)
# these were unfortunately left out of the make_json code.  
lsp['nooverwrite'] = False
lsp['mmdd'] = False


##################################################################################
# Run the Lomb Periodogram Code, gnssir

for doy in range(doy_list[0], doy_list[-1]+1):
    args = {'station': station.lower(), 'year': year, 'doy': doy, 'snr_type': isnr, 'extension': extension, 'lsp': lsp}
    guts.gnssir_guts(**args)



