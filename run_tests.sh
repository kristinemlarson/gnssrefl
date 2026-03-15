#!/usr/bin/env bash
#
# Run the full test suite locally in Docker.
#
# Usage:
#   ./run_tests.sh [--quick | --full | --smoke-only]
#
#   --quick       Regression tests only (skip smoke tests)  [default]
#   --full        Smoke tests + regression tests
#   --smoke-only  Smoke tests only
#
# After a run, inspect results locally:
#   test/data/expected/<test_name>/   golden output (pinned baseline)
#   test/data/actual/<test_name>/     current code output
#
#   diff -r test/data/expected/test_gnssir_output_unchanged \
#          test/data/actual/test_gnssir_output_unchanged

set -euo pipefail

IMAGE_NAME="gnssrefl-test"
CONTAINER_NAME="gnssrefl-test-$$"
PINNED=$(cat "$(dirname "$0")/test/GOLDEN_COMMIT")

usage() {
    echo "Usage: $0 [--quick | --full | --smoke-only]"
    echo "  --quick       Regression tests only (skip smoke tests)  [default]"
    echo "  --full        Smoke tests + regression tests"
    echo "  --smoke-only  Smoke tests only"
    exit 1
}

MODE=quick
case "${1:-}" in
    --quick)      MODE=quick ;;
    --full)       MODE=full ;;
    --smoke-only) MODE=smoke ;;
    "")           MODE=quick ;;
    *)            usage ;;
esac

cleanup() {
    echo "Cleaning up container..."
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
}
trap cleanup EXIT

echo "=== Building Docker image (cached layers reused) ==="
docker build . -t "$IMAGE_NAME"

cleanup  # remove stale container from a previous interrupted run

echo "=== Starting container ==="
docker run --name "$CONTAINER_NAME" -d -v "$PWD:/src" "$IMAGE_NAME" tail -f /dev/null >/dev/null

if [ "$MODE" = full ] || [ "$MODE" = smoke ]; then
    echo "=== Running smoke tests ==="
    docker exec -i "$CONTAINER_NAME" /src/software_tests
fi

if [ "$MODE" = quick ] || [ "$MODE" = full ]; then
    echo "=== Generating expected output (pinned baseline) ==="
    docker exec -i "$CONTAINER_NAME" /src/test/run_processing.sh "$PINNED" /src/test/data/expected

    echo "=== Generating actual output (current code) ==="
    docker exec -i "$CONTAINER_NAME" /src/test/run_processing.sh local /src/test/data/actual

    echo "=== Installing test dependencies ==="
    docker exec -i "$CONTAINER_NAME" pip3 install -q 'pytest~=7.2' 'pytest-mock~=3.10'

    echo "=== Running pytest ==="
    docker exec -i "$CONTAINER_NAME" pytest /src/test -v
fi

echo ""
echo "=== Done ==="
echo "Inspect results:"
echo "  Golden:  test/data/expected/<test_name>/"
echo "  Actual:  test/data/actual/<test_name>/"
