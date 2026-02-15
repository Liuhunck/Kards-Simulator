from __future__ import annotations

import importlib
import inspect
import pkgutil

from .base import CardBase
from .specs import validate_card_class


def discover_card_classes() -> list[type[CardBase]]:
    classes: list[type[CardBase]] = []
    package_name = "kards_sim.cards"
    package = importlib.import_module(package_name)

    for module_info in pkgutil.walk_packages(package.__path__, package_name + "."):
        name = module_info.name
        if ".abilities." in name:
            continue
        if name.endswith(".base") or name.endswith(".samples"):
            continue
        module = importlib.import_module(name)
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if not issubclass(obj, CardBase) or obj is CardBase:
                continue
            if obj.__module__ != module.__name__:
                continue
            if obj.__name__.endswith("Base"):
                continue
            classes.append(obj)

    return classes


def validate_card_classes() -> list[str]:
    errors: list[str] = []
    classes = discover_card_classes()
    for cls in classes:
        try:
            validate_card_class(cls)
        except Exception as exc:
            errors.append(
                f"{cls.__module__}.{cls.__name__}: invalid card class ({exc})"
            )

    return errors


def main() -> int:
    errors = validate_card_classes()
    if errors:
        print("Card validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1
    print("All card classes are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
