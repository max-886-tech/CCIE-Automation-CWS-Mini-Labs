def nonempty_string:
    type == "string" and length > 0;

def valid_rule:
    type == "object" and (.name | nonempty_string) and (.allow_skip | type == "boolean");

def valid_run:
    type == "object"
    and (.name | nonempty_string)
    and (.status | nonempty_string)
    and (.id | type == "number" and . >= 1 and . <= 9007199254740991 and . == floor);

def validate_inputs:
    if ($policy | length) != 1 or ($jobs | length) != 1
        or ($policy[0] | type) != "array" or ($jobs[0] | type) != "array" then
        error("Each input must contain exactly one JSON array")
    elif ($policy[0] | length) == 0 or (all($policy[0][]; valid_rule) | not) then
        error("Policy must contain at least one valid job rule")
    elif ([$policy[0][].name] | length != (unique | length)) then
        error("Policy job names must be unique")
    elif (all($jobs[0][]; valid_run) | not) then
        error("Each job needs a name, status, and positive safe integer id")
    elif ([$jobs[0][].id] | length != (unique | length)) then
        error("Job IDs must be unique")
    else
        .
    end;

def check_job($rule; $runs):
    ([$runs[] | select(.name == $rule.name)] | max_by(.id)) as $job
    | {
        name: $rule.name,
        job_id: $job.id,
        status: ($job.status // "missing"),
        passed: ($job.status == "success" or ($job.status == "skipped" and $rule.allow_skip))
    };

validate_inputs
| [$policy[0][] | check_job(.; $jobs[0])] as $checks
| {
    deployable: ($checks | all(.passed)),
    checks: $checks
}
