from __future__ import annotations

import sys

from .engine import Engine
from .resolver import Resolver
from .state import GameState
from .types import InstanceId, PlayerId
from .actions import Attack, EndTurn, PlayCard, Advance

from .cards import (
    GermanyHeadquarters,
    SovietHeadquarters,
    # Germany
    Regiment1,
    Regiment432,
    Tank35T,
    Tank38T,
    StugIIIF,
    Bf109E,
    PanzerIIIL,
    Flak88,
    PantherG,
    # Italy
    FiatCR42,
    FiatG50,
    SavoiaCavalry,
    M1340,
    # Neutral
    Infantry,
    ArtilleryStrike,
)


def _print_state(state: GameState) -> None:
    p0 = state.players[PlayerId(0)]
    p1 = state.players[PlayerId(1)]
    hp_p0 = state.inst(p0.hq_iid).current_health
    hp_p1 = state.inst(p1.hq_iid).current_health
    print(f"Turn {state.turn} | Active: P{int(state.active_player)}")

    def fmt_unit(iid: InstanceId) -> str:
        ci = state.inst(iid)
        name = ci.card.name
        if hasattr(ci.card, "attack_value"):
            ex = "Z" if ci.exhausted else " "
            return f"{name}({ci.current_attack}/{ci.current_health}|op={ci.operation_cost}){ex}"
        return name

    def render_supportline(pid: PlayerId) -> str:
        parts = [f"{fmt_unit(iid)}(iid={int(iid)})" for iid in state.supportline[pid]]
        return f"  P{int(pid)} supportline: " + " | ".join(parts)

    def render_frontline() -> str:
        parts = [f"{fmt_unit(iid)}(iid={int(iid)})" for iid in state.frontline]
        owner = state.frontline_owner()
        prefix = "    " + (f"P{int(owner)} " if owner is not None else "   ")
        return prefix + "frontline: " + " | ".join(parts)

    print(f"P1 HQ={hp_p1} credits={p1.credits}/{p1.max_credits} hand={len(p1.hand)} deck={len(p1.deck)}")
    print(render_supportline(PlayerId(1)))
    print(render_frontline())
    print(render_supportline(PlayerId(0)))
    print(f"P0 HQ={hp_p0} credits={p0.credits}/{p0.max_credits} hand={len(p0.hand)} deck={len(p0.deck)}")
    if state.game_over:
        print(f"*** GAME OVER – Winner: P{int(state.winner)} ***")
    print()


def main() -> int:
    script = None
    if "--script" in sys.argv:
        i = sys.argv.index("--script")
        if i + 1 < len(sys.argv):
            script = sys.argv[i + 1]

    seed = 1
    if "--seed" in sys.argv:
        i = sys.argv.index("--seed")
        if i + 1 < len(sys.argv):
            seed = int(sys.argv[i + 1])

    engine = Engine(resolver=Resolver())

    deck0 = [
        GermanyHeadquarters,
        Regiment1, Regiment1, Regiment1,       # 1费步兵 x3
        Regiment432, Regiment432,              # 1费肉盾步兵 x2
        Tank35T, Tank35T,                      # 2费坦克 x2
        StugIIIF, StugIIIF,                    # 2费突击炮 x2
        Tank38T, Tank38T,                      # 3费坦克(抽牌) x2
        Bf109E, Bf109E,                        # 3费战斗机 x2
        PanzerIIIL,                            # 3费坦克(类型加成) x1
        PantherG,                              # 5费重坦 x1
        Flak88,                                # 6费火炮 x1
        ArtilleryStrike, ArtilleryStrike,      # 2费指令 x2
    ]
    deck1 = [
        SovietHeadquarters,
        SavoiaCavalry, SavoiaCavalry, SavoiaCavalry,  # 1费闪击骑兵 x3
        FiatCR42, FiatCR42, FiatCR42,                  # 1费战斗机 x3
        Infantry, Infantry,                            # 1费步兵 x2
        FiatG50, FiatG50,                              # 2费战斗机(治疗) x2
        M1340, M1340,                                  # 3费坦克(条件闪击) x2
        Tank38T, Tank38T,                              # 3费坦克(抽牌) x2
        Bf109E, Bf109E,                                # 3费战斗机 x2
        PantherG,                                      # 5费重坦 x1
        ArtilleryStrike, ArtilleryStrike,              # 2费指令 x2
    ]
    state = Engine.new_game(deck0, deck1, seed=seed)
    print(f"Seed: {seed}")

    if script is not None:
        cmds = [c.strip() for c in script.split(";") if c.strip()]
        it = iter(cmds)

        def _next() -> str:
            try:
                return next(it)
            except StopIteration:
                return "quit"

        input_fn = _next
    else:
        input_fn = lambda: input("cmd> ")  # noqa: E731

    cmd_history: list[str] = []

    print("Kards-Simulator CLI (MVP). Type 'help' for commands.\n")
    while True:
        _print_state(state)
        if state.game_over:
            return 0
        raw = input_fn().strip()
        cmd = raw.split()
        if not cmd:
            continue
        if cmd[0] in {"quit", "exit"}:
            return 0
        if cmd[0] == "help":
            print("Commands:")
            print("  hand(h)                                   - list hand cards")
            print("  deploy(d) <hand_index> <support_index>    - deploy unit from hand")
            print("  order(o) <hand_index> <target_iid>        - play damage order")
            print("  adv(a) <support_index> <front_index>      - advance to frontline")
            print("  atk(k) <attacker_iid> <defender_iid>      - attack unit")
            print("  end(e)                                    - end turn")
            print("  replay(r)                                 - export command history")
            continue
        if cmd[0] in ("replay", "r"):
            print(f"--seed {seed} --script \"{';'.join(cmd_history)}\"")
            continue

        ap = state.active_player
        player = state.players[ap]
        res = None

        if cmd[0] in ("hand", "h"):
            for idx, iid in enumerate(player.hand):
                ci = state.inst(iid)
                cost = getattr(ci.card, "cost", "?")
                uc = getattr(ci.card, "unit_class", None)
                tag = uc.value if uc else ci.card.card_type.value
                stats = f" {ci.current_attack}/{ci.current_health} op={ci.operation_cost}" if uc else ""
                print(f"[{idx}] iid={int(iid)} {ci.card.name} ({tag}) cost={cost}{stats}")
            continue

        elif cmd[0] in ("deploy", "d") and len(cmd) == 3:
            hi, si = int(cmd[1]), int(cmd[2])
            if hi < 0 or hi >= len(player.hand):
                print("invalid hand index")
                continue
            iid = player.hand[hi]
            res = engine.step(state, PlayCard(player_id=ap, card=iid, index=si))

        elif cmd[0] in ("adv", "a") and len(cmd) == 3:
            si, fi = int(cmd[1]), int(cmd[2])
            if si < 0 or si >= len(state.supportline[ap]):
                print("invalid supportline index")
                continue
            iid = state.supportline[ap][si]
            res = engine.step(state, Advance(player_id=ap, card=iid, index=fi))

        elif cmd[0] in ("order", "o") and len(cmd) == 3:
            hi = int(cmd[1])
            target = InstanceId(int(cmd[2]))
            iid = player.hand[hi]
            res = engine.step(state, PlayCard(player_id=ap, card=iid, target=target))

        elif cmd[0] in ("atk", "k") and len(cmd) == 3:
            res = engine.step(
                state,
                Attack(
                    player_id=ap,
                    attacker=InstanceId(int(cmd[1])),
                    defender=InstanceId(int(cmd[2])),
                ),
            )

        elif cmd[0] in ("end", "e"):
            res = engine.step(state, EndTurn(player_id=ap))

        else:
            print("unknown command, try 'help'")
            continue

        if res is not None:
            cmd_history.append(raw)
            if res.violation is not None:
                print(f"RuleViolation: {res.violation}")
            else:
                for ev in res.events:
                    print(f"event: {ev}")

    return 0
