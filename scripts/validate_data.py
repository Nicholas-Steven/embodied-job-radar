from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.radar.schema import validate_job
from scripts.radar.utils import load_json


def main() -> int:
    jobs = load_json(ROOT / "data/jobs.json", [])
    ids = set()
    for job in jobs:
        errors = validate_job(job)
        if job["id"] in ids:
            errors.append("duplicate id")
        ids.add(job["id"])
        if job.get("status") == "expired" and job.get("freshness") == "active":
            errors.append("expired job marked active")
        if errors:
            print(job.get("id"), "; ".join(errors), file=sys.stderr)
            return 1
    if not (ROOT / "site/index.html").exists():
        print("site build missing", file=sys.stderr)
        return 1
    print(f"validated {len(jobs)} jobs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

