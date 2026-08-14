# Architecture

## 边界

Embodied Job Radar 是独立项目，不修改 `embodied-research-radar`。运行时是纯静态 GitHub Pages；抓取、标准化、去重、状态更新、匹配和构建只在 GitHub Actions 中执行。

## 数据流

```text
companies.yaml / sources.yaml / keywords.yaml / profile.yaml
                              ↓
                    Source Adapters（逐源隔离）
                              ↓
              normalize → relevance gate → schema
                              ↓
                 identity resolution → lifecycle merge
                              ↓
             deterministic match → optional LLM analysis
                              ↓
          data/jobs.json + stats.json + update-report.json
                              ↓
                   build_site.py → site/ → Pages
```

## 数据合同

事实字段和分析字段严格分层。公司、岗位、地点、学历、薪资、日期、JD、状态与投递地址只能来自来源页面；分析模块只能写匹配解释、短板、建议和简历提示。未知事实使用 `null`、空数组或“未公开”。

## 来源适配器

- `RecordsSource`：稳定招聘公告的结构化事实，保留公告与官方投递双链接。
- `XboticsMarkdownSource`：Tier 3 自动发现；过滤纯社招，解析最近 90 天校招/实习/博士线索。
- 新来源只需实现 `discover() -> SourceResult` 并在 `ADAPTERS` 注册；单源失败不会中断其他来源。

## 生命周期与去重

身份优先级为职位 ID、公司+规范化标题+城市、再到高阈值标题相似度。共享同一公司招聘入口不会导致不同职位合并。数据源失败时旧记录原样保留；只有明确截止日期或结束证据才允许过期。内容哈希变化写入最多 8 个历史快照。

## 匹配模块

`config/profile.yaml` 是唯一用户画像入口。确定性基线按研究方向、技能、项目经验、学历、真机、论文方向和工程栈七组权重计分。LLM 是可选增强层；失败只标记 `ai_status=pending`，不阻塞数据更新。

## Web 与性能

前端读取 JSON，在浏览器完成全文搜索、城市多选、筛选、排序、公司聚合、可信度与分页渲染。首版每次渲染 24 条，足以平滑扩展到数千条；达到约 5000 条后可按月份/状态拆分 JSON，不改变 Schema。

