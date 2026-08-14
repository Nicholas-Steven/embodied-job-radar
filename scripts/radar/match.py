from __future__ import annotations

import re


WEIGHTS = {
    "research": 25,
    "skills": 20,
    "experience": 15,
    "degree": 10,
    "real_robot": 10,
    "paper": 10,
    "engineering": 10,
}

LABELS = {"VLA": "VLA方向一致", "机器人操作": "机器人操作方向一致", "视觉力觉": "视觉力觉融合方向一致", "失败检测/恢复": "失败检测/恢复研究相关", "模型评测": "模型评测职责相关", "仿真": "机器人仿真经验相关", "World Model": "状态理解/世界模型相关", "强化学习": "强化学习方向相关"}


def _tokens(values) -> set[str]:
    return {re.sub(r"[^0-9a-z\u4e00-\u9fff+#]+", "", str(value).lower()) for value in values if value}


def _level(score: int) -> str:
    if score >= 90: return "S"
    if score >= 80: return "A"
    if score >= 70: return "B"
    if score >= 60: return "C"
    return "D"


def score_job(job: dict, profile: dict) -> dict:
    topics = set(job.get("topics") or [])
    skills = _tokens(job.get("skills") or [])
    text = " ".join([job.get("title", ""), job.get("description", ""), " ".join(job.get("requirements") or []), " ".join(topics)]).lower()
    profile_research = " ".join(profile.get("research") or []).lower()
    aligned_topics = {"VLA", "机器人操作", "Robot Learning", "模仿学习", "强化学习", "Diffusion Policy", "视觉力觉", "失败检测/恢复", "World Model", "仿真", "Sim2Real", "模型评测", "后训练", "模型部署"}
    research_hits = [topic for topic in topics if topic in aligned_topics or topic.lower().replace(" ", "_") in profile_research]
    research = min(WEIGHTS["research"], 18 if research_hits else 5)
    if len(research_hits) >= 2:
        research = WEIGHTS["research"]

    known = _tokens((profile.get("experience") or []) + (profile.get("learning") or []))
    skill_hits = skills & known
    topic_skill_points = {"VLA": 10, "机器人操作": 7, "视觉力觉": 10, "失败检测/恢复": 10, "模型评测": 8, "强化学习": 6, "模仿学习": 7, "Diffusion Policy": 8, "仿真": 6, "Sim2Real": 6, "模型部署": 5, "后训练": 5, "World Model": 6, "Robot Learning": 6}
    topic_points = sorted((topic_skill_points.get(topic, 0) for topic in topics), reverse=True)[:2]
    skills_score = min(WEIGHTS["skills"], len(skill_hits) * 4 + sum(topic_points) + (3 if "python" in text else 0))

    experience_markers = [("部署", "pi0.5 deployment"), ("数据", "robot demonstration data collection"), ("抓取", "robot grasping"), ("仿真", "robot simulation"), ("vla", "pi0.5 deployment"), ("操作", "robot grasping")]
    exp_hits = [label for label, profile_term in experience_markers if label in text and profile_term in (profile.get("experience") or [])]
    experience = min(WEIGHTS["experience"], len(exp_hits) * 4)
    if "VLA" in topics and "机器人操作" in topics:
        experience = 15
    elif "VLA" in topics:
        experience = max(experience, 10)
    elif topics & {"模型评测", "失败检测/恢复", "视觉力觉", "仿真", "Sim2Real"}:
        experience = max(experience, 8)

    degree_text = job.get("degree", "")
    degree = 10 if degree_text in {"未公开", "不限", "本科", "本科及以上", "硕士", "硕士及以上"} else 2 if "博士" in degree_text else 6
    robot = 10 if any(term in text for term in ("机械臂", "机器人", "真机", "操作")) and profile.get("hardware") else 3
    paper = 7 if any(term in text for term in ("论文", "研究", "算法研究", "顶会")) and research_hits else 3
    engineering_terms = [term for term in ("python", "linux", "ros2", "c++", "cuda", "tensorrt", "部署") if term in text]
    engineering = min(10, 3 + len(engineering_terms) * 2)
    score = max(0, min(100, round(research + skills_score + experience + degree + robot + paper + engineering)))

    reasons = [LABELS.get(topic, f"{topic}方向相关") for topic in research_hits[:4]]
    if robot >= 10: reasons.append("有真实机器人与机械臂实验背景")
    if "数据" in text: reasons.append("有机器人示教数据采集经验")
    reasons = list(dict.fromkeys(reasons))[:5]

    gaps = []
    for needle, label in (("c++", "C++工程能力需要进一步证明"), ("isaac lab", "Isaac Lab项目经验不足"), ("强化学习", "强化学习完整项目证据不足"), ("cuda", "CUDA/推理优化经验需补强")):
        if needle in text and needle.replace(" ", "") not in known:
            gaps.append(label)
    if "博士" in degree_text:
        gaps.append("岗位偏好或限定博士背景")

    tips = []
    if "VLA" in topics: tips.append("突出π0.5部署、真机测试与失败案例分析")
    if "机器人操作" in topics: tips.append("量化机械臂抓取与示教数据采集规模")
    if "视觉力觉" in topics: tips.append("说明六维力传感器与视觉力觉融合方案")
    if "仿真" in topics or "Sim2Real" in topics: tips.append("补充仿真到真机的评测指标和复现实验")
    if not tips: tips.append("用可复现项目结果对应岗位核心职责")

    recommendation = "强烈建议投递" if score >= 90 else "建议投递" if score >= 80 else "可以尝试" if score >= 70 else "低优先级" if score >= 60 else "暂不建议"
    job.update(match_score=score, match_level=_level(score), match_reasons=reasons, skill_gaps=gaps[:4], recommendation=recommendation, resume_tips=tips[:4])
    return job
