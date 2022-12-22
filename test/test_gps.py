import subprocess
from unittest import mock

import os
import wget

from gnssrefl.gps import *


def test_get_sopac_navfile(mocker):
    mocker.patch("wget.download")
    mocker.patch("os.path.exists")
    mocker.patch("subprocess.call")
    os.path.exists.return_value = True
    assert (
        get_sopac_navfile("p1031050.20.snr66", "2020", "20", "105")
        == "p1031050.20.snr66"
    )
    wget.download.assert_called_once_with(
        "ftp://garner.ucsd.edu/pub/rinex/2020/105/p1031050.20.snr66.Z",
        "p1031050.20.snr66.Z",
    )
    os.path.exists.assert_called_once_with("p1031050.20.snr66")
    subprocess.call.assert_called_once_with(["uncompress", "p1031050.20.snr66.Z"])
