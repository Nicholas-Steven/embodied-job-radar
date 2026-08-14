# Embodied Job Radar

面向 2027 届工科硕士的具身智能岗位雷达：追踪 VLA、机器人操作、Robot Learning、强化学习、视觉力觉、仿真、模型评测、后训练、部署与机器人软件岗位。

目标在线地址：<https://nicholas-steven.github.io/embodied-job-radar/>

> 数据质量顺序：真实岗位 > 官方来源 > 正确状态 > 正确投递链接 > 多源核验 > 数量。最终招聘状态以企业官方页面为准。

## 功能

- 多来源发现：官方/高校公告优先，社区索引只作 Tier 3 线索。
- 全国城市：不在采集阶段限制城市；前端支持城市搜索和多选。
- 全文搜索与组合筛选：校招/实习与社招/全职分开选择，支持方向、学历、招聘类型、匹配度、状态和时间。
- 低干扰卡片：匹配度和个人分析默认折叠，可按需展开；岗位卡片提供蓝色事实信息带、薪资（来源明确时）和悬浮反馈。
- 职位去重与生命周期：保留多个来源、JD 内容哈希、首次/最后发现和历史岗位。
- 个人匹配：0–100 分、S–D 等级、适配原因、能力短板、投递和简历建议。
- 可信度：`OFFICIAL`、`VERIFIED`、`AGGREGATED`、`UNVERIFIED`。
- 公司视图：当前岗位、高匹配岗位、历史岗位、技能与招聘城市。
- 静态部署：浏览器读取 JSON，无账户、无后端、适配 GitHub Pages。
- 自动更新：北京时间每天 08:30 与 20:30，并支持手动触发。

## 截图

发布后的首页可直接通过上方在线地址查看；首页包含总览统计、今日最值得投、组合筛选、岗位解释和招聘趋势。仓库的 `web/` 是可直接审阅的完整界面源文件。

## 数据现状

首次快照由可核验的 2027 校招公告/官网记录与 Xbotics 公开社区索引自动生成。当前配置包含 8 个来源，具体数量、成功/失败来源与官方核验数始终以 `data/stats.json` 和 `logs/update-report.json` 为准；README 不写死会过期的数量。

当前适配器：

1. `RecordsSource`：清华/兰大等高校公告，以及千寻、银河、字节、自变量、它石智航、松灵、积加等官方招聘入口。
2. `XboticsMarkdownSource`：最近 90 天的校招、实习、应届与博士线索；自动排除纯社招。

当前结构已为企业官网列表页、大学就业网和搜索发现适配器预留统一契约。Tier 3 记录不会被标记成官网核验。

## 目录

```text
.
├── .github/workflows/update.yml
├── config/
│   ├── companies.yaml
│   ├── keywords.yaml
│   ├── profile.yaml
│   └── sources.yaml
├── data/
│   ├── jobs.json
│   └── stats.json
├── logs/update-report.json
├── scripts/
│   ├── update_jobs.py
│   ├── build_site.py
│   ├── validate_data.py
│   └── radar/
├── tests/
├── web/
├── ARCHITECTURE.md
└── DATA_SCHEMA.md
```

## 本地运行

需要 Python 3.11+。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/update_jobs.py --no-ai
python scripts/build_site.py
python -m http.server 8000 --directory site
```

打开 <http://localhost:8000/>。

第一次建立全新快照可使用：

```bash
python scripts/update_jobs.py --no-ai --bootstrap
```

日常更新不要使用 `--bootstrap`，否则会丢失已有生命周期上下文。

## 配置

### 增加公司

在 `config/companies.yaml` 增加：

```yaml
- name: 新公司
  career_url: https://example.com/careers
```

公司清单是官方入口和发现范围的种子，不限制自动发现的新公司。

### 增加关键词

在 `config/keywords.yaml` 的 `topics` 或 `skills` 中增加规范标签及同义词。事实字段不会因为关键词命中而被补写；关键词只用于相关性分类。

### 更新个人 Profile

编辑 `config/profile.yaml`。评分代码读取该配置，未把个人经历写死在前端。只填写真实经历；匹配解释和简历提示不会创造不存在的项目。

### 增加数据源

优先在 `config/sources.yaml` 配置。需要新页面结构时，在 `scripts/radar/sources.py` 中实现 `SourceAdapter.discover()` 并注册到 `ADAPTERS`。适配器必须：

- 返回原始来源 URL；
- 未公开字段保持空或“未公开”；
- 不把搜索结果/聚合页标成官方；
- 单源失败时返回失败报告，不删除旧岗位。

## LLM 配置

LLM 只允许改进分析字段：匹配原因、短板、建议和简历提示。岗位名称、公司、薪资、地点、学历、届次、日期、状态、JD 和链接禁止由模型补写。

GitHub Secret：

- `LLM_API_KEY`

GitHub Variables：

- `LLM_BASE_URL`
- `LLM_MODEL`

未配置或 API 失败时，确定性评分照常运行，新增岗位照常写入，`ai_status` 保持 `not_requested` 或 `pending`，工作流不会因此失败。

## GitHub Pages

推送到公开仓库 `Nicholas-Steven/embodied-job-radar` 的 `main` 分支。工作流具有 Pages 权限并执行：测试 → 发现 → 规范化 → 去重 → 生命周期合并 → 匹配 → 构建 → 验证 → 保存数据 → 部署。

定时计划使用 UTC：

```yaml
- cron: "30 0,12 * * *"
```

对应北京时间 08:30 与 20:30，无夏令时。也可在 Actions 页面用 `workflow_dispatch` 手动更新。

## 数据可信度与已知限制

- 部分招聘页面使用强 JavaScript 渲染或反自动化措施，可能只能保留公告级事实。
- 没有明确截止日期时不会猜测；状态可能显示“未知”。
- 社区源适合发现，不等于企业背书；使用前应打开来源或官网再次核对。
- 首轮没有前一周快照，因此趋势显示“样本不足”，不会编造增量。
- `salary` 只有来源明确披露时才填写；聚合薪资不自动等同校招薪资。

## 测试与质量门槛

测试覆盖日期、城市、学历、届次、招聘类型、状态、来源解析、去重、通用投递入口误合并、匹配分边界、未知事实、URL、Schema 和静态站构建。部署前额外验证：必填字段、URL、分数边界、生命周期顺序、过期状态和重复 ID。

## 免责声明

本项目只整理公开招聘信息，不代表招聘方。岗位可能随时调整或关闭；投递、资格和截止时间以企业官方页面为准。不得将本项目用于绕过访问控制、付费墙或网站条款。
