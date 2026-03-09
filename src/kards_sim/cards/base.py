from __future__ import annotations

from typing import TYPE_CHECKING

from ..types import CardType, Keyword, Nation

if TYPE_CHECKING:
    from ..events import Event, TriggerContext
    from ..state import GameState


class CardBase:
    """Root base class for every card in the game.

    Subclass hierarchy
    ------------------
    CardBase
    ├── HeadquartersCard   – HQ / base
    ├── UnitCard           – deployable military units
    ├── OrderCard          – one-shot effect cards
    └── CountermeasureCard – reactive trap cards

    Keywords vs. abilities
    ----------------------
    *Keywords* are common, reusable mechanics (Guard, Blitz, …) listed in
    ``keywords``.  Their logic lives in the resolver / rules modules.

    *Abilities* are card-specific effects implemented by overriding the
    trigger-hook methods below (``on_deploy``, ``on_destroy``, …).  This
    gives every card maximum flexibility to define unique behaviour.
    """

    # ---- card identity (set on each concrete card class) -----------------
    name: str = "Unnamed Card"
    card_type: CardType = CardType.ORDER
    nation: Nation = Nation.NEUTRAL
    description: str = ""
    """简短的中文能力描述，用于 CLI 展示。"""

    # ---- keyword abilities (reusable mechanics) --------------------------
    keywords: frozenset[Keyword] = frozenset()

    # ---- parameterised keywords ------------------------------------------
    heavy_armor: int = 0
    """Heavy Armor level (1–3). Reduces incoming unit damage by this amount."""

    # ---- passive flags -----------------------------------------------------
    order_immune: bool = False
    """If True, this unit cannot be targeted by enemy order cards."""

    # ---- card-specific ability hooks -------------------------------------
    # Override any of these in a concrete card to add custom effects.
    # Each hook receives the current game state and a TriggerContext that
    # carries information about what triggered the hook (source, target,
    # player, amount, etc.).  Return a list of Event objects that the
    # resolver will enqueue.

    def on_deploy(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        """Called when THIS card is deployed onto the board."""
        return []

    def on_play(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        """Called when THIS card is played from hand (orders, countermeasures)."""
        return []

    def on_advance(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        """Called when THIS unit advances from supportline to frontline."""
        return []

    def on_retreat(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        """Called when THIS unit retreats from frontline to supportline."""
        return []

    def on_destroy(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        """Called when THIS card is destroyed (before removal)."""
        return []

    # ---- combat hooks ----------------------------------------------------

    def before_attack(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        """Called before THIS unit performs an attack."""
        return []

    def after_attack(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        """Called after THIS unit performs an attack."""
        return []

    def before_take_damage(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        """Called before THIS card takes damage."""
        return []

    def after_take_damage(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        """Called after THIS card takes damage."""
        return []

    def before_deal_damage(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        """Called before THIS card deals damage."""
        return []

    def after_deal_damage(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        """Called after THIS card deals damage."""
        return []

    # ---- turn lifecycle hooks --------------------------------------------

    def on_turn_start(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        """Called at the start of owner's turn while this card is on board."""
        return []

    def on_turn_end(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        """Called at the end of owner's turn while this card is on board."""
        return []

    # ---- global reaction hooks -------------------------------------------
    # These fire in response to events involving OTHER cards. Useful for
    # aura effects and reaction abilities.

    def on_any_deploy(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        """Called when ANY unit is deployed (not just this one)."""
        return []

    def on_any_play(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        """Called when ANY card is played."""
        return []

    def on_any_destroy(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        """Called when ANY unit is destroyed."""
        return []

    # ---- continuous modifiers (auras) ------------------------------------
    # These are queried by the state/resolver to compute effective stats.
    # Return the delta (can be negative).

    def attack_modifier(self, state: GameState, target_iid: int) -> int:
        """Continuous attack buff/debuff applied to *target_iid* while this card is on board."""
        return 0

    def health_modifier(self, state: GameState, target_iid: int) -> int:
        """Continuous health buff/debuff applied to *target_iid* while this card is on board."""
        return 0

    def cost_modifier(self, state: GameState, target_iid: int) -> int:
        """Continuous cost reduction/increase applied to *target_iid*."""
        return 0

    # ---- trigger dispatch ------------------------------------------------

    def dispatch_trigger(
        self, state: GameState, trigger: "Trigger", ctx: "TriggerContext"
    ) -> list[Event]:
        """Route a trigger enum to the matching hook method."""
        from ..events import Trigger

        method_name = _TRIGGER_METHOD_MAP.get(trigger)
        if method_name is not None:
            method = getattr(self, method_name)
            return method(state, ctx)
        return []


_TRIGGER_METHOD_MAP: dict = {}


def _build_trigger_map() -> None:
    from ..events import Trigger

    global _TRIGGER_METHOD_MAP
    _TRIGGER_METHOD_MAP = {
        Trigger.TURN_START: "on_turn_start",
        Trigger.TURN_END: "on_turn_end",
        Trigger.ON_DEPLOY: "on_deploy",
        Trigger.ON_PLAY: "on_play",
        Trigger.ON_ADVANCE: "on_advance",
        Trigger.ON_RETREAT: "on_retreat",
        Trigger.ON_DESTROY: "on_destroy",
        Trigger.ON_ANY_DEPLOY: "on_any_deploy",
        Trigger.ON_ANY_PLAY: "on_any_play",
        Trigger.ON_ANY_DESTROY: "on_any_destroy",
        Trigger.BEFORE_ATTACK: "before_attack",
        Trigger.AFTER_ATTACK: "after_attack",
        Trigger.BEFORE_DEAL_DAMAGE: "before_deal_damage",
        Trigger.AFTER_DEAL_DAMAGE: "after_deal_damage",
        Trigger.BEFORE_TAKE_DAMAGE: "before_take_damage",
        Trigger.AFTER_TAKE_DAMAGE: "after_take_damage",
    }


_build_trigger_map()
