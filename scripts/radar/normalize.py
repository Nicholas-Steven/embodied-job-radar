from __future__ import annotations

import re
from datetime import date

from .utils import extract_cities, normalize_date, normalize_space


def infer_degree(text: str) -> str:
    lower = text.lower()
    if "博士" in text and not any(term in text for term in ("硕士", "本科", "硕博")):
        return "博士"
    if "硕士及以上" in text or "硕博" in text:
        return "硕士及以上"
    if "本科及以上" in text or "本科以上" in text:
        return "本科及以上"
    if "学历不限" in text:
        return "不限"
    if "硕士" in text or "master" in lower:
        return "硕士"
    if "本科" in text or "bachelor" in lower:
        return "本科"
    return "未公开"


def infer_graduate_year(text: str) -> list[int]:
    years = {int(value) for value in re.findall(r"(?:20)?(2[5-9])届", text)}
    return sorted({2000 + year if year < 100 else year for year in years})


def infer_job_type(text: str) -> str:
    if "实习转正" in text or "可转正" in text:
        return "实习转正"
    if "提前批" in text:
        return "提前批"
    if "实习" in text:
        return "实习"
    if any(term in text for term in ("校招", "校园招聘", "应届")):
        return "正式校招"
    return "未知"


def infer_status(deadline: str | None, text: str = "", today: date | None = None) -> str:
    today = today or date.today()
    if any(term in text for term in ("招聘已结束", "已截止", "停止招聘")):
        return "expired"
    normalized = normalize_date(deadline)
    if not normalized:
        return "open" if any(term in text for term in ("招聘中", "热招", "开放时间：即日起")) else "unknown"
    delta = (date.fromisoformat(normalized) - today).days
    if delta < 0:
        return "expired"
    if delta <= 7:
        return "closing_soon"
    return "open"


def classify_terms(text: str, keyword_config: dict) -> tuple[list[str], list[str]]:
    normalized = normalize_space(text).lower()
    topics = [name for name, terms in keyword_config.get("topics", {}).items() if any(term.lower() in normalized for term in terms)]
    skills = [name for name, terms in keyword_config.get("skills", {}).items() if any(term.lower() in normalized for term in terms)]
    return topics, skills


def normalize_record(record: dict, keyword_config: dict) -> dict:
    text = " ".join(str(record.get(key) or "") for key in ("title", "description", "requirements", "location_raw"))
    inferred_topics, inferred_skills = classify_terms(text, keyword_config)
    record["title"] = normalize_space(record.get("title"))
    record["company"] = normalize_space(record.get("company"))
    record["city"] = list(dict.fromkeys((record.get("city") or []) + extract_cities(record.get("location_raw") or "")))
    record["degree"] = record.get("degree") if record.get("degree") not in (None, "") else infer_degree(text)
    record["graduate_year"] = record.get("graduate_year") or infer_graduate_year(text)
    record["job_type"] = record.get("job_type") or infer_job_type(text)
    record["published_date"] = normalize_date(record.get("published_date"))
    record["deadline"] = normalize_date(record.get("deadline"))
    record["status"] = record.get("status") or infer_status(record.get("deadline"), text)
    record["topics"] = list(dict.fromkeys((record.get("topics") or []) + inferred_topics))
    record["skills"] = list(dict.fromkeys((record.get("skills") or []) + inferred_skills))
    record["doctoral_exclusive"] = record.get("degree") == "博士" or "博士专属" in text
    return record

