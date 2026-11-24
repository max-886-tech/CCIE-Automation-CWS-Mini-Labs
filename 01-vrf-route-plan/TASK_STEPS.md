# Task 01 Solution Steps

## 1. Run the starter

From the extracted pack directory, open the first task and run the starter.

```bash
cd 01-vrf-route-plan/preconfig
python3.9 route_plan.py fixtures/desired.json fixtures/current.json
python3.9 verify.py
```

The starter proposes additions from raw strings. The verifier shows where it misses canonical matching, ownership, and validation.

## 2. Normalize and index the rows

In `index_routes()`, check for a decimal prefix length after `/` and reject scope IDs marked with `%`. Use `ipaddress.ip_network(prefix, strict=False)` to mask host bits and `ipaddress.ip_address(next_hop)` to parse the next hop. Check that `.version` matches. Build a dictionary keyed by `(vrf, network)` and store the parsed next hop and owner as the value. Check for an existing key before inserting. For example, `203.0.113.99/26` and `203.0.113.64/26` have the same canonical network.

## 3. Classify and sort the changes

In `build_plan()`, iterate over the union of both dictionaries’ keys. This exposes new routes, disappeared routes, and routes present in both files. Use `(vrf, network.version, int(network.network_address), network.prefixlen)` as the sort key. Compare parsed next hops and apply the action table. A manual route only appears in the report when it conflicts with a desired next hop. Print parsed addresses and networks with `str()` so the report uses canonical values.

The CLI already maps the `blocked` list and input errors to exit codes. A valid plan with a conflict still includes every other action.

## 4. Verify the completed task

Run these commands from the task’s `preconfig/` directory after making your changes, or use `cd ../final_solution` to run the supplied implementation.

```bash
python3.9 verify.py
status=0
python3.9 route_plan.py fixtures/desired.json fixtures/current.json || status=$?
printf 'Planner exit code %s\n' "$status"
```

The verifier should report six passing tests. The sample run should show these actions and exit code `1`.

| Action | VRF | Prefixes in report order |
| --- | --- | --- |
| Add | `BLUE`, then `GREEN` | `10.44.2.0/24`, `10.44.10.0/24`, `203.0.113.0/25`, `2001:db8:20::/64` |
| Replace | `BLUE` | `198.51.100.0/24`, next hop changes from `192.0.2.5` to `192.0.2.11` |
| Remove | `BLUE` | `172.16.9.0/24` |
| Blocked | `GREEN` | `198.51.100.0/24`, manual next hop `192.0.2.12` conflicts with desired `192.0.2.13` |
