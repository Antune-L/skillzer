#!/usr/bin/env bash
set -euo pipefail

INPUT="${1:?usage: render-prd-html.sh <file.prd.json> [output.html]}"
OUTPUT="${2:-${INPUT%.json}.html}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "$SCRIPT_DIR/renderPrd.py" "$INPUT" "$OUTPUT"
