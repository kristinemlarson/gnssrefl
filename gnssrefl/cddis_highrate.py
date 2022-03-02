import gnssrefl.gps as g
import sys
import wget
import subprocess
import os 

def cddis_highrate(station, year, month, day,stream):
    """
    author: kristine larson
    inputs: station name, year, month, day
    picks up a higrate RINEX file from Geoscience Australia
    you can input day =0 and it will assume month is day of year
    not sure if it merges them ...
    2020 September 2 - moved to gz and new ftp site
    ??? does not appear to have Rinex 2 files anymore ???
    ??? goes they switched in 2020 .... ???
    """
    if len(station) == 4:
        version = 2
    else:
        version = 3
    crnxpath = g.hatanaka_version()
    gfzpath = g.gfz_version()
    alpha='abcdefghijklmnopqrstuvwxyz'
    # if doy is input
    if day == 0:
        doy=month
        d = g.doy2ymd(year,doy);
        month = d.month; day = d.day
    doy,cdoy,cyyyy,cyy = g.ymd2doy(year,month,day); cyy = cyyyy[2:4]

    if not os.path.isfile(gfzpath):
        print('You need to install gfzrnx to use high-rate RINEX data in my code.')
        return

    gns = 'https://cddis.nasa.gov/archive/gnss/data/highrate/' 
    gns = gns + cyyyy + '/'+ cdoy + '/' +cyy + 'd/'
    #YYYY/DDD/YYt/HH/mmmmDDDHMM.YYt.gz


    print('WARNING: Get yourself a cup of coffeee. Downloading 96 files takes a long time.')
    fileF = 0
    streamID  = '_R_'
    for h in range(0,24):
        # subdirectory
        ch = '{:02d}'.format(h)
        print('Hour: ', ch)
        for e in ['00', '15', '30', '45']:
            if version == 2:
                oname = station + cdoy + alpha[h] + e + '.' + cyy + 'o'; 
                file_name, crnx_name, file_name2, crnx_name2, exe1, exe2 = indecisiveArchives(station,year,doy,cyyyy,cyy,cdoy,alpha[h],e) 
            else:
                file_name = station.upper() + streamID + cyyyy + cdoy + ch + e + '_15M_01S_MO.crx.gz'
                crnx_name = file_name[:-3] 
                oname = station.upper() + streamID + cyyyy + cdoy + ch + e + '_15M_01S_MO.rnx' # do we need this?

            new_way_dir = '/gnss/data/highrate/' + cyyyy + '/' + cdoy + '/' + cyy + 'd/' + ch + '/'
            print(station,new_way_dir,file_name)
            if os.path.isfile(oname):
                fileF = fileF + 1
            else:
                try:
                    g.cddis_download(file_name,new_way_dir)
                    if (version == 3):
                        subprocess.call(['gunzip',file_name])
                        subprocess.call([crnxpath, crnx_name])
                        subprocess.call(['rm',crnx_name])
                    if (version == 2):
                        if os.path.isfile(file_name):
                            subprocess.call([exe1,file_name])
                            subprocess.call([crnxpath, crnx_name])
                            subprocess.call(['rm',crnx_name])
                        else:
                            g.cddis_download(file_name2,new_way_dir)
                            subprocess.call([exe2,file_name2])
                            subprocess.call([crnxpath, crnx_name2])
                            subprocess.call(['rm',crnx_name2])
                except:
                    okok = 1
                if os.path.isfile(oname):
                    fileF = fileF + 1
    if version == 2:
        searchpath = station + cdoy + '*.' + cyy + 'o'
        rinexname = station + cdoy + '0.' + cyy + 'o'
        tmpname = station + cdoy + '0.' + cyy + 'o.tmp'
    else:
        searchpath = station.upper() + streamID + cyyyy + cdoy + '*.rnx'
        rinexname = station.upper() + streamID + cyyyy + cdoy + '0000_01D_01S_MO.rnx'
        tmpname = rinexname + 'tmp'

    print('Attempt to merge the 15 minute files using gfzrnx and move to ', rinexname)
    if (fileF > 0): # files exist
        subprocess.call([gfzpath,'-finp', searchpath, '-fout', tmpname, '-vo',str(version),'-f','-q'])
        cm = 'rm ' + searchpath 
        if os.path.isfile(tmpname): # clean up
            ok = 1
            subprocess.call(cm,shell=True)
            subprocess.call(['mv',tmpname,rinexname])
            print('File created ', rinexname)

def indecisiveArchives(station,year,doy,cyyyy,cyy, cdoy,chh,cmm):
    """
    deal with the insanity at the CDDIS archives, where they change
    things alllllll the time.
    files were Z until they were gz.  And soon will be a tar file ....
    """
# Before being merged into tar files, all Unix compressed RINEX V2 data with file 
#  extension ".Z" will be switched to gzip compression with the file extension ".gz". This 
#  change in compression is in accordance with the IGS transition to gzip conversion for 
#  RINEX V2 data after December 1, 2020.
#
# 335 is december 1 2020
    T0 = 2020 + 335/365.25
    if ((year+doy/365.25) <= T0):
        file_name = station + cdoy + chh + cmm + '.' + cyy + 'd.Z'
        crnx_name = file_name[:-2]
        file_name2 = station + cdoy + chh + cmm + '.' + cyy + 'd.gz'
        crnx_name2 = file_name2[:-3]
        exe1 = 'uncompress'
        exe2 = 'gunzip'
    else:
        file_name = station + cdoy +  chh + cmm + '.' + cyy + 'd.gz'
        crnx_name = file_name[:-3]
        file_name2 = station + cdoy + chh + cmm + '.' + cyy + 'd.Z'
        crnx_name2 = file_name2[:-2]
        exe2 = 'uncompress'
        exe1 = 'gunzip'

    return file_name, crnx_name, file_name2, crnx_name2, exe1, exe2
