import numpy as np
import re
import datetime
import struct

import gnssrefl.gps as g

# Joakim Strandberg wrote this code originally-
# I made some small changes ???  Kristine M. Larson

class RinexError(Exception):
    pass


def getrinexversion(filename):
    """ Scan the file for RINEX version number.

    Parameters
    ----------
    filename : str
        Filename of the rinex file

    Returns
    -------
    version : str
        Version number.
    """
    with open(filename, 'r') as f:
        line = f.readline()
        while 'RINEX VERSION / TYPE' not in line:
            line = f.readline()

            if 'END OF HEADER' in line:
                raise RinexError("No 'RINEX VERSION / TYPE' found.")
    return line[:9].strip()


def readheader(lines, rinexversion):
    # See no reason for keeping this public. Should have been private from the start.
    print("WARNING! Deprecated!")
    return _readheader(lines, rinexversion)


def _readheader(lines, rinexversion):
    """ Read and return header information for the RINEX file

    Parameters
    ----------
    lines : list[str]
        List of each line in the RINEX file.

    rinexversion : str
        Version number for the RINEX file

    Returns
    -------
    header : dict
        Dict containing the header information from the RINEX file.

    headerlines : list[int]
        List of starting line for the headers of each data block.

    headerlengths : list[int]
        List of length for the headers of each data block. 'None' for rinex3.

    obstimes : list[datetime.datetime]
        List of time of measurement for each measurement epoch.

    satlists : list[list[str]]
        List containing lists of satellites present in each block.

    satset : set(str)
        Set containing all satellites in the data.
    """
    try:
        if '2.1' in rinexversion:
            return _readheader_v21x(lines)
        elif '3' in rinexversion:
            return _readheader_v3(lines)
        else:
            raise RinexError('RINEX v%s is not supported.' % rinexversion)

    except KeyError as e:
        raise RinexError('Missing required header %s' % str(e))


def _readheader_v21x(lines):
    """ Read rinex version 2.10 and 2.11 
    """

    header = {}
    # Capture header info

    for i, line in enumerate(lines):
        if "END OF HEADER" in line:
            i += 1  # skip to data
            break

        if line[60:80].strip() not in header:  # Header label
            header[line[60:80].strip()] = line[:60]  # don't strip for fixed-width parsers
            # string with info
        else:
            header[line[60:80].strip()] += "\n"+line[:60]
            # concatenate to the existing string

    rowpersat = 1 + (len(header['# / TYPES OF OBSERV'][6:].split())-1) // 5

    timeoffirstobs = [part for part in header['TIME OF FIRST OBS'].split()]

    headerlines = []
    headerlengths = []
    obstimes = []
    epochsatlists = []
    # for those of who do not like datetime
    gpstime = np.empty(shape=[0, 2])
    satset = set()

    century = int(timeoffirstobs[0][:2]+'00')
    # This will result in an error if the record overlaps the end of the century. So if someone feels this is a major
    # problem, feel free to fix it. Personally can't bother to do it...

    pattern = re.compile('(\s{2}\d|\s\d{2}){2}')

    while i < len(lines):
        if pattern.match(lines[i][:6]):  # then it's the first line in a header record
            if int(lines[i][28]) in (0, 1, 6):  # CHECK EPOCH FLAG  STATUS
                headerlines.append(i)
                year, month, day, hour = lines[i][1:3], lines[i][4:6], lines[i][7:9], lines[i][10:12]
                minute, second = lines[i][13:15], lines[i][16:26]
                obstimes.append(datetime.datetime(year=century+int(year),
                                                  month=int(month),
                                                  day=int(day),
                                                  hour=int(hour),
                                                  minute=int(minute),
                                                  second=int(float(second)),
                                                  microsecond=int(float(second) % 1 * 100000)))

                week, sow = g.kgpsweek(century+int(year), int(month), int(day), int(hour), int(minute), int(float(second)))
                ne = np.array((week,sow))
                gpstime = np.vstack((gpstime,ne))

                numsats = int(lines[i][29:32])  # Number of visible satellites %i3
                headerlengths.append(1 + (numsats-1)//12)  # number of lines in header, depends on how many svs on view

                if numsats > 12:
                    sv = []
                    for s in range(numsats):
                        if s > 0 and s % 12 == 0:
                            i += 1
                        sv.append(lines[i][32+(s % 12)*3:35+(s % 12)*3])
                    epochsatlists.append(sv)

                else:
                    epochsatlists.append([lines[i][32+s*3:35+s*3] for s in range(numsats)])

                i += numsats*rowpersat+1

            else:  # there was a comment or some header info
                flag = int(lines[i][28])
                if flag != 4:
                    print(flag)
                skip = int(lines[i][30:32])
                i += skip+1
        else:
            # We have screwed something up and have to iterate to get to the next header row, or eventually the end.
            i += 1

    for satlist in epochsatlists:
        satset = satset.union(satlist)

    return header, headerlines, headerlengths, obstimes, epochsatlists, satset, gpstime 


def _readheader_v3(lines):
    """ Read rinex version 3 """

    header = {}
    # Capture header info

    for i, line in enumerate(lines):
        if "END OF HEADER" in line:
            i += 1  # skip to data
            break

        if line[60:80].strip() not in header:  # Header label
            header[line[60:80].strip()] = line[:60]  # don't strip for fixed-width parsers
            # string with info
        else:
            header[line[60:80].strip()] += "\n"+line[:60]
            # concatenate to the existing string

    headerlines = []
    obstimes = []
    epochsatlists = []
    satset = set()

    while i < len(lines):
        if lines[i][0] == '>':  # then it's the first line in a header record
            if int(lines[i][31]) in (0, 1, 6):  # CHECK EPOCH FLAG  STATUS
                headerlines.append(i)
                year, month, day, hour = lines[i][2:6], lines[i][7:9], lines[i][10:12], lines[i][13:15]
                minute, second = lines[i][16:18], lines[i][19:30]
                obstimes.append(datetime.datetime(year=int(year),
                                                  month=int(month),
                                                  day=int(day),
                                                  hour=int(hour),
                                                  minute=int(minute),
                                                  second=int(float(second)),
                                                  microsecond=int(float(second) % 1 * 100000)))

                numsats = int(lines[i][33:35])  # Number of visible satellites %i3

                sv = []
                for j in range(numsats):
                    sv.append(lines[i+1+j][:3])

                i += numsats+1
                epochsatlists.append(sv)

            else:  # there was a comment or some header info
                flag = int(lines[i][31])
                if flag != 4:
                    print(flag)
                skip = int(lines[i][30:32])
                i += skip+1
        else:
            # We have screwed something up and have to iterate to get to the next header row, or eventually the end.
            i += 1

    for satlist in epochsatlists:
        satset = satset.union(satlist)

    headerlengths = None
    return header, headerlines, headerlengths, obstimes, epochsatlists, satset


def _converttofloat(numberstr):
    try:
        return float(numberstr)
    except ValueError:
        return np.nan


def _readblocks(lines, rinexversion, header, headerlines, headerlengths, epochsatlists, satset):
    """ Read and return information in the blocks for the RINEX file

    Parameters
    ----------
    lines : list[str]
        List of each line in the RINEX file.

    rinexversion : str
        Version number for the RINEX file.

    header : dict
        Dict containing the header information from the RINEX file.

    headerlines : list[int]
        List of starting line for the headers of each data block.

    headerlengths : list[int]
        List of length for the headers of each data block.

    satlists : list[list[str]]
        List containing lists of satellites present in each block.

    satset : set(str)
        Set containing all satellites in the data.

    Returns
    -------
    observationdata : dict
        Dict with data-arrays.

    satlists : dict
        Dict with lists of visible satellites.

    prntoidx : dict
        Dict with translation dicts.

    obstypes : dict
        Dict with observation types.
    """
    try:
        if '2.1' in rinexversion:
            return _readblocks_v21(lines, header, headerlines, headerlengths, epochsatlists, satset)
        elif '3' in rinexversion:
            return _readblocks_v3(lines, header, headerlines, epochsatlists, satset)
        else:
            raise RinexError('RINEX v%s is not supported.' % rinexversion)

    except KeyError as e:
        raise RinexError('Missing required header %s' % str(e))



def _readblocks_v21(lines, header, headerlines, headerlengths, epochsatlists, satset):
    """ Read the lines of data.

    Parameters
    ----------
    lines : list[str]
        List of each line in the RINEX file.

    header : dict
        Dict containing the header information from the RINEX file.

    headerlines : list[int]
        List of starting line for the headers of each data block.

    headerlengths : list[int]
        List of length for the headers of each data block.

    satlists : list[list[str]]
        List containing lists of satellites present in each block.

    satset : set(str)
        Set containing all satellites in the data.

    Returns
    -------
    observationdata : dict
        Dict with data-arrays.

    satlists : dict
        Dict with lists of visible satellites.

    prntoidx : dict
        Dict with translation dicts.

    obstypes : dict
        Dict with observation types.

    See also
    --------
    processrinexfile : The wrapper.
    """
    observables = header['# / TYPES OF OBSERV'][6:].split()
    nobstypes = len(observables)
    rowpersat = 1 + (nobstypes-1) // 5
    nepochs = len(headerlines)

    systemletters = set([letter for letter in set(''.join(satset)) if letter.isalpha()])
    satlists = {letter: [] for letter in systemletters}

    observationdata = {}
    prntoidx = {}
    obstypes = {}

    for sat in satset:
        satlists[sat[0]].append(int(sat[1:]))

    for letter in systemletters:
        satlists[letter].sort()
        nsats = len(satlists[letter])
        observationdata[letter] = np.nan * np.zeros((nepochs, nsats, nobstypes))
        prntoidx[letter] = {prn: idx for idx, prn in enumerate(satlists[letter])}
        obstypes[letter] = observables  # Proofing for V3 functionality

    fmt = '14s 2x '*nobstypes
    fieldstruct = struct.Struct(fmt)
    parse = fieldstruct.unpack_from

    for iepoch, (headerstart, headerlength, satlist) in enumerate(zip(headerlines, headerlengths, epochsatlists)):
        for i, sat in enumerate(satlist):
            datastring = ''.join(["{:<80}".format(line.rstrip()) for line in
                                  lines[headerstart+headerlength+rowpersat*i:headerstart+headerlength+rowpersat*(i+1)]])
            try:
                data = np.array([_converttofloat(number.decode('ascii')) for number in parse(datastring.encode('ascii'))])

                systemletter = sat[0]
                prn = int(sat[1:])

                observationdata[systemletter][iepoch, prntoidx[systemletter][prn], :] = data
            except struct.error:
                continue

    for letter in observationdata:
        kept_observables = [i for i in range(len(obstypes[letter])) if np.sum(~np.isnan(observationdata[letter][:,:,i]))>0]
        observationdata[letter] = observationdata[letter][:, :, kept_observables]
        obstypes[letter] = [obstypes[letter][i] for i in kept_observables]

    return observationdata, satlists, prntoidx, obstypes


def _readblocks_v3(lines, header, headerlines, epochsatlists, satset):
    """ Read the lines of data for rinex 3 files.

    Parameters
    ----------
    lines : list[str]
        List of each line in the RINEX file.

    header : dict
        Dict containing the header information from the RINEX file.

    headerlines : list[int]
        List of starting line for the headers of each data block.

    satlists : list[list[str]]
        List containing lists of satellites present in each block.

    satset : set(str)
        Set containing all satellites in the data.

    Returns
    -------
    observationdata : dict
        Dict with data-arrays.

    satlists : dict
        Dict with lists of visible satellites.

    prntoidx : dict
        Dict with translation dicts.

    obstypes : dict
        Dict with observation types.

    See also
    --------
    processrinexfile : The wrapper.
    """
    nepochs = len(headerlines)

    obstypes = {}
    systemletter = ''
    for line in header['SYS / # / OBS TYPES'].splitlines():
        if line[0] != ' ':
            systemletter = line[0]
            obstypes[systemletter] = line[6:].split()
        else:
            # It's a continuation line and we just add the obstypes
            obstypes[systemletter].extend(line[6:].split())

    systemletters = [key for key in obstypes]
    satlists = {letter: [] for letter in systemletters}

    observationdata = {}
    prntoidx = {}
    parser = {}

    for sat in satset:
        satlists[sat[0]].append(int(sat[1:]))

    for letter in systemletters:

        if len(satlists[letter]) == 0:
            # No data exist for the system. Delete and skip.
            satlists.pop(letter)
            continue

        satlists[letter].sort()
        nsats = len(satlists[letter])
        nobstypes = len(obstypes[letter])
        observationdata[letter] = np.nan * np.zeros((nepochs, nsats, nobstypes))
        prntoidx[letter] = {prn: idx for idx, prn in enumerate(satlists[letter])}

        fmt = '3x' + '14s 2x ' * (nobstypes-1) + '14s'
        parser[letter] = struct.Struct(fmt)

    for iepoch, (headerstart, satlist) in enumerate(zip(headerlines, epochsatlists)):
        for i, sat in enumerate(satlist):
            datastring = lines[headerstart+1+i]

            systemletter = sat[0]
            prn = int(sat[1:])

            try:
                data = np.array([_converttofloat(number.decode('ascii'))
                                 for number in parser[systemletter].unpack_from(datastring.encode('ascii'))])

                observationdata[systemletter][iepoch, prntoidx[systemletter][prn], :] = data
            except struct.error:
                continue
                #print('Data loss for %s at epoch %i' % (sat, iepoch))

    for letter in observationdata:
        kept_observables = [i for i in range(len(obstypes[letter])) if np.sum(~np.isnan(observationdata[letter][:,:,i]))>0]
        observationdata[letter] = observationdata[letter][:, :, kept_observables]
        obstypes[letter] = [obstypes[letter][i] for i in kept_observables]

    return observationdata, satlists, prntoidx, obstypes


def processrinexfile(filename, savefile=None):
    """ Process a RINEX file into python format

    Parameters
    ----------
    filename : str
        Filename of the rinex file

    savefile : str, optional
        Name of file to save data to. If supplied the data is saved to a compressed npz file.

    Returns
    -------
    observationdata : dict
        Dict with a nobs x nsats x nobstypes nd-array for each satellite constellation containing the measurements. The
        keys of the dict correspond to the systemletter as used in RINEX files (G for GPS, R for GLONASS, etc).

        nobs is the number of observations in the RINEX data, nsats the number of visible satellites for the particular
        system during the whole measurement period, and nobstypes is the number of different properties recorded.

    satlists : dict
        Dict containing the full list of visible satellites during the whole measurement period for each satellite
        constellation.

    prntoidx : dict
        Dict which for each constellation contains a dict which translates the PRN number into the index of the
        satellite in the observationdata array.

    obstypes : dict
        Dict containing the observables recorded for each satellite constellation.

    header : dict
        Dict containing the header information from the RINEX file.

    obstimes : list[datetime.datetime]
        List of time of measurement for each measurement epoch.

    """
    rinexversion = getrinexversion(filename)

    with open(filename, 'r') as f:
        lines = f.read().splitlines(True)

    header, headerlines, headerlengths, obstimes, epochsatlists, satset,gpstime = _readheader(lines, rinexversion)
    observationdata, satlists, prntoidx, obstypes = _readblocks(lines, rinexversion, header, headerlines,
                                                                headerlengths, epochsatlists, satset)

    if savefile is not None:
        saverinextonpz(savefile, observationdata, satlists, prntoidx, obstypes, header, obstimes)

    return observationdata, satlists, prntoidx, obstypes, header, obstimes, gpstime 


def mergerinexfiles(filelist, savefile=None):
    """ Process several rinexfiles and merges them into one file.

    Can be used to for example merge several rinexfiles from the same day to a single file. All files must be from the
    same receiver and have the same version. No guarantees are given if files are from different receivers.

    !!! Currently only functional for RINEX3. !!!


    Parameters
    ----------
    filename : str
        Filename of the rinex file

    savefile : str, optional
        Name of file to save data to. If supplied the data is saved to a compressed npz file.

    Returns
    -------
    observationdata : dict
        Dict with a nobs x nsats x nobstypes nd-array for each satellite constellation containing the measurements. The
        keys of the dict correspond to the systemletter as used in RINEX files (G for GPS, R for GLONASS, etc).

        nobs is the number of observations in the RINEX data, nsats the number of visible satellites for the particular
        system during the whole measurement period, and nobstypes is the number of different properties recorded.

    satlists : dict
        Dict containing the full list of visible satellites during the whole measurement period for each satellite
        constellation.

    prntoidx : dict
        Dict which for each constellation contains a dict which translates the PRN number into the index of the
        satellite in the observationdata array.

    obstypes : dict
        Dict containing the observables recorded for each satellite constellation.

    header : dict
        Dict containing the header information from the first RINEX file.

    obstimes : list[datetime.datetime]
        List of time of measurement for each measurement epoch.
    """

    rinexversion = getrinexversion(filelist[0])

    if '3' in rinexversion:

        with open(filelist[0], 'r') as f:
            lines = f.read().splitlines(True)

        if len(filelist) > 1:
            for filename in filelist[1:]:
                with open(filename, 'r') as f:
                    line = f.readline()
                    while 'END OF HEADER' not in line:
                        line = f.readline()
                    lines.extend(f.read().splitlines(True))

        header, headerlines, headerlengths, obstimes, epochsatlists, satset = _readheader(lines, rinexversion)
        observationdata, satlists, prntoidx, obstypes = _readblocks(lines, rinexversion, header, headerlines,
                                                                    headerlengths, epochsatlists, satset)

        if savefile is not None:
            saverinextonpz(savefile, observationdata, satlists, prntoidx, obstypes, header, obstimes)

        return observationdata, satlists, prntoidx, obstypes, header, obstimes



    else:
        NotImplementedError('Multiple file merging is not implemented for RINEX 2 yet.')
        #TODO: implement

        #for filename in filelist:
        #    if not getrinexversion(filename) == rinexversion:
        #        raise RinexError('All files are not the same RINEX version.')

        #observationdata, satlists, prntoidx, obstypes, header, obstimes = processrinexfile(filename[0], savefile=None)

        #if len(filelist) > 1:
        #    for filename in filelist[1:]:
        #        observationdata_add, satlists_add, prntoidx_add, obstypes_add, header_add, obstimes_add = processrinexfile(filename, savefile=None)

        #        for key in observationdata:
        #            if satlists[key]
        #                observationdata[key] = np.append(observationdata[key], observationdata_add[key])

        # On another level? Sätta ihop data tidigare, dvs läsa alla headers först?



def separateobservables(observationdata, obstypes):
    """
    Parameters
    ----------
    observationdata : dict
        Data dict as returned by processrinexfile, or loadrinexfromnpz.

    obstypes : dict
        Dict with observation types for each system as returned by processrinexfile, or loadrinexfromnpz.

    Returns
    -------
    separatedobservationdata : dict
        Dict for each system where the data for each observable is separated into its own dict. I.e. to access the P1
        data for GPS from a RINEX2 file it is only necessary to write `separatedobservationdata['G']['C1']`.
    """

    separatedobservationdata = dict()
    for systemletter in observationdata:
        separatedobservationdata[systemletter] = dict()
        for idx, obstype in enumerate(obstypes[systemletter]):
            separatedobservationdata[systemletter][obstype] = observationdata[systemletter][:, :, idx]
    return separatedobservationdata


def saverinextonpz(savefile, observationdata, satlists, prntoidx, obstypes, header, obstimes):
    """ Save data to numpy's npz format.

    Parameters
    ----------
    savefile : str
        Path to where to save the data.

    observationdata, satlists, prntoidx, obstypes, header, obstimes: dict
        Data as returned from processrinexfile

    See Also
    --------
    processrinexfile
    """
    savestruct = {'systems': []}

    for systemletter in observationdata:
        savestruct[systemletter+'systemdata'] = observationdata[systemletter]
        savestruct[systemletter+'systemsatlists'] = satlists[systemletter]
        savestruct[systemletter+'prntoidx'] = prntoidx[systemletter]
        savestruct[systemletter+'obstypes'] = obstypes[systemletter]
        savestruct['systems'].append(systemletter)

    savestruct['obstimes'] = obstimes
    savestruct['header'] = header

    np.savez_compressed(savefile, **savestruct)


def loadrinexfromnpz(npzfile):
    """ Load data previously stored in npz-format

    Parameters
    ----------
    npzfile : str
        Path to the stored data.

    Returns
    -------
    observationdata, satlists, prntoidx, obstypes, header, obstimes: dict
        Data in the same format as returned by processrinexfile
    """
    rawdata = np.load(npzfile)

    observationdata = {}
    satlists = {}
    prntoidx = {}
    obstypes = {}

    for systemletter in rawdata['systems']:
        observationdata[systemletter] = rawdata[systemletter+'systemdata']
        satlists[systemletter] = list(rawdata[systemletter+'systemsatlists'])
        prntoidx[systemletter] = rawdata[systemletter+'prntoidx'].item()
        obstypes[systemletter] = list(rawdata[systemletter+'obstypes'])

    header = rawdata['header'].item()
    obstimes = list(rawdata['obstimes'])

    return observationdata, satlists, prntoidx, obstypes, header, obstimes
