"""
Unit tests for FileManagement class improvements in the improved_RH_filestructure branch.

Tests cover:
- New directory structure implementation
- Backwards compatibility fallback logic
- Extension parameter handling
- Edge cases and error conditions
- Path resolution priority

These tests are designed to run fast and locally without requiring external data processing.
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from gnssrefl.utils import FileManagement, FileTypes


@pytest.fixture
def temp_refl_code():
    """Create a temporary REFL_CODE directory structure for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create basic directory structure
        (temp_path / "input").mkdir()
        (temp_path / "Files").mkdir()
        (temp_path / "2023" / "phase").mkdir(parents=True)
        
        with patch.dict(os.environ, {'REFL_CODE': str(temp_path)}):
            yield temp_path


class TestFileManagementBasics:
    """Test basic FileManagement functionality."""
    
    def test_string_file_type_conversion(self, temp_refl_code):
        """Test that string file types are properly converted to FileTypes enum."""
        fm = FileManagement("TEST", "make_json")
        assert fm.file_type == FileTypes.make_json
    
    def test_invalid_string_file_type_raises_error(self, temp_refl_code):
        """Test that invalid string file types raise appropriate error."""
        with pytest.raises(ValueError, match="Unknown file type: 'invalid_type'"):
            FileManagement("TEST", "invalid_type")
    
    def test_enum_file_type_accepted(self, temp_refl_code):
        """Test that FileTypes enum values are accepted directly."""
        fm = FileManagement("TEST", FileTypes.make_json)
        assert fm.file_type == FileTypes.make_json


class TestJSONFileHandling:
    """Test JSON file path resolution and fallback logic."""
    
    def test_json_path_no_extension_new_format(self, temp_refl_code):
        """Test JSON path generation for new directory structure without extension."""
        fm = FileManagement("TEST", "make_json")
        path = fm.get_file_path()
        expected = temp_refl_code / "input" / "TEST" / "TEST.json"
        assert path == expected
        # Directory should be created
        assert path.parent.exists()
    
    def test_json_path_with_extension_new_format(self, temp_refl_code):
        """Test JSON path generation for new directory structure with extension."""
        fm = FileManagement("TEST", "make_json", extension="custom")
        path = fm.get_file_path()
        expected = temp_refl_code / "input" / "TEST" / "custom" / "TEST.json"
        assert path == expected
        assert path.parent.exists()
    
    def test_json_fallback_no_extension(self, temp_refl_code):
        """Test JSON file fallback from new to legacy format without extension."""
        # Create legacy file
        legacy_path = temp_refl_code / "input" / "TEST.json"
        legacy_path.write_text('{"test": "data"}')
        
        fm = FileManagement("TEST", "make_json")
        found_path, format_type = fm.find_json_file()
        
        assert found_path == legacy_path
        assert format_type == "legacy_station"
    
    def test_json_fallback_with_extension(self, temp_refl_code):
        """Test JSON file fallback from new to legacy format with extension."""
        # Create legacy extension file
        legacy_path = temp_refl_code / "input" / "TEST.custom.json"
        legacy_path.write_text('{"test": "data"}')
        
        fm = FileManagement("TEST", "make_json", extension="custom")
        found_path, format_type = fm.find_json_file()
        
        assert found_path == legacy_path
        assert format_type == "legacy_extension"
    
    def test_json_priority_new_over_legacy(self, temp_refl_code):
        """Test that new format takes priority over legacy when both exist."""
        # Create both legacy and new format files
        legacy_path = temp_refl_code / "input" / "TEST.json"
        legacy_path.write_text('{"legacy": "data"}')
        
        new_dir = temp_refl_code / "input" / "TEST"
        new_dir.mkdir()
        new_path = new_dir / "TEST.json"
        new_path.write_text('{"new": "data"}')
        
        fm = FileManagement("TEST", "make_json")
        found_path, format_type = fm.find_json_file()
        
        assert found_path == new_path
        assert format_type == "station_dir"


class TestAprioriRHFileHandling:
    """Test apriori RH file path resolution and frequency handling."""
    
    def test_apriori_rh_l2_default(self, temp_refl_code):
        """Test apriori RH path for L2 (default frequency)."""
        fm = FileManagement("TEST", "apriori_rh_file", frequency=20)
        path = fm.get_file_path()
        expected = temp_refl_code / "input" / "TEST" / "TEST_phaseRH_L2.txt"
        assert path == expected
    
    def test_apriori_rh_l1(self, temp_refl_code):
        """Test apriori RH path for L1 frequency."""
        fm = FileManagement("TEST", "apriori_rh_file", frequency=1)
        path = fm.get_file_path()
        expected = temp_refl_code / "input" / "TEST" / "TEST_phaseRH_L1.txt"
        assert path == expected
    
    def test_apriori_rh_l5(self, temp_refl_code):
        """Test apriori RH path for L5 frequency (experimental)."""
        fm = FileManagement("TEST", "apriori_rh_file", frequency=5)
        path = fm.get_file_path()
        expected = temp_refl_code / "input" / "TEST" / "TEST_phaseRH_L5.txt"
        assert path == expected
    
    def test_apriori_rh_with_extension(self, temp_refl_code):
        """Test apriori RH path with extension."""
        fm = FileManagement("TEST", "apriori_rh_file", frequency=20, extension="custom")
        path = fm.get_file_path()
        expected = temp_refl_code / "input" / "TEST" / "custom" / "TEST_phaseRH_L2.txt"
        assert path == expected
    
    def test_apriori_rh_legacy_fallback_l2(self, temp_refl_code):
        """Test apriori RH fallback to legacy L2 format."""
        # Create legacy L2 file (no frequency suffix for backwards compatibility)
        legacy_path = temp_refl_code / "input" / "TEST_phaseRH.txt"
        legacy_path.write_text("# Legacy L2 data")
        
        fm = FileManagement("TEST", "apriori_rh_file", frequency=20)
        found_path, format_type = fm.find_apriori_rh_file()
        
        assert found_path == legacy_path
        assert format_type == 'legacy'
    
    def test_apriori_rh_legacy_fallback_l1(self, temp_refl_code):
        """Test apriori RH fallback to legacy L1 format."""
        # Create legacy L1 file
        legacy_path = temp_refl_code / "input" / "TEST_phaseRH_L1.txt"
        legacy_path.write_text("# Legacy L1 data")
        
        fm = FileManagement("TEST", "apriori_rh_file", frequency=1)
        found_path, format_type = fm.find_apriori_rh_file()
        
        assert found_path == legacy_path
        assert format_type == 'legacy'


class TestPhaseFileHandling:
    """Test phase file path generation with extension support."""
    
    def test_phase_file_path_basic(self, temp_refl_code):
        """Test basic phase file path generation."""
        fm = FileManagement("TEST", "phase_file", year=2023, doy=100)
        path = fm.get_file_path()
        expected = temp_refl_code / "2023" / "phase" / "TEST" / "100.txt"
        assert path == expected
    
    def test_phase_file_path_with_extension(self, temp_refl_code):
        """Test phase file path generation with extension."""
        fm = FileManagement("TEST", "phase_file", year=2023, doy=100, extension="custom")
        path = fm.get_file_path()
        expected = temp_refl_code / "2023" / "phase" / "TEST" / "custom" / "100.txt"
        assert path == expected
    
    def test_phase_file_requires_year_doy(self, temp_refl_code):
        """Test that phase file generation works with year and doy parameters."""
        # This should not raise an error when year and doy are provided
        fm = FileManagement("TEST", "phase_file", year=2023, doy=100)
        path = fm.get_file_path()
        assert "2023" in str(path)
        assert "100.txt" in str(path)


class TestVolumetricWaterContentFiles:
    """Test volumetric water content file handling."""
    
    def test_vwc_path_no_extension(self, temp_refl_code):
        """Test VWC file path without extension."""
        fm = FileManagement("TEST", "volumetric_water_content")
        path = fm.get_file_path()
        expected = temp_refl_code / "Files" / "TEST" / "TEST_vwc.txt"
        assert path == expected
    
    def test_vwc_path_with_extension(self, temp_refl_code):
        """Test VWC file path with extension."""
        fm = FileManagement("TEST", "volumetric_water_content", extension="custom")
        path = fm.get_file_path()
        expected = temp_refl_code / "Files" / "TEST" / "custom" / "TEST_vwc.txt"
        assert path == expected


class TestDailyAvgPhaseFiles:
    """Test daily average phase file handling."""
    
    def test_daily_avg_phase_path_no_extension(self, temp_refl_code):
        """Test daily avg phase file path without extension."""
        fm = FileManagement("TEST", "daily_avg_phase_results")
        path = fm.get_file_path()
        expected = temp_refl_code / "Files" / "TEST" / "TEST_phase.txt"
        assert path == expected
    
    def test_daily_avg_phase_path_with_extension(self, temp_refl_code):
        """Test daily avg phase file path with extension."""
        fm = FileManagement("TEST", "daily_avg_phase_results", extension="custom")
        path = fm.get_file_path()
        expected = temp_refl_code / "Files" / "TEST" / "custom" / "TEST_phase.txt"
        assert path == expected


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_string_extension_vs_none(self, temp_refl_code):
        """Test that empty string extension behaves the same as no extension."""
        fm_empty = FileManagement("TEST", "make_json", extension="")
        fm_none = FileManagement("TEST", "make_json", extension=None)
        
        # Both should generate the same path structure (no extension subdirectory)
        path_empty = fm_empty.get_file_path()
        path_none = fm_none.get_file_path()
        
        expected = temp_refl_code / "input" / "TEST" / "TEST.json"
        assert path_empty == expected
        assert path_none == expected
    
    def test_extension_sanitization_not_implemented(self, temp_refl_code):
        """Test that extension with special characters is not currently sanitized."""
        # This test documents current behavior - extensions are used as-is
        fm = FileManagement("TEST", "make_json", extension="test/bad")
        path = fm.get_file_path()
        
        # This will create a path with the problematic extension
        # In a production system, you'd want to sanitize this
        assert "test/bad" in str(path)
    
    def test_directory_creation_disabled(self, temp_refl_code):
        """Test that directory creation can be disabled."""
        fm = FileManagement("TEST", "make_json", extension="newdir")
        path = fm.get_file_path(ensure_directory=False)
        
        # Directory should not exist
        assert not path.parent.exists()
        
        # But path should still be correct
        expected = temp_refl_code / "input" / "TEST" / "newdir" / "TEST.json"
        assert path == expected
    
    def test_invalid_file_type_enum_error(self, temp_refl_code):
        """Test error handling for invalid FileTypes enum access."""
        fm = FileManagement("TEST", "make_json")
        
        # Manually set an invalid file type to test error handling
        fm.file_type = "invalid_type"
        
        with pytest.raises(ValueError, match="The file type you requested does not exist"):
            fm.get_file_path()


class TestBackwardsCompatibility:
    """Test backwards compatibility scenarios."""
    
    def test_mixed_legacy_new_files_priority(self, temp_refl_code):
        """Test behavior when both legacy and new format files exist."""
        station = "TEST"
        
        # Create legacy JSON file
        legacy_json = temp_refl_code / "input" / f"{station}.json"
        legacy_json.write_text('{"legacy": true}')
        
        # Create new format JSON file
        new_dir = temp_refl_code / "input" / station
        new_dir.mkdir()
        new_json = new_dir / f"{station}.json"
        new_json.write_text('{"new": true}')
        
        fm = FileManagement(station, "make_json")
        found_path, format_type = fm.find_json_file()
        
        # New format should take priority
        assert found_path == new_json
        assert format_type == "station_dir"
    
    def test_extension_fallback_behavior(self, temp_refl_code):
        """Test extension fallback behavior matches documentation."""
        station = "TEST"
        extension = "custom"
        
        # Create only legacy extension file
        legacy_ext = temp_refl_code / "input" / f"{station}.{extension}.json"
        legacy_ext.write_text('{"extension": "legacy"}')
        
        fm = FileManagement(station, "make_json", extension=extension)
        found_path, format_type = fm.find_json_file()
        
        assert found_path == legacy_ext
        assert format_type == "legacy_extension"


class TestFrequencyMapping:
    """Test frequency to suffix mapping logic."""
    
    def test_frequency_mapping_consistency(self, temp_refl_code):
        """Test that frequency mapping is consistent across file types."""
        # L2C (20) should map to L2
        fm_l2c = FileManagement("TEST", "apriori_rh_file", frequency=20)
        path_l2c = fm_l2c._get_apriori_rh_path()
        assert "L2" in str(path_l2c)
        
        # L1 (1) should map to L1
        fm_l1 = FileManagement("TEST", "apriori_rh_file", frequency=1)
        path_l1 = fm_l1._get_apriori_rh_path()
        assert "L1" in str(path_l1)
        
        # L5 (5) should map to L5
        fm_l5 = FileManagement("TEST", "apriori_rh_file", frequency=5)
        path_l5 = fm_l5._get_apriori_rh_path()
        assert "L5" in str(path_l5)
    
    def test_default_frequency_handling(self, temp_refl_code):
        """Test default frequency handling when none specified."""
        fm = FileManagement("TEST", "apriori_rh_file")  # No frequency specified
        path = fm._get_apriori_rh_path()
        # Should default to L2
        assert "L2" in str(path)


if __name__ == "__main__":
    # Allow running tests directly with: python test_file_management.py
    pytest.main([__file__, "-v"])