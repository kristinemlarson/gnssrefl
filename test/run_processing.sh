#!/usr/bin/env bash
#
# Install a version of gnssrefl and run the regression test suite,
# writing output to the specified directory.
#
# Usage:
#   ./test/run_processing.sh <version> <output_dir>
#
# <version> is either:
#   - A git commit hash (installs from GitHub)
#   - "local" (installs from /src in Docker, or . if not in Docker)
#
# <output_dir> is where per-test REFL_CODE trees will be created, e.g.:
#   <output_dir>/test_gnssir_output_unchanged/2025/results/mchl/011.txt
#
# Both run_tests.sh (local) and .github/workflows/ci.yml call this script.

set -euo pipefail

if [ $# -ne 2 ]; then
    echo "Usage: $0 <version|local> <output_dir>" >&2
    exit 1
fi

VERSION=$1
OUTPUT_DIR=$2
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FIXTURE_DIR="$SCRIPT_DIR/data/refl_code"
REPO_URL="https://github.com/kristinemlarson/gnssrefl"
ORIG_REFL_CODE="${REFL_CODE:-}"

# --- Install the requested version ---
if [ "$VERSION" = "local" ]; then
    if [ -d /src ]; then
        pip3 install -q /src
    else
        pip3 install -q .
    fi
else
    # Prefer local git archive (works with unpushed commits); fall back to GitHub
    if [ -d /src/.git ] && git -C /src cat-file -e "$VERSION" 2>/dev/null; then
        _tmpdir=$(mktemp -d)
        git -C /src archive "$VERSION" | tar -x -C "$_tmpdir"
        pip3 install -q --force-reinstall "$_tmpdir"
        rm -rf "$_tmpdir"
    else
        pip3 install -q --force-reinstall "$REPO_URL/archive/${VERSION}.tar.gz"
    fi
fi

echo "Installed gnssrefl: $(pip3 show gnssrefl | grep Version)"

# --- Set up and run each test's REFL_CODE tree ---

setup_refl_code() {
    local test_name=$1
    local R="$OUTPUT_DIR/$test_name"

    rm -rf "$R"
    mkdir -p "$R/2025/snr/mchl" "$R/2025/results/mchl" \
             "$R/2025/phase/mchl" "$R/2025/arcs/mchl" \
             "$R/input/mchl" "$R/Files" "$R/logs" "$R/phase"

    cp "$FIXTURE_DIR"/2025/snr/mchl/*.snr66.gz "$R/2025/snr/mchl/"
    cp "$FIXTURE_DIR"/input/mchl/mchl.json "$R/input/mchl/"
    cp "$FIXTURE_DIR"/input/mchl/mchl_phaseRH_L2.txt "$R/input/mchl/"
    cp "$FIXTURE_DIR"/input/mchl_refr.txt "$R/input/"

    # Use the real gpt_1wA.pickle from the Docker REFL_CODE if available,
    # otherwise create a stub (the pre-generated refraction file is sufficient).
    if [ -n "$ORIG_REFL_CODE" ] && [ -f "$ORIG_REFL_CODE/input/gpt_1wA.pickle" ]; then
        cp "$ORIG_REFL_CODE/input/gpt_1wA.pickle" "$R/input/"
    else
        touch "$R/input/gpt_1wA.pickle"
    fi

    echo "$R"
}

run_test() {
    local test_name=$1
    shift
    local R
    R=$(setup_refl_code "$test_name")
    export REFL_CODE="$R"
    "$@"
    echo "  $test_name: done"
}

echo "=== Processing test data into $OUTPUT_DIR ==="

# extract_arcs tests (Python API — foundational, run first)
run_test test_extract_arcs_output_unchanged \
    python3 "$SCRIPT_DIR/run_extract_arcs.py" test_extract_arcs_output_unchanged

run_test test_extract_arcs_from_file_output_unchanged \
    python3 "$SCRIPT_DIR/run_extract_arcs.py" test_extract_arcs_from_file_output_unchanged

# Generate multi-constellation config, then run extract_arcs_from_station
run_test test_extract_arcs_from_station_output_unchanged \
    bash -c 'gnssir_input mchl -lat -26.358904661 -lon 148.144960505 -height 534.591379 -Hortho 497.0014 -allfreq T && python3 "'"$SCRIPT_DIR"'/run_extract_arcs.py" test_extract_arcs_from_station_output_unchanged'

run_test test_gnssir_output_unchanged \
    gnssir mchl 2025 11

run_test test_gnssir_midnite_output_unchanged \
    gnssir mchl 2025 11 -midnite T

run_test test_phase_output_unchanged \
    bash -c 'gnssir mchl 2025 11 && phase mchl 2025 11'

run_test test_gnssir_arcs_unchanged \
    gnssir mchl 2025 11 -savearcs T

run_test test_gnssir_midnite_arcs_unchanged \
    gnssir mchl 2025 11 -midnite T -savearcs T

echo "=== Done: output in $OUTPUT_DIR ==="
