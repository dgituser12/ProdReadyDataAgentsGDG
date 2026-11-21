#!/usr/bin/env python3
"""Evaluate the dependency-free route classifier against labelled JSON cases."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from orchestration.router import deterministic_route


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=Path("evals/route_eval_cases.json"))
    args = parser.parse_args()
    payload = json.loads(args.cases.read_text())
    cases = payload["cases"]
    correct = 0
    for case in cases:
        actual = deterministic_route(case["question"]).route
        expected = case["expected_route"]
        passed = actual == expected
        correct += int(passed)
        print(f'{"PASS" if passed else "FAIL"} {case["id"]}: expected={expected} actual={actual}')
    accuracy = correct / len(cases) if cases else 0.0
    print(f"Accuracy: {correct}/{len(cases)} = {accuracy:.1%}")
    if correct != len(cases):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
