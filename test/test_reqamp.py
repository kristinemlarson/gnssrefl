"""Unit tests for per-frequency reqAmp handling.

Covers the shared expand_amplitudes helper (used by gnssir_input, gnssir, and
phase to turn a -ampl command-line value into one required amplitude per
frequency) and the warn-and-normalize behaviour of read_json_file when a stored
json has a reqAmp list that does not match its freqs list.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from gnssrefl.utils import expand_amplitudes
from gnssrefl.gnssir_v2 import read_json_file


class TestExpandAmplitudes:
    """The -ampl expand-and-validate rule shared by every CLI."""

    def test_none_returns_none(self):
        """None means the caller keeps its json value / default."""
        assert expand_amplitudes(None, [1, 20, 5]) is None

    def test_scalar_broadcasts(self):
        """A bare scalar broadcasts to every frequency."""
        assert expand_amplitudes(6.0, [1, 20, 5]) == [6.0, 6.0, 6.0]

    def test_single_value_list_broadcasts(self):
        """argparse nargs='*' gives a one-element list for a single value; it broadcasts."""
        assert expand_amplitudes([8.0], [1, 20, 5]) == [8.0, 8.0, 8.0]

    def test_matched_list_used_positionally(self):
        """A list matching the frequency count is used one-per-frequency."""
        assert expand_amplitudes([6.0, 4.0, 2.0], [1, 20, 5]) == [6.0, 4.0, 2.0]

    def test_mismatched_list_exits(self):
        """Any other count is a user error at the prompt: hard exit."""
        with pytest.raises(SystemExit):
            expand_amplitudes([6.0, 4.0], [1, 20, 5])


@pytest.fixture
def temp_refl_code():
    """Temporary REFL_CODE directory so read_json_file resolves a test station json."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        (temp_path / "input" / "test").mkdir(parents=True)
        with patch.dict(os.environ, {'REFL_CODE': str(temp_path)}):
            yield temp_path


def write_config(temp_path, freqs, reqAmp):
    """Write a minimal station json with the given freqs and reqAmp lists."""
    json_path = temp_path / "input" / "test" / "test.json"
    json_path.write_text(json.dumps({'freqs': freqs, 'reqAmp': reqAmp}))
    return json_path


class TestReadJsonFileNormalizesDesync:
    """A desynced stored json warns and normalizes instead of crashing."""

    def test_too_long_reqamp_is_truncated(self, temp_refl_code):
        """reqAmp longer than freqs no longer loads silently; it is trimmed to match."""
        write_config(temp_refl_code, [1, 20, 5], [6.0, 6.0, 6.0, 6.0, 6.0])
        config = read_json_file('test')
        assert len(config['reqAmp']) == len(config['freqs'])

    def test_too_short_reqamp_is_padded(self, temp_refl_code):
        """reqAmp shorter than freqs no longer exits; it is padded to match."""
        write_config(temp_refl_code, [1, 20, 5], [7.0])
        config = read_json_file('test')
        assert len(config['reqAmp']) == len(config['freqs'])
        assert config['reqAmp'] == [7.0, 7.0, 7.0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
