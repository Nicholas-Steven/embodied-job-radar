from __future__ import annotations

from difflib import SequenceMatcher

from .utils import canonical_text


def identity_key(job: dict) -> tuple[str, str, tuple[str, ...]]:
    return (
        canonical_text(job.get("company")),
        canonical_text(job.get("title")),
        tuple(sorted(job.get("city") or [])),
    )


def similarity(left: dict, right: dict) -> float:
    if canonical_text(left.get("company")) != canonical_text(right.get("company")):
        return 0.0
    lt, rt = canonical_text(left.get("title")), canonical_text(right.get("title"))
    title_score = SequenceMatcher(None, lt, rt).ratio()
    lc, rc = set(left.get("city") or []), set(right.get("city") or [])
    city_score = 1.0 if not lc or not rc or lc & rc else 0.0
    return title_score * 0.85 + city_score * 0.15


def merge_jobs(primary: dict, incoming: dict) -> dict:
    official_first = incoming.get("official_verified") and not primary.get("official_verified")
    winner, other = (incoming, primary) if official_first else (primary, incoming)
    merged = dict(winner)
    for key in ("city", "graduate_year", "requirements", "skills", "topics", "other_apply_urls"):
        merged[key] = list(dict.fromkeys((winner.get(key) or []) + (other.get(key) or [])))
    urls = [u for u in [winner.get("source_url"), other.get("source_url"), *(merged.get("other_apply_urls") or [])] if u]
    merged["other_apply_urls"] = list(dict.fromkeys(u for u in urls if u not in {merged.get("official_apply_url"), merged.get("source_url")}))
    merged["source_count"] = max(int(primary.get("source_count") or 1), int(incoming.get("source_count") or 1), len(set(urls)))
    merged["official_verified"] = bool(primary.get("official_verified") or incoming.get("official_verified"))
    merged["official_apply_url"] = primary.get("official_apply_url") or incoming.get("official_apply_url")
    return merged


def deduplicate(jobs: list[dict]) -> tuple[list[dict], int]:
    unique: list[dict] = []
    duplicates = 0
    for job in jobs:
        match_index = None
        for index, existing in enumerate(unique):
            same_job_id = job.get("job_id") and job.get("job_id") == existing.get("job_id")
            exact = identity_key(job) == identity_key(existing)
            fuzzy = similarity(job, existing) >= 0.92
            if same_job_id or exact or fuzzy:
                match_index = index
                break
        if match_index is None:
            unique.append(job)
        else:
            unique[match_index] = merge_jobs(unique[match_index], job)
            duplicates += 1
    return unique, duplicates

