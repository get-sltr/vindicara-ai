#!/usr/bin/env bash
# Build the Lambda deployment artifact at lambda_package/ for VindicaraAPI.
#
# Produces a directory containing the `vindicara` package and all runtime
# dependencies from the [api] extra, targeting Amazon Linux 2023 (Python 3.13
# Lambda runtime, x86_64). Run from anywhere; resolves to repo root.
#
# Output: <repo>/lambda_package/  (gitignored)
# Consumed by: src/vindicara/infra/stacks/api_stack.py:34
#              lambda_.Code.from_asset("lambda_package")
#
# Why --platform manylinux2014_x86_64: bcrypt and cryptography ship native
# wheels. Building on macOS without --platform produces darwin wheels that
# fail to import inside the Linux Lambda runtime. manylinux2014_x86_64 wheels
# are forward-compatible with Amazon Linux 2023's glibc.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PKG_DIR="$REPO_ROOT/lambda_package"

cd "$REPO_ROOT"

echo "==> Cleaning $PKG_DIR"
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR"

echo "==> Installing vindicara[api] into $PKG_DIR (manylinux2014_x86_64, py3.13)"
pip install \
  --target "$PKG_DIR" \
  --platform manylinux2014_x86_64 \
  --only-binary=:all: \
  --python-version 3.13 \
  --implementation cp \
  --upgrade \
  ".[api]"

# The engine depends on `projectair>=1.2.0,<2.0`, which pip satisfies from PyPI.
# The published release lags the working tree (PyPI 1.3.1 vs 1.4.0 here), so the
# bundle would ship an airsdk without modules the engine imports (airsdk.health
# landed in 1.4.0). Overlay the in-repo package so the tree always wins. Pure
# Python, so none of the manylinux flags apply.
echo "==> Overlaying in-repo projectair over the PyPI resolution"
pip install --target "$PKG_DIR" --upgrade --no-deps "$REPO_ROOT/packages/projectair"

echo "==> Trimming bytecode caches and test directories"
find "$PKG_DIR" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
find "$PKG_DIR" -type d -name "tests" -prune -exec rm -rf {} + 2>/dev/null || true
find "$PKG_DIR" -type d -name "*.dist-info" -prune -exec sh -c 'rm -rf "$1"/RECORD' _ {} \; 2>/dev/null || true

SIZE=$(du -sh "$PKG_DIR" | awk '{print $1}')
echo "==> lambda_package built: $SIZE"
echo "==> Sanity check: handler import path"
test -f "$PKG_DIR/vindicara/lambda_handler.py" \
  && echo "    found vindicara/lambda_handler.py" \
  || { echo "ERROR: vindicara/lambda_handler.py missing in $PKG_DIR" >&2; exit 1; }

# Guard the stale-projectair failure mode: a bundle built against the PyPI
# release imports fine locally and only fails at Lambda cold start with
# "No module named 'airsdk.health'". Fail the build here instead.
echo "==> Sanity check: bundled airsdk is the in-repo one"
test -f "$PKG_DIR/airsdk/health.py" \
  && echo "    found airsdk/health.py" \
  || { echo "ERROR: airsdk/health.py missing; lambda_package has a stale projectair" >&2; exit 1; }
