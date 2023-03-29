# -*- coding: utf-8 -*-
import argparse
import wget
import os
import subprocess
import sys
from shutil import which 


def newchip_gfzrnx(exedir):
    """
    installs the gfzrnx executable and stores in the EXE directory

    Parameters
    ----------
    exedir : str
        location of the executable directory

    """
    savename = 'gfzrnx'
    finalpath = exedir + '/' + savename
    if os.path.exists(finalpath):
        print('The gfzrnx executable already exists')
    else:
        print('Installing gfzrnx')
        localname = 'gfzrnx_osxarm64'
        dfile = 'https://morefunwithgps.com/public_html/' + localname
        wget.download(dfile, savename)
        os.chmod(savename,0o777)
        if os.path.exists(savename):
            subprocess.call(['mv', '-f',savename, exedir])
    return

def newchip_hatanaka(exedir):
    """
    compiles hatanaka code if an existing executable is not there
    stores in EXE directory

    Parameters
    ----------
    exedir : str
        location of the executable directory

    """
    savename = 'CRX2RNX'
    finalpath = exedir + '/' + savename
    if os.path.exists(finalpath):
        print('This Hatanaka executable already exists')
    else:
        print('The Hatanaka CRX2RNX source code will be compiled. This requires gcc.')
        exists = which('gcc')
        if exists is None:
            print('gcc does not exist')
            sys.exit()

        sourcefile = 'crx2rnx.c'; sourceexe =  'crx2rnx.e'
        print('local sourcefile ','docs/' + sourcefile)
        if os.path.exists('docs/' + sourcefile):
            print('Hatanaka source code found locally')
            s = 'docs/' + sourcefile
            subprocess.call(['gcc', s, '-o', sourceexe])
        else:
            print('Hatanaka source code found at github')
            cfile = 'https://raw.githubusercontent.com/kristinemlarson/gnssrefl/master/docs/crx2rnx.c'
            print(cfile)
            wget.download(cfile, sourcefile)
            subprocess.call(['gcc', sourcefile, '-o', sourceexe])
        if os.path.exists(sourceexe):
            print('Hatanaka success - moving to EXE directory')
            subprocess.call(['mv', '-f', sourceexe, finalpath])
            subprocess.call(['rm', '-f', sourcefile])
        else:
            print('no Hatanaka success')
            sys.exit()

    return

def checkexist(exe):
    """
    check to see if an executable exists

    Parameters
    ----------
    exe : str
        executable name to check

    """

    exists = which(exe)
    if exists is None:
        print(exe + ' does not exist on your system. You need to install it.')


def download_chmod_move(url,savename,exedir):
    """
    download an executable, chmod it, and store it locally

    Parameters
    -----------
    url : string
        external location of the executable

    savename : string
        name of the executable

    exedir : string
        name of local executable directory (EXE environment variable)

    """
    f = exedir + '/' + savename
    if os.path.exists(f):
        print('You already have this executable: '+ savename)
    else:
        wget.download(url,savename)
        os.chmod(savename,0o777)
        subprocess.call(['mv', '-f',savename, exedir])
        print('\n Executable stored:', savename)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("opsys", help="operating system (linux64, macos, or mac-newchip)", type=str)
    args = parser.parse_args().__dict__

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def installexe(opsys: str):
    """
    Command line interface to install non-python executables, specifically
    CRX2RNX and gfzrnx. 

    https://stackoverflow.com/questions/12791997/how-do-you-do-a-simple-chmod-x-from-within-python


    Parameters
    ----------
    opsys : string
        operating system. Allowed values are linux64,  macos, and mac-newchip 
        PC users should use the docker, where these executables 
        come pre-installed

    """

    exedir = os.environ['EXE']
    if not os.path.exists(exedir):
        print('You need to define the EXE environment variable. Exiting')
        sys.exit()
    else:
        print('Your executable environment area: ', exedir)

    checkexist('gzip')
    checkexist('xz')
    checkexist('unzip')
    checkexist('compress')
    checkexist('wget')

    # where the executable files are (currently) stored publicly

    sto = 'https://morefunwithgps.com/public_html/'

    if (opsys == 'linux64'):
        print('Only 64 bit static versions will be provided.')
        print('For 32 bit you will need to check the appropriate websites.')
        savename = 'CRX2RNX'
        url = sto + savename + '.' + opsys + '.e'
        download_chmod_move(url, savename, exedir)

        savename = 'gfzrnx'
        url = sto + 'gfzrnx.' + opsys + '.e'
        download_chmod_move(url, savename, exedir)

        savename = 'teqc'
        if os.path.exists(exedir + '/' + savename):
            print('Executable already exists:', savename)

        else:
            # static executable 64bit
            url = 'https://www.unavco.org/software/data-processing/teqc/development/teqc_CentOSLx86_64s.zip'
            print('Downloading teqc from: ', url)
            try:
                wget.download(url, savename + '.zip')
                subprocess.call(['unzip', savename + '.zip' ])
                subprocess.call(['mv', '-f', savename, exedir])
                subprocess.call(['rm', '-f', savename + '.zip' ])
                print('\n Executable stored:', savename)
            except:
                print('Some kind of kerfuffle trying to install teqc')

    elif (opsys == 'macos'):
        savename = 'CRX2RNX'
        url = sto + savename + '.' + opsys + '.e'
        download_chmod_move(url, savename, exedir)

        savename = 'teqc'
        if os.path.exists(exedir + '/' + savename):
            print('Executable already exists:', savename)
        else:
        # added 2021sep13
            url = 'https://www.unavco.org/software/data-processing/teqc/development/teqc_OSX_i5_gcc4.3d_64.zip'
            print('Downloading teqc from: ', url)
            try:
                wget.download(url, savename + '.zip')
                subprocess.call(['unzip', savename + '.zip' ])
                subprocess.call(['mv', '-f', savename, exedir])
                subprocess.call(['rm', '-f', savename + '.zip' ])
                print('\n Executable stored:', savename)
            except:
                print('Some kind of kerfuffle trying to install teqc')

        savename = 'gfzrnx'
        url = sto + 'gfzrnx.' + opsys + '.e'
        download_chmod_move(url, savename, exedir)
    elif (opsys == 'mac-newchip'):
        print('There is no teqc executable for this architecture, so none will be installed.')
        newchip_hatanaka(exedir)
        newchip_gfzrnx(exedir)

    else:
        print('We do not recognize your operating system input. Exiting.')
        sys.exit()


def main():
    """
    command line code that downloads helper GNSS codes: Hatanaka and gfzrnx

    Parameters
    ----------
    opsys : string
        operating system. Allowed values are linux64,  macos, and mac-newchip
        PC users should use the docker, where these executables
        come pre-installed

    """
    args = parse_arguments()
    installexe(**args)


if __name__ == "__main__":
    main()
