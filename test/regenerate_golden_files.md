# Running Regression Tests

## Quick start (local, via Docker)

```bash
./run_tests.sh
```

This builds the Docker image, generates both expected (golden) and actual
output, then runs pytest. After completion, both sets of files are on your
local filesystem:

- `test/data/expected/<test_name>/` — output from the pinned baseline version
- `test/data/actual/<test_name>/` — output from the current code

You can diff them directly:

```bash
diff -r test/data/expected/test_gnssir_output_unchanged \
       test/data/actual/test_gnssir_output_unchanged
```

## How it works

`test/run_processing.sh <version> <output_dir>` installs a version of
gnssrefl (either a git hash or `local`), then runs gnssir/phase against
committed test fixtures, writing a per-test REFL_CODE tree under `<output_dir>`.

`run_tests.sh` calls it twice — once with the pinned baseline hash, once
with the current code — then runs pytest to compare the two trees.

## Changing the baseline version

Edit the `PINNED` variable in `run_tests.sh` and `PINNED_VERSION` in
`.github/workflows/ci.yml`.

## Test data (committed)

These input files stay committed in the repo:

- `test/data/refl_code/2025/snr/mchl/*.snr66.gz` (3 SNR files for days 010-012)
- `test/data/refl_code/input/mchl/mchl.json`
- `test/data/refl_code/input/mchl/mchl_phaseRH_L2.txt`
- `test/data/refl_code/input/mchl_refr.txt`
