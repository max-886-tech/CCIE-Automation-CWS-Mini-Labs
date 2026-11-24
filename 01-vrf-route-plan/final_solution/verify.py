import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


LAB = Path(__file__).resolve().parent


def route(vrf, prefix, next_hop, **extra):
    return {"vrf": vrf, "prefix": prefix, "next_hop": next_hop, **extra}


class RoutePlanTests(unittest.TestCase):
    def run_cli(self, desired, current):
        return subprocess.run(
            [sys.executable, str(LAB / "route_plan.py"), str(desired), str(current)],
            text=True, capture_output=True, check=False,
        )

    def run_with_rows(self, desired, current):
        with TemporaryDirectory() as directory:
            desired_path = Path(directory) / "desired.json"
            current_path = Path(directory) / "current.json"
            desired_path.write_text(json.dumps(desired), encoding="utf-8")
            current_path.write_text(json.dumps(current), encoding="utf-8")
            return self.run_cli(desired_path, current_path)

    def assert_input_error(self, result):
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr)

    def test_bundled_snapshot_matches_all_four_action_lists(self):
        result = self.run_cli(LAB / "fixtures/desired.json", LAB / "fixtures/current.json")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout), {
            "add": [
                route("BLUE", "10.44.2.0/24", "192.0.2.7"),
                route("BLUE", "10.44.10.0/24", "192.0.2.9"),
                route("GREEN", "203.0.113.0/25", "192.0.2.20"),
                route("GREEN", "2001:db8:20::/64", "2001:db8::1"),
            ],
            "replace": [dict(vrf="BLUE", prefix="198.51.100.0/24",
                             current_next_hop="192.0.2.5", desired_next_hop="192.0.2.11")],
            "remove": [route("BLUE", "172.16.9.0/24", "192.0.2.6")],
            "blocked": [dict(vrf="GREEN", prefix="198.51.100.0/24",
                             current_next_hop="192.0.2.12", desired_next_hop="192.0.2.13")],
        })

    def test_ipv6_equivalence_and_manual_route_preservation(self):
        desired = [route("BLUE", "2001:0DB8::99/64", "2001:0db8:0:0::1")]
        current = [
            route("BLUE", "2001:db8::/64", "2001:db8::1", owner="manual"),
            route("BLUE", "192.0.2.0/24", "198.51.100.2", owner="manual"),
        ]
        result = self.run_with_rows(desired, current)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), dict(add=[], replace=[], remove=[], blocked=[]))

    def test_overlapping_cidrs_are_distinct_and_sorted_by_prefix_length(self):
        desired = [
            route("BLUE", "192.0.2.17/25", "198.51.100.1"),
            route("BLUE", "192.0.2.19/24", "198.51.100.2"),
        ]
        result = self.run_with_rows(desired, [])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([r["prefix"] for r in json.loads(result.stdout)["add"]],
                         ["192.0.2.0/24", "192.0.2.0/25"])

    def test_duplicate_canonical_key_is_an_error_in_either_input(self):
        first = route("BLUE", "192.0.2.17/24", "198.51.100.1")
        second = route("BLUE", "192.0.2.0/24", "198.51.100.1")
        self.assert_input_error(self.run_with_rows([first, second], []))
        self.assert_input_error(self.run_with_rows([], [
            {**first, "owner": "automation"}, {**second, "owner": "manual"},
        ]))

    def test_rejects_bad_cidr_family_and_owner(self):
        cases = [
            ([route("BLUE", "192.0.2.0/33", "198.51.100.1")], []),
            ([route("BLUE", "192.0.2.0/24", "2001:db8::1")], []),
            ([route("BLUE", "2001:db8::/64", "fe80::1%eth0")], []),
            ([], [route("BLUE", "192.0.2.0/24", "198.51.100.1", owner="unknown")]),
        ]
        for desired, current in cases:
            with self.subTest(desired=desired, current=current):
                self.assert_input_error(self.run_with_rows(desired, current))

    def test_invalid_json_is_an_input_error(self):
        with TemporaryDirectory() as directory:
            malformed = Path(directory) / "malformed.json"
            malformed.write_text("{", encoding="utf-8")
            self.assert_input_error(self.run_cli(malformed, LAB / "fixtures/current.json"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
