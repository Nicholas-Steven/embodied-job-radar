from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def build(output: Path) -> Path:
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(ROOT / "web", output)
    assets = output / "data"
    assets.mkdir(parents=True, exist_ok=True)
    for name in ("jobs.json", "stats.json"):
        shutil.copy2(ROOT / "data" / name, assets / name)
    shutil.copy2(ROOT / "logs/update-report.json", assets / "update-report.json")
    source_configs = yaml.safe_load((ROOT / "config/sources.yaml").read_text(encoding="utf-8")).get("sources", [])
    source_registry = [{
        "id": item.get("id"),
        "name": item.get("name"),
        "tier": item.get("tier", 3),
        "adapter": item.get("adapter"),
        "company": item.get("company"),
        "source_url": item.get("source_url"),
        "official_apply_url": item.get("official_apply_url"),
    } for item in source_configs]
    (assets / "sources.json").write_text(json.dumps(source_registry, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / ".nojekyll").write_text("", encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public", action="store_true", help="also build the Sites public/radar copy")
    args = parser.parse_args()
    output = build(ROOT / "site")
    if args.public:
        build(ROOT / "public/radar")
    print(json.dumps({"built": str(output), "public": args.public}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
