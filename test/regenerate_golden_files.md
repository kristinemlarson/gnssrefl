# Golden Files

Golden files are the expected output that regression tests compare against.
They are **generated automatically in CI** from a pinned version of gnssrefl,
so they never need to be committed.

## How it works

The CI workflow (`.github/workflows/ci.yml`) has a step that:

1. Installs a pinned release (e.g. `gnssrefl==3.19.0`) inside the Docker container
2. Runs `gnssir` and `phase` on the committed test data to produce golden files
3. Reinstalls the current branch code
4. Runs pytest, which compares current output against the golden files

Because both generation and testing happen in the same Docker container, there
are no platform differences (Mac ARM vs Linux x86_64) to cause false failures.

## Changing the baseline version

Edit the `pip3 install gnssrefl==X.Y.Z` line in `.github/workflows/ci.yml`.

## Running tests locally

To run tests locally, you need to generate golden files first. Use the same
commands from the CI step, substituting `$REFL_CODE` for your local path:

```bash
# Install the pinned version
pip install gnssrefl==3.19.0

# Run gnssir and phase, then copy output to test/data/expected/
# (see ci.yml for the exact commands)

# Reinstall your local code
pip install .

# Run tests
pytest test/
```

## Test data (committed)

These input files stay committed in the repo:

- `test/data/refl_code/2025/snr/mchl/*.snr66.gz` (3 SNR files for days 010-012)
- `test/data/refl_code/input/mchl/mchl.json`
- `test/data/refl_code/input/mchl/mchl_phaseRH_L2.txt`
- `test/data/refl_code/input/mchl_refr.txt`
