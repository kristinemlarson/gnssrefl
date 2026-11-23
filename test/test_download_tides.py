import pytest

import gnssrefl.download_tides as download_tides


@pytest.fixture
def calls(monkeypatch, tmp_path):
    monkeypatch.setenv('REFL_CODE', str(tmp_path))
    monkeypatch.setattr(download_tides.g, 'check_environ_variables', lambda: None)
    seen = {}
    monkeypatch.setattr(download_tides.download_noaa, 'download_noaa', lambda *a: seen.setdefault('noaa', a))
    monkeypatch.setattr(download_tides.download_ioc, 'download_ioc', lambda *a: seen.setdefault('ioc', a))
    return seen


def run(monkeypatch, *argv):
    monkeypatch.setattr('sys.argv', ['download_tides', *argv])
    download_tides.main()


def test_noaa_passes_datum_and_subdir(monkeypatch, calls):
    run(monkeypatch, '8768094', 'noaa', '-date1', '20210101', '-date2', '20210103', '-datum', 'navd', '-subdir', 'xx')
    assert calls['noaa'] == ('8768094', '20210101', '20210103', None, False, 'navd', 'xx')


def test_noaa_datum_defaults_to_mllw(monkeypatch, calls):
    run(monkeypatch, '8768094', 'noaa', '-date1', '20210101', '-date2', '20210103')
    assert calls['noaa'] == ('8768094', '20210101', '20210103', None, False, 'mllw', None)


def test_ioc_passes_sensor_and_subdir(monkeypatch, calls):
    run(monkeypatch, 'thul', 'ioc', '-date1', '20210101', '-date2', '20210103', '-sensor', 'rad', '-subdir', 'xx')
    assert calls['ioc'] == ('thul', '20210101', '20210103', None, False, False, 'rad', 'xx')
