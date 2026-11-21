#!/usr/bin/env python3
"""Evaluate deterministic route and specialist-target baselines."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from orchestration.router import deterministic_route
from orchestration.delegation import specialists_for_question


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=ROOT / "evals" / "multi_agent_eval_cases.json")
    args = parser.parse_args()
    payload = json.loads(args.cases.read_text(encoding="utf-8"))
    passed = 0
    for case in payload["cases"]:
        actual_route = deterministic_route(case["question"]).route
        actual_specialists = list(specialists_for_question(case["question"]))
        ok = actual_route == case["expected_route"] and actual_specialists == case["expected_specialists"]
        passed += int(ok)
        print(
            f'{"PASS" if ok else "FAIL"} {case["id"]}: '
            f'route={actual_route}; specialists={actual_specialists}'
        )
    total = len(payload["cases"])
    print(f"Baseline: {passed}/{total} cases passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
