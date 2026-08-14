from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from scripts.build_site import ROOT, build
from scripts.radar.deduplicate import deduplicate
from scripts.radar.match import score_job
from scripts.radar.normalize import extract_cities, infer_degree, infer_graduate_year, infer_job_type, infer_status, normalize_record
from scripts.radar.schema import make_job, validate_job
from scripts.radar.sources import XboticsMarkdownSource
from scripts.radar.utils import normalize_date, valid_http_url


class NormalizeTests(unittest.TestCase):
    def test_date_normalization(self):
        self.assertEqual(normalize_date("2026年8月4日"), "2026-08-04")
        self.assertEqual(normalize_date("2026.7.9"), "2026-07-09")
        self.assertIsNone(normalize_date("未公开"))

    def test_city_normalization(self):
        self.assertEqual(extract_cities("北京 / 深圳 / 合肥"), ["北京", "深圳", "合肥"])

    def test_degree_normalization(self):
        self.assertEqual(infer_degree("本科及以上学历"), "本科及以上")
        self.assertEqual(infer_degree("机器人相关专业博士学位"), "博士")

    def test_graduate_year(self):
        self.assertEqual(infer_graduate_year("面向27届和2028届"), [2027, 2028])

    def test_job_type(self):
        self.assertEqual(infer_job_type("27届校招实习，可转正"), "实习转正")

    def test_status_detection(self):
        self.assertEqual(infer_status("2026-08-18", today=date(2026, 8, 14)), "closing_soon")
        self.assertEqual(infer_status("2026-08-01", today=date(2026, 8, 14)), "expired")
        self.assertEqual(infer_status(None, "招聘中", date(2026, 8, 14)), "open")


class DataTests(unittest.TestCase):
    def sample(self, **overrides):
        values = dict(company="测试机器人", title="VLA算法工程师", source_url="https://example.com/jobs/1", status="open", city=["北京"], topics=["VLA", "机器人操作"])
        values.update(overrides)
        return make_job(**values)

    def test_schema_valid(self):
        self.assertEqual(validate_job(self.sample()), [])

    def test_schema_rejects_empty_title(self):
        self.assertIn("title is required", validate_job(self.sample(title="")))

    def test_broken_url_rejected(self):
        self.assertFalse(valid_http_url("javascript:alert(1)"))
        self.assertIn("invalid source_url", validate_job(self.sample(source_url="not-a-url")))

    def test_deduplication(self):
        one = self.sample(source_url="https://example.com/a")
        two = self.sample(source_url="https://another.example/b", official_apply_url="https://official.example/apply", official_verified=True)
        jobs, count = deduplicate([one, two])
        self.assertEqual(len(jobs), 1)
        self.assertEqual(count, 1)
        self.assertTrue(jobs[0]["official_verified"])

    def test_general_apply_url_does_not_merge_titles(self):
        one = self.sample(title="VLA算法工程师", official_apply_url="https://example.com/campus")
        two = self.sample(title="机器人软件工程师", official_apply_url="https://example.com/campus")
        jobs, _ = deduplicate([one, two])
        self.assertEqual(len(jobs), 2)

    def test_match_score_bounds(self):
        profile = {"research": ["VLA", "robot_manipulation"], "experience": ["pi0.5 deployment", "robot grasping"], "hardware": ["robot arm"], "learning": ["Python", "C++"]}
        job = score_job(self.sample(), profile)
        self.assertGreaterEqual(job["match_score"], 0)
        self.assertLessEqual(job["match_score"], 100)
        self.assertIn(job["match_level"], "SABCD")

    def test_unknown_facts_remain_unknown(self):
        record = normalize_record({"company":"甲","title":"机器人算法","source_url":"https://example.com"}, {"topics":{},"skills":{}})
        job = make_job(**record)
        self.assertIsNone(job["salary"])
        self.assertIsNone(job["deadline"])
        self.assertEqual(job["degree"], "未公开")


class SourceTests(unittest.TestCase):
    def test_xbotics_parsing_and_social_exclusion(self):
        markdown = """**[2026.8.10]**\n[甲机器人 - VLA算法工程师/仿真工程师 - 27届校招](https://example.com/a)\n\n**[2026.8.9]**\n[乙公司 - 机器人销售经理 - 社招](https://example.com/b)"""
        cfg = {"id":"feed","name":"feed","adapter":"xbotics_markdown","raw_url":"https://example.com/readme","source_url":"https://example.com/repo","lookback_days":365}
        with patch("scripts.radar.sources.fetch_text", return_value=markdown):
            result = XboticsMarkdownSource(cfg, {"topics":{"VLA":["vla"],"仿真":["仿真"]},"skills":{}}).discover()
        self.assertTrue(result.ok)
        self.assertEqual([job["title"] for job in result.jobs], ["VLA算法工程师", "仿真工程师"])
        self.assertTrue(all(job["source_tier"] == 3 for job in result.jobs))


class BuildTests(unittest.TestCase):
    def test_build_site(self):
        with tempfile.TemporaryDirectory() as temp:
            output = build(Path(temp) / "site")
            self.assertTrue((output / "index.html").exists())
            self.assertTrue((output / "data/jobs.json").exists())
            jobs = json.loads((output / "data/jobs.json").read_text(encoding="utf-8"))
            self.assertIsInstance(jobs, list)


if __name__ == "__main__":
    unittest.main()

