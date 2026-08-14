from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import yaml

from .ai import enrich_job
from .match import score_job
from .schema import validate_job
from .sources import run_source
from .storage import merge_with_existing
from .utils import atomic_json, load_json, now_iso, today_iso


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _stats(jobs: list[dict], previous: dict | None = None) -> dict:
    today = today_iso()
    active = [job for job in jobs if job.get("status") in {"open", "closing_soon"}]
    new_today = [job for job in jobs if job.get("first_seen") == today]
    topics: dict[str, int] = {}
    cities: dict[str, int] = {}
    for job in active:
        for topic in job.get("topics") or []:
            topics[topic] = topics.get(topic, 0) + 1
        for city in job.get("city") or []:
            cities[city] = cities.get(city, 0) + 1
    return {
        "generated_at": now_iso(),
        "active_jobs": len(active),
        "new_today": len(new_today),
        "high_match": sum(1 for job in active if (job.get("match_score") or 0) >= 80),
        "closing_soon": sum(1 for job in jobs if job.get("status") == "closing_soon"),
        "total_jobs": len(jobs),
        "official_verified": sum(1 for job in jobs if job.get("official_verified")),
        "unknown_status": sum(1 for job in jobs if job.get("status") == "unknown"),
        "topics": dict(sorted(topics.items(), key=lambda item: (-item[1], item[0]))),
        "cities": dict(sorted(cities.items(), key=lambda item: (-item[1], item[0]))),
        "trend": {"status": "样本不足", "items": []} if not previous else previous.get("trend", {"status": "样本不足", "items": []}),
    }


def run(root: Path, use_ai: bool = True, preserve_existing: bool = True) -> tuple[list[dict], dict]:
    source_cfg = _load_yaml(root / "config/sources.yaml")
    keyword_cfg = _load_yaml(root / "config/keywords.yaml")
    profile = _load_yaml(root / "config/profile.yaml")
    existing = load_json(root / "data/jobs.json", []) if preserve_existing else []
    discovered: list[dict] = []
    successful, failed = [], []
    for config in source_cfg.get("sources") or []:
        result = run_source(config, keyword_cfg)
        if result.ok:
            successful.append({"id": result.source_id, "name": result.source_name, "jobs": len(result.jobs)})
            discovered.extend(result.jobs)
        else:
            failed.append({"id": result.source_id, "name": result.source_name, "error": result.error})
    jobs, merge_report = merge_with_existing(existing, discovered)
    llm_failures = 0
    for job in jobs:
        score_job(job, profile)
        if use_ai:
            _, failed_ai = enrich_job(job, profile)
            llm_failures += int(failed_ai)
    errors = {job["id"]: validate_job(job) for job in jobs if validate_job(job)}
    if errors:
        raise ValueError(f"job validation failed: {errors}")
    previous_stats = load_json(root / "data/stats.json", {})
    stats = _stats(jobs, previous_stats)
    report = {
        "run_at": now_iso(),
        "successful_sources": successful,
        "failed_sources": failed,
        "discovered_jobs": len(discovered),
        **merge_report,
        "expired_jobs": sum(1 for job in jobs if job.get("status") == "expired"),
        "official_verified": stats["official_verified"],
        "high_match_new": sum(1 for job in jobs if job.get("first_seen") == today_iso() and (job.get("match_score") or 0) >= 80),
        "llm_failures": llm_failures,
    }
    atomic_json(root / "data/jobs.json", jobs)
    atomic_json(root / "data/stats.json", stats)
    atomic_json(root / "logs/update-report.json", report)
    return jobs, report
