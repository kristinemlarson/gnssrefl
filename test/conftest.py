import os
import shutil
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

FIXTURE_DIR = Path(__file__).parent / "data" / "refl_code"


@pytest.fixture
def refl_code_with_mchl(tmp_path):
    """Set up a REFL_CODE tree with mchl fixture data for regression tests."""
    # Copy SNR files
    snr_dst = tmp_path / "2025" / "snr" / "mchl"
    snr_dst.mkdir(parents=True)
    snr_src = FIXTURE_DIR / "2025" / "snr" / "mchl"
    for f in snr_src.glob("*.snr66.gz"):
        shutil.copy2(f, snr_dst / f.name)

    # Copy JSON config and apriori RH
    input_dst = tmp_path / "input" / "mchl"
    input_dst.mkdir(parents=True)
    input_src = FIXTURE_DIR / "input" / "mchl"
    shutil.copy2(input_src / "mchl.json", input_dst / "mchl.json")
    shutil.copy2(input_src / "mchl_phaseRH_L2.txt", input_dst / "mchl_phaseRH_L2.txt")

    # Copy pre-generated refraction file (avoids needing gpt_1wA.pickle)
    refr_src = FIXTURE_DIR / "input" / "mchl_refr.txt"
    if refr_src.exists():
        shutil.copy2(refr_src, tmp_path / "input" / "mchl_refr.txt")

    # Create empty gpt_1wA.pickle to prevent gnssir_cl from trying to download it.
    # The actual pickle is 21MB and not needed — the refraction file above is sufficient.
    (tmp_path / "input" / "gpt_1wA.pickle").touch()

    # Create required output directories
    for subdir in ["Files", "logs", "phase"]:
        (tmp_path / subdir).mkdir(parents=True, exist_ok=True)
    (tmp_path / "2025" / "results" / "mchl").mkdir(parents=True)
    (tmp_path / "2025" / "phase" / "mchl").mkdir(parents=True)

    with patch.dict(os.environ, {
        "REFL_CODE": str(tmp_path),
        "ORBITS": ".",
        "EXE": ".",
    }):
        yield tmp_path
