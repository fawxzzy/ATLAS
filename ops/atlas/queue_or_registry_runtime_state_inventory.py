from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root

FAMILY_ROOT_REF = "runtime/state/ai-long-run-batch-orchestration/queue-or-registry"
QUEUE_HOME_REF = f"{FAMILY_ROOT_REF}/queue-home"
REGISTRY_HOME_REF = f"{FAMILY_ROOT_REF}/registry-home"
INVENTORY_NOTE = (
    "inventory proves only present runtime-state population under the admitted queue-or-registry family; "
    "it does not infer live queue semantics from absent or placeholder paths"
)


class QueueOrRegistryRuntimeStateInventoryError(RuntimeError):
    pass


@dataclass(frozen=True)
class QueueOrRegistryRuntimeStateInventoryResult:
    family_root_ref: str
    family_root_exists: bool
    queue_home_exists: bool
    registry_home_exists: bool
    inventory_status: str
    family_entry_count: int
    json_candidate_count: int
    directory_candidate_count: int
    json_candidate_refs: tuple[str, ...]
    directory_candidate_refs: tuple[str, ...]
    note: str = INVENTORY_NOTE

    def to_payload(self) -> dict[str, Any]:
        return {
            "family_root_ref": self.family_root_ref,
            "family_root_exists": self.family_root_exists,
            "queue_home_exists": self.queue_home_exists,
            "registry_home_exists": self.registry_home_exists,
            "inventory_status": self.inventory_status,
            "family_entry_count": self.family_entry_count,
            "json_candidate_count": self.json_candidate_count,
            "directory_candidate_count": self.directory_candidate_count,
            "json_candidate_refs": list(self.json_candidate_refs),
            "directory_candidate_refs": list(self.directory_candidate_refs),
            "note": self.note,
        }


def build_queue_or_registry_runtime_state_inventory(
    *,
    root: Path | None = None,
) -> QueueOrRegistryRuntimeStateInventoryResult:
    base_root = (root or atlas_root()).resolve()
    family_root = base_root / FAMILY_ROOT_REF
    queue_home = base_root / QUEUE_HOME_REF
    registry_home = base_root / REGISTRY_HOME_REF

    if not family_root.exists():
        return QueueOrRegistryRuntimeStateInventoryResult(
            family_root_ref=FAMILY_ROOT_REF,
            family_root_exists=False,
            queue_home_exists=False,
            registry_home_exists=False,
            inventory_status="unpopulated-family-root",
            family_entry_count=0,
            json_candidate_count=0,
            directory_candidate_count=0,
            json_candidate_refs=(),
            directory_candidate_refs=(),
        )

    if not family_root.is_dir():
        raise QueueOrRegistryRuntimeStateInventoryError(
            f"Admitted queue-or-registry family root is not a directory: {FAMILY_ROOT_REF}"
        )

    json_candidate_refs: list[str] = []
    directory_candidate_refs: list[str] = []
    family_entries = 0

    for path in sorted(family_root.rglob("*")):
        if path == family_root:
            continue
        relative_ref = atlas_relative(path, root=base_root)
        family_entries += 1
        if path.is_dir():
            directory_candidate_refs.append(relative_ref)
        elif path.is_file() and path.suffix.lower() == ".json":
            json_candidate_refs.append(relative_ref)

    inventory_status = "family-root-only"
    if family_entries:
        if queue_home.exists() and registry_home.exists():
            inventory_status = "queue-and-registry-populated"
        elif queue_home.exists():
            inventory_status = "queue-home-populated"
        elif registry_home.exists():
            inventory_status = "registry-home-populated"
        else:
            inventory_status = "non-standard-family-populated"

    return QueueOrRegistryRuntimeStateInventoryResult(
        family_root_ref=FAMILY_ROOT_REF,
        family_root_exists=True,
        queue_home_exists=queue_home.exists(),
        registry_home_exists=registry_home.exists(),
        inventory_status=inventory_status,
        family_entry_count=family_entries,
        json_candidate_count=len(json_candidate_refs),
        directory_candidate_count=len(directory_candidate_refs),
        json_candidate_refs=tuple(json_candidate_refs),
        directory_candidate_refs=tuple(directory_candidate_refs),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inventory the admitted queue-or-registry runtime-state family without inferring live queue semantics."
    )
    parser.add_argument("--root", type=Path, default=atlas_root())
    args = parser.parse_args(argv)

    try:
        payload = build_queue_or_registry_runtime_state_inventory(root=args.root.resolve()).to_payload()
    except QueueOrRegistryRuntimeStateInventoryError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
