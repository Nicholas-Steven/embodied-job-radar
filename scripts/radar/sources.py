from __future__ import annotations

import re
import ssl
from dataclasses import dataclass
from datetime import date, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from .normalize import infer_job_type, infer_graduate_year, normalize_record
from .schema import make_job
from .utils import normalize_date, normalize_space


USER_AGENT = "EmbodiedJobRadar/1.0 (+https://github.com/Nicholas-Steven/embodied-job-radar)"


def fetch_text(url: str, timeout: int = 25) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,text/plain"})
    context = ssl.create_default_context()
    with urlopen(request, timeout=timeout, context=context) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


@dataclass
class SourceResult:
    source_id: str
    source_name: str
    jobs: list[dict]
    ok: bool
    error: str | None = None


class SourceAdapter:
    def __init__(self, config: dict, keyword_config: dict):
        self.config = config
        self.keyword_config = keyword_config

    def discover(self) -> SourceResult:
        raise NotImplementedError


class RecordsSource(SourceAdapter):
    """Configuration-backed, source-cited records for announcements with stable facts."""

    def discover(self) -> SourceResult:
        cfg = self.config
        common = cfg.get("common") or {}
        jobs = []
        for item in cfg.get("records") or []:
            record = {
                **common,
                **item,
                "company": cfg.get("company", ""),
                "source_name": cfg.get("name", ""),
                "source_url": cfg.get("source_url", ""),
                "source_tier": cfg.get("tier", 3),
                "official_apply_url": cfg.get("official_apply_url"),
                "official_verified": bool(cfg.get("official_verified", False)),
            }
            jobs.append(make_job(**normalize_record(record, self.keyword_config)))
        return SourceResult(cfg["id"], cfg.get("name", cfg["id"]), jobs, True)


class XboticsMarkdownSource(SourceAdapter):
    DATE_LINE = re.compile(r"\*\*\[(20\d{2}[.\-/]\d{1,2}[.\-/]\d{1,2})\]\*\*")
    LINK_LINE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    def discover(self) -> SourceResult:
        cfg = self.config
        try:
            markdown = fetch_text(cfg["raw_url"])
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            return SourceResult(cfg["id"], cfg.get("name", cfg["id"]), [], False, f"{type(exc).__name__}: {exc}")
        cutoff = date.today() - timedelta(days=int(cfg.get("lookback_days", 90)))
        jobs: list[dict] = []
        entries = []
        pending_date = None
        for line in markdown.splitlines():
            date_match = self.DATE_LINE.search(line)
            if date_match:
                pending_date = date_match.group(1)
                continue
            link_match = self.LINK_LINE.search(line)
            if pending_date and link_match:
                entries.append((pending_date, link_match.group(1), urljoin(cfg["source_url"] + "/", link_match.group(2))))
                pending_date = None
        for raw_date, label, target_url in entries:
            published = normalize_date(raw_date)
            if not published or date.fromisoformat(published) < cutoff:
                continue
            parts = [normalize_space(part) for part in re.split(r"\s+-\s+", label) if normalize_space(part)]
            if len(parts) < 2:
                continue
            company = parts[0]
            role_text = parts[1] if len(parts) == 2 else " - ".join(parts[1:-1])
            type_text = parts[-1] if len(parts) > 2 else label
            eligibility = f"{role_text} {type_text}"
            relevant_terms = ("具身", "机器人", "vla", "算法", "仿真", "控制", "slam", "导航", "模型", "数据", "软件", "c++", "python", "ros", "感知", "视觉", "触觉", "规划", "部署", "infra", "强化学习", "机械臂", "灵巧手")
            if not any(term in role_text.lower() for term in relevant_terms):
                continue
            if "社招" in type_text and not any(term in eligibility for term in ("校招", "应届", "实习", "经验不限", "0-1年", "0—1年")):
                continue
            if not any(term in eligibility.lower() for term in ("校招", "应届", "实习", "27届", "2027", "博士", "研究助理", "vla", "机器人", "具身")):
                continue
            titles = [normalize_space(value) for value in re.split(r"[/／]", role_text) if normalize_space(value)]
            if not titles or len(titles) > 14:
                titles = [role_text]
            for title in titles:
                record = normalize_record({
                    "company": company,
                    "title": title,
                    "description": "",
                    "job_type": infer_job_type(eligibility),
                    "graduate_year": infer_graduate_year(eligibility),
                    "published_date": published,
                    "status": "unknown",
                    "source_name": cfg.get("name", ""),
                    "source_url": target_url,
                    "source_tier": 3,
                    "official_apply_url": None,
                    "official_verified": False,
                    "doctoral_exclusive": "博士" in type_text and not any(term in type_text for term in ("硕士", "本科", "实习")),
                }, self.keyword_config)
                jobs.append(make_job(**record))
        return SourceResult(cfg["id"], cfg.get("name", cfg["id"]), jobs, True)


ADAPTERS = {"records": RecordsSource, "xbotics_markdown": XboticsMarkdownSource}


def run_source(config: dict, keyword_config: dict) -> SourceResult:
    adapter = ADAPTERS.get(config.get("adapter"))
    if not adapter:
        return SourceResult(config.get("id", "unknown"), config.get("name", "unknown"), [], False, "unsupported adapter")
    try:
        return adapter(config, keyword_config).discover()
    except Exception as exc:  # one source must never abort the full update
        return SourceResult(config.get("id", "unknown"), config.get("name", "unknown"), [], False, f"{type(exc).__name__}: {exc}")
