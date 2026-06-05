from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ops._atlas import atlas_root, normalize_slashes
from ops.cortex._artifacts import read_json
from ops.cortex.kernel import runtime_cortex_root

SHADOW_AGENT_REGISTRY_CONTRACT_VERSION = "atlas.cortex.shadow-agent-registry.v1"
SHADOW_AGENT_STAGES = {"exportable-now", "shadow-only", "blocked"}
SHADOW_AGENT_ADMISSIBILITY_STATES = {"exportable-now", "shadow-only", "blocked"}


def default_shadow_agent_registry_path(root: Path | None = None) -> Path:
    return runtime_cortex_root(root) / "shadow-agent-registry.seed.v1.json"


def _required_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Expected non-empty string for {field}.")
    return value.strip()


def _optional_string(payload: dict[str, Any], field: str) -> str | None:
    value = payload.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Expected string or null for {field}.")
    stripped = value.strip()
    return stripped or None


def _string_list(payload: dict[str, Any], field: str) -> tuple[str, ...]:
    value = payload.get(field, [])
    if not isinstance(value, list):
        raise ValueError(f"Expected list for {field}.")
    ordered: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"Expected string entries in {field}.")
        stripped = item.strip()
        if not stripped or stripped in seen:
            continue
        seen.add(stripped)
        ordered.append(stripped)
    return tuple(ordered)


class ShadowAgentBlockedError(ValueError):
    pass


@dataclass(frozen=True)
class ShadowAgentRecord:
    contract_id: str
    agent_id: str
    family_name: str
    trigger: str
    purpose: str
    trigger_family: str
    stable_inputs: tuple[str, ...]
    expected_proof_artifact: str
    fallback_path: str
    fallback_behavior: str
    owner_boundary: str
    non_claim_boundary: str
    admissibility_state: str
    stage: str
    runnable: bool
    blocked_reason: str | None = None
    source_refs: tuple[str, ...] = ()

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "ShadowAgentRecord":
        stage = _required_string(payload, "stage")
        if stage not in SHADOW_AGENT_STAGES:
            raise ValueError(f"Unsupported shadow agent stage: {stage}.")
        admissibility_state = _required_string(payload, "admissibility_state")
        if admissibility_state not in SHADOW_AGENT_ADMISSIBILITY_STATES:
            raise ValueError(f"Unsupported shadow agent admissibility_state: {admissibility_state}.")
        if stage != admissibility_state:
            raise ValueError("Shadow agent stage must match admissibility_state.")
        runnable = bool(payload.get("runnable", False))
        blocked_reason = _optional_string(payload, "blocked_reason")
        if stage == "blocked":
            if runnable:
                raise ValueError("Blocked shadow agents must not be runnable.")
            if blocked_reason is None:
                raise ValueError("Blocked shadow agents must include blocked_reason.")
        return cls(
            contract_id=_required_string(payload, "contract_id"),
            agent_id=_required_string(payload, "id"),
            family_name=_required_string(payload, "family_name"),
            trigger=_required_string(payload, "trigger"),
            purpose=_required_string(payload, "purpose"),
            trigger_family=_required_string(payload, "trigger_family"),
            stable_inputs=_string_list(payload, "stable_inputs"),
            expected_proof_artifact=_required_string(payload, "expected_proof_artifact"),
            fallback_path=_required_string(payload, "fallback_path"),
            fallback_behavior=_required_string(payload, "fallback_behavior"),
            owner_boundary=_required_string(payload, "owner_boundary"),
            non_claim_boundary=_required_string(payload, "non_claim_boundary"),
            admissibility_state=admissibility_state,
            stage=stage,
            runnable=runnable,
            blocked_reason=blocked_reason,
            source_refs=_string_list(payload, "source_refs"),
        )

    @property
    def eligible_for_shadowing(self) -> bool:
        return self.admissibility_state == "shadow-only"

    @property
    def exportable_now(self) -> bool:
        return self.admissibility_state == "exportable-now"

    @property
    def blocked(self) -> bool:
        return self.admissibility_state == "blocked"

    def to_payload(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "id": self.agent_id,
            "family_name": self.family_name,
            "trigger": self.trigger,
            "purpose": self.purpose,
            "trigger_family": self.trigger_family,
            "stable_inputs": list(self.stable_inputs),
            "expected_proof_artifact": self.expected_proof_artifact,
            "fallback_path": self.fallback_path,
            "fallback_behavior": self.fallback_behavior,
            "owner_boundary": self.owner_boundary,
            "non_claim_boundary": self.non_claim_boundary,
            "admissibility_state": self.admissibility_state,
            "stage": self.stage,
            "runnable": self.runnable,
            "blocked_reason": self.blocked_reason,
            "source_refs": list(self.source_refs),
        }


@dataclass(frozen=True)
class ShadowAgentRegistry:
    source_receipts: tuple[str, ...]
    agents: tuple[ShadowAgentRecord, ...]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "ShadowAgentRegistry":
        agent_payloads = payload.get("agents", [])
        if not isinstance(agent_payloads, list):
            raise ValueError("Expected list for agents.")
        records = tuple(ShadowAgentRecord.from_payload(item) for item in agent_payloads if isinstance(item, dict))
        ids = [item.agent_id for item in records]
        if len(ids) != len(set(ids)):
            raise ValueError("Shadow agent ids must be unique.")
        return cls(
            source_receipts=_string_list(payload, "source_receipts"),
            agents=records,
        )

    @property
    def eligible_agents(self) -> tuple[ShadowAgentRecord, ...]:
        return tuple(item for item in self.agents if item.eligible_for_shadowing)

    @property
    def exportable_agents(self) -> tuple[ShadowAgentRecord, ...]:
        return tuple(item for item in self.agents if item.exportable_now)

    @property
    def blocked_agents(self) -> tuple[ShadowAgentRecord, ...]:
        return tuple(item for item in self.agents if item.blocked)

    def agent_by_id(self, agent_id: str) -> ShadowAgentRecord:
        for item in self.agents:
            if item.agent_id == agent_id:
                return item
        raise KeyError(agent_id)

    def to_payload(self) -> dict[str, Any]:
        return {
            "contract_version": SHADOW_AGENT_REGISTRY_CONTRACT_VERSION,
            "source_receipts": list(self.source_receipts),
            "agents": [item.to_payload() for item in self.agents],
        }


def load_shadow_agent_registry(
    *,
    path: Path | None = None,
    root: Path | None = None,
) -> ShadowAgentRegistry:
    payload = read_json(path or default_shadow_agent_registry_path(root))
    if payload.get("contract_version") != SHADOW_AGENT_REGISTRY_CONTRACT_VERSION:
        raise ValueError("Unexpected Cortex shadow agent registry contract version.")
    return ShadowAgentRegistry.from_payload(payload)


def resolve_shadow_agent_for_consumption(
    agent_id: str,
    *,
    path: Path | None = None,
    root: Path | None = None,
) -> ShadowAgentRecord:
    registry = load_shadow_agent_registry(path=path, root=root)
    try:
        agent = registry.agent_by_id(agent_id)
    except KeyError as exc:
        raise ValueError(f"Expected shadow agent {agent_id} in the registry.") from exc
    if not agent.eligible_for_shadowing or not agent.runnable:
        detail = f"Shadow agent {agent_id} is not eligible for consumption."
        if agent.blocked_reason:
            detail = f"{detail} {agent.blocked_reason}"
        raise ShadowAgentBlockedError(detail)
    return agent


def build_shadow_agent_registry_summary(
    *,
    path: Path | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    resolved_path = (path or default_shadow_agent_registry_path(root or atlas_root())).resolve()
    registry = load_shadow_agent_registry(path=resolved_path, root=root)
    return {
        "contract_version": SHADOW_AGENT_REGISTRY_CONTRACT_VERSION,
        "registry_path": normalize_slashes(str(resolved_path)),
        "source_receipts": list(registry.source_receipts),
        "agent_count": len(registry.agents),
        "contract_count": len(registry.agents),
        "exportable_contract_ids": [item.contract_id for item in registry.exportable_agents],
        "shadow_contract_ids": [item.contract_id for item in registry.eligible_agents],
        "blocked_contract_ids": [item.contract_id for item in registry.blocked_agents],
        "eligible_agent_ids": [item.agent_id for item in registry.eligible_agents],
        "blocked_agent_ids": [item.agent_id for item in registry.blocked_agents],
        "agents": [item.to_payload() for item in registry.agents],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the Cortex shadow-agent registry summary.")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--registry-path", type=Path)
    args = parser.parse_args(argv)

    summary = build_shadow_agent_registry_summary(
        root=args.root.resolve() if args.root is not None else None,
        path=args.registry_path.resolve() if args.registry_path is not None else None,
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
