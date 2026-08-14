from __future__ import annotations

import json
import os
from urllib.request import Request, urlopen


ANALYSIS_FIELDS = {"match_reasons", "skill_gaps", "recommendation", "resume_tips"}


def enrich_job(job: dict, profile: dict) -> tuple[dict, bool]:
    api_key = os.getenv("LLM_API_KEY", "").strip()
    base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")
    model = os.getenv("LLM_MODEL", "").strip()
    if not (api_key and base_url and model):
        return job, False
    prompt = {
        "task": "仅基于给定岗位事实和用户配置，改进匹配解释。不得新增或改写任何岗位事实。",
        "job": {key: job.get(key) for key in ("title", "company", "description", "requirements", "skills", "topics", "degree")},
        "profile": profile,
        "output": {"match_reasons": ["2-5条"], "skill_gaps": ["0-4条"], "recommendation": "强烈建议投递|建议投递|可以尝试|低优先级|暂不建议", "resume_tips": ["2-4条"]},
    }
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": json.dumps(prompt, ensure_ascii=False)}], "response_format": {"type": "json_object"}, "temperature": 0.1}).encode()
    request = Request(f"{base_url}/chat/completions", data=body, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=45) as response:
            payload = json.loads(response.read().decode("utf-8"))
        parsed = json.loads(payload["choices"][0]["message"]["content"])
        for key in ANALYSIS_FIELDS:
            if key in parsed:
                job[key] = parsed[key]
        job["ai_status"] = "complete"
        return job, False
    except Exception:
        job["ai_status"] = "pending"
        return job, True

