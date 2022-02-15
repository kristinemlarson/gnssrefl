import datetime
import json
import os
import requests
import sys
import subprocess
import wget
from urllib.parse import urlparse
import gnssrefl.gps as g

# kristine Larson, February 2022
# new libraries to download Rinex 3 files

def swapRS(stream):
    """
    profound function that swaps R to S and vice versa
    """
    if stream == 'R':
        newstream = 'S'
    else:
        newstream = 'R'
    return newstream


def universal(station9ch, year, doy, archive,srate,stream):
    """
    seamless archive for rinex 3 files ... 
    """
    # define the file name
    print('Searching the ', archive, ' archive with rate/filetype', srate, stream)
    foundit = False

    file_name,cyyyy,cdoy = filename_plus(station9ch,year,doy,srate,stream)
    dir1 = ''
    dir2 = ''

    try:
        if (archive == 'ign'):
            dir1='ftp://igs.ensg.ign.fr/pub/igs/data/' + cyyyy + '/' + cdoy + '/'
            wget.download(dir1+file_name,file_name)
        elif archive == 'bkg':
            dir1 = 'https://igs.bkg.bund.de/root_ftp/IGS/obs/' + cyyyy + '/' + cdoy + '/'
            dir2 = 'https://igs.bkg.bund.de/root_ftp/EUREF/obs/' + cyyyy + '/' + cdoy + '/'
            wget.download(dir1+file_name,file_name)
            if not (os.path.exists(file_name)):
                wget.download(dir2+file_name,file_name)
        elif (archive == 'bev'):
            dir1 = 'https://gnss.bev.gv.at/at.gv.bev.dc/data/obs/' + cyyyy + '/' + cdoy + '/'
            wget.download(dir1+file_name,file_name)
        elif (archive == 'ga'):
            QUERY_PARAMS, headers = ga_stuff(station9ch, year, doy)
            API_URL = 'https://data.gnss.ga.gov.au/api/rinexFiles/'  
            request = requests.get(API_URL, QUERY_PARAMS, headers=headers)
        #request.raise_for_status()
        # i don't know how to read this - so doing it the dumb way
            if len(json.loads(request.content)) == 1:
                for query_response_item in json.loads(request.content):
                    file_url = query_response_item['fileLocation']
                    file_name = urlparse(file_url).path.rsplit('/', 1)[1]
                    wget.download(file_url,file_name)
        elif (archive == 'unavco'):
            dir1 = 'https://data.unavco.org/archive/gnss/rinex3/obs/' + cyyyy + '/' + cdoy + '/'
            wget.download(dir1+file_name,file_name)
        elif (archive == 'cddis'):
            new_way_dir = '/gnss/data/daily/' + cyyyy + '/' + cdoy + '/' + cyyyy[2:4] + 'd/'
            g.cddis_download(file_name,new_way_dir)
        else:
            return '', ''
    except:
        okokok = 1

    if os.path.exists(file_name):
        print('File exists: ', file_name, ' at ', archive)
        foundit = True

    return file_name,foundit

def filename_plus(station9ch,year,doy,srate,stream):
    """
    """
    cyyyy = str(year)
    cdoy = '{:03d}'.format(doy)
    crate = '{:02d}'.format(srate)
    upper = station9ch.upper()
    ff = upper + '_' + stream + '_' + cyyyy + cdoy + '0000_01D_' + crate + 'S_MO'
    ext = '.crx.gz'
    file_name = ff + ext

    return file_name, cyyyy, cdoy

def ga_stuff(station, year, doy):
    """
    takes 9 ch station name and year and doy 
    and returns some things that GA wants to download a Rinex 3 file
    """
    d = datetime.datetime(year, 1, 1) + datetime.timedelta(days=(doy-1))
    month = int(d.month); day = int(d.day)
    cmonth = '{:02d}'.format(month); cday = '{:02d}'.format(day)


    QUERY_PARAMS = {}
    QUERY_PARAMS['stationId'] = station[0:4].upper()
    QUERY_PARAMS['fileType'] = 'obs'
    QUERY_PARAMS['filePeriod'] = '01D'
    QUERY_PARAMS['rinexVersion'] = '3'
    QUERY_PARAMS['startDate'] = str(year) + '-' + cmonth + '-' + cday + 'T00:00:00Z'
    QUERY_PARAMS['endDate'] =   str(year) + '-' + cmonth + '-' + cday + 'T23:59:30Z'

    headers = {}
    headers['Accept-Encoding'] = 'gzip'

    return QUERY_PARAMS, headers

def universal_all(station9ch, year, doy, srate,stream):
    """
    """
    foundit = False

    for archive in ['unavco','cddis','bkg','bev']:
        if archive == 'unavco':
            srate_in = 15
        else:
            srate_in = srate
        # only look if you haven't found it
        if (not foundit):
            file_name,dd = universal(station9ch, year, doy, archive,srate_in,stream)
            if os.path.exists(file_name):
                foundit = True

    return file_name, foundit
