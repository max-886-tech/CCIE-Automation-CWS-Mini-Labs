#!/usr/bin/env bash
set -euo pipefail

lab_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
fixtures="$lab_dir/fixtures"
scratch_dir=$(mktemp -d)
trap 'rm -rf -- "$scratch_dir"' EXIT
failures=0

check() {
    local label=$1 expected_code=$2 policy=$3 jobs=$4 filter=$5 actual_code=0
    bash "$lab_dir/gate.sh" "$policy" "$jobs" >"$scratch_dir/report.json" \
        2>"$scratch_dir/errors.txt" || actual_code=$?
    if [[ $actual_code != "$expected_code" ]]; then
        printf 'FAIL %s (exit %s, expected %s)\n' "$label" "$actual_code" "$expected_code"
    elif (( expected_code == 2 )); then
        if [[ ! -s "$scratch_dir/report.json" && -s "$scratch_dir/errors.txt" ]]; then
            printf 'PASS %s\n' "$label"
            return
        fi
        printf 'FAIL %s (expected diagnostic on stderr only)\n' "$label"
    elif jq --exit-status --slurp "length == 1 and (.[0] | $filter)" \
        "$scratch_dir/report.json" >/dev/null; then
        printf 'PASS %s\n' "$label"
        return
    else
        printf 'FAIL %s (unexpected report)\n' "$label"
        cat "$scratch_dir/report.json"
    fi
    failures=$((failures + 1))
}

blocked_report='(. == {deployable:false, checks:[
    {name:"render-config", job_id:122, status:"failed", passed:false},
    {name:"offline-smoke", job_id:120, status:"skipped", passed:true},
    {name:"lint-yaml", job_id:145, status:"success", passed:true},
    {name:"schema-check", job_id:109, status:"failed", passed:false},
    {name:"rollback-check", job_id:null, status:"missing", passed:false}
]})'

check 'reports failed retries and missing jobs in policy order' \
    1 "$fixtures/policy.json" "$fixtures/jobs.json" "$blocked_report"
jq 'reverse' "$fixtures/jobs.json" >"$scratch_dir/reversed.json"
check 'reversing job order keeps the report identical' \
    1 "$fixtures/policy.json" "$scratch_dir/reversed.json" "$blocked_report"
check 'passing required jobs permit release despite optional failure' \
    0 "$fixtures/policy.json" "$fixtures/jobs-pass.json" \
    '.deployable == true and (.checks | length == 5 and all(.passed))'

jq '. + [{id: 133, name: "lint-yaml", status: "skipped"}]' \
    "$fixtures/jobs-pass.json" >"$scratch_dir/skipped.json"
check 'a skip blocks a job without an explicit policy allowance' \
    1 "$fixtures/policy.json" "$scratch_dir/skipped.json" \
    '.deployable == false and .checks[2] == {name:"lint-yaml", job_id:133, status:"skipped", passed:false}'

printf '[]\n' >"$scratch_dir/empty.json"
check 'an empty job export reports every required job missing' \
    1 "$fixtures/policy.json" "$scratch_dir/empty.json" \
    '.deployable == false and (.checks | length == 5 and all(.status == "missing" and .job_id == null and .passed == false))'
check 'an empty release policy is an input error' \
    2 "$scratch_dir/empty.json" "$fixtures/jobs.json" ''

jq '. + [.[0]]' "$fixtures/jobs.json" >"$scratch_dir/duplicate.json"
check 'duplicate job IDs are input errors' \
    2 "$fixtures/policy.json" "$scratch_dir/duplicate.json" ''
printf '{\n' >"$scratch_dir/malformed.json"
check 'malformed JSON is an input error' \
    2 "$fixtures/policy.json" "$scratch_dir/malformed.json" ''

if (( failures != 0 )); then
    printf '%s check(s) failed.\n' "$failures" >&2
    exit 1
fi
printf 'All 8 checks passed.\n'
