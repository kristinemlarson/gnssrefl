import json
import numpy as np
import os
import platform
import warnings

from enum import Enum
from typing import get_type_hints
from pathlib import Path


def frequency_to_name(freq):
    """
    Convert frequency number to standard name.
    
    Parameters
    ----------
    freq : int
        Frequency number
        
    Returns
    -------
    str
        Frequency name (L1, L2C, L5) or Unknown for unsupported frequencies
    """
    freq_map = {1: 'L1', 20: 'L2C', 5: 'L5'}
    return freq_map.get(freq, f'Unknown({freq})')


def validate_input_datatypes(obj, **kwargs):
    hints = get_type_hints(obj)

    # iterate all type hints
    for attr_name, attr_type in hints.items():
        if attr_name == 'return':
            continue
        try:
            if kwargs[attr_name] is None:
                pass
            elif not isinstance(kwargs[attr_name], attr_type):
                raise TypeError('Argument %r is not of type %s' % (attr_name, attr_type))
        except KeyError:
            pass


def str2bool(args, expected_bools):
    if type(expected_bools) is str:
        expected_bools = [expected_bools]
    elif type(expected_bools) is list:
        pass
    else:
        print('str2bool accepts a string or a list of strings')

    for string in expected_bools:
        if isinstance(args[string], bool):
            pass
        elif args[string] is None:
            pass
        elif args[string].lower() in ('yes', 'true', 't', 'y', '1'):
            args[string] = True
        elif args[string].lower() in ('no', 'false', 'f', 'n', '0'):
            args[string] = False

    return args


class FileTypes(str, Enum):
    """
    Files to either read from or save to.
    """
    apriori_rh_file = "apriori_rh_file"
    daily_avg_phase_results = "daily_avg_phase_results"
    make_json = "make_json"
    phase_file = "phase_file"
    volumetric_water_content = "volumetric_water_content"
    directory = "directory"


# TODO we should do something like this below for all of our file structuring so it's all in one place
# If we decide to change directories paths etc later then we would only need to change it here and nowhere else
class FileManagement:
    """
    FileManagement is designed to easily read the files that this package relies on.
    Required parameters include station and file_type from FileTypes class.
    Optional parameters are year, doy, and file_not_found_ok.
    """

    def __init__(self, station, file_type: FileTypes, year: int = None, doy: int = None, file_not_found_ok: bool = False, frequency: int = None, extension: str = ''):
        self.station = station
        self.file_type: FileTypes = file_type
        self.year = year
        self.doy = doy
        self.file_not_found_ok = file_not_found_ok
        self.frequency = frequency
        self.extension = extension

        self.xdir = Path(os.environ["REFL_CODE"])

    def get_file_path(self):
        """
        Get the path of a specific file from the FileTypes class.
        Returns file paths requested as a string
        """
        if self.file_type in FileTypes.__dict__.keys():
            files = {FileTypes.apriori_rh_file: self._get_apriori_rh_path(),
                     FileTypes.daily_avg_phase_results: self.xdir / "Files" / f"{self.station}_phase.txt",
                     FileTypes.make_json: self._get_json_path(),
                     FileTypes.volumetric_water_content: self.xdir / "Files" / f"{self.station}_vwc.txt"
                     }

            if self.year and self.doy:
                files[FileTypes.phase_file] = self.xdir / str(self.year) / 'phase' / str(self.station) / f'{self.doy:03d}.txt'

            return files[self.file_type]
        else:
            raise ValueError("The file type you requested does not exist")

    def _get_apriori_rh_path(self):
        """
        Generate backwards-compatible apriori RH file paths with frequency and extension support.
        
        New naming convention:
        - No extension: {station}_phaseRH_L{freq}.txt  
        - With extension: {station}_phaseRH_L{freq}_{extension}.txt
        
        Fallback for legacy files:
        - L2 legacy: {station}_phaseRH.txt (no L2 suffix)
        - L1 legacy: {station}_phaseRH_L1.txt
        """
        # Determine base directory
        base_dir = self.xdir / "input"
        if self.extension:
            base_dir = base_dir / self.extension
        
        # Generate new format filename
        if self.frequency is None:
            # Default to L2 if no frequency specified
            freq_suffix = "L2"
        else:
            freq_suffix = f"L{self.frequency}"
        
        if self.extension:
            filename = f"{self.station}_phaseRH_{freq_suffix}_{self.extension}.txt"
        else:
            filename = f"{self.station}_phaseRH_{freq_suffix}.txt"
        
        return base_dir / filename

    def find_apriori_rh_file(self):
        """
        Find apriori RH file with backwards compatibility fallback.
        
        Search order:
        1. New format: {station}_phaseRH_L{freq}[_{extension}].txt
        2. Legacy fallback: {station}_phaseRH[_L1].txt (L2 default, L1 explicit)
        
        Returns: (Path, bool) - (file_path, is_legacy_format)
        """
        # Try new format first
        new_path = self._get_apriori_rh_path()
        if new_path.exists():
            return new_path, False
        
        # Try legacy format fallback
        base_dir = self.xdir / "input"  # Legacy files are always in root input/
        
        if self.frequency == 1:
            # L1 legacy format
            legacy_path = base_dir / f"{self.station}_phaseRH_L1.txt"
        else:
            # L2 legacy format (no frequency suffix)
            legacy_path = base_dir / f"{self.station}_phaseRH.txt"
        
        if legacy_path.exists():
            return legacy_path, True
        
        # Return new format path even if it doesn't exist (for writing new files)
        return new_path, False

    def _get_json_path(self):
        """
        Generate JSON file paths with station/extension directory structure.
        
        New directory structure:
        - No extension: input/{station}/{station}.json
        - With extension: input/{station}/{extension}/{station}.json
        """
        if self.extension:
            json_dir = self.xdir / "input" / self.station / self.extension
            return json_dir / f"{self.station}.json"
        else:
            json_dir = self.xdir / "input" / self.station
            return json_dir / f"{self.station}.json"

    def find_json_file(self):
        """
        Find JSON file with backwards compatibility fallback.
        
        Search order (no cross-priority):
        - No extension: 
          1. input/{station}/{station}.json (new format)
          2. input/{station}.json (legacy fallback)
        - With extension:
          1. input/{station}/{extension}/{station}.json (new format)  
          2. input/{station}.{extension}.json (legacy fallback)
        
        Returns: (Path, str) - (file_path, format_type)
        """
        if self.extension:
            # Extension specified: try new extension format first
            extension_dir_path = self.xdir / "input" / self.station / self.extension / f"{self.station}.json"
            if extension_dir_path.exists():
                return extension_dir_path, 'extension_dir'
            
            # Fall back to legacy extension format
            legacy_ext_path = self.xdir / "input" / f"{self.station}.{self.extension}.json"
            if legacy_ext_path.exists():
                return legacy_ext_path, 'legacy_extension'
        else:
            # No extension: try new station format first
            station_dir_path = self.xdir / "input" / self.station / f"{self.station}.json"
            if station_dir_path.exists():
                return station_dir_path, 'station_dir'
            
            # Fall back to legacy station format
            legacy_station_path = self.xdir / "input" / f"{self.station}.json"
            if legacy_station_path.exists():
                return legacy_station_path, 'legacy_station'
        
        # Return new format path for writing
        return self._get_json_path(), 'new_format'

    def read_file(self, transpose=False, **kwargs):
        """
        Reads the requested file amd returns results of file as an array.
        Can use transpose parameter to transpose the results.
        """
        file_path = self.get_file_path()
        if file_path.exists():
            pass
        else:
            if not self.file_not_found_ok:
                raise FileNotFoundError(f"{file_path} does not exist.")
        if file_path.suffix == ".json":
            with open(file_path, 'r') as my_json:
                return json.load(my_json)
        else:
            if file_path.stat().st_size > 0:
                result = np.genfromtxt(file_path, **kwargs)

                if transpose is False:
                    return result
                else:
                    return result.T


def read_files_in_dir(directory, transpose=False):
    """
    Read all files in a given directory. Directory given must be an absolute path.
    Returns an n-d array of results.
    Can use optional parameter transpose to transpose the results.
    """
    dir_path = Path(directory)
    if dir_path.is_absolute():
        # Make sure directory exists
        if dir_path.exists():
            # Make sure given path is a directory - not a file
            if dir_path.is_dir():
                data = []
                #result_files = list(dir_path.glob("*.txt"))
                result_files = list(dir_path.glob("???.txt"))
                if result_files is not None:
                    for file in result_files:

                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            file_data = np.genfromtxt(file, comments='%')

                        if (len(file_data) > 0):
                            if len(np.shape(file_data)) == 1:
                                data.append(file_data)
                            else:
                                data.extend(file_data)
                    if data is not None:
                        if transpose:
                            data = np.array(data)
                            return data.T
                        else:
                            return data
                    else:
                        print(f"Files returned no data")
                else:
                    print(f"There are no files to read in this directory: {dir_path}")
            else:
                raise NotADirectoryError(f"path is not a directory. {dir_path}")
        else:
            print(f"Directory does not exist: {dir_path}")
    else:
        raise ValueError(f"path is not absolute. Please provide an absolute path: {dir_path}")

def check_environment():
    try:
        os.environ['ORBITS']
        os.environ['REFL_CODE']
        os.environ['EXE']

        environment_set = True
    except KeyError:
        environment_set = False

    return environment_set


def set_environment(refl_code, orbits, exe):
    os.environ['ORBITS'] = str(Path(orbits))
    os.environ['REFL_CODE'] = str(Path(refl_code))
    os.environ['EXE'] = str(Path(exe))
    print('environment variable ORBITS set to path', os.environ['ORBITS'],
          '\nenvironment variable REFL_CODE set to path', os.environ['REFL_CODE'],
          '\nenvironment variable EXE set to path', os.environ['EXE'])


def get_sys():
    system = platform.platform().lower()
    valid_os = ['linux64', 'macos']

    for os in valid_os:
        if os in system:
            if os == 'macos':
                if platform.processor() == 'arm':
                    os = 'mac-newchip'
            return os
