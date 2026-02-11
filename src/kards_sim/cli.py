from __future__ import annotations

import sys

from .engine import Engine
from .state import GameState
from .resolver import Resolver
from .types import PlayerId, InstanceId
from .actions import Attack, EndTurn, PlayCard, Advance

from .cards.abilities.registry import default_registry
from .cards.samples import sample_card_registry


def _print_state(state: GameState) -> None:
    p0 = state.players[PlayerId(0)]
    p1 = state.players[PlayerId(1)]
    hp_p0 = state.get_instance(p0.base_card_id).current_health
    hp_p1 = state.get_instance(p1.base_card_id).current_health
    print(f"Turn {state.turn} | Active: P{int(state.active_player)}")

    def fmt_unit(iid: InstanceId) -> str:
        inst = state.get_instance(iid)
        name = state.get_def(inst.def_id).name
        return name

    def render_supportline(pid: PlayerId) -> str:
        parts: list[str] = []
        for iid in state.supportline[pid]:
            parts.append(f"{fmt_unit(iid)}(iid={int(iid)})")
        prefix = f"  P{int(pid)} supportline: "
        return prefix + " | ".join(parts)

    def render_frontline() -> str:
        parts: list[str] = []
        owner = state.frontline_owner()
        for iid in state.frontline:
            parts.append(f"{fmt_unit(iid)}(iid={int(iid)})")
        prefix = "    " + (f"P{int(owner)} " if owner is not None else "   ")
        return prefix + "frontline: " + " | ".join(parts)

    print(
        f"P1 HQ={hp_p1} credits={p1.credits}/{p1.max_credits} hand={len(p1.hand)} deck={len(p1.deck)}"
    )
    print(render_supportline(PlayerId(1)))
    print(render_frontline())
    print(render_supportline(PlayerId(0)))
    print(
        f"P0 HQ={hp_p0} credits={p0.credits}/{p0.max_credits} hand={len(p0.hand)} deck={len(p0.deck)}"
    )
    print()


def main() -> int:
    script = None
    if "--script" in sys.argv:
        i = sys.argv.index("--script")
        if i + 1 < len(sys.argv):
            script = sys.argv[i + 1]

    engine = Engine(resolver=Resolver(registry=default_registry()))
    registry = sample_card_registry()

    # Sample decks (keep small for now)
    deck0 = ["UNIT_INF_1"] * 8 + ["ORDER_DMG_2"] * 4 + ["UNIT_DRAW_2"] * 2
    deck1 = ["UNIT_INF_1"] * 8 + ["ORDER_DMG_2"] * 4 + ["UNIT_DRAW_2"] * 2
    state = Engine.new_game(registry, deck0, deck1, seed=1)

    if script is not None:
        # Run a short scripted session (semicolon-separated), then exit.
        # Example: python -m kards_sim --script "hand; play 0 frontline 0; end; quit"
        cmds = [c.strip() for c in script.split(";") if c.strip()]
        it = iter(cmds)

        def _next() -> str:
            try:
                return next(it)
            except StopIteration:
                return "quit"

        input_fn = _next
    else:
        input_fn = lambda: input("cmd> ")

    print("Kards-Simulator CLI (MVP). Type 'help' for commands.\n")
    while True:
        _print_state(state)
        cmd = input_fn().strip().split()
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
            continue

        ap = state.active_player
        player = state.players[ap]

        if cmd[0] == "hand" or cmd[0] == "h":
            for idx, iid in enumerate(player.hand):
                d = state.get_def(state.get_instance(iid).def_id)
                print(
                    f"[{idx}] iid={int(iid)} {d.name} ({d.card_type.value}) cost={d.cost}"
                )
            continue

        if (cmd[0] == "deploy" or cmd[0] == "d") and len(cmd) == 3:
            hi = int(cmd[1])
            si = int(cmd[2])

            if hi < 0 or hi >= len(player.hand):
                print("invalid hand index")
                continue

            iid = player.hand[hi]

            res = engine.step(
                state,
                PlayCard(player_id=ap, card=iid, index=si),
            )
        elif (cmd[0] == "adv" or cmd[0] == "a") and len(cmd) == 3:
            si = int(cmd[1])
            fi = int(cmd[2])

            if si < 0 or si >= len(state.supportline[ap]):
                print("invalid supportline index")
                continue

            iid = state.supportline[ap][si]

            res = engine.step(
                state,
                Advance(
                    player_id=ap,
                    card=iid,
                    index=fi,
                ),
            )
        elif (cmd[0] == "order" or cmd[0] == "o") and len(cmd) == 3:
            hi = int(cmd[1])
            target = InstanceId(int(cmd[2]))
            iid = player.hand[hi]
            res = engine.step(state, PlayCard(player_id=ap, card=iid, target=target))
        elif (cmd[0] == "atk" or cmd[0] == "k") and len(cmd) == 3:
            res = engine.step(
                state,
                Attack(
                    player_id=ap,
                    attacker=InstanceId(int(cmd[1])),
                    defender=InstanceId(int(cmd[2])),
                ),
            )
        elif cmd[0] == "end" or cmd[0] == "e":
            res = engine.step(state, EndTurn(player_id=ap))
        else:
            print("unknown command, try 'help'")
            continue

        if res.violation is not None:
            print(f"RuleViolation: {res.violation}")
        else:
            for ev in res.events:
                print(f"event: {ev}")
