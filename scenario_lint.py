#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
史鉴推演 · 场景校验器（确定性闸门，"程序可检"的那道地基）

把每个场景拆成 blind / sealed 两文件，用机器强制：
  1) 维度词表不漂移   —— trains_dims ⊆ 全系统唯一的 DIMS（直接 import 自 stats.py）
  2) 盲/封不泄题       —— blind 文件里不许出现答案字段（史实选择/出处/致死/可迁移原则…）
  3) 出处不缺失        —— 每条 ground_truth 必带 citations，confidence ∈ {high,med,low,unknown}
  4) 诱饵必在          —— 至少一个锚点 is_real_turning_point: false（对抗"每刻皆史诗"选题偏差）
  5) 结构一致          —— 字段齐全、锚点连续、blind 与 sealed 锚点 1:1 对齐
  6) v2 资源盘合规     —— scenario-blind/v2 须有 assets 六类齐全、人和逐人字段齐全（谋主沙盘模式地基）；
                          blind v2 必须配 sealed v2（execution_friction 才有处可封）

过不了这道闸，场景就进不了 library。新增 100 个场景也因此结构一致、可被调度器调用。

用法：
  python scenario_lint.py                 # 扫 library/ 下所有 *.blind.md
  python scenario_lint.py 路径/某.blind.md  # 只查一个
退出码：全过=0，任一 FAIL=1（可挂 CI / pre-commit）。
"""
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("需要 PyYAML：pip install pyyaml", file=sys.stderr)
    sys.exit(2)

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

# —— 维度词表单一来源：直接借 stats.py 的 DIMS。两处共用一份定义 = 机制上防漂移 ——
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from stats import DIMS as CANON_DIMS
except Exception:
    CANON_DIMS = ["信息利用", "风险定价", "反证强度", "目标对齐", "盲点意识"]

TIERS = {"快推", "精推"}
CONF_OK = {"high", "med", "low", "unknown"}
# blind 文件里一旦出现这些 token，说明答案泄进了盲区
SEALED_TOKENS = [
    "actual_choice", "actual_outcome", "ground_truth", "citations",
    "transferable_principle", "counterfactual_model", "lethal",
    "fiction_vs_fact", "council", "史实选择", "可迁移原则", "致死",
    "execution_friction",
]

BLIND_SCHEMAS = {"scenario-blind/v1", "scenario-blind/v2"}
SEALED_SCHEMAS = {"scenario-sealed/v1", "scenario-sealed/v2"}
# v2 资源盘：六类资源 + 人和逐人属性（"人不会丝滑执行意图"的结构化载体）
ASSET_KEYS = ["天时", "地利", "兵粮", "利益网", "掣肘", "人和"]
PERSON_KEYS = ["名", "角色", "能力", "你以为的忠诚", "私利", "掣肘", "反噬信号"]


def parse_frontmatter(path: Path):
    """取 --- 包裹的 YAML 头。返回 (data, 原始frontmatter文本, err)。"""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "", "缺少 YAML frontmatter（文件未以 --- 开头）"
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return None, "", "frontmatter 未闭合（缺第二个 ---）"
    raw = "\n".join(lines[1:end])
    try:
        return yaml.safe_load(raw), raw, None
    except yaml.YAMLError as e:
        return None, raw, f"YAML 解析失败：{e}"


def check_blind(path: Path, errs: list):
    data, raw, err = parse_frontmatter(path)
    if err:
        errs.append(err)
        return None
    if not isinstance(data, dict):
        errs.append("frontmatter 不是映射结构")
        return None

    schema = data.get("schema")
    if schema not in BLIND_SCHEMAS:
        errs.append(f"schema 应 ∈ {sorted(BLIND_SCHEMAS)}，实为 {schema!r}")
    is_v2 = schema == "scenario-blind/v2"

    # —— v2 资源盘闸门：六类齐全，人和逐人字段齐全 ——
    if is_v2:
        assets = data.get("assets")
        if not isinstance(assets, dict):
            errs.append("v2 须有顶层 assets（资源盘），且为映射结构")
        else:
            for k in ASSET_KEYS:
                v = assets.get(k)
                if not isinstance(v, list) or not v:
                    errs.append(f"assets.{k} 缺失或非非空列表")
            for i, p in enumerate(assets.get("人和") or [], 1):
                if not isinstance(p, dict):
                    errs.append(f"assets.人和[{i}] 不是映射结构")
                    continue
                missing = [k for k in PERSON_KEYS if not p.get(k)]
                if missing:
                    errs.append(f"assets.人和[{i}]（{p.get('名', '?')}）缺字段：{missing}")
    elif data.get("assets") is not None:
        errs.append("v1 不应有 assets；要用资源盘请升 schema 到 scenario-blind/v2")

    meta = data.get("meta") or {}
    for k in ("id", "title", "protagonist", "goal", "tier", "trains_dims", "source_anchor"):
        if not meta.get(k):
            errs.append(f"meta 缺字段：{k}")

    if meta.get("tier") not in TIERS:
        errs.append(f"meta.tier 应 ∈ {TIERS}，实为 {meta.get('tier')!r}")

    # —— 词表闸门：调度器靠 trains_dims 匹配弱项，名字必须逐字命中 canonical ——
    td = meta.get("trains_dims") or []
    if not td:
        errs.append("meta.trains_dims 不能为空（否则调度器无法据弱项调用本场景）")
    bad = [d for d in td if d not in CANON_DIMS]
    if bad:
        errs.append(f"trains_dims 含非 canonical 维度 {bad}；只允许 {CANON_DIMS}（防词表漂移）")

    anchors = data.get("anchors") or []
    if not anchors:
        errs.append("anchors 为空")
    ids = []
    has_decoy = False
    for a in anchors:
        aid = a.get("id")
        ids.append(aid)
        tag = f"锚{aid}"
        if not a.get("situation"):
            errs.append(f"{tag} 缺 situation")
        ib = a.get("info_boundary") or {}
        for seg in ("known", "unknown", "believed_false"):
            if not isinstance(ib.get(seg), list) or not ib.get(seg):
                errs.append(f"{tag} info_boundary.{seg} 缺失或非列表")
        if not isinstance(a.get("is_real_turning_point"), bool):
            errs.append(f"{tag} is_real_turning_point 必须是布尔")
        elif a["is_real_turning_point"] is False:
            has_decoy = True
        if not a.get("decision_prompt"):
            errs.append(f"{tag} 缺 decision_prompt")
        gs = a.get("gold_score", None)
        if gs is not None and not isinstance(gs, (int, float)):
            errs.append(f"{tag} gold_score 须为数字或 null（校准钩子）")

    if ids and ids != list(range(1, len(ids) + 1)):
        errs.append(f"锚点 id 必须从 1 连续：实为 {ids}")
    if not has_decoy:
        errs.append("至少需 1 个诱饵锚点（is_real_turning_point: false），否则养成『每刻皆史诗』错觉")

    # —— 泄题闸门：盲区里不许出现答案 token ——
    low = raw.lower()
    leaked = [t for t in SEALED_TOKENS if t.lower() in low]
    if leaked:
        errs.append(f"blind 文件疑似泄题，出现封存字段/词：{leaked}")

    return {"id": meta.get("id"), "anchor_ids": ids, "is_v2": is_v2}


def check_sealed(path: Path, blind_info, errs: list):
    data, _, err = parse_frontmatter(path)
    if err:
        errs.append(err)
        return
    if not isinstance(data, dict):
        errs.append("sealed frontmatter 不是映射结构")
        return

    schema = data.get("schema")
    if schema not in SEALED_SCHEMAS:
        errs.append(f"sealed.schema 应 ∈ {sorted(SEALED_SCHEMAS)}，实为 {schema!r}")
    if blind_info and blind_info.get("is_v2") and schema != "scenario-sealed/v2":
        errs.append("blind 是 v2（带资源盘），sealed 必须同升 scenario-sealed/v2（封 execution_friction）")

    if blind_info and data.get("scenario_id") != blind_info["id"]:
        errs.append(f"scenario_id({data.get('scenario_id')!r}) 与 blind.meta.id({blind_info['id']!r}) 不一致")

    gt = data.get("ground_truth") or []
    gt_ids = [g.get("anchor_id") for g in gt]
    if blind_info and sorted(gt_ids) != sorted(blind_info["anchor_ids"]):
        errs.append(f"ground_truth 锚点 {gt_ids} 与 blind 锚点 {blind_info['anchor_ids']} 未 1:1 对齐")

    if schema == "scenario-sealed/v2":
        with_friction = [g for g in gt if g.get("execution_friction")]
        if not with_friction:
            errs.append("sealed v2 须至少一个锚点带 execution_friction（否则资源盘没有对账面）")

    for g in gt:
        tag = f"史实锚{g.get('anchor_id')}"
        for k in ("actual_choice", "actual_outcome", "transferable_principle"):
            if not g.get(k):
                errs.append(f"{tag} 缺 {k}")
        cites = g.get("citations") or []
        if not cites:
            errs.append(f"{tag} 无 citations —— 无出处的史实=编造，禁止")
        for c in cites:
            if not c.get("source"):
                errs.append(f"{tag} 某 citation 缺 source")
            if c.get("confidence") not in CONF_OK:
                errs.append(f"{tag} citation.confidence 应 ∈ {CONF_OK}，实为 {c.get('confidence')!r}")


def lint_one(blind_path: Path) -> bool:
    sealed_path = blind_path.with_name(blind_path.name.replace(".blind.md", ".sealed.md"))
    errs = []
    blind_info = check_blind(blind_path, errs)
    if not sealed_path.exists():
        errs.append(f"缺少配套封存文件：{sealed_path.name}")
    else:
        check_sealed(sealed_path, blind_info, errs)

    name = blind_path.name.replace(".blind.md", "")
    if errs:
        print(f"✗ FAIL  {name}")
        for e in errs:
            print(f"        - {e}")
        return False
    print(f"✓ PASS  {name}  (锚点 {len(blind_info['anchor_ids'])}，词表/盲封/出处/诱饵 全过)")
    return True


def main():
    args = sys.argv[1:]
    here = Path(__file__).resolve().parent
    if args:
        targets = [Path(args[0])]
    else:
        targets = sorted((here / "library").rglob("*.blind.md"))
    if not targets:
        print("未找到任何 *.blind.md。先把场景按 schema 拆成 blind/sealed 两文件。")
        sys.exit(0)
    print(f"canonical 维度（单一来源 stats.DIMS）：{CANON_DIMS}")
    print("=" * 56)
    ok = all(lint_one(p) for p in targets)
    print("=" * 56)
    print("全部通过 ✅" if ok else "存在未通过场景 ❌（进不了 library）")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
