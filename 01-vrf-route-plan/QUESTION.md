# Task 01 VRF Route Change Planner

Your team needs a read-only change plan from a source-of-truth file and a simulated routing snapshot. Several prefixes contain host bits, IPv6 addresses appear in different forms, and two VRFs can hold the same prefix. Operators also own some routes manually. Complete the planner so each proposed action respects that ownership.

Work in `preconfig/` and edit `route_plan.py` only. Use Python 3.9 and its standard library.

## Inputs

Run the planner with the desired routes first and the current snapshot second.

```bash
python3.9 route_plan.py fixtures/desired.json fixtures/current.json
```

Each file contains a JSON array of route objects with `vrf`, `prefix`, and `next_hop`. VRF names are non-empty, case-sensitive strings. A prefix must be IPv4 or IPv6 with a `/` followed by its decimal prefix length. Next hops must be IP address literals from the same address family. Use unscoped addresses. The current snapshot also has `owner` set to `automation` or `manual` for each row.

## Requirements

1. Match routes by `(vrf, canonical prefix)`. Mask host bits and normalize next hops before comparing them. Different VRFs and different prefix lengths identify distinct routes. A repeated canonical key within either input is an error, even if its next hop is identical.
2. Fill the plan according to the desired and current state.

| Desired | Current | Plan action |
| --- | --- | --- |
| Present | Absent | `add` |
| Absent | Owned by `automation` | `remove` |
| Absent | Owned by `manual` | Omit |
| Present | Same next hop | Omit |
| Present | Different next hop, owned by `automation` | `replace` |
| Present | Different next hop, owned by `manual` | `blocked` |

3. Emit one JSON object with all four action arrays, including empty arrays. Every row has `vrf` and the canonical `prefix`. Use `next_hop` for `add` and `remove`. Use `current_next_hop` and `desired_next_hop` for `replace` and `blocked`. Emit canonical next hops as strings.
4. Sort each array by VRF name, IP family (IPv4 first), numeric network address, then ascending prefix length.
5. Use exit code `0` for a plan with no blocked routes and `1` for a plan with one or more blocked routes. Emit the full plan in both cases. For invalid or unreadable input, exit `2` with a diagnostic on stderr and empty stdout.

## Verification

```bash
python3.9 verify.py
```

The supplied snapshot should produce four additions, one replacement, one removal, and one blocked route. Its exit code is `1`.
