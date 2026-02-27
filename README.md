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

### Run tests

```powershell
pytest -v
```

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
    │   ├── regiment_1.py
    │   ├── regiment_432.py
    │   └── tank_35t.py
    ├── soviet/             # Soviet nation cards
    ├── usa/                # USA nation cards
    ├── britain/            # Britain nation cards
    ├── japan/              # Japan nation cards
    └── neutral/            # Neutral (shared) cards
        ├── infantry.py
        ├── radio_team.py
        ├── light_tank.py
        ├── field_gun.py
        ├── fighter.py
        ├── bomber.py
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
