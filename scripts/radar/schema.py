from __future__ import annotations

from .utils import content_hash, now_iso, stable_id, today_iso, valid_http_url


STATUSES = {"open", "closing_soon", "expired", "unknown"}


def make_job(**values) -> dict:
    source_url = values.get("source_url") or ""
    job = {
        "id": values.get("id") or stable_id(values.get("company", ""), values.get("title", ""), source_url, values.get("job_id", "")),
        "job_id": values.get("job_id") or None,
        "company": values.get("company", ""),
        "company_en": values.get("company_en", ""),
        "title": values.get("title", ""),
        "city": list(dict.fromkeys(values.get("city") or [])),
        "location_raw": values.get("location_raw") or "未公开",
        "job_type": values.get("job_type") or "未知",
        "graduate_year": values.get("graduate_year") or [],
        "degree": values.get("degree") or "未公开",
        "salary": values.get("salary"),
        "published_date": values.get("published_date"),
        "deadline": values.get("deadline"),
        "status": values.get("status") if values.get("status") in STATUSES else "unknown",
        "description": values.get("description") or "",
        "requirements": values.get("requirements") or [],
        "skills": values.get("skills") or [],
        "topics": values.get("topics") or [],
        "source_name": values.get("source_name") or "",
        "source_url": source_url,
        "source_tier": int(values.get("source_tier") or 3),
        "official_apply_url": values.get("official_apply_url"),
        "other_apply_urls": values.get("other_apply_urls") or [],
        "official_verified": bool(values.get("official_verified", False)),
        "source_count": int(values.get("source_count") or 1),
        "first_seen": values.get("first_seen") or today_iso(),
        "last_seen": values.get("last_seen") or today_iso(),
        "last_verified": values.get("last_verified") or now_iso(),
        "updated_at": values.get("updated_at") or now_iso(),
        "match_score": values.get("match_score"),
        "match_level": values.get("match_level"),
        "match_reasons": values.get("match_reasons") or [],
        "skill_gaps": values.get("skill_gaps") or [],
        "recommendation": values.get("recommendation") or "",
        "resume_tips": values.get("resume_tips") or [],
        "freshness": values.get("freshness") or "",
        "content_hash": values.get("content_hash") or "",
        "history": values.get("history") or [],
        "ai_status": values.get("ai_status") or "not_requested",
        "doctoral_exclusive": bool(values.get("doctoral_exclusive", False)),
    }
    job["content_hash"] = job["content_hash"] or content_hash(job)
    return job


def validate_job(job: dict) -> list[str]:
    errors: list[str] = []
    for key in ("id", "company", "title", "source_url"):
        if not job.get(key):
            errors.append(f"{key} is required")
    if job.get("status") not in STATUSES:
        errors.append("invalid status")
    score = job.get("match_score")
    if score is not None and not 0 <= score <= 100:
        errors.append("match_score outside 0..100")
    if job.get("source_url") and not valid_http_url(job["source_url"]):
        errors.append("invalid source_url")
    if job.get("official_apply_url") and not valid_http_url(job["official_apply_url"]):
        errors.append("invalid official_apply_url")
    if job.get("first_seen", "") > job.get("last_seen", ""):
        errors.append("first_seen after last_seen")
    return errors

