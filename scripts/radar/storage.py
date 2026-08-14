from __future__ import annotations

from datetime import date

from .deduplicate import deduplicate, identity_key, merge_jobs
from .normalize import infer_status
from .utils import content_hash, now_iso, today_iso


FACT_FIELDS = (
    "company", "title", "city", "location_raw", "job_type", "graduate_year", "degree", "salary",
    "published_date", "deadline", "status", "description", "requirements", "skills", "topics",
    "source_url", "official_apply_url", "official_verified",
)


def merge_with_existing(existing_jobs: list[dict], discovered_jobs: list[dict]) -> tuple[list[dict], dict]:
    discovered, duplicates = deduplicate(discovered_jobs)
    existing_by_key = {identity_key(job): job for job in existing_jobs}
    seen_keys = set()
    output: list[dict] = []
    added = updated = 0
    for fresh in discovered:
        key = identity_key(fresh)
        seen_keys.add(key)
        old = existing_by_key.get(key)
        if old is None:
            added += 1
            output.append(fresh)
            continue
        merged = merge_jobs(old, fresh)
        merged["id"] = old["id"]
        merged["first_seen"] = old.get("first_seen") or today_iso()
        merged["last_seen"] = today_iso()
        merged["last_verified"] = now_iso()
        merged["history"] = list(old.get("history") or [])
        new_hash = content_hash(merged)
        if new_hash != old.get("content_hash"):
            updated += 1
            merged["history"].append({"changed_at": now_iso(), "content_hash": old.get("content_hash"), "facts": {k: old.get(k) for k in FACT_FIELDS}})
            merged["history"] = merged["history"][-8:]
            merged["updated_at"] = now_iso()
        merged["content_hash"] = new_hash
        output.append(merged)

    for old in existing_jobs:
        if identity_key(old) in seen_keys:
            continue
        preserved = dict(old)
        preserved["status"] = infer_status(preserved.get("deadline"), "", date.today()) if preserved.get("deadline") else preserved.get("status", "unknown")
        output.append(preserved)

    output, cross_duplicates = deduplicate(output)
    report = {"new_jobs": added, "updated_jobs": updated, "duplicate_jobs": duplicates + cross_duplicates, "preserved_jobs": max(0, len(output) - len(discovered))}
    return sorted(output, key=lambda job: (job.get("published_date") or "", job.get("first_seen") or ""), reverse=True), report

