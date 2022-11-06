import scipy.io
from scipy.interpolate import interp2d
import os

class EGM96geoid:
    """ Class for EGM96 geoid corrections

    :example:

    >>> egm = EGM06geoid()
    >>> egm.heights(lat=10, lon=30)
    -5.32
    """

    def __init__(self):
        self.geoid = {}

        # Loads the struct called: geoid  
        #
        #    'grid' = geoid height (m) in .25deg steps
        #    'lats' = row vector of latitudes, deg (-92,92)
        #    'lons' = row vector of longitudes, deg (-2,362)

        xdir = os.environ['REFL_CODE']
        # this may go better in the input directory - but using Files for now
        egmfile = xdir + '/Files/' + 'EGM96geoidDATA.mat'
        matdata = scipy.io.loadmat(egmfile)
        names = matdata['geoid'].dtype.names

        for name, arr in zip(names, matdata['geoid'].item()):
            self.geoid[name] = arr.astype('float')

        # create interpolating function from grid data
        self.h = interp2d(self.geoid['lons'][0,:], self.geoid['lats'][0,:], self.geoid['grid'], kind='cubic', bounds_error=True)

    def height(self, lat: float, lon: float):
        # One set of lat lon in, one height out

        lon = lon % 360 # Make sure 0 <= lon < 360

        # Fix geoid height at hundreth of a meter
        return round(self.h(lon, lat)[0], 2)

    
