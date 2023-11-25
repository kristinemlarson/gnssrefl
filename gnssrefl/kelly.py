import numpy as np
import os
import requests
import subprocess
import time

import gnssrefl.gps as g

from pathlib import Path

# https://pypi.org/project/earthscope-sdk/
from earthscope_sdk.auth.device_code_flow import DeviceCodeFlowSimple
from earthscope_sdk.auth.auth_flow import NoTokensError


def the_kelly_simple_way(url,filename):
    """
    new way to access rinex files at unavco
    using earthscope-sdk
    downloads file  - does not translate or uncompress

    Updated 2023 august 20 to place and expect the token in REFL_CODE

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
    thedir = os.environ['REFL_CODE']
    token_path = thedir
    #print(token_path)
    device_flow = DeviceCodeFlowSimple(Path(token_path))

    print('Seeking permission from Earthscope to use their archive')
    # had turned this off when nothing worked
    if True:
        try:
    # get access token from local path
            pat = 'path1'
            device_flow.get_access_token_refresh_if_necessary()
        except:
    # if no token was found locally, do the device code flow
            pat = 'path2'
            device_flow.do_flow()

    device_flow.get_access_token_refresh_if_necessary()

    s1 = time.time()
    token = device_flow.access_token
    s2 = time.time()
    #print('Time it took doing whatever ', s2-s1)

    headers = {}
    headers['authorization'] = 'Bearer ' + token

    s1 = time.time()
    r = requests.get(url, headers=headers)
    s2 = time.time()
    # Opens a local file of same name as remote file for writing to
    # check to see that the file exists
    if (r.status_code == requests.codes.ok):
        #print('File was found', filename)
        with open(filename, 'wb') as f:
            for data in r:
                f.write(data)
        #f.close() 

        foundit = True
    else:
        #print('File was not found', filename)
        foundit = False

    return foundit, filename
