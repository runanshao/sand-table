---
schema: scenario-blind/v1
meta:
  id: caocao-guandu
  title: 官渡之战
  region: 东汉末·中原
  protagonist: 曹操
  goal: 在实力悬殊下不被袁绍吞掉，保住中原根基
  tier: 精推
  decision_types: ['资源耗尽下的去留', '可疑情报的取舍', '高风险奇袭', '压力下的集中']
  trains_dims: ['风险定价', '反证强度', '目标对齐', '盲点意识']
  source_anchor: '《三国志·武帝纪》《荀彧传》《荀攸传》，裴注引《曹瞒传》'
  persona_warning: '用你自己的判断，别演"奸雄曹操"。你只是一个兵少粮缺、背后还有许都要守的人。'
  fiction_warning: '你脑中的官渡可能来自《三国演义》。一律以《三国志》对账，演义虚构处揭示时标红——识别"你被小说带偏了没"本身是一道判断课。'
anchors:
  - id: 1
    title: 相持
    situation: '粮快没了，后方不稳。你和袁绍在官渡已对垒数月。'
    info_boundary:
      known:
        - '你兵力远少于袁绍（你约数万，袁绍号十余万）。'
        - '两军在官渡对垒已数月，你军粮将尽，士卒疲乏。'
        - '后方许都人心浮动，已有人暗通袁绍。'
      unknown:
        - '袁绍营中此刻在争什么。'
        - '这场相持还要多久。'
        - '你的粮还能撑几天的精确数字。'
      believed_false:
        - '"再拖下去先垮的一定是我"——也许袁绍那边也撑得难受。'
    traps: []
    is_real_turning_point: true
    decision_prompt: '你是退守许都（缩短补给、保存实力），还是继续顶在官渡？给出选择和理由。'
    gold_score: null
  - id: 2
    title: 一封请战书
    situation: '相持期间，军中对"要不要主动出击"起了争论。'
    info_boundary:
      known:
        - '部将中有人主张趁夜劫袁绍前营某部，说"挫其锐气、振我军心"。'
        - '也有人说粮草要紧、不宜浪战。'
      unknown:
        - '袁绍各营的虚实布防。'
        - '这一击就算赢，能不能改变大局。'
      believed_false:
        - '"打一仗就能扭转士气"——士气问题的根子是粮和前景，未必靠一场小胜解决。'
    traps:
      - '看着重要、其实不重要：劫营小胜不改变补给与全局，押注于此才是风险。'
    is_real_turning_point: false
    decision_prompt: '你准不准这次主动劫营？'
    gold_score: null
  - id: 3
    title: 叛将夜投
    situation: '深夜，对面阵营一名谋士突然来投，献上一条赌身家的计策。'
    info_boundary:
      known:
        - '袁绍帐下谋士许攸突然来投，称因家人在邺城犯法被审治，一怒离袁。'
        - '他献计：袁绍全部军粮屯于乌巢，守备不算森严，若轻兵奇袭烧之，袁军不战自乱。'
        - '他说得出乌巢的位置和守将。'
      unknown:
        - '许攸说的是真是假。'
        - '这会不会是袁绍设的诱敌之计（你冲出去袭乌巢，主力被埋伏，许都再被端）。'
        - '乌巢真实守备到底多强。'
      believed_false:
        - '"刚叛变来的人不可信"——但也可能正因为他刚从对面来，才掌握你最需要的情报。'
    traps: []
    is_real_turning_point: true
    decision_prompt: '一个一刻钟前还是敌人的叛将，献上赌身家的计策。你信，还是不信？信的话怎么验、怎么下注？'
    gold_score: null
  - id: 4
    title: 背后火起
    situation: '你已轻兵抵近乌巢，正要纵火强攻，背后却传来动静。'
    info_boundary:
      known:
        - '哨马来报：袁绍已发觉，分兵来救，一支救兵正扑向你背后。'
        - '与此同时，你留守的大营也可能正被袁绍主力猛攻。'
        - '部将请求：分一半人回头挡住救兵。'
      unknown:
        - '大营到底撑不撑得住。'
        - '救兵到底多少、多快。'
        - '你正面这把火能不能一鼓拿下。'
      believed_false:
        - '"两头都得顾"——分兵看似稳妥，实则可能两头都不够。'
    traps: []
    is_real_turning_point: true
    decision_prompt: '腹背受敌。你分兵回挡救兵，还是集中全力先破乌巢？'
    gold_score: null
---

# 官渡之战 · 盲区（engine 读 frontmatter；本文件不含任何史实结局）

> 本文件供「情境官」使用，**只描述当事人此刻能感知的信息**。
> 史实选择、实际结果、出处、致死概率、可迁移原则——全在配套的 `guandu.sealed.md`，
> 由「史官/裁判」在**评分落盘之后**才读取。两文件物理分离即写序墙的物理化。
>
> `is_real_turning_point` 是给评分/校验用的隐藏元数据，**情境官不得向用户透露**哪个锚点是不是转折点。
