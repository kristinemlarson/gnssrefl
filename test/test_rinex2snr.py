from gnssrefl.rinex2snr import *
from gnssrefl.gps import *


REFL_CODE = os.environ["REFL_CODE"]

def test_quickname():
    assert (
        quickname("p103", 2020, "20", "105", "99")
        == f"{REFL_CODE}/2020/snr/p103/p1031050.20.snr99"
    )


#def test_geoidCorrection():
#    assert (
#        geoidCorrection(48.54619475, -123.00761051)
#        == -20.85
#    )


