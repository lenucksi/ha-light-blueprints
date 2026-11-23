"""Minimal structural validation for the blueprint and example YAML files."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml


class BlueprintLoader(yaml.SafeLoader):
    """SafeLoader that tolerates Home Assistant blueprint tags."""


def _unknown_tag(loader: BlueprintLoader, tag_suffix: str, node: yaml.Node) -> object:
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return loader.construct_mapping(node)


BlueprintLoader.add_multi_constructor("!", _unknown_tag)

ROOT = Path(__file__).resolve().parent.parent
TARGETS = [
    ROOT / "blueprints/night-mode/night-mode.yaml",
    ROOT / "blueprints/sunrise/sunrise_simulation.yaml",
    ROOT / "examples/helpers.yaml",
    ROOT / "examples/automations.yaml",
]

errors: list[str] = []
for target in TARGETS:
    try:
        data = yaml.load(target.read_text(encoding="utf-8"), Loader=BlueprintLoader)
    except yaml.YAMLError as err:  # noqa: PERF203
        errors.append(f"{target.relative_to(ROOT)}: YAML error: {err}")
        continue
    rel = target.relative_to(ROOT)
    if rel.name == "automations.yaml":
        if not isinstance(data, list):
            errors.append(f"{rel}: expected a list of automations")
        continue
    if not isinstance(data, dict):
        errors.append(f"{rel}: expected a mapping")
        continue
    if str(rel).startswith("blueprints/") and "blueprint" not in data:
        errors.append(f"{rel}: missing 'blueprint' key")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"Validated {len(TARGETS)} YAML files")
