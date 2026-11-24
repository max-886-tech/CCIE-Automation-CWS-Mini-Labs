import argparse
import json
from pathlib import Path
import sys


def load_rows(path):
    with path.open(encoding="utf-8") as source:
        rows = json.load(source)
    if not isinstance(rows, list):
        raise ValueError(f"{path} must contain an array of routes")
    return rows


def index_routes(rows, path, *, observed):
    routes = {}
    for number, row in enumerate(rows, start=1):
        label = f"{path} row {number}"
        if not isinstance(row, dict):
            raise ValueError(f"{label} must be an object")
        vrf = row.get("vrf")
        prefix = row.get("prefix")
        next_hop = row.get("next_hop")
        owner = row.get("owner") if observed else "automation"
        if not isinstance(vrf, str) or not vrf:
            raise ValueError(f"{label} needs a non-empty VRF name")
        if not isinstance(prefix, str) or not isinstance(next_hop, str):
            raise ValueError(f"{label} needs string prefix and next_hop fields")
        if owner not in ("automation", "manual"):
            raise ValueError(f"{label} needs owner automation or manual")

        # TODO 1: Validate and normalize prefix and next hop. Reject duplicate keys.
        routes[(vrf, prefix)] = (next_hop, owner)
    return routes


def build_plan(desired, current):
    plan = {"add": [], "replace": [], "remove": [], "blocked": []}
    # TODO 2: Reconcile all route keys in the specified order and respect ownership.
    for key, (next_hop, _) in desired.items():
        if key not in current:
            vrf, prefix = key
            plan["add"].append({"vrf": vrf, "prefix": prefix, "next_hop": next_hop})
    return plan


def main():
    parser = argparse.ArgumentParser(description="Plan route changes from local JSON files.")
    parser.add_argument("desired", type=Path)
    parser.add_argument("current", type=Path)
    args = parser.parse_args()

    try:
        desired = index_routes(load_rows(args.desired), args.desired, observed=False)
        current = index_routes(load_rows(args.current), args.current, observed=True)
        plan = build_plan(desired, current)
    except (OSError, ValueError) as error:
        print(f"Input error: {error}", file=sys.stderr)
        return 2

    print(json.dumps(plan, indent=2))
    return 1 if plan["blocked"] else 0


if __name__ == "__main__":
    sys.exit(main())
