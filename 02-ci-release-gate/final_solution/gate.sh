#!/usr/bin/env bash
set -euo pipefail

if (( $# != 2 )); then
    printf 'Usage: bash gate.sh POLICY.json JOBS.json\n' >&2
    exit 2
fi

script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
report=$(jq --null-input \
    --slurpfile policy "$1" \
    --slurpfile jobs "$2" \
    -f "$script_dir/gate.jq") || exit 2

printf '%s\n' "$report"
jq --exit-status '.deployable' <<<"$report" >/dev/null
