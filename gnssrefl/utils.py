import json
import numpy as np
import os
import platform
import warnings

from enum import Enum
from typing import get_type_hints
from pathlib import Path


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
    arcs_directory = "arcs_directory"
    directory = "directory"


# TODO we should do something like this below for all of our file structuring so it's all in one place
# If we decide to change directories paths etc later then we would only need to change it here and nowhere else
class FileManagement:
    """
    FileManagement is designed to easily read the files that this package relies on.
    Required parameters include station and file_type from FileTypes class.
    Optional parameters are year, doy, and file_not_found_ok.
    """

    def __init__(self, station, file_type, year: int = None, doy: int = None, file_not_found_ok: bool = False, frequency: int = None, extension: str = ''):
        self.station = station
        
        # Convert string to FileTypes enum if needed for better usability
        if isinstance(file_type, str):
            if not hasattr(FileTypes, file_type):
                valid_types = [attr for attr in dir(FileTypes) if not attr.startswith('_')]
                raise ValueError(f"Unknown file type: '{file_type}'. Valid types: {valid_types}")
            self.file_type = getattr(FileTypes, file_type)
        else:
            self.file_type = file_type
        self.year = year
        self.doy = doy
        self.file_not_found_ok = file_not_found_ok
        # Validate frequency parameter
        if frequency is not None:
            VALID_FREQUENCIES = [1, 5, 20]
            if frequency not in VALID_FREQUENCIES:
                raise ValueError(f"Invalid frequency {frequency}. Valid frequencies: {VALID_FREQUENCIES}")
        
        self.frequency = frequency
        self.extension = extension

        if "REFL_CODE" not in os.environ:
            raise EnvironmentError("REFL_CODE environment variable not set")
        self.xdir = Path(os.environ["REFL_CODE"])

    def get_file_path(self, ensure_directory=True):
        """
        Get the path of a specific file from the FileTypes class.
        
        Parameters
        ----------
        ensure_directory : bool, optional
            If True, creates the parent directory if it doesn't exist. Default is True.
            
        Returns
        -------
        Path
            File path requested as a Path object
        """
        if isinstance(self.file_type, FileTypes):
            files = {FileTypes.apriori_rh_file: self._get_apriori_rh_path(),
                     FileTypes.daily_avg_phase_results: self._get_daily_avg_phase_path(),
                     FileTypes.make_json: self._get_json_path(),
                     FileTypes.volumetric_water_content: self._get_volumetric_water_content_path()
                     }

            if self.year and self.doy:
                phase_path = self.xdir / str(self.year) / 'phase' / str(self.station)
                if self.extension:
                    phase_path = phase_path / self.extension
                files[FileTypes.phase_file] = phase_path / f'{self.doy:03d}.txt'

            file_path = files[self.file_type]
            
            # Create directory if requested
            if ensure_directory:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
            return file_path
        else:
            raise ValueError("The file type you requested does not exist")

    def get_directory_path(self, ensure_directory=True):
        """
        Get the path of a specific directory from the FileTypes class.
        
        Parameters
        ----------
        ensure_directory : bool, optional
            If True, creates the directory if it doesn't exist. Default is True.
            
        Returns
        -------
        Path
            Directory path requested as a Path object
        """
        if isinstance(self.file_type, FileTypes):
            directories = {FileTypes.arcs_directory: self._get_arcs_directory_path()}
            
            if self.file_type not in directories:
                raise ValueError(f"File type {self.file_type} is not a directory type")
            
            directory_path = directories[self.file_type]
            
            # Create directory if requested
            if ensure_directory:
                directory_path.mkdir(parents=True, exist_ok=True)
                
            return directory_path
        else:
            raise ValueError("The file type you requested does not exist")

    def _get_apriori_rh_path(self):
        """
        Generate apriori RH file paths with station/extension directory structure.
        
        Directory structure:
        - No extension: input/{station}/{station}_phaseRH_L{freq}.txt
        - With extension: input/{station}/{extension}/{station}_phaseRH_L{freq}.txt
        
        Fallback for legacy files in input/ root directory.
        """
        # Determine base directory with station/extension structure
        base_dir = self.xdir / "input" / self.station
        if self.extension:
            base_dir = base_dir / self.extension
        
        # Generate clean filename (extension handled by directory structure)
        if self.frequency is None:
            # Default to L2 if no frequency specified
            freq_suffix = "L2"
        elif self.frequency == 20:
            freq_suffix = "L2"  # Map L2C (20) to clean L2 naming
        else:
            freq_suffix = f"L{self.frequency}"
        
        filename = f"{self.station}_phaseRH_{freq_suffix}.txt"
        
        return base_dir / filename

    def find_apriori_rh_file(self):
        """
        Find apriori RH file with backwards compatibility fallback.
        
        Search order:
        1. New format: input/{station}/[{extension}/]{station}_phaseRH_L{freq}.txt
        2. Legacy fallback: input/{station}_phaseRH[_L1|_L5].txt (L2 has no suffix)
        
        Returns:
            tuple: (Path, str) - (file_path, format_type)
                format_type: 'new_format', 'legacy'
        """
        # Try new format first
        new_path = self._get_apriori_rh_path()
        if new_path.exists():
            return new_path, 'new_format'
        
        # Try legacy format fallback in root input/ directory
        base_dir = self.xdir / "input"
        
        if self.frequency == 1:
            legacy_path = base_dir / f"{self.station}_phaseRH_L1.txt"
        elif self.frequency == 20 or self.frequency is None:
            # L2C legacy has no frequency suffix for backwards compatibility
            legacy_path = base_dir / f"{self.station}_phaseRH.txt"
        elif self.frequency == 5:
            legacy_path = base_dir / f"{self.station}_phaseRH_L5.txt"
        else:
            legacy_path = base_dir / f"{self.station}_phaseRH_L{self.frequency}.txt"
        
        if legacy_path.exists():
            return legacy_path, 'legacy'
        
        # Return new format path for writing new files
        return new_path, 'new_format'

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

    def _get_daily_avg_phase_path(self):
        """
        Generate phase file paths with station/extension directory structure.
        
        New directory structure:
        - No extension: Files/{station}/{station}_phase.txt
        - With extension: Files/{station}/{extension}/{station}_phase.txt
        """
        if self.extension:
            phase_dir = self.xdir / "Files" / self.station / self.extension
            return phase_dir / f"{self.station}_phase.txt"
        else:
            phase_dir = self.xdir / "Files" / self.station
            return phase_dir / f"{self.station}_phase.txt"

    def find_daily_avg_phase_file(self):
        """
        Find daily average phase file with backwards compatibility fallback.
        
        Search order:
        - No extension: 
          1. Files/{station}/{station}_phase.txt (new format)
          2. Files/{station}_phase.txt (legacy fallback)
        - With extension:
          1. Files/{station}/{extension}/{station}_phase.txt (new format)  
          2. Files/{station}_phase.txt (legacy fallback - no extension separation in legacy)
        
        Returns: (Path, str) - (file_path, format_type)
        """
        if self.extension:
            # Extension specified: try new extension format first
            extension_dir_path = self.xdir / "Files" / self.station / self.extension / f"{self.station}_phase.txt"
            if extension_dir_path.exists():
                return extension_dir_path, 'extension_dir'
            
            # Fall back to legacy format (no extension distinction in legacy)
            legacy_path = self.xdir / "Files" / f"{self.station}_phase.txt"
            if legacy_path.exists():
                return legacy_path, 'legacy'
        else:
            # No extension: try new station format first
            station_dir_path = self.xdir / "Files" / self.station / f"{self.station}_phase.txt"
            if station_dir_path.exists():
                return station_dir_path, 'station_dir'
            
            # Fall back to legacy format
            legacy_path = self.xdir / "Files" / f"{self.station}_phase.txt"
            if legacy_path.exists():
                return legacy_path, 'legacy'
        
        # Return new format path for writing
        return self._get_daily_avg_phase_path(), 'new_format'

    def _get_volumetric_water_content_path(self):
        """
        Generate volumetric water content file paths with station/extension directory structure.
        
        New directory structure:
        - No extension: Files/{station}/{station}_vwc.txt
        - With extension: Files/{station}/{extension}/{station}_vwc.txt
        """
        if self.extension:
            vwc_dir = self.xdir / "Files" / self.station / self.extension
            return vwc_dir / f"{self.station}_vwc.txt"
        else:
            vwc_dir = self.xdir / "Files" / self.station
            return vwc_dir / f"{self.station}_vwc.txt"

    def find_volumetric_water_content_file(self):
        """
        Find volumetric water content file with backwards compatibility fallback.
        
        Search order:
        - No extension: 
          1. Files/{station}/{station}_vwc.txt (new format)
          2. Files/{station}_vwc.txt (legacy fallback)
        - With extension:
          1. Files/{station}/{extension}/{station}_vwc.txt (new format)  
          2. Files/{station}_vwc.txt (legacy fallback - no extension separation in legacy)
        
        Returns: (Path, str) - (file_path, format_type)
        """
        if self.extension:
            # Extension specified: try new extension format first
            extension_dir_path = self.xdir / "Files" / self.station / self.extension / f"{self.station}_vwc.txt"
            if extension_dir_path.exists():
                return extension_dir_path, 'extension_dir'
            
            # Fall back to legacy format (no extension distinction in legacy)
            legacy_path = self.xdir / "Files" / f"{self.station}_vwc.txt"
            if legacy_path.exists():
                return legacy_path, 'legacy'
        else:
            # No extension: try new station format first
            station_dir_path = self.xdir / "Files" / self.station / f"{self.station}_vwc.txt"
            if station_dir_path.exists():
                return station_dir_path, 'station_dir'
            
            # Fall back to legacy format
            legacy_path = self.xdir / "Files" / f"{self.station}_vwc.txt"
            if legacy_path.exists():
                return legacy_path, 'legacy'
        
        # Return new format path for writing
        return self._get_volumetric_water_content_path(), 'new_format'

    def _get_arcs_directory_path(self):
        """
        Generate arcs directory path with extension support.
        
        Directory structure:
        - No extension: {year}/arcs/{station}/{doy}/
        - With extension: {year}/arcs/{station}/{extension}/{doy}/
        """
        if not self.year or not self.doy:
            raise ValueError("Year and day of year required for arcs directory")
        
        cdoy = f'{self.doy:03d}'
        
        if self.extension:
            # With extension: {year}/arcs/{station}/{extension}/{doy}/
            return self.xdir / str(self.year) / "arcs" / self.station / self.extension / cdoy
        else:
            # No extension: {year}/arcs/{station}/{doy}/
            return self.xdir / str(self.year) / "arcs" / self.station / cdoy

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
