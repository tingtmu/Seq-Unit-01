#!/usr/bin/env bash
# Runs every pipeline step in order. Each step is one script in scripts/ reading config/.
set -euo pipefail
cd "$(dirname "$0")/.."

# Steps, in order. Add one line per step, e.g.:
# python scripts/01_qc.py --config config/config.yaml --out results/qc
