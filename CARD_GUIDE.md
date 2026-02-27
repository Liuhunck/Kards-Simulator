# 卡牌开发指南

本文档面向 AI 或开发者，说明如何在本项目中添加一张新的 Kards 卡牌。

---

## 1. 项目结构概览

```
src/kards_sim/
├── types.py            # 枚举：CardType, UnitClass, Nation, Keyword 等
├── state.py            # GameState, CardInstance（可变运行时状态）
├── events.py           # 事件类型：DamageDealt, BuffApplied, HealApplied 等
├── resolver.py         # 行动解析、事件队列、关键词机制
├── rules.py            # 规则校验
│
└── cards/
    ├── base.py             # CardBase — 根基类，定义所有触发钩子
    ├── unit.py             # UnitCard — 军事单位基类
    ├── order.py            # OrderCard — 命令卡基类
    ├── countermeasure.py   # CountermeasureCard — 反制卡基类
    ├── headquarters.py     # HeadquartersCard — 总部基类
    ├── __init__.py         # 汇总导出所有卡牌
    │
    ├── germany/            # 德国卡牌
    ├── soviet/             # 苏联卡牌
    ├── usa/                # 美国卡牌
    ├── britain/            # 英国卡牌
    ├── japan/              # 日本卡牌
    ├── italy/              # 意大利卡牌
    └── neutral/            # 中立卡牌
```

---

## 2. 添加一张新卡牌的步骤

### 步骤 1：创建卡牌文件

在 `cards/{nation}/` 下创建 `.py` 文件，文件名使用蛇形命名。

### 步骤 2：编写卡牌类

根据卡牌类型继承对应基类，设置类属性，用中文 docstring 描述卡牌。

### 步骤 3：注册导出

需要在 **三个地方** 添加导出：

1. `cards/{nation}/__init__.py` — 添加 import 和 `__all__`
2. `cards/__init__.py` — 添加 import、加入 `ALL_CARD_CLASSES` 列表、加入 `__all__`

### 步骤 4：运行测试

```bash
.venv/Scripts/python.exe -m pytest tests/ -v
```

---

## 3. 卡牌类编写规范

### 3.1 基本模板（无能力白板单位）

```python
from __future__ import annotations

from ...types import Nation, UnitClass
from ..unit import UnitCard


class MyUnit(UnitCard):
    """单位名称 — 简短描述。"""

    name = "单位名称"
    nation = Nation.GERMANY       # 所属国家
    unit_class = UnitClass.TANK   # 兵种
    cost = 3                      # 部署费用
    acost = 1                     # 行动费用
    attack_value = 2              # 攻击力
    health_value = 3              # 生命值
```

### 3.2 带关键词的单位

关键词通过 `keywords` 属性声明，引擎自动处理逻辑。

```python
from ...types import Keyword, Nation, UnitClass
from ..unit import UnitCard


class MyUnit(UnitCard):
    """某单位 — 拥有闪击和烟幕。"""

    name = "某单位"
    nation = Nation.GERMANY
    unit_class = UnitClass.TANK
    cost = 2
    acost = 1
    attack_value = 2
    health_value = 3
    keywords = frozenset({Keyword.BLITZ, Keyword.SMOKESCREEN})
```

**可用关键词：**

| 关键词 | 枚举值 | 效果 |
|--------|--------|------|
| 守护 | `Keyword.GUARD` | 相邻非守护单位不能被攻击（轰炸机/火炮除外） |
| 闪击 | `Keyword.BLITZ` | 部署当回合即可行动 |
| 狂怒 | `Keyword.FURY` | 每回合可攻击两次 |
| 伏击 | `Keyword.AMBUSH` | 被攻击时先手反击 |
| 烟幕 | `Keyword.SMOKESCREEN` | 移动/攻击前不能被攻击 |
| 动员 | `Keyword.MOBILIZE` | 每回合+1/+1，受伤后失效 |
| 远程 | `Keyword.LONG_RANGE` | 无视战线邻接限制 |
| 抵抗 | `Keyword.RESISTANCE` | 受命令卡伤害减1 |

**带等级的关键词（独立属性）：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `heavy_armor` | `int` (0–3) | 重甲等级，受到的单位伤害减少该数值。0 = 无重甲 |

重甲不写在 `keywords` frozenset 中，而是作为独立的类属性声明：

```python
class MyTank(UnitCard):
    heavy_armor = 2  # 重甲2，减伤2点
```

`state.has_keyword(iid, Keyword.HEAVY_ARMOR)` 会自动检查 `heavy_armor > 0`，无需额外处理。

### 3.3 带专属能力的单位

通过覆写触发钩子方法实现。每个钩子接收 `state`（游戏状态）和 `ctx`（触发上下文），返回 `list[Event]`。

**TriggerContext 字段：**
- `ctx.player_id` — 触发玩家
- `ctx.source` — 触发源卡牌的 InstanceId
- `ctx.target` — 目标卡牌的 InstanceId（可为 None）
- `ctx.target_player` — 目标玩家（可为 None）
- `ctx.amount` — 数值（如伤害量，可为 None）
- `ctx.self_iid` — 当前被调用钩子的卡牌自身的 InstanceId（全局反应钩子中尤为重要）

**导入模式（避免循环导入）：**

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from ...types import Nation, UnitClass
from ..unit import UnitCard

if TYPE_CHECKING:
    from ...events import Event, TriggerContext
    from ...state import GameState
```

事件类在方法体内导入：

```python
def on_deploy(self, state: GameState, ctx: TriggerContext) -> list[Event]:
    from ...events import CardDrawn
    from ...resolver import enqueue_draw
    # ...
```

---

## 4. 可用的触发钩子

| 钩子方法 | 触发时机 |
|----------|----------|
| `on_deploy` | 当此单位部署到场上时 |
| `on_play` | 当此卡从手中打出时（命令/反制） |
| `on_advance` | 当此单位从后方推进到前线时 |
| `on_retreat` | 当此单位从前线撤退到后方时 |
| `on_destroy` | 当此单位被摧毁时（移除前） |
| `before_attack` | 当此单位发起攻击前 |
| `after_attack` | 当此单位完成攻击后 |
| `before_deal_damage` | 当此单位造成伤害前 |
| `after_deal_damage` | 当此单位造成伤害后 |
| `before_take_damage` | 当此单位受到伤害前 |
| `after_take_damage` | 当此单位受到伤害后 |
| `on_turn_start` | 拥有者回合开始时（在场时） |
| `on_turn_end` | 拥有者回合结束时（在场时） |
| `on_any_deploy` | 任意单位被部署时（全局反应） |
| `on_any_play` | 任意卡牌被打出时（全局反应） |
| `on_any_destroy` | 任意单位被摧毁时（全局反应） |

---

## 5. 可用的事件类型

在钩子中返回这些事件，resolver 会自动处理：

```python
from ...events import DamageDealt, BuffApplied, HealApplied, CardDrawn
```

| 事件 | 用途 | 字段 |
|------|------|------|
| `DamageDealt` | 造成伤害 | `source`, `target`, `target_player`, `amount` |
| `BuffApplied` | 增益/减益 | `source`, `target`, `attack_delta`, `health_delta` |
| `HealApplied` | 治疗（不超过最大值） | `source`, `target`, `amount` |
| `CardDrawn` | 抽牌 | `player_id`, `card` |

抽牌需配合 `enqueue_draw`：

```python
from ...resolver import enqueue_draw
drawn = enqueue_draw(state, ctx.player_id)
if drawn is not None:
    events.append(CardDrawn(player_id=ctx.player_id, card=drawn))
```

---

## 6. 常用 state API

```python
# 获取卡牌实例（可变状态）
ci = state.inst(iid)           # -> CardInstance
ci.current_health              # 当前生命值
ci.current_attack              # 当前攻击力
ci.operation_cost              # 当前行动费用
ci.exhausted                   # 是否已疲劳
ci.owner                       # 拥有者 PlayerId

# 获取卡牌定义（不可变模板）
card = state.card(iid)         # -> CardBase 子类实例
card.name                      # 卡牌名称
card.unit_class                # 兵种
card.keywords                  # 关键词集合

# 棋盘查询
state.board_unit_iids()                 # 场上所有单位 iid 列表
state.friendly_board_iids(player_id)    # 友方单位 iid 列表
state.enemy_board_iids(player_id)       # 敌方单位 iid 列表
state.has_keyword(iid, Keyword.BLITZ)   # 检查关键词

# 玩家信息
state.players[pid].hq_iid     # 总部 iid
state.opponent(pid)            # 对手 PlayerId
```

---

## 7. 特殊机制

### 7.1 双重兵种（counts_as）

若卡牌需要同时算作多种兵种，覆写 `counts_as` 方法：

```python
class MyUnit(UnitCard):
    unit_class = UnitClass.INFANTRY

    def counts_as(self, uc: UnitClass) -> bool:
        return uc in (UnitClass.INFANTRY, UnitClass.TANK)
```

其他卡牌检查兵种时应使用 `card.counts_as(UnitClass.XXX)` 而不是 `card.unit_class == ...`。

### 7.2 临时攻击力修改（before/after_attack）

对特定目标翻倍攻击力的模式：

```python
_attack_boosted: bool = False

def before_attack(self, state, ctx):
    target_card = state.card(ctx.target)
    if hasattr(target_card, "counts_as") and target_card.counts_as(UnitClass.TANK):
        ci = state.inst(ctx.source)
        ci.current_attack *= 2
        self._attack_boosted = True
    return []

def after_attack(self, state, ctx):
    if self._attack_boosted:
        ci = state.inst(ctx.source)
        ci.current_attack //= 2
        self._attack_boosted = False
    return []
```

### 7.3 动态自增益（基于场上状态）

当卡牌的攻击力需要根据场上状态动态变化时，使用 `on_deploy` + `on_any_deploy` + `on_any_destroy` 组合，配合 `ctx.self_iid` 获取自身 iid：

```python
_type_bonus: int = 0

def _calc_bonus(self, state, my_iid):
    owner = state.inst(my_iid).owner
    # ... 计算逻辑 ...
    return bonus

def _refresh_bonus(self, state, my_iid):
    new_bonus = self._calc_bonus(state, my_iid)
    delta = new_bonus - self._type_bonus
    if delta != 0:
        ci = state.inst(my_iid)
        ci.current_attack += delta
        self._type_bonus = new_bonus

def on_deploy(self, state, ctx):
    self._type_bonus = 0
    self._refresh_bonus(state, ctx.self_iid)
    return []

def on_any_deploy(self, state, ctx):
    if ctx.source == ctx.self_iid:
        return []
    self._refresh_bonus(state, ctx.self_iid)
    return []

def on_any_destroy(self, state, ctx):
    if ctx.source == ctx.self_iid:
        return []
    self._refresh_bonus(state, ctx.self_iid)
    return []
```

### 7.4 条件性闪击

部署时根据条件赋予闪击（设置 `ci.exhausted = False`）：

```python
def on_deploy(self, state, ctx):
    ci = state.inst(ctx.source)
    if some_condition:
        ci.exhausted = False
    return []
```

---

## 8. 命令卡模板

```python
from ...types import Nation
from ..order import OrderCard


class MyOrder(OrderCard):
    """命令名称 — 效果描述。"""

    name = "命令名称"
    nation = Nation.NEUTRAL
    cost = 2

    def on_play(self, state, ctx):
        from ...events import DamageDealt
        if ctx.target is not None or ctx.target_player is not None:
            return [DamageDealt(source=ctx.source, target=ctx.target,
                                target_player=ctx.target_player, amount=2)]
        return []
```

---

## 9. 注册检查清单

添加新卡牌后，确认以下文件已更新：

- [ ] `cards/{nation}/{card_file}.py` — 卡牌类文件已创建
- [ ] `cards/{nation}/__init__.py` — 已添加 import 和 `__all__` 条目
- [ ] `cards/__init__.py` — 已添加 import、`ALL_CARD_CLASSES` 条目、`__all__` 条目
- [ ] 测试通过：`.venv/Scripts/python.exe -m pytest tests/ -v`

---

## 10. YAML 模板工作流

项目根目录下有 `card_template.yaml`，用户会在其中填写新卡牌信息，然后交给 AI 实现。

**AI 收到模板后的操作流程：**

1. 读取 `card_template.yaml`
2. 根据模板内容创建 `cards/{nation}/{card_file}.py`
3. 更新 `cards/{nation}/__init__.py`
4. 更新 `cards/__init__.py`（import、`ALL_CARD_CLASSES`、`__all__`）
5. 编写对应测试到 `tests/test_cards.py`
6. 运行 `.venv/Scripts/python.exe -m pytest tests/ -v` 确认通过

**注意事项：**
- docstring 使用中文
- 类名使用 PascalCase，文件名使用 snake_case
- 所有开发在 `.venv` 虚拟环境中进行，不要使用全局 Python 环境
- 测试文件分类：引擎测试在 `test_engine.py`，关键词测试在 `test_keywords.py`，卡牌测试在 `test_cards.py`
- 测试夹具和辅助函数在 `tests/conftest.py`
