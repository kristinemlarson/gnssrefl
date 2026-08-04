import gzip
import stat

import pytest

from gnssrefl.rinex2snr import *
from gnssrefl.gps import *

import gnssrefl.rinex2snr as rnx
import gnssrefl.rinex2snr_cl as rnx_cl


REFL_CODE = os.environ["REFL_CODE"]

HEADER3 = ('{0:<60s}RINEX VERSION / TYPE\n'.format('     3.04           OBSERVATION DATA    M') +
           '{0:<60s}MARKER NAME\n'.format('FUNN') +
           '{0:<60s}TIME OF FIRST OBS\n'.format('  2022     1    15     0     0    0.0000000     GPS') +
           '{0:<60s}END OF HEADER\n'.format(''))
HEADER2 = HEADER3.replace('     3.04 ', '     2.11 ')
CRINEX = '{0:<60s}CRINEX VERS   / TYPE\n'.format('3.0                 COMPACT RINEX FORMAT') + HEADER3
NAVIGATION = HEADER3.replace('OBSERVATION DATA    M', 'N: GNSS NAV DATA    M')


@pytest.fixture
def gnssrefl_dirs(tmp_path, monkeypatch):
    """points REFL_CODE and ORBITS at empty directories so nothing real is read or written"""
    monkeypatch.setenv('REFL_CODE', str(tmp_path / 'refl_code'))
    monkeypatch.setenv('ORBITS', str(tmp_path / 'orbits'))
    os.makedirs(tmp_path / 'orbits')


@pytest.fixture
def translated(tmp_path, monkeypatch, gnssrefl_dirs):
    """stands in for CRX2RNX, and records what conv2snr was handed"""
    crnxpath = tmp_path / 'CRX2RNX'
    crnxpath.write_text('#!/bin/sh\ncp "$1" "${1%.*}.rnx"\n')
    crnxpath.chmod(crnxpath.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setattr(rnx.g, 'hatanaka_version', lambda: str(crnxpath))

    calls = []

    def fake_conv2snr(year, doy, station, option, orbtype, receiverrate, dec_rate, archive, log, **kwargs):
        given = kwargs.get('rinex3_filename') or kwargs.get('rinex2_filename')
        calls.append({'given': given, 'contents': open(given).read(), 'kwargs': kwargs})
        log.close()

    monkeypatch.setattr(rnx, 'conv2snr', fake_conv2snr)
    return calls


@pytest.fixture
def handed_over(monkeypatch, gnssrefl_dirs):
    """records what the command line worked out and passed on, without translating anything"""
    calls = []
    monkeypatch.setattr(rnx, 'translate_rinex_file', lambda *args: calls.append(args))
    return calls


def test_quickname():
    assert quickname("p103", 2020, "20", "105", "99") == f"{REFL_CODE}/2020/snr/p103/p1031050.20.snr99"


@pytest.mark.parametrize("name, contents, expected", [
    ('MCHL00AUS_R_20220150000_01D_30S_MO.crx.gz', None, ('mchl', 2022, 15, 3)),
    ('p0411320.20o', None, ('p041', 2020, 132, 2)),
    ('tgho0010.99o.Z', None, ('tgho', 1999, 1, 2)),
    ('name_that_helps_nobody', HEADER3, ('funn', 2022, 15, 3)),
    ('funn0150.22o', HEADER3, ('funn', 2022, 15, 3)),
    ('name_that_helps_nobody', 'this is not a RINEX file at all\n', (None, None, None, 0)),
    ('BRDC00IGS_R_20220150000_01D_MN.rnx', NAVIGATION, ('brdc', 2022, 15, 0)),
])
def test_identify_rinex_file(tmp_path, name, contents, expected):
    obsfile = tmp_path / name
    if contents:
        obsfile.write_text(contents)
    assert identify_rinex_file(str(obsfile)) == expected


@pytest.mark.parametrize("name, contents, kwarg, ending", [
    ('FUNN00XXX_R_20220150000_01D_30S_MO.rnx.gz', HEADER3, 'rinex3_filename', '.rnx'),
    ('funn0150.22o', HEADER2, 'rinex2_filename', '.22o'),
    ('FUNN00XXX_R_20220150000_01D_30S_MO.crx.gz', CRINEX, 'rinex3_filename', '.rnx'),
    ('data_from_the_receiver', CRINEX, 'rinex3_filename', '.rnx'),
    ('FUNN00XXX_R_20220150000_01D_30S_MO.crx', HEADER3, 'rinex3_filename', '.crx'),
])
def test_translate_rinex_file(tmp_path, translated, name, contents, kwarg, ending):
    obsfile = tmp_path / name
    if name.endswith('.gz'):
        with gzip.open(obsfile, 'wt') as f:
            f.write(contents)
    else:
        obsfile.write_text(contents)

    rnx.translate_rinex_file(str(obsfile), 'funn', 2022, 15, 66, 'gbm', 0, False, True)

    assert [kwarg] == list(translated[0]['kwargs'].keys() - {'gzip'})
    assert translated[0]['given'].endswith(ending)
    assert translated[0]['contents'] == contents
    assert obsfile.read_bytes()
    assert not os.path.isdir(os.path.dirname(translated[0]['given']))


def test_cl_input_file(tmp_path, handed_over):
    obsfile = tmp_path / 'name_that_helps_nobody'
    obsfile.write_text(HEADER3)

    rnx_cl.rinex2snr(input_file=str(obsfile), orb='gnss')
    rnx_cl.rinex2snr('abcd', 2021, 300, input_file=str(obsfile), orb='gnss')

    assert handed_over[0][1:6] == ('funn', 2022, 15, 66, 'gbm')
    assert handed_over[1][1:4] == ('abcd', 2021, 300)


def test_cl_input_folder(tmp_path, handed_over):
    folder = tmp_path / 'campaign'
    os.makedirs(folder / 'subdir')
    (folder / 'FUNN00XXX_R_20220150000_01D_30S_MO.rnx').write_text(HEADER3)
    (folder / 'abcd0300.21o').write_text(HEADER2)
    (folder / 'readme.txt').write_text('notes about the campaign\n')
    (folder / 'subdir' / 'wxyz0300.21o').write_text(HEADER2)

    rnx_cl.rinex2snr(input_folder=str(folder), orb='gnss')

    # the readme is skipped, the subdirectory is not searched, and both files get the orbit given
    assert [call[1:4] for call in handed_over] == [('abcd', 2021, 30), ('funn', 2022, 15)]
    assert [call[5] for call in handed_over] == ['gbm', 'gbm']


def test_cl_input_folder_keeps_going_after_a_bad_file(tmp_path, monkeypatch, gnssrefl_dirs):
    folder = tmp_path / 'campaign'
    os.makedirs(folder)
    for name in ['aaaa0300.21o', 'bbbb0300.21o', 'cccc0300.21o']:
        (folder / name).write_text(HEADER2)
    seen = []

    def explode(input_file, station, *args):
        seen.append(station)
        if station == 'bbbb':
            raise RuntimeError('rinpy could not read this one')

    monkeypatch.setattr(rnx, 'translate_rinex_file', explode)
    rnx_cl.rinex2snr(input_folder=str(folder), orb='gnss')

    assert seen == ['aaaa', 'bbbb', 'cccc']


def test_cl_refusals(tmp_path, handed_over):
    folder = tmp_path / 'campaign'
    os.makedirs(folder)
    junk = tmp_path / 'name_that_helps_nobody'
    junk.write_text('this is not a RINEX file at all\n')

    rnx_cl.rinex2snr(input_file=str(junk))
    rnx_cl.rinex2snr(input_file=str(folder))
    rnx_cl.rinex2snr(input_file=str(junk), input_folder=str(folder))
    rnx_cl.rinex2snr('abcd', 2021, 30, input_folder=str(folder))
    rnx_cl.rinex2snr()

    assert handed_over == []
