# Task 02 Solution Steps

## 1. Reproduce the bug

From the extracted pack directory, run the starter and immediately inspect its exit code.

```bash
cd 02-ci-release-gate/preconfig
bash gate.sh fixtures/policy.json fixtures/jobs.json
printf 'Gate exit code %s\n' "$?"
bash verify.sh
```

The starter reports `deployable: false` and exits `0`. Its report also picks the early `render-config` success over the later failure.

## 2. Select an attempt per rule

In `check_job()` in `gate.jq`, keep attempts whose `.name` matches the rule. Use `max_by(.id)` on that array to select the latest row. An empty match gives `null`. The existing report fields convert that into a null `job_id` and the status `missing`.

Iterate through the policy to build `checks`, so the result order comes from the policy. For each selected job, `passed` should be the boolean expression `status == "success" or (status == "skipped" and allow_skip)`, using the status of the selected attempt and `allow_skip` from its policy rule.

## 3. Return the decision to the caller

In `gate.sh`, print the captured JSON once. Then run `jq --exit-status '.deployable'` on that report and discard the second command’s stdout. Using the projected boolean gives code `0` for `true` and `1` for `false`. The starter already maps input or parsing errors to `2` before it reaches the print command.

## 4. Verify both outcomes

Run these commands from the task’s `preconfig/` directory after making your changes, or use `cd ../final_solution` to run the supplied implementation.

```bash
bash verify.sh
status=0
bash gate.sh fixtures/policy.json fixtures/jobs.json || status=$?
printf 'Blocked fixture exit code %s\n' "$status"
status=0
bash gate.sh fixtures/policy.json fixtures/jobs-pass.json || status=$?
printf 'Passing fixture exit code %s\n' "$status"
```

All eight checks should pass. The blocked export should exit `1` and show the rows below. The passing export should exit `0`, with `deployable: true` and five passing checks.

| Job | Selected ID | Status | Passed |
| --- | --- | --- | --- |
| `render-config` | 122 | `failed` | `false` |
| `offline-smoke` | 120 | `skipped` | `true` |
| `lint-yaml` | 145 | `success` | `true` |
| `schema-check` | 109 | `failed` | `false` |
| `rollback-check` | `null` | `missing` | `false` |

Reference for the jq behavior used above. [jq 1.6 manual](https://jqlang.org/manual/v1.6/)
