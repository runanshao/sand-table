# 史鉴推演 · sand-table

> 沙盘：将帅在上面推演生死的那张桌子。代入历史、推演决策、对账判断。

> 一个把你代入真实历史决策点、用**史实对账**来训练**现实决断力**的 Claude Code / Amp 技能。
> A Claude Code skill that drops you into real historical decision points, role-plays the figure, then **reckons your judgment against what actually happened** — to train real-world decisiveness.

## 核心卖点：判断力的持续改善闭环（不是历史故事的数量）
价值**不在场景多广**——场景只是燃料。卖点是：**每一次互动都闭成一个数据点，汇进一条随时间的判断力曲线，让你的判断力可见地持续变好。**
- 头条指标永远是"你在持续变好吗"：判断质量趋势（早半段 vs 近半段）、最弱维是否被攻克、课程毕业进度、现实决策入环胜率。
- 燃料不限历史局：**历史推演 + 现实决策 + 任何一次快速判断**，同一套五维、同一条曲线。
- 每次互动**强制闭环**：入数据 + 给一句"本次后最弱维/趋势"回执，绝不空转。

**核心不是"扮演历史"，是"对账判断"。** 历史唯一不可替代的价值：**结局已知 = 自带标准答案 = 真实反馈回路**。你做决策、写理由，AI 在揭示史实前先打分，再让你看：你撑到第几步、**本该死在第几步**、是判断对还是运气好。

---

## 为什么它和别的"历史游戏"不一样（设计哲学 = 卖点）

1. **对账，不是沉浸**。沉浸是手段，跟史实对账才是目的。
2. **判断 ≠ 结果**。评分只看"决策时刻的推理质量"，与你是否复刻历史、这局是死是活**无关**。项羽乌江自刎，未必每步判断都比刘邦差——他只是输了那一把。
3. **生存是皮，不是尺**。"撑了几关/何时死"是动机层；计分永远只看判断质量。终局摆出 **「实际撑到第几锚」 vs 「本该死在第几锚」**，当场拆穿是判断好还是运气吊着。
4. **反马屁裁判**。AI 是会编造历史、会拍马屁的裁判——所以有诚实护栏：史实附**出处+置信度**、不确定就明说、**鼓励你当场质疑裁判**（抓裁判的错本身就是判断训练）。
5. **样本量诚实**。n<5 一律只算"观察"，绝不拿噪音当规律。
6. **必须迁移到现实**。每局末尾**强制**把学到的可迁移原则用到你眼下一个真实决策上（对接 `hu-deduction`）。历史局只是热身——不上真实重量，等于白练。

> 借鉴：掌握清单 / 先复述再决策 / 三层理解（萃取可迁移原则），思路来自 [Thariq S 的教学框架 gist](https://gist.github.com/ThariqS/1389dcdff9eba4789887a2211370f06b)。

---

## 安装

```bash
git clone <this-repo> ~/.claude/skills/史鉴推演
# 物理隔离墙（已结构化场景的史实揭示）依赖 historian 子 agent。
# Claude Code 只从 ~/.claude/agents/ 发现 agent，故把随库发布的那份装过去
#（库内 agents/historian.md 是 source-of-truth）：
cp ~/.claude/skills/史鉴推演/agents/historian.md ~/.claude/agents/historian.md
```
Windows PowerShell：
```powershell
git clone <this-repo> $HOME\.claude\skills\史鉴推演
Copy-Item $HOME\.claude\skills\史鉴推演\agents\historian.md $HOME\.claude\agents\historian.md
```
重启 Claude Code 后，对它说 `史鉴推演 官渡` 或 `把我放进于谦的北京保卫战`。

> **没装 historian 也能玩**：未结构化的旧场景走纪律墙；但已结构化场景（官渡/夷陵）的精推揭示需要它，否则物理墙断成半截。
>
> 需要 Python 3.8+。`stats.py` / `render.py` 纯标准库、零依赖；`scenario_lint.py`（新增场景时校验）需 PyYAML：`pip install pyyaml`。

---

## 怎么玩（一局示例）

```
你：史鉴推演 官渡，精推
AI：[信息边界卡] 你是曹操，建安五年，粮将尽…… 你怎么读这个局？
你：（先复述）+ 决策 + 可证伪理由
AI：[揭示前打分·五维] → [揭示三线：史实/实际结果/对照体]
    → [致死概率估计] → [萃取一条可迁移原则]
…… 终局：[本该死 vs 实际死 对账] → [现实决策桥：把这条原则用到你真实的某个决断上]
```
跑完一局：
- `python stats.py` —— 终端版复盘（判断质量轨迹、最弱维、证伪缺失率、本该死/实际死）。
- `python render.py` —— 生成离线可视化报告 `report.html`（五维雷达 / 轨迹 / 死亡对账 / 盲点清单；零依赖内联 SVG，可截图）。浏览器打开即看。

---

## 目录

```
史鉴推演/
  SKILL.md                 引擎：流程 + 铁规 + 三角色 + 现实决策桥
  references/
    scenario-format.md     拆题格式（信息边界/诱饵/致死条件/可迁移原则/可核出处）
    scoring-rubric.md       五维评分 + 致死概率 + 死亡对账
    adjudication.md         反事实裁定（因果+基率+置信度+何时致死）
  library/
    CATALOG.md             选题菜单（按朝代：商/周/春秋战国/秦汉/三国/隋唐/宋/明/清 + 国外）
    caocao/guandu.blind.md   场景·盲区：官渡之战（情境官只读这个）
    caocao/guandu.sealed.md  场景·封存：官渡史实/出处/致死/对照体（historian 子 agent 读）
    sanguo/yiling.blind.md   场景·盲区：夷陵之战（情境官只读这个）
    sanguo/yiling.sealed.md  场景·封存：夷陵史实/出处/致死/对照体（historian 子 agent 读）
    ming/yuqian-beijing.md  场景：于谦·北京保卫战（《明史》）
    intl/cuban-missile-crisis.md  场景：古巴导弹危机（ExComm 记录）
  stats.py                 确定性复盘（终端，无三方依赖）
  render.py                可视化复盘 → report.html（离线内联 SVG，无三方依赖）
  scenario_lint.py         场景校验器（blind/sealed schema 闸门 · 需 PyYAML）
  agents/
    historian.md           史官子 agent（物理墙·读 sealed 揭示）→ 安装时复制到 ~/.claude/agents/
  mastery.example.md       判断力掌握清单（课程表）模板
  profile.example.md       判断力档案模板
  decisions.example.jsonl  决策日志样例
  docs/DESIGN.md           设计 + 盲点修复记录
```
> 个人数据（`decisions.jsonl` / `profile.md` / `mastery.md`）已 `.gitignore`，不会被提交。

---

## 自己加场景

照 `references/scenario-format.md`：每个锚点要有信息边界卡、史实出处+置信度、≥1 诱饵、致死条件、可迁移原则、"揭示前不可见"分隔。**只用公共史实原创合成，演义只能当选题/氛围并标红——不要粘贴受版权保护的原文。**

---

## 现状与路线

**v0.x · 实验性**。当前 4 个场景（官渡、夷陵、于谦、古巴导弹危机）+ [选题菜单](library/CATALOG.md)（覆盖商/周/春秋战国/秦汉/三国/隋唐/宋/明/清 + 国外，二十余候选，按需建），单人自用为主。
- 路线：从菜单持续建场景（只建史料扎实的）· 判断原理库 · 难度分级 · 间隔重复调度 · （可选）Agent SDK 独立版。
- 诚实提醒：判断力能否真迁移到现实，取决于"现实决策桥"有没有被真正用起来。历史局只是健身房。

## 许可

代码（`stats.py`）MIT。场景内容为公共史实的原创合成，请勿提交受版权保护的改编作品原文。
