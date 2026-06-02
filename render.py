#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
史鉴推演 · 可视化复盘报告（离线 HTML，纯标准库，零第三方依赖）

读 decisions.jsonl，生成一个自包含的 report.html：五维雷达 / 判断质量轨迹 /
关键指标 / 本该死vs实际死 / 盲点清单。所有图为内联 SVG，离线可看、可截图。

设计铁规：图越漂亮越要把诚实写在脸上——顶部横幅显著标 N 与"观察/候选规律"，
并声明"这些是 AI 判断、会抖动、不可复现，不是测量"。别给噪音穿西装。

用法：
  python render.py                  # 读同目录 decisions.jsonl → report.html
  python render.py 日志路径 报告路径
然后浏览器打开 report.html（Windows: start report.html）。
"""
import html
import math
import sys
from pathlib import Path

# 复用 stats.py 的读取与常量（同目录）
sys.path.insert(0, str(Path(__file__).resolve().parent))
from stats import load, load_real, DIMS, RULE_N, missing_falsifier  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

DIM_SHORT = {"信息利用": "信息", "风险定价": "风险", "反证强度": "反证",
             "目标对齐": "目标", "盲点意识": "盲点"}


def esc(s):
    return html.escape(str(s))


def radar_svg(dim_avg, size=360, maxval=2.0):
    cx = cy = size / 2
    R = size * 0.34
    dims = [d for d in DIMS if d in dim_avg]
    n = len(dims)
    if n < 3:
        return "<p>数据不足以画雷达（需≥3维）。</p>"
    weakest = min(dims, key=lambda d: dim_avg[d])

    def pt(i, r):
        ang = -math.pi / 2 + i * 2 * math.pi / n
        return cx + r * math.cos(ang), cy + r * math.sin(ang)

    out = [f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}">']
    # 网格环
    for lvl in (0.5, 1.0, 1.5, 2.0):
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, R * lvl / maxval) for i in range(n)))
        out.append(f'<polygon points="{pts}" fill="none" stroke="#2b3550" stroke-width="1"/>')
    # 轴线 + 标签
    for i, d in enumerate(dims):
        x, y = pt(i, R)
        out.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#2b3550" stroke-width="1"/>')
        lx, ly = pt(i, R + 22)
        color = "#ff6b6b" if d == weakest else "#9fb0d0"
        anchor = "middle"
        if lx < cx - 5:
            anchor = "end"
        elif lx > cx + 5:
            anchor = "start"
        out.append(f'<text x="{lx:.1f}" y="{ly:.1f}" fill="{color}" font-size="13" '
                   f'text-anchor="{anchor}" dominant-baseline="middle">{esc(DIM_SHORT.get(d, d))} {dim_avg[d]:.2f}</text>')
    # 数据多边形
    data = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, R * dim_avg[d] / maxval) for i, d in enumerate(dims)))
    out.append(f'<polygon points="{data}" fill="rgba(108,166,255,0.28)" stroke="#6ca6ff" stroke-width="2"/>')
    for i, d in enumerate(dims):
        x, y = pt(i, R * dim_avg[d] / maxval)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#6ca6ff"/>')
    out.append("</svg>")
    return "".join(out)


def trajectory_svg(anchors, w=560, h=300):
    recs = [a for a in anchors if isinstance(a.get("总分"), (int, float))]
    if not recs:
        return "<p>暂无总分数据。</p>"
    recs = sorted(recs, key=lambda r: (r.get("场景", ""), r.get("锚点", 0)))
    pad_l, pad_b, pad_t, pad_r = 38, 46, 20, 16
    iw, ih = w - pad_l - pad_r, h - pad_b - pad_t
    n = len(recs)

    def X(i):
        return pad_l + (iw * i / max(1, n - 1))

    def Y(v):
        return pad_t + ih * (1 - v / 10.0)

    out = [f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}">']
    for gv in (0, 2, 4, 6, 8, 10):
        y = Y(gv)
        out.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w-pad_r}" y2="{y:.1f}" stroke="#222c44" stroke-width="1"/>')
        out.append(f'<text x="{pad_l-8}" y="{y+4:.1f}" fill="#6b7794" font-size="11" text-anchor="end">{gv}</text>')
    line = " ".join(f"{X(i):.1f},{Y(r['总分']):.1f}" for i, r in enumerate(recs))
    out.append(f'<polyline points="{line}" fill="none" stroke="#6ca6ff" stroke-width="2.5"/>')
    last_scene = None
    for i, r in enumerate(recs):
        x, y = X(i), Y(r["总分"])
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#6ca6ff"/>')
        out.append(f'<text x="{x:.1f}" y="{y-10:.1f}" fill="#cdd7ee" font-size="11" text-anchor="middle">{r["总分"]}</text>')
        scene = r.get("场景", "")
        if scene != last_scene:
            out.append(f'<text x="{x:.1f}" y="{h-16}" fill="#8a96b5" font-size="11" text-anchor="middle">{esc(scene)}</text>')
            if last_scene is not None:
                out.append(f'<line x1="{x-2:.1f}" y1="{pad_t}" x2="{x-2:.1f}" y2="{h-pad_b}" stroke="#39456a" stroke-dasharray="3 3"/>')
            last_scene = scene
    out.append(f'<text x="{pad_l}" y="14" fill="#6b7794" font-size="11">判断质量 / 10（按锚点顺序）</text>')
    out.append("</svg>")
    return "".join(out)


def gauge_html(label, pct, danger_above=50):
    color = "#ff6b6b" if pct >= danger_above else "#6ca6ff"
    return (f'<div class="gauge"><div class="gbar"><div class="gfill" style="width:{pct:.0f}%;background:{color}"></div></div>'
            f'<div class="glab">{esc(label)} <b style="color:{color}">{pct:.0f}%</b></div></div>')


def build(anchors, summaries, real_recs=None):
    real_recs = real_recs or []
    n = len(anchors)
    scenes = sorted({a.get("场景", "?") for a in anchors})
    # 五维均分
    dim_avg = {}
    for d in DIMS:
        vals = [a["五维"][d] for a in anchors if isinstance(a.get("五维", {}).get(d), (int, float))]
        if vals:
            dim_avg[d] = sum(vals) / len(vals)
    scores = [a["总分"] for a in anchors if isinstance(a.get("总分"), (int, float))]
    avg = sum(scores) / len(scores) if scores else 0
    weakest = min(dim_avg, key=dim_avg.get) if dim_avg else "—"
    miss = sum(1 for a in anchors if missing_falsifier(a))
    miss_pct = miss / n * 100 if n else 0
    rule_state = "候选规律（仍需更多场景验证）" if n >= RULE_N else "观察（样本不足，不构成规律）"

    # 盲点标签
    tags = []
    for a in anchors:
        for t in a.get("盲点标签", []) or []:
            tags.append((a.get("场景", "?"), a.get("锚点", "?"), t))

    # 死亡对账
    death_rows = []
    for s in summaries:
        if "本该死锚点" in s or "本该死" in s:
            should = s.get("本该死锚点", s.get("本该死", "?"))
            actual = s.get("实际死锚点", s.get("实际死", "?"))
            death_rows.append((s.get("场景", "?"), should, actual))

    css = """
    *{box-sizing:border-box} body{margin:0;background:#0d1322;color:#cdd7ee;
      font-family:-apple-system,'Segoe UI','Microsoft YaHei',sans-serif;line-height:1.5}
    .wrap{max-width:920px;margin:0 auto;padding:28px 20px 60px}
    h1{font-size:22px;margin:0 0 4px} .sub{color:#7c89a8;font-size:13px;margin-bottom:18px}
    .banner{background:#241a1a;border:1px solid #5a3a3a;border-radius:10px;padding:12px 16px;margin-bottom:22px;font-size:13px;color:#e8b3b3}
    .grid{display:flex;flex-wrap:wrap;gap:18px}
    .card{background:#141c2f;border:1px solid #232f4a;border-radius:12px;padding:16px 18px;flex:1 1 300px}
    .card h2{font-size:14px;margin:0 0 10px;color:#9fb0d0;font-weight:600}
    .kpi{display:flex;gap:18px;flex-wrap:wrap}
    .kpi .b{font-size:26px;font-weight:700;color:#6ca6ff} .kpi .l{font-size:12px;color:#7c89a8}
    .weak{color:#ff6b6b!important}
    .gauge{margin-top:8px} .gbar{height:9px;background:#222c44;border-radius:6px;overflow:hidden}
    .gfill{height:100%} .glab{font-size:12px;color:#9fb0d0;margin-top:4px}
    ul{margin:6px 0 0;padding-left:18px} li{font-size:12.5px;color:#aeb9d6;margin:3px 0}
    table{width:100%;border-collapse:collapse;font-size:12.5px} td,th{padding:5px 6px;text-align:left;border-bottom:1px solid #222c44}
    .note{color:#ff9e6b}
    """
    H = []
    H.append(f"<!doctype html><html lang='zh'><head><meta charset='utf-8'>")
    H.append(f"<meta name='viewport' content='width=device-width,initial-scale=1'>")
    H.append(f"<title>史鉴推演 · 判断力复盘</title><style>{css}</style></head><body><div class='wrap'>")
    H.append("<h1>史鉴推演 · 判断力复盘</h1>")
    H.append(f"<div class='sub'>场景：{esc('、'.join(scenes))} ｜ 锚点数 N={n}</div>")
    # 诚实横幅
    H.append(f"<div class='banner'>⚠️ 诚实声明：图中的五维分、致死概率是 <b>AI 的判断，会抖动、不可复现，不是测量</b>。"
             f"当前 N={n}，结论级别：<b>{esc(rule_state)}</b>。图越漂亮，越要记得这点。</div>")

    # 头条：判断力持续改善（卖点）
    sc = sorted([a for a in anchors if isinstance(a.get("总分"), (int, float))],
                key=lambda r: (str(r.get("ts", "")), str(r.get("场景", "")), r.get("锚点", 0)))
    pend = sum(1 for r in real_recs if r.get("status") == "pending")
    res = sum(1 for r in real_recs if r.get("status") == "resolved")
    if len(sc) >= 4:
        half = len(sc) // 2
        early = sum(r["总分"] for r in sc[:half]) / half
        late = sum(r["总分"] for r in sc[half:]) / (len(sc) - half)
        delta = late - early
        col = "#5fd08a" if delta >= 0.5 else ("#ff6b6b" if delta <= -0.5 else "#9fb0d0")
        arrow = "↑ 持续改善" if delta >= 0.5 else ("↓ 退步" if delta <= -0.5 else "→ 持平")
        trend = (f"<span style='font-size:30px;font-weight:700;color:{col}'>{arrow} {delta:+.1f}</span>"
                 f"<div class='l'>早半段 {early:.1f} → 近半段 {late:.1f}（{esc(sc[0].get('ts','?'))}→{esc(sc[-1].get('ts','?'))}）</div>")
    else:
        trend = f"<span style='font-size:20px;color:#9fb0d0'>计分决策 {len(sc)} 个，还不够看趋势（需≥4）</span>"
    H.append("<div class='card' style='border-color:#2e4a6a;background:#0f1a2e'>"
             "<h2>判断力 · 持续改善（头条指标——这工具的卖点）</h2>"
             f"{trend}"
             f"<div class='l' style='margin-top:6px'>现实决策入环：待复盘 {pend} ｜ 已复盘 {res}（闭环在现实上的进度）</div></div>")

    H.append("<div class='grid'>")
    # 雷达
    H.append(f"<div class='card'><h2>五维形状（红轴=最弱，该练）</h2>{radar_svg(dim_avg)}</div>")
    # 轨迹
    H.append(f"<div class='card'><h2>判断质量轨迹</h2>{trajectory_svg(anchors)}</div>")
    H.append("</div>")

    H.append("<div class='grid' style='margin-top:18px'>")
    # 关键指标
    H.append("<div class='card'><h2>关键指标</h2><div class='kpi'>")
    H.append(f"<div><div class='b'>{avg:.1f}</div><div class='l'>全局均分/10</div></div>")
    H.append(f"<div><div class='b weak'>{esc(weakest)}</div><div class='l'>最弱维（定向主攻）</div></div>")
    H.append("</div>")
    H.append(gauge_html("证伪条件缺失率", miss_pct))
    H.append("</div>")
    # 死亡对账
    H.append("<div class='card'><h2>本该死 vs 实际死</h2>")
    if death_rows:
        H.append("<table><tr><th>场景</th><th>本该死@锚</th><th>实际死@锚</th><th>解读</th></tr>")
        for scene, should, actual in death_rows:
            note = ""
            if isinstance(should, (int, float)) and isinstance(actual, (int, float)):
                note = "运气吊着你" if actual > should else ("判断没错·输在运气" if actual < should else "判断=命运")
            H.append(f"<tr><td>{esc(scene)}</td><td>{esc(should)}</td><td>{esc(actual)}</td><td class='note'>{esc(note)}</td></tr>")
        H.append("</table>")
        H.append("<div class='l' style='margin-top:6px;color:#7c89a8'>记的是「本该死」——练判断，不练赌运气。</div>")
    else:
        H.append("<div class='l' style='color:#7c89a8'>暂无（推演走到高致死锚点后出现）。</div>")
    H.append("</div></div>")

    # 盲点清单
    H.append("<div class='card' style='margin-top:18px'><h2>盲点清单（语义聚类需人判断，不机械臆断）</h2><ul>")
    if tags:
        for scene, anc, t in tags:
            H.append(f"<li>[{esc(scene)}·锚{esc(anc)}] {esc(t)}</li>")
    else:
        H.append("<li>暂无。</li>")
    H.append("</ul></div>")

    # 现实决策台账（闭环在现实上——真考核）
    import datetime
    today = datetime.date.today().isoformat()
    pending = [r for r in real_recs if r.get("status") == "pending"]
    resolved = [r for r in real_recs if r.get("status") == "resolved"]
    H.append("<div class='card' style='margin-top:18px'><h2>现实决策台账（现实决断力的真考核）</h2>")
    if real_recs:
        H.append(f"<div class='l' style='color:#7c89a8;margin-bottom:6px'>待复盘 {len(pending)} ｜ 已复盘 {len(resolved)}</div>")
        H.append("<table><tr><th>日期</th><th>真实决策</th><th>选择</th><th>状态/复盘</th></tr>")
        for r in real_recs:
            st = r.get("status", "?")
            due = str(r.get("复盘日期", ""))
            flag = " ⏰到期" if st == "pending" and due and due <= today else ""
            badge = f"<span class='note'>{esc(st)}{flag}</span> {esc(due)}"
            H.append(f"<tr><td>{esc(r.get('ts','?'))}</td><td>{esc(r.get('决策','?'))}</td>"
                     f"<td>{esc(r.get('选择','?'))}</td><td>{badge}</td></tr>")
        H.append("</table>")
        H.append("<div class='l' style='margin-top:6px;color:#7c89a8'>历史局只是热身；这张表的胜率，才是这工具的最终成绩单。守『判断≠结果』。</div>")
    else:
        H.append("<div class='l' style='color:#7c89a8'>暂无。每局末把一个真实决策写进 real_decisions.jsonl，到期复盘真实结果。</div>")
    H.append("</div>")

    H.append("</div></body></html>")
    return "".join(H)


def main():
    args = sys.argv[1:]
    log = Path(args[0]) if args else Path(__file__).with_name("decisions.jsonl")
    out = Path(args[1]) if len(args) > 1 else Path(__file__).with_name("report.html")
    anchors, summaries = load(log)
    if not anchors:
        print("没有可视化的锚点记录。先去跑一局。", file=sys.stderr)
        sys.exit(1)
    real_name = "real_decisions.example.jsonl" if log.name.endswith(".example.jsonl") else "real_decisions.jsonl"
    real_recs = load_real(log.with_name(real_name))
    out.write_text(build(anchors, summaries, real_recs), encoding="utf-8")
    print(f"已生成：{out}")
    print("浏览器打开它（Windows: start report.html ｜ mac: open report.html）。")


if __name__ == "__main__":
    main()
