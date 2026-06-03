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
RULE_N = 5      # 同类样本 < RULE_N 只算"观察"，不下"规律"
MIN_PER_DIM = 3  # 某维样本 < 此值 → 冷启动 breadth 模式（先铺五维，不急定向）


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
        if rec.get("数据有效") is False or rec.get("类型") == "校准":
            continue  # 排除无效样本(如通电验收)与校准跑分，判断力曲线只收干净数据
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


# ========== workflow 确定性零件：诊断 / 推荐 / 校准 ==========

def diagnose(anchors):
    """确定性诊断：五维均分、最弱维、复发盲点、证伪缺失、早晚趋势。供 --diagnose 与 recommend 复用。"""
    dims = defaultdict(list)
    for a in anchors:
        wd = a.get("五维", {})
        for d in DIMS:
            if isinstance(wd.get(d), (int, float)):
                dims[d].append(wd[d])
    dim_avg = {d: sum(v) / len(v) for d, v in dims.items() if v}
    dim_n = {d: len(v) for d, v in dims.items()}
    n = len(anchors)
    weakest = min(dim_avg, key=dim_avg.get) if dim_avg else None
    tagc = Counter()
    for a in anchors:
        for t in a.get("盲点标签", []) or []:
            tagc[t] += 1
    recurring = sorted([(t, c) for t, c in tagc.items() if c >= 2], key=lambda x: -x[1])
    miss = sum(1 for a in anchors if missing_falsifier(a))
    scored = sorted([a for a in anchors if isinstance(a.get("总分"), (int, float))],
                    key=lambda r: (str(r.get("ts", "")), str(r.get("场景", "")), r.get("锚点", 0)))
    trend = None
    if len(scored) >= 4:
        h = len(scored) // 2
        early = sum(r["总分"] for r in scored[:h]) / h
        late = sum(r["总分"] for r in scored[h:]) / (len(scored) - h)
        trend = (round(early, 1), round(late, 1), round(late - early, 1))
    return {"n": n, "dim_avg": dim_avg, "dim_n": dim_n, "weakest": weakest,
            "recurring": recurring, "miss": miss, "trend": trend,
            "label": "观察" if n < RULE_N else "可作定向"}


def print_diagnose(anchors):
    d = diagnose(anchors)
    print("=" * 56)
    print("判断力诊断（确定性 · diagnose）")
    print("=" * 56)
    if not d["dim_avg"]:
        print("还没有可诊断的锚点。先跑几局。")
        return
    print(f"样本 N={d['n']}  [{d['label']}]")
    print("\n五维均分（升序，越靠前越该练）:")
    for dim in sorted(d["dim_avg"], key=d["dim_avg"].get):
        print(f"  {dim}: {d['dim_avg'][dim]:.2f}  (n={d['dim_n'].get(dim, 0)})")
    print(f"\n最弱维：【{d['weakest']}】 ← 定向出题信号")
    if d["n"]:
        print(f"证伪条件缺失率：{d['miss']}/{d['n']} = {d['miss'] / d['n'] * 100:.0f}%")
    if d["recurring"]:
        tag = "候选规律" if d["n"] >= RULE_N else "观察(n<5)"
        print(f"\n复发盲点（≥2次，{tag}）:")
        for t, c in d["recurring"]:
            print(f"  ×{c}  {t}")
    else:
        print("\n复发盲点：暂无（无≥2次的标签）")
    if d["trend"]:
        e, l, delta = d["trend"]
        arrow = "↑改善" if delta >= 0.5 else ("↓退步" if delta <= -0.5 else "→持平")
        print(f"\n趋势：早半 {e} → 近半 {l}  {arrow} ({delta:+})")
    else:
        print("\n趋势：计分锚点 <4，还看不出。")


def load_blind_library(here):
    """读 library 下所有 *.blind.md 的 meta（trains_dims 等）。需 PyYAML；缺则返回 None。"""
    try:
        import yaml
    except ImportError:
        return None
    lib = []
    for p in sorted((here / "library").rglob("*.blind.md")):
        lines = p.read_text(encoding="utf-8").splitlines()
        if not lines or lines[0].strip() != "---":
            continue
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
        if end is None:
            continue
        try:
            data = yaml.safe_load("\n".join(lines[1:end])) or {}
        except yaml.YAMLError:
            continue
        meta = data.get("meta", {}) or {}
        lib.append({"id": meta.get("id"), "title": meta.get("title"),
                    "tier": meta.get("tier"), "trains_dims": meta.get("trains_dims", []) or []})
    return lib


def recommend(anchors, here):
    """确定性下一局推荐：冷启动 breadth / 弱项 targeted，按 trains_dims 与目标维度重叠排场景。"""
    d = diagnose(anchors)
    lib = load_blind_library(here)
    if lib is None:
        return {"error": "需要 PyYAML 才能读场景 trains_dims：pip install pyyaml"}
    dim_n = d["dim_n"]
    undersampled = [dim for dim in DIMS if dim_n.get(dim, 0) < MIN_PER_DIM]
    if undersampled:
        mode, targets = "breadth", undersampled
    else:
        mode, targets = "targeted", ([d["weakest"]] if d["weakest"] else [])
    ranked = []
    for s in lib:
        overlap = [dim for dim in s["trains_dims"] if dim in targets]
        if overlap:
            ranked.append((len(overlap), s, overlap))
    ranked.sort(key=lambda x: -x[0])
    return {"mode": mode, "targets": targets, "weakest": d["weakest"],
            "dim_n": dim_n, "candidates": ranked, "n": d["n"]}


def print_recommend(anchors, here):
    r = recommend(anchors, here)
    print("=" * 56)
    print("下一局推荐（确定性 · recommend）")
    print("=" * 56)
    if "error" in r:
        print(r["error"]); return
    if r["mode"] == "breadth":
        print(f"模式：breadth 冷启动（有维度样本 <{MIN_PER_DIM}，先把五维铺开、不急定向）")
        print(f"待补样本的维度：{r['targets']}")
    else:
        print("模式：targeted 定向（五维样本已够）")
        print(f"主攻最弱维：【{r['weakest']}】")
    if not r["candidates"]:
        print("\n场景库里没有 trains_dims 命中目标维度的场景——该补这类场景了。")
        return
    print("\n候选场景（按命中目标维度数排序）:")
    for ov, s, overlap in r["candidates"]:
        print(f"  [{ov}] {s['title']}（{s['id']}） trains={s['trains_dims']} ← 命中 {overlap}")
    top = r["candidates"][0][1]
    print(f"\n→ 推荐下一局：{top['title']}（{top['id']}，{top['tier']}）")


def load_jsonl(path):
    if not path.exists():
        return []
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except json.JSONDecodeError:
            continue
    return out


def calibrate(here):
    """裁判校准：固定金标决策的裁判跑分 vs 冻结金标分，测系统性偏移(松/紧)与重测噪声底。
    gold=calibration.jsonl（入库）；runs=calibration_runs.jsonl（个人，跑校准模式时追加，带 case_id）。"""
    from statistics import mean, pstdev
    gold = {g["case_id"]: g for g in load_jsonl(here / "calibration.jsonl")}
    runs = load_jsonl(here / "calibration_runs.jsonl")
    out = {"gold_n": len(gold), "run_n": len(runs), "cases": [],
           "overall_bias": None, "noise_floor": None, "dim_bias": {}}
    if not gold or not runs:
        return out
    per_case_bias = []
    dim_diffs = defaultdict(list)
    for cid, g in gold.items():
        rs = [r for r in runs if r.get("case_id") == cid and isinstance(r.get("总分"), (int, float))]
        if not rs:
            continue
        totals = [r["总分"] for r in rs]
        bias = mean(totals) - g.get("gold总分", 0)
        spread = pstdev(totals) if len(totals) >= 2 else None
        per_case_bias.append(bias)
        for dim in DIMS:
            gv = g.get("gold五维", {}).get(dim)
            jv = [r["五维"][dim] for r in rs
                  if isinstance(r.get("五维", {}).get(dim), (int, float))]
            if isinstance(gv, (int, float)) and jv:
                dim_diffs[dim].append(mean(jv) - gv)
        out["cases"].append({"case_id": cid, "gold": g.get("gold总分"),
                             "judge_mean": round(mean(totals), 2), "bias": round(bias, 2),
                             "retest_spread": (round(spread, 2) if spread is not None else None),
                             "runs": len(totals)})
    if per_case_bias:
        out["overall_bias"] = round(mean(per_case_bias), 2)
        spreads = [c["retest_spread"] for c in out["cases"] if c["retest_spread"] is not None]
        out["noise_floor"] = round(max(spreads), 2) if spreads else None
        out["dim_bias"] = {dim: round(mean(v), 2) for dim, v in dim_diffs.items()}
    return out


def print_calibrate(here):
    c = calibrate(here)
    print("=" * 56)
    print("裁判校准（确定性 · calibrate）—— 仪器没校准，曲线就不可信")
    print("=" * 56)
    print(f"金标 {c['gold_n']} 例 ｜ 校准跑分 {c['run_n']} 条")
    if not c["cases"]:
        print("\n还没有可比对的校准跑分。跑法：")
        print("  进入「校准模式」，让裁判盲评 calibration.jsonl 里每个固定决策，")
        print("  把它的五维+总分追加进 calibration_runs.jsonl（带同一 case_id），再跑本命令。")
        return
    print("\n逐例（裁判均分 vs 金标，bias>0=偏松）:")
    for x in c["cases"]:
        sp = f"，重测波动±{x['retest_spread']}" if x["retest_spread"] is not None else ""
        print(f"  {x['case_id']}: 金标{x['gold']} / 裁判{x['judge_mean']}  bias {x['bias']:+}{sp}  (n={x['runs']})")
    print(f"\n总体偏移：{c['overall_bias']:+}"
          f"（裁判系统性{'偏松' if c['overall_bias'] > 0 else ('偏紧' if c['overall_bias'] < 0 else '居中')}）")
    if c["noise_floor"] is not None:
        print(f"重测噪声底：±{c['noise_floor']} —— 判断质量变化小于这个数，是裁判抖动、不是你真变了")
    if c["dim_bias"]:
        print("分维偏移:", "  ".join(f"{k}{v:+}" for k, v in c["dim_bias"].items()))
    if c["run_n"] < RULE_N:
        print(f"\n诚实：校准跑分 {c['run_n']}<{RULE_N}，以上为『观察』非定论，多跑几轮才算数。")
    print("\n用法：把'总体偏移'从本期判断力曲线里扣掉，才是去偏后的真趋势。")


# ========== CLI ==========

def main():
    args = [a for a in sys.argv[1:]]
    here = Path(__file__).resolve().parent
    flags = {f for f in ("--diagnose", "--recommend", "--calibrate") if f in args}
    for f in flags:
        args.remove(f)
    scenario = None
    if "--scenario" in args:
        i = args.index("--scenario")
        scenario = args[i + 1] if i + 1 < len(args) else None
        del args[i:i + 2]
    path = Path(args[0]) if args else here / "decisions.jsonl"

    ran = False
    if "--calibrate" in flags:
        print_calibrate(here)
        ran = True
    if flags & {"--diagnose", "--recommend"}:
        anchors, _ = load(path, scenario)
        if "--diagnose" in flags:
            print_diagnose(anchors)
        if "--recommend" in flags:
            print_recommend(anchors, here)
        ran = True
    if ran:
        return

    # 默认：完整复盘
    anchors, summaries = load(path, scenario)
    real_name = "real_decisions.example.jsonl" if path.name.endswith(".example.jsonl") else "real_decisions.jsonl"
    real_recs = load_real(path.with_name(real_name))
    report_improvement(anchors, real_recs)   # 头条先打
    report(anchors, summaries)
    report_real(real_recs)


if __name__ == "__main__":
    main()
