---
schema: scenario-blind/v1
meta:
  id: liubei-yiling
  title: 夷陵之战
  region: 三国·蜀吴边境（夷陵/猇亭）
  protagonist: 刘备
  goal: 复兴汉室——注意，是这个，不是别的。
  tier: 精推
  decision_types: ['情绪/复仇下的目标对齐', '深入敌境的部署风险', '沉没成本下的止损']
  trains_dims: ['目标对齐', '风险定价', '盲点意识', '反证强度']
  source_anchor: '《三国志·先主传/赵云传/陆逊传/张飞传》，裴注；曹丕评连营见《文帝纪》'
  persona_warning: '用你自己的判断，别演"重情重义的刘皇叔"。你此刻是个刚登基、又刚失去结义兄弟、被悲愤和威望同时架着的人。'
  focus_note: '本场专练目标对齐：当复仇情绪、皇帝面子、哀兵士气一起推着你，你还守得住"真实战略目标"吗？'
anchors:
  - id: 1
    title: 伐不伐吴
    situation: '孙吴袭杀关羽、夺了荆州。你刚称帝，群臣为"打不打吴"吵翻了。'
    info_boundary:
      known:
        - '孙吴袭杀关羽、夺了荆州，是直接凶手。你刚称帝，需要立威。'
        - '赵云等力谏：国贼是曹魏不是孙吴，应先图关中、北伐曹魏，不该为私仇伐盟友、两线树敌。'
        - '另一派顺着你的悲愤主战。'
      unknown:
        - '伐吴能否速胜。'
        - '曹魏会不会趁你东征抄你后路。'
        - '孙吴的真实抵抗强度与统帅是谁。'
      believed_false:
        - '"哀兵必胜 + 我的威望，足以碾过东吴"。'
    traps: []
    is_real_turning_point: true
    decision_prompt: '举国伐吴，还是咽下这口气、按战略先对付曹魏？给：① 决定　② 最强反方（替你没选的那方说最硬的话）　③ 证伪条件。'
    gold_score: null
  - id: 2
    title: 一封讣告
    situation: '大军将发，后方传来噩耗。'
    info_boundary:
      known:
        - '三弟张飞临行前被帐下部将张达、范彊所杀，二人持其首级顺流投奔了孙吴。'
        - '又一个结义兄弟没了，凶手也入了吴。军中悲愤更盛。'
      unknown:
        - '这件事会不会动摇军心或将领忠诚。'
        - '它对你东征的胜算到底有没有实质影响。'
      believed_false:
        - '"连三弟也死在通往孙吴的路上——这更证明我非伐吴不可"。'
    traps:
      - '看着重要、其实不重要：又一桩血仇，但它是情绪燃料，不改变"你真实敌人是谁"的战略算式——让它进一步劫持目标才是陷阱。'
    is_real_turning_point: false
    decision_prompt: '张飞之死、凶手投吴。这件事该不该改变、或如何改变你的决策？（你也可以判断它根本不该改变什么——但要说清为什么。）'
    gold_score: null
  - id: 3
    title: 扎营
    situation: '大军已深入吴境数百里。正值盛夏酷暑。'
    info_boundary:
      known:
        - '正值盛夏酷暑，水军舍舟转陆，你沿途依山傍林、结连营数百里驻扎避暑。'
        - '吴军统帅是年轻的陆逊，避战坚守、不与你决战。'
      unknown:
        - '陆逊为何死守不战（是怯，还是在等什么）。'
        - '林地连营在夏季意味着什么风险。'
        - '你的补给线拉多长了。'
      believed_false:
        - '"对方不敢战 = 我占上风"。'
    traps: []
    is_real_turning_point: true
    decision_prompt: '陆逊不出来打，你大军就这样依山林连营相持，对不对？要不要调整部署？① 决定　② 最强反方　③ 证伪条件。'
    gold_score: null
  - id: 4
    title: 顿兵
    situation: '相持已数月，速胜的指望落空。'
    info_boundary:
      known:
        - '士气与锐气在消磨，补给越拉越长。继续耗，还是另寻打法。'
      unknown:
        - '陆逊会不会、何时会反击。'
        - '你已经投入这么多，撤退会不会前功尽弃、有损帝威。'
      believed_false:
        - '"已经打到这儿了，撤了就白来、丢脸"。'
    traps: []
    is_real_turning_point: true
    decision_prompt: '继续顿兵相持，还是及时收手/变阵？① 决定　② 最强反方　③ 证伪条件。'
    gold_score: null
---

# 夷陵之战 · 盲区（engine 读 frontmatter；本文件不含任何史实结局）

> 供「情境官」使用，只描述当事人此刻能感知的信息。史实/出处/致死/对照体/可迁移原则全在 `yiling.sealed.md`。
> `is_real_turning_point` 是隐藏元数据，情境官不得向用户透露哪个锚点是不是转折点。
