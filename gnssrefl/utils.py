import json
import numpy as np
import os
import platform
import subprocess
import warnings

from enum import Enum
from typing import get_type_hints
from pathlib import Path
from gnssrefl.gnss_frequencies import is_valid_frequency, all_frequencies, get_file_suffix


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
    gnssir_result = "gnssir_result"
    gnssir_failqc_result = "gnssir_failqc_result"
    arcs_directory = "arcs_directory"
    individual_tracks = "individual_tracks"
    vwc_outputs = "vwc_outputs"
    snr_file = "snr_file"
    directory = "directory"
    tracks_file = "tracks_file"
    vwc_tracks_file = "vwc_tracks_file"


# TODO we should do something like this below for all of our file structuring so it's all in one place
# If we decide to change directories paths etc later then we would only need to change it here and nowhere else
class FileManagement:
    """
    FileManagement is designed to easily read the files that this package relies on.
    Required parameters include station and file_type from FileTypes class.
    Optional parameters are year, doy, and file_not_found_ok.
    """

    def __init__(self, station, file_type, year: int = None, doy: int = None, file_not_found_ok: bool = False, frequency: int = None, extension: str = '', snr_type: int = None):
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
            if not is_valid_frequency(frequency):
                raise ValueError(f"Invalid frequency {frequency}. Valid frequencies: {all_frequencies()}")
        
        self.frequency = frequency
        self.extension = extension
        self.snr_type = snr_type

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
                     FileTypes.volumetric_water_content: self._get_volumetric_water_content_path(),
                     FileTypes.tracks_file: self.get_tracks_file_path(),
                     FileTypes.vwc_tracks_file: self.get_vwc_tracks_file_path(),
                     }

            if self.year and self.doy:
                phase_path = self.xdir / str(self.year) / 'phase' / str(self.station)
                if self.extension:
                    phase_path = phase_path / self.extension
                files[FileTypes.phase_file] = phase_path / f'{self.doy:03d}.txt'

                result_path = self.xdir / str(self.year) / 'results' / str(self.station)
                if self.extension:
                    result_path = result_path / self.extension
                files[FileTypes.gnssir_result] = result_path / f'{self.doy:03d}.txt'
                files[FileTypes.gnssir_failqc_result] = result_path / 'failQC' / f'{self.doy:03d}.txt'

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
            if self.file_type == FileTypes.arcs_directory:
                directory_path = self._get_arcs_directory_path()
            elif self.file_type == FileTypes.individual_tracks:
                directory_path = self._get_individual_tracks_path()
            elif self.file_type == FileTypes.vwc_outputs:
                directory_path = self._get_vwc_outputs_path()
            else:
                raise ValueError(f"File type {self.file_type} is not a directory type")

            # Create directory if requested
            if ensure_directory:
                directory_path.mkdir(parents=True, exist_ok=True)

            return directory_path
        else:
            raise ValueError("The file type you requested does not exist")

    def _apriori_rh_base_dir(self):
        """Station-scoped input directory, optionally suffixed with an extension."""
        base_dir = self.xdir / "input" / self.station
        if self.extension:
            base_dir = base_dir / self.extension
        return base_dir

    def _preregistry_apriori_rh_suffix(self):
        """Pre-registry suffix scheme: L1/L2/L5, with L2C (fr=20) aliased to L2."""
        fr = self.frequency
        if fr == 1:
            return "_L1"
        if fr == 5:
            return "_L5"
        # None, 2, 20 all mapped to "_L2" in the old scheme
        return "_L2"

    def _get_apriori_rh_path(self):
        """
        Generate the canonical apriori RH file path using the frequency registry.

        Directory structure:
        - No extension: input/{station}/{station}_phaseRH<suffix>.txt
        - With extension: input/{station}/{extension}/{station}_phaseRH<suffix>.txt

        Suffix comes from gnss_frequencies.get_file_suffix (e.g. '_G_L2C', '_E_L1'),
        matching the convention used by VWC and track files.
        """
        freq_code = self.frequency if self.frequency is not None else 20
        filename = f"{self.station}_phaseRH{get_file_suffix(freq_code)}.txt"
        return self._apriori_rh_base_dir() / filename

    def find_apriori_rh_file(self):
        """
        Find apriori RH file with backwards compatibility fallback.

        Search order:
        1. New (registry) format: input/{station}/[{ext}/]{station}_phaseRH_<C>_<label>.txt
        2. Pre-registry station-dir format: input/{station}/[{ext}/]{station}_phaseRH_L{1,2,5}.txt
        3. Legacy root format: input/{station}_phaseRH[_L1|_L5].txt (L2 has no suffix)

        Returns
        -------
        tuple of (Path, str)
            (file_path, format_type) where format_type is one of
            'new_format', 'preregistry', 'legacy'.
        """
        new_path = self._get_apriori_rh_path()
        if new_path.exists():
            return new_path, 'new_format'

        # Pre-registry station-dir names (L2C aliased to _L2)
        preregistry_path = self._apriori_rh_base_dir() / f"{self.station}_phaseRH{self._preregistry_apriori_rh_suffix()}.txt"
        if preregistry_path.exists():
            return preregistry_path, 'preregistry'

        # Legacy root format: input/{station}_phaseRH[_L1|_L5].txt
        base_dir = self.xdir / "input"
        if self.frequency == 1:
            legacy_path = base_dir / f"{self.station}_phaseRH_L1.txt"
        elif self.frequency in (20, 2) or self.frequency is None:
            legacy_path = base_dir / f"{self.station}_phaseRH.txt"
        elif self.frequency == 5:
            legacy_path = base_dir / f"{self.station}_phaseRH_L5.txt"
        else:
            legacy_path = base_dir / f"{self.station}_phaseRH_L{self.frequency}.txt"

        if legacy_path.exists():
            return legacy_path, 'legacy'

        # Nothing on disk — return new format path for writing
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

    def get_tracks_file_path(self):
        """Path to the multi-GNSS tracks.json file.

        Directory structure:
        - No extension: Files/{station}/tracks.json
        - With extension: Files/{station}/{extension}/tracks.json
        """
        base = self.xdir / "Files" / self.station
        if self.extension:
            base = base / self.extension
        return base / "tracks.json"

    def get_vwc_tracks_file_path(self):
        """Path to the vwc_tracks.json file written by ``vwc_input``.

        Same schema as ``tracks.json`` with one added per-epoch field
        (``apriori_RH``). Consumed by ``phase`` and ``vwc``.

        Directory structure:
        - No extension: Files/{station}/vwc_tracks.json
        - With extension: Files/{station}/{extension}/vwc_tracks.json
        """
        base = self.xdir / "Files" / self.station
        if self.extension:
            base = base / self.extension
        return base / "vwc_tracks.json"

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

    def _get_individual_tracks_path(self):
        """
        Generate individual tracks directory path with extension support.

        Directory structure:
        - No extension: Files/{station}/individual_tracks/
        - With extension: Files/{station}/{extension}/individual_tracks/
        """
        if self.extension:
            return self.xdir / "Files" / self.station / self.extension / "individual_tracks"
        else:
            return self.xdir / "Files" / self.station / "individual_tracks"

    def _get_vwc_outputs_path(self):
        """Per-frequency vwc output directory.

        Directory structure:
        - No extension: Files/{station}/vwc_outputs/{label}/
        - With extension: Files/{station}/{extension}/vwc_outputs/{label}/

        ``label`` comes from ``get_file_suffix`` with the leading underscore
        stripped (e.g. ``G_L1``, ``C_L5``).
        """
        if self.frequency is None:
            raise ValueError("frequency is required for vwc_outputs")
        label = get_file_suffix(self.frequency).lstrip('_')
        base = self.xdir / "Files" / self.station
        if self.extension:
            base = base / self.extension
        return base / "vwc_outputs" / label

    def _get_snr_path(self, uppercase=False):
        """
        Construct the base (uncompressed) SNR file path.

        Path pattern: {REFL_CODE}/{yyyy}/snr/{station}/{station}{doy}0.{yy}.snr{type}
        """
        if not self.year or not self.doy or self.snr_type is None:
            raise ValueError("Year, doy, and snr_type required for SNR files")
        cyyyy = str(self.year)
        cyy = cyyyy[2:]
        cdoy = f'{self.doy:03d}'
        sta = self.station.upper() if uppercase else self.station
        filename = f'{sta}{cdoy}0.{cyy}.snr{self.snr_type}'
        return self.xdir / cyyyy / 'snr' / sta / filename

    def find_snr_file(self, gzip=None):
        """
        Find an SNR file, optionally converting to match the desired storage format.

        Parameters
        ----------
        gzip : bool or None
            If None (default): find whatever exists, no conversion.
            If True: prefer .gz. Compress uncompressed files.
            If False: prefer uncompressed. Decompress .gz files.

        Returns
        -------
        tuple: (Path, bool) - (file_path, found)
        """
        for uppercase in [False, True]:
            base = self._get_snr_path(uppercase=uppercase)
            gz_path = Path(str(base) + '.gz')

            if gzip is None:
                # Read-only: return whatever exists, prefer .gz
                if gz_path.exists():
                    return gz_path, True
                if base.exists():
                    return base, True
            elif gzip:
                if gz_path.exists():
                    return gz_path, True
                if base.exists():
                    subprocess.call(['gzip', str(base)])
                    if gz_path.exists():
                        return gz_path, True
            else:
                if base.exists():
                    return base, True
                if gz_path.exists():
                    subprocess.call(['gunzip', str(gz_path)])
                    if base.exists():
                        return base, True

        return self._get_snr_path(), False

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

QC_FILTER_ORDER = ['track', 'ediff', 'L2C/L5', 'tooclose', 'noise', 'amp', 'pk2noise', 'delT']


def circular_mean_deg(angles):
    """Circular mean of angles in degrees, handling the 0/360 wrap correctly."""
    rad = np.deg2rad(angles)
    return np.rad2deg(np.arctan2(np.mean(np.sin(rad)), np.mean(np.cos(rad)))) % 360


def circular_distance_deg(a, b):
    """Shortest angular distance between two azimuths in degrees.

    Works with scalars and numpy arrays (via broadcasting).
    """
    d = np.abs(a - b) % 360
    return np.minimum(d, 360 - d)


def pre_check_arc(meta, station_config):
    """Quick QC check using arc metadata only. Returns (passed, fail_reason).

    Checks ediff and delT — no LSP results needed, so call before strip_compute.
    """
    e1 = meta['e1']; e2 = meta['e2']
    ediff = station_config['ediff']

    if (meta['ele_start'] - e1) > ediff:
        return False, 'ediff'
    if (meta['ele_end'] - e2) < -ediff:
        return False, 'ediff'
    if meta['delT'] >= station_config['delTmax']:
        return False, 'delT'

    return True, None


def check_arc_quality(meta, peak_rh, max_amp, noise, station_config):
    """Apply QC filters to a single arc. Returns (passed, fail_reason)."""
    e1 = meta['e1']; e2 = meta['e2']
    ediff = station_config['ediff']
    min_height = station_config['minH']; max_height = station_config['maxH']
    pk_noise = station_config['PkNoise']; del_t_max = station_config['delTmax']
    try:
        req_amp = station_config['reqAmp'][station_config['freqs'].index(meta['freq'])]
    except (ValueError, IndexError):
        req_amp = station_config['reqAmp'][0]

    if (meta['ele_start'] - e1) > ediff:
        return False, 'ediff'
    if (meta['ele_end'] - e2) < -ediff:
        return False, 'ediff'

    if (peak_rh == 0) and (max_amp == 0):
        return False, 'tooclose'
    if abs(peak_rh - min_height) < 0.10:
        return False, 'tooclose'
    if abs(peak_rh - max_height) < 0.10:
        return False, 'tooclose'

    if noise <= 0:
        return False, 'noise'
    if max_amp <= req_amp:
        return False, 'amp'
    if max_amp / noise <= pk_noise:
        return False, 'pk2noise'
    if meta['delT'] >= del_t_max:
        return False, 'delT'

    return True, None


def format_qc_summary(freq, n_total, qc_counts, n_saved):
    """Build condensed QC summary showing only filters that rejected arcs."""
    parts = [f'Freq {freq} quality control: {n_total} arcs']
    running = n_total
    for name in QC_FILTER_ORDER:
        n_rejected = qc_counts.get(name, 0)
        if n_rejected > 0:
            running -= n_rejected
            parts.append(f'{name} {running}')
    parts.append(f'{n_saved} saved')
    return ' -> '.join(parts)


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
