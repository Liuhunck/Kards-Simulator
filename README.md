# Kards-Simulator

A Python engine for simulating [KARDS: The WWII Card Game](https://www.kards.com/), designed for both interactive play and reinforcement learning integration.

## Quick Start

### Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### Run the CLI

```powershell
python -m kards_sim
```

指定随机种子（方便复现同一局面）：

```powershell
python -m kards_sim --seed 42
```

### Run tests

```powershell
pytest -v
```

## How to Play

启动 CLI 后，游戏会打印当前棋盘状态，并等待你输入指令。输入 `help` 查看所有可用命令：

| 命令 | 缩写 | 格式 | 说明 |
|------|------|------|------|
| `hand` | `h` | `hand` | 查看当前手牌（显示序号、iid、名称、兵种、费用、攻/血/行动费） |
| `deploy` | `d` | `deploy <手牌序号> <支援线位置>` | 从手牌部署单位到支援线 |
| `order` | `o` | `order <手牌序号> <目标iid>` | 打出指令牌，指定目标单位的 iid |
| `adv` | `a` | `adv <支援线序号> <前线位置>` | 将支援线上的单位推进到前线 |
| `atk` | `k` | `atk <攻击者iid> <防御者iid>` | 用指定单位攻击目标（需要足够的行动费） |
| `end` | `e` | `end` | 结束当前回合 |
| `replay` | `r` | `replay` | 导出本局操作历史（见下方说明） |
| `quit` | — | `quit` | 退出游戏 |

### 操作回放与导出

在游戏过程中随时输入 `replay`（或 `r`），CLI 会输出一条完整的命令行字符串，包含当前的种子和你执行过的所有操作，例如：

```
--seed 42 --script "hand;d 0 0;e;hand;d 1 0;atk 3 5;e"
```

你可以直接复制这段输出，粘贴到命令行中重新运行，即可完整复现这一局的操作：

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
```

- **HQ**: 总部血量，降为 0 则输掉游戏
- **credits**: 当前费用 / 最大费用（每回合自动增长）
- **hand**: 手牌数量
- **deck**: 牌库剩余数量
- 单位显示格式：`名称(攻击/血量|op=行动费)` 后跟 `Z` 表示已行动过（exhausted）

## Project Structure

```
src/kards_sim/
├── engine.py           # Game engine: creates games, drives the resolver
├── state.py            # GameState, PlayerState, CardInstance (mutable runtime state)
├── types.py            # Enums: CardType, UnitClass, Nation, Lane, Zone, Keyword
├── events.py           # Event hierarchy + Trigger enum
├── actions.py          # Player actions: PlayCard, Advance, Attack, EndTurn
├── resolver.py         # Action resolution, event queue, keyword mechanics
├── rules.py            # Rule validation (play, deploy, advance, attack)
├── cli.py              # Interactive CLI
│
└── cards/
    ├── base.py             # CardBase – root class with trigger hooks
    ├── unit.py             # UnitCard base
    ├── order.py            # OrderCard base
    ├── countermeasure.py   # CountermeasureCard base
    ├── headquarters.py     # HeadquartersCard base
    │
    ├── germany/            # German nation cards
    │   ├── headquarters.py
    │   ├── regiment_1.py, regiment_432.py
    │   ├── tank_35t.py, tank_38t.py, stug_iii_f.py
    │   ├── panzer_iii_l.py, panther_g.py
    │   ├── bf109e.py
    │   └── flak_88.py
    ├── italy/              # Italian nation cards
    │   ├── fiat_cr42.py, fiat_g50.py
    │   ├── m13_40.py
    │   └── savoia_cavalry.py
    ├── soviet/             # Soviet nation cards
    ├── usa/                # USA nation cards
    ├── britain/            # Britain nation cards
    ├── japan/              # Japan nation cards
    └── neutral/            # Neutral (shared) cards
        ├── infantry.py, radio_team.py
        ├── light_tank.py, field_gun.py
        ├── fighter.py, bomber.py
        ├── artillery_strike.py
        └── sample_countermeasure.py
```

## Architecture

### Keywords vs. Card-specific Abilities

**Keywords** are reusable mechanics shared by many cards. They are defined as
`Keyword` enum values and handled entirely by the engine (resolver + rules):

| Keyword | Effect |
|---------|--------|
| `GUARD` | Adjacent non-guard units cannot be attacked (except by bombers/artillery) |
| `BLITZ` | Can operate (move/attack) on the deployment turn |
| `FURY` | Can attack twice per turn |
| `AMBUSH` | When attacked, strikes first; if attacker dies, it deals no damage |
| `SMOKESCREEN` | Cannot be attacked by enemies until it moves or attacks |
| `MOBILIZE` | Gains +1/+1 at turn start; lost when damaged |
| `LONG_RANGE` | Ignores lane adjacency restrictions |
| `RESISTANCE` | Takes 1 less damage from orders |

**Heavy Armor** is a levelled keyword (1–3) declared as a separate attribute:

```python
class MyUnit(UnitCard):
    keywords = frozenset({Keyword.GUARD})
    heavy_armor = 2  # Reduces incoming unit damage by 2
```

**Card-specific abilities** are implemented by overriding trigger hooks on `CardBase`:

```python
class Tank35T(UnitCard):
    def on_deploy(self, state, ctx):
        # Reduce operation cost when friendly infantry is present
        ...
```

Available trigger hooks:
- `on_deploy`, `on_play`, `on_advance`, `on_retreat`, `on_destroy`
- `before_attack`, `after_attack`
- `before_deal_damage`, `after_deal_damage`
- `before_take_damage`, `after_take_damage`
- `on_turn_start`, `on_turn_end`
- `on_any_deploy`, `on_any_play`, `on_any_destroy` (global reactions)
- `attack_modifier`, `health_modifier`, `cost_modifier` (continuous auras)

### Adding a New Card

1. Create a file under `cards/{nation}/` (e.g. `cards/germany/my_new_unit.py`)
2. Subclass `UnitCard`, `OrderCard`, or `CountermeasureCard`
3. Set the required class attributes (`name`, `cost`, `attack_value`, etc.)
4. Add keywords via `keywords = frozenset({...})`
5. Override trigger hooks for custom abilities
6. Export from `cards/{nation}/__init__.py` and `cards/__init__.py`

### RL Integration

Call `state.to_observation()` to get a stable dict representation of the game
state suitable for use as an observation space. The engine is fully
deterministic given a seed, making it suitable for RL training loops.
