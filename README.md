# Kards-Simulator

基于 Python 的 [KARDS: The WWII Card Game](https://www.kards.com/) 模拟引擎，支持交互式对局和强化学习（RL）训练。

## 快速开始

### 安装

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### 启动 CLI

```powershell
python -m kards_sim
```

指定随机种子（方便复现同一局面）：

```powershell
python -m kards_sim --seed 42
```

### 运行测试

```powershell
pytest -v
```

## 游戏玩法

启动 CLI 后，游戏会打印当前棋盘状态，并等待你输入指令。输入 `help` 查看所有可用命令：

| 命令 | 缩写 | 格式 | 说明 |
|------|------|------|------|
| `hand` | `h` | `hand` | 查看当前手牌（显示序号、iid、名称、兵种、费用、攻/血/行动费、技能描述） |
| `deploy` | `d` | `deploy <手牌序号> <supportline 位置>` | 从手牌部署单位到 supportline |
| `order` | `o` | `order <手牌序号> <目标iid>` | 打出 order 牌，指定目标单位的 iid |
| `adv` | `a` | `adv <supportline 序号> <frontline 位置>` | 将 supportline 上的单位推进到 frontline |
| `atk` | `k` | `atk <攻击者iid> <防御者iid>` | 用指定单位攻击目标（需要足够的 credits） |
| `end` | `e` | `end` | 结束当前回合 |
| `replay` | `r` | `replay` | 导出本局操作历史（见下方说明） |
| `quit` | — | `quit` | 退出游戏 |

### 操作回放与导出

在游戏过程中随时输入 `replay`（或 `r`），CLI 会输出一条完整的命令行字符串，包含当前的种子和你执行过的所有操作，例如：

```
--seed 42 --script "hand;d 0 0;e;hand;d 1 0;atk 3 5;e"
```

直接复制这段输出，粘贴到命令行中重新运行，即可完整复现这一局的操作：

```powershell
python -m kards_sim --seed 42 --script "hand;d 0 0;e;hand;d 1 0;atk 3 5;e"
```

这对于调试 bug 或分享特定局面非常方便——遇到问题时先 `replay` 导出，再用导出的命令复现。

### 棋盘阅读

每回合开始时 CLI 会打印如下格式的棋盘：

```
Turn 1 | Active: P0
P1 HQ=20 credits=1/1 hand=4 deck=16
  P1 supportline: ...
     frontline: ...
  P0 supportline: ...
P0 HQ=20 credits=1/1 hand=4 deck=16
-- abilities --
  iid=8 35(t)坦克(tank): 部署时若有友方步兵，行动费-1
```

- **HQ**: 总部血量，降为 0 则败北
- **credits**: 当前费用 / 最大费用（每回合自动增长）
- **hand**: 手牌数量
- **deck**: 牌库剩余数量
- 单位显示格式：`名称(攻击/血量|op=行动费)` 后跟 `Z` 表示已行动（exhausted）
- **-- abilities --**: 棋盘下方按 iid 列出场上所有带技能单位的描述

## 项目结构

```
src/kards_sim/
├── engine.py           # 游戏引擎：创建对局、驱动 Resolver
├── state.py            # GameState / PlayerState / CardInstance（运行时可变状态）
├── types.py            # 枚举：CardType, UnitClass, Nation, Lane, Zone, Keyword
├── events.py           # Event 事件体系 + Trigger 枚举
├── actions.py          # 玩家动作：PlayCard, Advance, Attack, EndTurn
├── resolver.py         # 动作解析、事件队列、Keyword 机制
├── rules.py            # 规则校验（出牌、部署、推进、攻击）
├── cli.py              # 交互式命令行界面
│
└── cards/
    ├── base.py             # CardBase — 所有卡牌的根类，定义 trigger hooks
    ├── unit.py             # UnitCard 基类
    ├── order.py            # OrderCard 基类
    ├── countermeasure.py   # CountermeasureCard 基类
    ├── headquarters.py     # HeadquartersCard 基类
    │
    ├── germany/            # 德国卡牌
    │   ├── headquarters.py
    │   ├── regiment_1.py, regiment_432.py
    │   ├── tank_35t.py, tank_38t.py, stug_iii_f.py
    │   ├── panzer_iii_l.py, panther_g.py
    │   ├── bf109e.py
    │   └── flak_88.py
    ├── italy/              # 意大利卡牌
    │   ├── fiat_cr42.py, fiat_g50.py
    │   ├── m13_40.py
    │   └── savoia_cavalry.py
    ├── soviet/             # 苏联卡牌
    ├── usa/                # 美国卡牌
    ├── britain/            # 英国卡牌
    ├── japan/              # 日本卡牌
    └── neutral/            # 中立（通用）卡牌
        ├── infantry.py, radio_team.py
        ├── light_tank.py, field_gun.py
        ├── fighter.py, bomber.py
        ├── artillery_strike.py
        └── sample_countermeasure.py
```

## 架构设计

### Keyword（关键词）与卡牌专属能力

**Keyword** 是多张卡牌共享的通用机制，定义为 `Keyword` 枚举值，逻辑完全由引擎（Resolver + Rules）处理：

| Keyword | 效果 |
|---------|------|
| `GUARD` | 守护 — 相邻的非守护单位不可被攻击（bomber / artillery 除外） |
| `BLITZ` | 闪击 — 部署当回合即可行动（移动/攻击） |
| `FURY` | 狂怒 — 每回合可攻击两次 |
| `AMBUSH` | 伏击 — 被攻击时先手反击；若攻击者被击杀则不造成伤害 |
| `SMOKESCREEN` | 烟幕 — 未移动/攻击前不可被敌方单位攻击 |
| `MOBILIZE` | 动员 — 回合开始时获得 +1/+1；受伤后失去该效果 |
| `LONG_RANGE` | 远程 — 无视战线（lane）距离限制 |
| `RESISTANCE` | 抵抗 — 受到 order 伤害减少 1 点 |

**Heavy Armor（重甲）** 是带等级的关键词（1–3），作为单独属性声明：

```python
class MyUnit(UnitCard):
    keywords = frozenset({Keyword.GUARD})
    heavy_armor = 2  # 受到单位伤害减少 2 点
```

**卡牌专属能力** 通过重写 `CardBase` 上的 trigger hooks 实现：

```python
class Tank35T(UnitCard):
    def on_deploy(self, state, ctx):
        # 场上有友方 infantry 时，行动费 -1
        ...
```

可用的 trigger hooks：
- `on_deploy`, `on_play`, `on_advance`, `on_retreat`, `on_destroy`
- `before_attack`, `after_attack`
- `before_deal_damage`, `after_deal_damage`
- `before_take_damage`, `after_take_damage`
- `on_turn_start`, `on_turn_end`
- `on_any_deploy`, `on_any_play`, `on_any_destroy`（全局反应钩子）
- `attack_modifier`, `health_modifier`, `cost_modifier`（持续光环）

### 添加新卡牌

1. 在 `cards/{nation}/` 下创建文件（如 `cards/germany/my_new_unit.py`）
2. 继承 `UnitCard`、`OrderCard` 或 `CountermeasureCard`
3. 设置必要的类属性（`name`, `cost`, `attack_value`, `description` 等）
4. 通过 `keywords = frozenset({...})` 添加 Keyword
5. 重写 trigger hooks 实现专属能力
6. 在 `cards/{nation}/__init__.py` 和 `cards/__init__.py` 中导出

> 详细的卡牌开发指南请参见 [CARD_GUIDE.md](CARD_GUIDE.md)，卡牌定义模板请参见 [card_template.yaml](card_template.yaml)。

### 单位类型（UnitClass）

| UnitClass | 说明 |
|-----------|------|
| `INFANTRY` | 步兵 |
| `TANK` | 坦克 |
| `ARTILLERY` | 火炮 |
| `FIGHTER` | 战斗机 |
| `BOMBER` | 轰炸机 |

### RL 集成

调用 `state.to_observation()` 可获取稳定的 dict 表示，适合作为 observation space。引擎在给定 seed 后完全确定性运行，适用于 RL 训练循环。
