#!/usr/bin/env bash
set -euo pipefail

USAGE="usage: render-prd-html.sh <file.prd.json> [output.html] [--previous <old.prd.json>]"
INPUT=""
OUTPUT=""
PREVIOUS=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --previous)
      PREVIOUS="${2:?$USAGE}"
      shift 2
      ;;
    *)
      if [[ -z "$INPUT" ]]; then
        INPUT="$1"
      elif [[ -z "$OUTPUT" ]]; then
        OUTPUT="$1"
      else
        echo "$USAGE" >&2
        exit 2
      fi
      shift
      ;;
  esac
done

if [[ -z "$INPUT" ]]; then
  echo "$USAGE" >&2
  exit 2
fi
OUTPUT="${OUTPUT:-${INPUT%.json}.html}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ARGUMENTS=("$INPUT" "$OUTPUT")
if [[ -n "$PREVIOUS" ]]; then
  ARGUMENTS+=(--previous "$PREVIOUS")
fi
python3 "$SCRIPT_DIR/renderPrd.py" "${ARGUMENTS[@]}"
