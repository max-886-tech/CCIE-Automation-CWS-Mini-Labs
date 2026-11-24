import argparse
import ipaddress
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

        if not prefix.partition("/")[2].isdecimal() or "%" in prefix or "%" in next_hop:
            raise ValueError(f"{label} needs an unscoped CIDR prefix and IP next hop")
        try:
            network = ipaddress.ip_network(prefix, strict=False)
            address = ipaddress.ip_address(next_hop)
        except ValueError as error:
            raise ValueError(f"{label}: {error}") from error
        if network.version != address.version:
            raise ValueError(f"{label} has a next hop from a different address family")

        key = (vrf, network)
        if key in routes:
            raise ValueError(f"{label} duplicates {vrf} {network}")
        routes[key] = (address, owner)
    return routes


def route_order(key):
    vrf, network = key
    return vrf, network.version, int(network.network_address), network.prefixlen


def build_plan(desired, current):
    plan = {"add": [], "replace": [], "remove": [], "blocked": []}
    for key in sorted(desired.keys() | current.keys(), key=route_order):
        vrf, network = key
        route = {"vrf": vrf, "prefix": str(network)}
        if key not in current:
            plan["add"].append({**route, "next_hop": str(desired[key][0])})
            continue

        current_hop, owner = current[key]
        if key not in desired:
            if owner == "automation":
                plan["remove"].append({**route, "next_hop": str(current_hop)})
            continue

        desired_hop, _ = desired[key]
        if current_hop != desired_hop:
            action = "blocked" if owner == "manual" else "replace"
            plan[action].append({
                **route,
                "current_next_hop": str(current_hop),
                "desired_next_hop": str(desired_hop),
            })
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
