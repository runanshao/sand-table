#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
史鉴推演 · 复盘统计（确定性，不靠 AI 记性）

读 decisions.jsonl，算出：判断质量轨迹、五维均分（最弱维=定向出题信号）、
证伪条件缺失率、盲点标签清单。诚实标注样本量。

用法：
  python stats.py                 # 读同目录 decisions.jsonl
  python stats.py 路径/decisions.jsonl
  python stats.py --scenario 官渡  # 只看某场景
"""
import json
import sys
from pathlib import Path
from collections import defaultdict, Counter

# Windows 终端默认 cp1252/cp936，打不出中文 → 强制 UTF-8 输出
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

DIMS = ["信息利用", "风险定价", "反证强度", "目标对齐", "盲点意识"]
RULE_N = 5  # 同类样本 < RULE_N 只算"观察"，不下"规律"


def load(path: Path, scenario_filter=None):
    """返回 (锚点记录, 整局复盘记录)。锚点记录 = 含'五维'字段的行。"""
    anchors, summaries, bad = [], [], 0
    if not path.exists():
        print(f"找不到日志：{path}", file=sys.stderr)
        sys.exit(1)
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            bad += 1
            continue
        if scenario_filter and rec.get("场景") != scenario_filter:
            continue
        if "五维" in rec:
            anchors.append(rec)
        elif rec.get("类型") == "整局复盘":
            summaries.append(rec)
    if bad:
        print(f"（跳过 {bad} 行无法解析的记录）", file=sys.stderr)
    return anchors, summaries


def missing_falsifier(rec) -> bool:
    """证伪条件缺失：空，或以 '(' 开头的元注释（如'(未明确给出)'）。"""
    v = (rec.get("证伪条件") or "").strip()
    return (not v) or v.startswith("(") or v.startswith("（")


def report(anchors, summaries):
    if not anchors:
        print("还没有可统计的锚点记录。先去跑一局。")
        return

    n = len(anchors)
    scenes = sorted({a.get("场景", "?") for a in anchors})
    print("=" * 56)
    print(f"史鉴推演 · 复盘统计   锚点数 N={n}   场景：{', '.join(scenes)}")
    print("=" * 56)

    # 1. 判断质量轨迹（按场景，按锚点序）
    print("\n【判断质量轨迹】(总分/10)")
    by_scene = defaultdict(list)
    for a in anchors:
        by_scene[a.get("场景", "?")].append(a)
    overall_scores = []
    for scene, recs in by_scene.items():
        recs.sort(key=lambda r: r.get("锚点", 0))
        scores = [r.get("总分") for r in recs if isinstance(r.get("总分"), (int, float))]
        overall_scores += scores
        traj = "→".join(str(s) for s in scores)
        avg = sum(scores) / len(scores) if scores else 0
        print(f"  {scene}: {traj}   均分 {avg:.1f}")
    if overall_scores:
        print(f"  全局均分：{sum(overall_scores)/len(overall_scores):.1f}/10")

    # 2. 五维均分 → 最弱维 = 定向出题信号
    print("\n【五维均分】(0-2，越低越该练)")
    dim_scores = defaultdict(list)
    for a in anchors:
        wd = a.get("五维", {})
        for d in DIMS:
            if isinstance(wd.get(d), (int, float)):
                dim_scores[d].append(wd[d])
    dim_avg = {d: (sum(v) / len(v)) for d, v in dim_scores.items() if v}
    for d in DIMS:
        if d in dim_avg:
            bar = "█" * round(dim_avg[d] * 5)
            print(f"  {d}: {dim_avg[d]:.2f}  {bar}")
    if dim_avg:
        weakest = min(dim_avg, key=dim_avg.get)
        tag = "观察" if n < RULE_N else "可作定向"
        print(f"  → 最弱维：【{weakest}】({dim_avg[weakest]:.2f})  ← 下一局定向出题应专戳这里  [{tag}, N={n}]")

    # 3. 证伪条件缺失率
    miss = sum(1 for a in anchors if missing_falsifier(a))
    print(f"\n【证伪条件缺失率】{miss}/{n} = {miss/n*100:.0f}%"
          + ("   ← 攻击型选手通病：决策时不写'什么算我错了'" if miss / n >= 0.5 else ""))

    # 4. 盲点标签清单（确定性只做罗列；聚类是判断不是计算）
    tags = []
    for a in anchors:
        for t in a.get("盲点标签", []) or []:
            tags.append((a.get("场景", "?"), a.get("锚点", "?"), t))
    print(f"\n【盲点标签清单】(共 {len(tags)} 条；语义聚类需人/AI 判断，脚本不臆断)")
    for scene, anc, t in tags:
        print(f"  · [{scene}·锚{anc}] {t}")

    # 4.5 死亡对账（生存层）——仅统计带相关字段的记录
    deaths = [s for s in summaries if ("本该死锚点" in s or "本该死" in s)]
    death_anchors = [a for a in anchors if a.get("致死概率")]
    if deaths or death_anchors:
        print("\n【死亡对账】(练判断不练赌运气：记的是'本该死'，不是'实际死')")
        for s in deaths:
            scene = s.get("场景", "?")
            should = s.get("本该死锚点", s.get("本该死", "?"))
            actual = s.get("实际死锚点", s.get("实际死", "?"))
            note = ""
            if isinstance(should, (int, float)) and isinstance(actual, (int, float)):
                if actual > should:
                    note = "  ← 实际>本该：运气吊着你，别当判断好"
                elif actual < should:
                    note = "  ← 实际<本该：判断没错，输在史实运气"
                else:
                    note = "  ← 判断与命运对齐"
            print(f"  {scene}: 本该死@锚{should} / 实际死@锚{actual}{note}")
        if death_anchors:
            print(f"  （{len(death_anchors)} 个锚点带致死概率估计）")

    # 5. 样本量诚实
    print("\n【样本量诚实】")
    if n < RULE_N:
        print(f"  N={n} < {RULE_N}：以上一律为『观察』，不构成『规律』。")
        print(f"  再积累 {RULE_N - n} 个锚点，复发盲点才够格被正式记入你的判断画像。")
    else:
        print(f"  N={n} ≥ {RULE_N}：复发≥2次的盲点可作候选规律，仍需跨场景验证。")
    print("=" * 56)


def load_real(path):
    """读现实决策台账（每行一条 JSON）。不存在则返回空。"""
    if not path.exists():
        return []
    recs = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            recs.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return recs


def report_real(recs):
    """现实决策台账——现实决断力的真考核（闭环在现实上，不在历史上）。"""
    if not recs:
        return
    import datetime
    today = datetime.date.today().isoformat()
    pending = [r for r in recs if r.get("status") == "pending"]
    resolved = [r for r in recs if r.get("status") == "resolved"]
    due = [r for r in pending if str(r.get("复盘日期", "9999")) <= today]
    print("\n【现实决策台账】(现实决断力的真考核——它才是这工具的最终成绩单)")
    print(f"  待复盘 {len(pending)}  ｜  已复盘 {len(resolved)}")
    if due:
        print("  ⏰ 已到期、开局应先复盘：")
        for r in due:
            print(f"     · {r.get('ts','?')} 「{r.get('决策','?')}」→ 选择:{r.get('选择','?')}  (复盘日 {r.get('复盘日期','?')})")
    elif pending:
        nxt = min(pending, key=lambda r: str(r.get("复盘日期", "9999")))
        print(f"  下一个复盘日：{nxt.get('复盘日期','?')} — 「{nxt.get('决策','?')}」")
    print("  规则：复盘真实决策同样守『判断≠结果』——判断好但运气背，不扣分；侥幸成了，照样点破。")


def report_improvement(anchors, real_recs):
    """头条指标：判断力是否在持续改善（卖点）。把所有计分决策按时间排成一条曲线，
    比早半段 vs 近半段，给出趋势；并报现实决策入环进度（闭环在现实上）。"""
    scored = [a for a in anchors if isinstance(a.get("总分"), (int, float))]
    scored.sort(key=lambda r: (str(r.get("ts", "")), str(r.get("场景", "")), r.get("锚点", 0)))
    print("=" * 56)
    print("判断力 · 持续改善（这工具的头条指标）")
    print("=" * 56)
    if len(scored) >= 4:
        half = len(scored) // 2
        early = sum(r["总分"] for r in scored[:half]) / half
        late = sum(r["总分"] for r in scored[half:]) / (len(scored) - half)
        delta = late - early
        arrow = "↑ 改善" if delta >= 0.5 else ("↓ 退步" if delta <= -0.5 else "→ 持平")
        span = f"{scored[0].get('ts','?')} → {scored[-1].get('ts','?')}"
        print(f"  时间跨度 {span} ｜ 计分决策 {len(scored)}")
        print(f"  早半段均分 {early:.1f}  →  近半段均分 {late:.1f}   {arrow}（{delta:+.1f}）")
    else:
        print(f"  计分决策 {len(scored)} 个——还不够看趋势（需≥4）。先多跑几次，把环喂起来。")
    pend = sum(1 for r in real_recs if r.get("status") == "pending")
    res = sum(1 for r in real_recs if r.get("status") == "resolved")
    print(f"  现实决策入环：待复盘 {pend} ｜ 已复盘 {res}  ← 闭环在现实上的进度（真考核）")
    print("=" * 56)


def main():
    args = [a for a in sys.argv[1:]]
    scenario = None
    if "--scenario" in args:
        i = args.index("--scenario")
        scenario = args[i + 1] if i + 1 < len(args) else None
        del args[i:i + 2]
    path = Path(args[0]) if args else Path(__file__).with_name("decisions.jsonl")
    anchors, summaries = load(path, scenario)
    real_name = "real_decisions.example.jsonl" if path.name.endswith(".example.jsonl") else "real_decisions.jsonl"
    real_recs = load_real(path.with_name(real_name))
    report_improvement(anchors, real_recs)   # 头条先打
    report(anchors, summaries)
    report_real(real_recs)


if __name__ == "__main__":
    main()
