# Job Schema

`data/jobs.json` 是岗位事实、生命周期和个性化分析的公开合同。

| 分组 | 字段 |
|---|---|
| 身份 | `id`, `job_id`, `company`, `company_en`, `title` |
| 地点与资格 | `city[]`, `location_raw`, `job_type`, `graduate_year[]`, `degree` |
| 招聘事实 | `salary`, `published_date`, `deadline`, `status`, `description`, `requirements[]` |
| 分类 | `skills[]`, `topics[]` |
| 来源 | `source_name`, `source_url`, `source_tier`, `official_apply_url`, `other_apply_urls[]`, `official_verified`, `source_count` |
| 生命周期 | `first_seen`, `last_seen`, `last_verified`, `updated_at`, `content_hash`, `history[]` |
| 个性化分析 | `match_score`, `match_level`, `match_reasons[]`, `skill_gaps[]`, `recommendation`, `resume_tips[]`, `ai_status` |

状态仅允许 `open`、`closing_soon`、`expired`、`unknown`。任何未知事实不得被推断成“合理值”。

