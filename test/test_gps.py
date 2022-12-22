import subprocess
from unittest import mock

import os
import urllib.error
import wget

from gnssrefl.gps import *


def test_get_sopac_navfile_working(mocker):
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


def test_get_sopac_navfile_error(mocker):
    mocker.patch("wget.download")
    mocker.patch("os.path.exists")
    mocker.patch("subprocess.call")
    wget.download.side_effect = urllib.error.URLError("404")
    os.path.exists.return_value = False
    assert (
        get_sopac_navfile("p1031050.20.snr66", "2020", "20", "105")
        == "p1031050.20.snr66"  # should this return None instead?
    )
    wget.download.assert_called_once_with(
        "ftp://garner.ucsd.edu/pub/rinex/2020/105/p1031050.20.snr66.Z",
        "p1031050.20.snr66.Z",
    )
    os.path.exists.assert_called_once_with("p1031050.20.snr66")
    assert subprocess.call.mock_calls == [
        mock.call(["rm", "-f", "p1031050.20.snr66.Z"]),
        mock.call(["rm", "-f", "p1031050.20.snr66"]),
    ]
