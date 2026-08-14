from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.radar.pipeline import run


def main() -> int:
    parser = argparse.ArgumentParser(description="Update Embodied Job Radar data")
    parser.add_argument("--no-ai", action="store_true", help="skip optional LLM enrichment")
    parser.add_argument("--bootstrap", action="store_true", help="rebuild the initial snapshot without prior lifecycle state")
    args = parser.parse_args()
    jobs, report = run(ROOT, use_ai=not args.no_ai, preserve_existing=not args.bootstrap)
    print(json.dumps({"jobs": len(jobs), **report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
