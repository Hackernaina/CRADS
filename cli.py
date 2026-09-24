"""SentinelAPI CLI — ingest a spec and optionally build a test plan.

  python cli.py samples/vuln_api.yaml            # inventory
  python cli.py samples/vuln_api.yaml --plan     # + Phase 2 test plan
  python cli.py samples/vuln_api.yaml --plan --no-llm > plan.json
"""
import argparse
import json
import sys

from sentinel import SpecError, ingest
from sentinel.planner import build_plan


def main() -> int:
    ap = argparse.ArgumentParser(description="SentinelAPI spec ingest + test planner")
    ap.add_argument("spec", help="path to OpenAPI/Swagger JSON or YAML")
    ap.add_argument("--plan", action="store_true", help="build Phase 2 test plan")
    ap.add_argument("--no-llm", action="store_true", help="deterministic rules only")
    args = ap.parse_args()

    try:
        inv = ingest(open(args.spec, "rb").read())
    except (SpecError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if not args.plan:
        json.dump(inv.to_dict(), sys.stdout, indent=2, default=str)
    else:
        plan = build_plan(inv, use_llm=not args.no_llm)
        json.dump(plan.to_dict(), sys.stdout, indent=2, default=str)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
