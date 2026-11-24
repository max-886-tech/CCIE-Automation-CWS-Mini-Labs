# Task 02 CI Release Gate

A deployment script consumes a local export of CI job attempts. Old successes can hide failed retries, and the current shell wrapper returns success whenever it prints a report. Finish the gate so the deployment decision reflects the latest required jobs and the shell exit code agrees with the JSON report.

Work in `preconfig/` and edit `gate.jq` and `gate.sh` only. Use Bash and jq 1.6. The exports in `fixtures/` model CI input on the workstation.

## Inputs

```bash
bash gate.sh fixtures/policy.json fixtures/jobs.json
```

- The policy file contains one non-empty JSON array of required job rules. Each rule has a unique, non-empty string `name` and a boolean `allow_skip`.
- The jobs file contains one JSON array of attempts in any order. Each attempt has a unique positive integer `id` up to `9007199254740991`, a non-empty string `name`, and a non-empty string `status`. A higher ID means a later attempt. Extra fields may be present.

## Requirements

1. Evaluate each required job once, in policy order. Match names exactly and select the matching attempt with the highest numeric ID. Ignore jobs outside the policy.
2. A required job passes on `success`. It also passes on `skipped` if its policy rule has `allow_skip: true`. Every other status blocks release, even when the export has `allow_failure: true`. A missing job also blocks release.
3. Print one JSON object with `deployable` and `checks`. The overall decision is `true` only when every check passes. Each check has `name`, `job_id`, `status`, and boolean `passed`. Report a missing job with `job_id: null`, `status: "missing"`, and `passed: false`.
4. Exit `0` if deployment is allowed and `1` if blocked. Print the JSON report in both cases. Invalid input or an unreadable file must exit `2` with a diagnostic on stderr and empty stdout. Input validation is provided in the starter.

## Verification

```bash
bash verify.sh
```

The `jobs.json` export should block release. The `jobs-pass.json` export should allow it, even though a job outside the policy failed.
