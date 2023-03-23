import requests
import subprocess
import gnssrefl.gps as g

from pathlib import Path

# https://pypi.org/project/earthscope-sdk/
from earthscope_sdk.auth.device_code_flow import DeviceCodeFlowSimple
from earthscope_sdk.auth.auth_flow import NoTokensError


def the_kelly_way(url,filename,o_or_d):
    """
    new way to access rinex files at unavco
    using earthscope-sdk
    downloads file, uncompresses, and hatanaka uncompresses

    Parameters
    ----------
    url : string
        path to the file
    filename : string
        rinexfilename you are downloading. Could be hatanaka or not
    o_or_d : string
        o or d file. the latter means hatanaka decompress

    Returns
    -------
    foundit : bool
        whether file was found
    """
    # hatanaka executable name
    crnxpath = g.hatanaka_version()

    # expecting Z compressed 
    rinexfiled = filename[:-2]

    token_path = './'
    device_flow = DeviceCodeFlowSimple(Path(token_path))

    try:
    # get access token from local path
        device_flow.get_access_token_refresh_if_necessary()
    except:
    # if no token was found locally, do the device code flow
        device_flow.do_flow()
    token = device_flow.access_token

    headers = {}
    headers['authorization'] = 'Bearer ' + token

    r = requests.get(url, headers=headers)
    # Opens a local file of same name as remote file for writing to
    # check to see that the file exists
    if (r.status_code == 200):
        with open(filename, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=1000):
                fd.write(chunk)
        fd.close()
        foundit = True
        subprocess.call(['uncompress',filename])
        if o_or_d == 'd':
            print('Hatanaka file was found and converted', filename)
            subprocess.call([crnxpath,rinexfiled])
            subprocess.call(['rm',rinexfiled]) # clean up
        else:
            print('Normal RINEX observation file was found and uncompressed', filename)

    else:
        print('File was not found', filename)
        foundit = False

    return foundit

def the_kelly_simple_way(url,filename):
    """
    new way to access rinex files at unavco
    using earthscope-sdk
    downloads file  - does not translate or uncompress

    Parameters
    ----------
    url : string
        path to the file
    filename : string
        rinexfilename you are downloading. Could be hatanaka or not

    Returns
    -------
    foundit : bool
        whether file was found
    """
    token_path = './'
    device_flow = DeviceCodeFlowSimple(Path(token_path))

    try:
    # get access token from local path
        device_flow.get_access_token_refresh_if_necessary()
    except:
    # if no token was found locally, do the device code flow
        device_flow.do_flow()
    token = device_flow.access_token

    headers = {}
    headers['authorization'] = 'Bearer ' + token

    r = requests.get(url, headers=headers)
    # Opens a local file of same name as remote file for writing to
    # check to see that the file exists
    if (r.status_code == 200):
        print('File was found', filename)
        with open(filename, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=1000):
                fd.write(chunk)
        fd.close()
        foundit = True
    else:
        print('File was not found', filename)
        foundit = False

    return foundit, filename
