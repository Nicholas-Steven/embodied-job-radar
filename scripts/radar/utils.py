from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


CITIES = [
    "北京", "上海", "深圳", "杭州", "苏州", "广州", "南京", "武汉", "成都", "西安",
    "合肥", "长沙", "天津", "重庆", "东莞", "宁波", "无锡", "郑州", "青岛", "厦门",
]


def today_iso() -> str:
    return datetime.now(timezone.utc).astimezone().date().isoformat()


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_space(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def canonical_text(value: str | None) -> str:
    text = normalize_space(value).lower()
    return re.sub(r"[^0-9a-z\u4e00-\u9fff+#]+", "", text)


def normalize_date(value: str | None) -> str | None:
    if not value:
        return None
    raw = normalize_space(value)
    match = re.search(r"(20\d{2})[年./-](\d{1,2})[月./-](\d{1,2})", raw)
    if not match:
        return None
    try:
        return date(*(int(part) for part in match.groups())).isoformat()
    except ValueError:
        return None


def extract_cities(text: str | None) -> list[str]:
    value = text or ""
    return [city for city in CITIES if city in value]


def stable_id(company: str, title: str, source_url: str = "", job_id: str = "") -> str:
    key = job_id or f"{canonical_text(company)}|{canonical_text(title)}|{urlparse(source_url).path}"
    return "job_" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def content_hash(job: dict) -> str:
    facts = {key: job.get(key) for key in (
        "company", "title", "city", "location_raw", "job_type", "graduate_year", "degree",
        "salary", "published_date", "deadline", "description", "requirements", "skills", "topics",
        "official_apply_url",
    )}
    payload = json.dumps(facts, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def valid_http_url(value: str | None) -> bool:
    if not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

