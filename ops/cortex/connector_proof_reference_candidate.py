from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ops._atlas import atlas_relative, atlas_root, normalize_slashes, resolve_atlas_path
from ops.cortex._artifacts import stable_json_digest, write_json
from ops.cortex.connector_evidence_inventory import (
    CONNECTOR_EVIDENCE_INVENTORY_CONTRACT_VERSION,
    default_connector_evidence_latest_json_path,
)
from ops.cortex.lifeline_audit_index import (
    CortexLifelineAuditIndexSummary,
    summarize_lifeline_audit_index,
)

CONNECTOR_PROOF_REFERENCE_CANDIDATE_CONTRACT_VERSION = (
    "atlas.cortex.connector-proof-reference-candidates.v1"
)

_SOURCE_MAP = {
    "github": "github",
    "vercel": "vercel",
    "lifeline": "lifeline_audit",
    "lifeline_audit": "lifeline_audit",
    "cortex": "cortex_artifact",
    "cortex_artifact": "cortex_artifact",
}


def _require_object(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"Expected object for {field_name}.")
    return value


def _normalize_string(value: str) -> str:
    return " ".join(value.strip().split())


def _require_non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Expected non-empty string for {field_name}.")
    normalized = _normalize_string(value)
    if not normalized:
        raise ValueError(f"Expected non-empty string for {field_name}.")
    return normalized


def _optional_string(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Expected string or null for {field_name}.")
    normalized = _normalize_string(value)
    return normalized or None


def _optional_path_or_url(value: Any, field_name: str) -> str | None:
    candidate = _optional_string(value, field_name)
    if candidate is None:
        return None
    if "://" in candidate:
        return candidate
    return normalize_slashes(candidate)


def _require_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"Expected boolean for {field_name}.")
    return value


def _require_list(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"Expected list for {field_name}.")
    return value


def _require_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Expected integer for {field_name}.")
    return value


def _ordered_unique_strings(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"Expected list for {field_name}.")
    ordered: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        normalized = _require_non_empty_string(item, f"{field_name}[{index}]")
        if normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


def _run_artifact_stem(run_id: str) -> str:
    normalized = normalize_slashes(_require_non_empty_string(run_id, "run_id"))
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", normalized.replace("/", "__"))
    stem = sanitized.strip(".-")
    if not stem:
        raise ValueError("Expected run_id to produce a usable artifact filename.")
    return stem


def _render_bool(value: bool) -> str:
    return "yes" if value else "no"


def _render_list(values: tuple[str, ...]) -> str:
    return " | ".join(values) if values else "none"


def _render_counts(values: dict[str, int]) -> str:
    if not values:
        return "none"
    return " | ".join(f"{key}={values[key]}" for key in sorted(values))


def _sorted_unique_strings(*groups: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                normalize_slashes(value)
                for group in groups
                for value in group
                if isinstance(value, str) and value.strip()
            }
        )
    )


def _slug(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", normalize_slashes(value).lower())
    collapsed = re.sub(r"-{2,}", "-", sanitized).strip(".-")
    return collapsed or "candidate"


@dataclass(frozen=True)
class ConnectorProofReferenceCandidateBlocker:
    source: str
    code: str
    message: str
    reference_ids: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "source": self.source,
            "code": self.code,
            "message": self.message,
            "reference_ids": list(self.reference_ids),
        }


@dataclass(frozen=True)
class ConnectorProofReferenceCandidate:
    candidate_id: str
    source: str
    kind: str
    owner_layer: str
    claim: str
    status: str
    artifact_or_url: str | None
    observed_at: str | None
    eligible_for_proof_reference: bool
    blockers: tuple[str, ...]
    source_inventory_path: str
    source_reference_id: str
    notes: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "source": self.source,
            "kind": self.kind,
            "owner_layer": self.owner_layer,
            "claim": self.claim,
            "status": self.status,
            "artifact_or_url": self.artifact_or_url,
            "observed_at": self.observed_at,
            "eligible_for_proof_reference": self.eligible_for_proof_reference,
            "blockers": list(self.blockers),
            "source_inventory_path": self.source_inventory_path,
            "source_reference_id": self.source_reference_id,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class CortexConnectorProofReferenceCandidateSet:
    run_id: str
    owner_layer: str
    source_inventory_path: str
    source_inventory_run_id: str
    lifeline_audit_index_path: str | None
    candidate_set_blocked: bool
    candidate_set_blockers: tuple[ConnectorProofReferenceCandidateBlocker, ...]
    candidates: tuple[ConnectorProofReferenceCandidate, ...]
    source_counts: dict[str, int]
    eligible_candidate_count: int
    rule_statement: str
    pattern_statement: str
    failure_mode_statement: str

    def to_payload(self) -> dict[str, object]:
        return {
            "contract_version": CONNECTOR_PROOF_REFERENCE_CANDIDATE_CONTRACT_VERSION,
            "run_id": self.run_id,
            "owner_layer": self.owner_layer,
            "source_inventory_path": self.source_inventory_path,
            "source_inventory_run_id": self.source_inventory_run_id,
            "lifeline_audit_index_path": self.lifeline_audit_index_path,
            "candidate_set_blocked": self.candidate_set_blocked,
            "candidate_set_blockers": [
                blocker.to_payload() for blocker in self.candidate_set_blockers
            ],
            "candidate_count": len(self.candidates),
            "eligible_candidate_count": self.eligible_candidate_count,
            "source_counts": dict(sorted(self.source_counts.items())),
            "candidates": [candidate.to_payload() for candidate in self.candidates],
            "rule_statement": self.rule_statement,
            "pattern_statement": self.pattern_statement,
            "failure_mode_statement": self.failure_mode_statement,
            "lifeline_receipt_truth_owner": "lifeline",
        }


@dataclass(frozen=True)
class PersistedConnectorProofReferenceCandidateSet:
    latest_artifact_path: Path
    latest_summary_path: Path | None
    run_artifact_path: Path
    run_summary_path: Path | None
    payload_digest: str
    payload: dict[str, object]
    summary: str

    def to_payload(self, *, root: Path | None = None) -> dict[str, object]:
        base = (root or atlas_root()).resolve()
        return {
            "latest_artifact_path": atlas_relative(self.latest_artifact_path, root=base),
            "latest_summary_path": (
                atlas_relative(self.latest_summary_path, root=base)
                if self.latest_summary_path is not None
                else None
            ),
            "run_artifact_path": atlas_relative(self.run_artifact_path, root=base),
            "run_summary_path": (
                atlas_relative(self.run_summary_path, root=base)
                if self.run_summary_path is not None
                else None
            ),
            "payload_digest": self.payload_digest,
            "summary": self.summary,
        }


@dataclass(frozen=True)
class _InventoryEvidenceEntry:
    source: str
    kind: str
    reference_id: str
    claim: str
    status: str
    observed_at: str | None
    artifact_or_url: str | None
    owner_layer: str
    eligible_for_proof_reference: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class _ConnectorEvidenceInventorySnapshot:
    run_id: str
    owner_layer: str
    source_inventory_path: str
    lifeline_audit_index_path: str | None
    connector_publication_blocked: bool
    connector_publication_blockers: tuple[ConnectorProofReferenceCandidateBlocker, ...]
    evidence: tuple[_InventoryEvidenceEntry, ...]


def _resolved_candidate_dir(
    *,
    root: Path | None = None,
    connector_candidate_root: Path | None = None,
) -> Path:
    base = (root or atlas_root()).resolve()
    return (
        connector_candidate_root.resolve()
        if connector_candidate_root is not None
        else base / "runtime" / "cortex" / "connector-proof-reference-candidates"
    )


def default_connector_proof_reference_candidate_latest_json_path(
    root: Path | None = None,
    *,
    connector_candidate_root: Path | None = None,
) -> Path:
    return _resolved_candidate_dir(
        root=root,
        connector_candidate_root=connector_candidate_root,
    ) / "latest.json"


def default_connector_proof_reference_candidate_latest_summary_path(
    root: Path | None = None,
    *,
    connector_candidate_root: Path | None = None,
) -> Path:
    return _resolved_candidate_dir(
        root=root,
        connector_candidate_root=connector_candidate_root,
    ) / "latest.txt"


def default_connector_proof_reference_candidate_run_dir(
    root: Path | None = None,
    *,
    connector_candidate_root: Path | None = None,
) -> Path:
    return _resolved_candidate_dir(
        root=root,
        connector_candidate_root=connector_candidate_root,
    ) / "runs"


def default_connector_proof_reference_candidate_run_json_path(
    run_id: str,
    root: Path | None = None,
    *,
    connector_candidate_root: Path | None = None,
) -> Path:
    return default_connector_proof_reference_candidate_run_dir(
        root=root,
        connector_candidate_root=connector_candidate_root,
    ) / f"{_run_artifact_stem(run_id)}.json"


def default_connector_proof_reference_candidate_run_summary_path(
    run_id: str,
    root: Path | None = None,
    *,
    connector_candidate_root: Path | None = None,
) -> Path:
    return default_connector_proof_reference_candidate_run_dir(
        root=root,
        connector_candidate_root=connector_candidate_root,
    ) / f"{_run_artifact_stem(run_id)}.txt"


def _read_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise error
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Malformed {label} JSON at {normalize_slashes(str(path))}: {error.msg}."
        ) from error
    if not isinstance(payload, dict):
        raise ValueError(
            f"Malformed {label} JSON at {normalize_slashes(str(path))}: expected top-level object."
        )
    return payload


def _coerce_blocker(
    payload: Any,
    *,
    field_name: str,
) -> ConnectorProofReferenceCandidateBlocker:
    value = _require_object(payload, field_name)
    return ConnectorProofReferenceCandidateBlocker(
        source=_require_non_empty_string(value.get("source"), f"{field_name}.source").lower(),
        code=_require_non_empty_string(value.get("code"), f"{field_name}.code"),
        message=_require_non_empty_string(value.get("message"), f"{field_name}.message"),
        reference_ids=_ordered_unique_strings(
            value.get("reference_ids"),
            f"{field_name}.reference_ids",
        ),
    )


def _coerce_inventory_evidence_entry(
    payload: Any,
    *,
    field_name: str,
) -> _InventoryEvidenceEntry:
    value = _require_object(payload, field_name)
    source = _require_non_empty_string(value.get("source"), f"{field_name}.source").lower()
    if source not in _SOURCE_MAP:
        raise ValueError(f"Unsupported inventory evidence source {source!r} in {field_name}.")
    return _InventoryEvidenceEntry(
        source=source,
        kind=_require_non_empty_string(value.get("kind"), f"{field_name}.kind").lower(),
        reference_id=_require_non_empty_string(
            value.get("reference_id"),
            f"{field_name}.reference_id",
        ),
        claim=_require_non_empty_string(value.get("claim"), f"{field_name}.claim"),
        status=_require_non_empty_string(value.get("status"), f"{field_name}.status").lower(),
        observed_at=_optional_string(value.get("observed_at"), f"{field_name}.observed_at"),
        artifact_or_url=_optional_path_or_url(
            value.get("artifact_or_url"),
            f"{field_name}.artifact_or_url",
        ),
        owner_layer=_require_non_empty_string(
            value.get("owner_layer"),
            f"{field_name}.owner_layer",
        ).lower(),
        eligible_for_proof_reference=_require_bool(
            value.get("eligible_for_proof_reference"),
            f"{field_name}.eligible_for_proof_reference",
        ),
        blockers=_ordered_unique_strings(value.get("blockers"), f"{field_name}.blockers"),
    )


def _load_inventory_snapshot(
    connector_inventory_path: str | Path | None,
    *,
    root: Path,
) -> _ConnectorEvidenceInventorySnapshot:
    resolved_path = (
        default_connector_evidence_latest_json_path(root)
        if connector_inventory_path is None
        else resolve_atlas_path(connector_inventory_path, root=root)
    )
    if not resolved_path.exists():
        raise FileNotFoundError(
            f"Connector evidence inventory not found at {normalize_slashes(str(resolved_path))}."
        )
    payload = _read_json_object(resolved_path, label="connector evidence inventory")
    contract_version = _require_non_empty_string(
        payload.get("contract_version"),
        "contract_version",
    )
    if contract_version != CONNECTOR_EVIDENCE_INVENTORY_CONTRACT_VERSION:
        raise ValueError(
            "Malformed connector evidence inventory JSON at "
            f"{normalize_slashes(str(resolved_path))}: expected contract_version "
            f"{CONNECTOR_EVIDENCE_INVENTORY_CONTRACT_VERSION}."
        )
    _require_bool(payload.get("inventory_only"), "inventory_only")
    _require_bool(
        payload.get("connector_observations_are_final_proof_references"),
        "connector_observations_are_final_proof_references",
    )
    evidence_payload = _require_list(payload.get("evidence"), "evidence")
    evidence = tuple(
        _coerce_inventory_evidence_entry(item, field_name=f"evidence[{index}]")
        for index, item in enumerate(evidence_payload)
    )
    evidence_count = _require_int(payload.get("evidence_count"), "evidence_count")
    if evidence_count != len(evidence):
        raise ValueError(
            "Malformed connector evidence inventory JSON at "
            f"{normalize_slashes(str(resolved_path))}: evidence_count must match evidence length."
        )
    blockers_payload = _require_list(
        payload.get("connector_publication_blockers"),
        "connector_publication_blockers",
    )
    blockers = tuple(
        _coerce_blocker(item, field_name=f"connector_publication_blockers[{index}]")
        for index, item in enumerate(blockers_payload)
    )
    return _ConnectorEvidenceInventorySnapshot(
        run_id=_require_non_empty_string(payload.get("run_id"), "run_id"),
        owner_layer=_require_non_empty_string(payload.get("owner_layer"), "owner_layer").lower(),
        source_inventory_path=normalize_slashes(atlas_relative(resolved_path, root=root)),
        lifeline_audit_index_path=_optional_path_or_url(
            payload.get("lifeline_audit_index_path"),
            "lifeline_audit_index_path",
        ),
        connector_publication_blocked=_require_bool(
            payload.get("connector_publication_blocked"),
            "connector_publication_blocked",
        ),
        connector_publication_blockers=blockers,
        evidence=evidence,
    )


def _blockers_from_lifeline_summary(
    summary: CortexLifelineAuditIndexSummary,
) -> tuple[ConnectorProofReferenceCandidateBlocker, ...]:
    return tuple(
        ConnectorProofReferenceCandidateBlocker(
            source="lifeline",
            code=blocker.code,
            message=blocker.message,
            reference_ids=blocker.receipt_paths,
        )
        for blocker in summary.connector_publication_blockers
    )


def _load_optional_lifeline_summary(
    *,
    explicit_lifeline_audit_index_path: str | Path | None,
    inventory_lifeline_audit_index_path: str | None,
    root: Path,
) -> CortexLifelineAuditIndexSummary | None:
    if explicit_lifeline_audit_index_path is not None:
        return summarize_lifeline_audit_index(explicit_lifeline_audit_index_path, root=root)
    if inventory_lifeline_audit_index_path is None:
        return None
    resolved_path = resolve_atlas_path(inventory_lifeline_audit_index_path, root=root)
    if not resolved_path.exists():
        return None
    return summarize_lifeline_audit_index(resolved_path, root=root)


def _merge_blockers(
    *groups: tuple[ConnectorProofReferenceCandidateBlocker, ...],
) -> tuple[ConnectorProofReferenceCandidateBlocker, ...]:
    merged: dict[str, ConnectorProofReferenceCandidateBlocker] = {}
    for group in groups:
        for blocker in group:
            existing = merged.get(blocker.code)
            if existing is None:
                merged[blocker.code] = blocker
                continue
            merged[blocker.code] = ConnectorProofReferenceCandidateBlocker(
                source=existing.source,
                code=existing.code,
                message=existing.message,
                reference_ids=_sorted_unique_strings(
                    existing.reference_ids,
                    blocker.reference_ids,
                ),
            )
    return tuple(merged[key] for key in sorted(merged))


def _candidate_sort_key(
    candidate: ConnectorProofReferenceCandidate,
) -> tuple[str, ...]:
    return (
        candidate.source,
        candidate.kind,
        candidate.source_reference_id,
        candidate.artifact_or_url or "",
        candidate.status,
        candidate.claim,
        candidate.owner_layer,
        candidate.observed_at or "",
    )


def _source_counts(
    candidates: tuple[ConnectorProofReferenceCandidate, ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for candidate in candidates:
        counts[candidate.source] = counts.get(candidate.source, 0) + 1
    return dict(sorted(counts.items()))


def _candidate_notes(
    *,
    source: str,
    source_reference_id: str,
    global_blockers: tuple[str, ...],
    local_blockers: tuple[str, ...],
    has_locator: bool,
) -> tuple[str, ...]:
    notes: list[str] = [
        f"Derived from connector evidence inventory reference {source_reference_id}.",
        "Candidate generation is read-only and does not publish proof references or mutate Lifeline receipts.",
    ]
    if source in {"github", "vercel"}:
        notes.append(
            "Connector evidence remains an observed surface only until later gated proof-reference pack integration."
        )
    if source == "cortex_artifact":
        notes.append(
            "Cortex-owned artifact evidence stays separate from proof-reference pack mutation in this lane."
        )
    if source == "lifeline_audit":
        notes.append(
            "Lifeline audit-index evidence is blocker-carrying receipt truth and is never treated as a final proof reference here."
        )
    if global_blockers:
        notes.append(
            "Global connector-publication blockers are active: "
            + ", ".join(global_blockers)
            + "."
        )
    if local_blockers:
        notes.append(
            "Candidate-local blockers are active: " + ", ".join(local_blockers) + "."
        )
    if not has_locator:
        notes.append("Candidate is missing an artifact_or_url locator.")
    return tuple(notes)


def _build_candidate(
    entry: _InventoryEvidenceEntry,
    *,
    source_inventory_path: str,
    global_blockers: tuple[str, ...],
) -> ConnectorProofReferenceCandidate:
    source = _SOURCE_MAP[entry.source]
    candidate_id = (
        f"{_slug(source)}--{_slug(entry.kind)}--{_slug(entry.reference_id)}"
    )
    blockers = _sorted_unique_strings(
        global_blockers,
        entry.blockers,
        ("missing_artifact_or_url",) if entry.artifact_or_url is None else (),
    )
    eligible_for_proof_reference = entry.eligible_for_proof_reference and not blockers
    return ConnectorProofReferenceCandidate(
        candidate_id=candidate_id,
        source=source,
        kind=entry.kind,
        owner_layer=entry.owner_layer,
        claim=entry.claim,
        status=entry.status,
        artifact_or_url=entry.artifact_or_url,
        observed_at=entry.observed_at,
        eligible_for_proof_reference=eligible_for_proof_reference,
        blockers=blockers,
        source_inventory_path=source_inventory_path,
        source_reference_id=entry.reference_id,
        notes=_candidate_notes(
            source=source,
            source_reference_id=entry.reference_id,
            global_blockers=global_blockers,
            local_blockers=entry.blockers,
            has_locator=entry.artifact_or_url is not None,
        ),
    )


def _dedupe_candidates(
    candidates: tuple[ConnectorProofReferenceCandidate, ...],
) -> tuple[ConnectorProofReferenceCandidate, ...]:
    ordered: list[ConnectorProofReferenceCandidate] = []
    seen: set[str] = set()
    for candidate in sorted(candidates, key=_candidate_sort_key):
        if candidate.candidate_id in seen:
            raise ValueError(
                "Expected unique candidate_id values in connector proof-reference candidate set."
            )
        seen.add(candidate.candidate_id)
        ordered.append(candidate)
    return tuple(ordered)


def build_connector_proof_reference_candidates(
    connector_inventory_path: str | Path | None = None,
    *,
    lifeline_audit_index_path: str | Path | None = None,
    root: Path | None = None,
) -> CortexConnectorProofReferenceCandidateSet:
    base = (root or atlas_root()).resolve()
    inventory = _load_inventory_snapshot(connector_inventory_path, root=base)
    lifeline_summary = _load_optional_lifeline_summary(
        explicit_lifeline_audit_index_path=lifeline_audit_index_path,
        inventory_lifeline_audit_index_path=inventory.lifeline_audit_index_path,
        root=base,
    )

    merged_blockers = _merge_blockers(
        inventory.connector_publication_blockers,
        _blockers_from_lifeline_summary(lifeline_summary) if lifeline_summary is not None else (),
    )
    if inventory.connector_publication_blocked and not merged_blockers:
        merged_blockers = (
            ConnectorProofReferenceCandidateBlocker(
                source="inventory",
                code="connector_publication_blocked",
                message=(
                    "Connector evidence inventory reported a global publication block without enumerated details."
                ),
                reference_ids=(),
            ),
        )

    global_blocker_codes = tuple(blocker.code for blocker in merged_blockers)
    candidates = _dedupe_candidates(
        tuple(
            _build_candidate(
                entry,
                source_inventory_path=inventory.source_inventory_path,
                global_blockers=global_blocker_codes,
            )
            for entry in inventory.evidence
        )
    )
    return CortexConnectorProofReferenceCandidateSet(
        run_id=inventory.run_id,
        owner_layer="cortex",
        source_inventory_path=inventory.source_inventory_path,
        source_inventory_run_id=inventory.run_id,
        lifeline_audit_index_path=(
            lifeline_summary.lifeline_audit_index_path
            if lifeline_summary is not None
            else inventory.lifeline_audit_index_path
        ),
        candidate_set_blocked=bool(merged_blockers),
        candidate_set_blockers=merged_blockers,
        candidates=candidates,
        source_counts=_source_counts(candidates),
        eligible_candidate_count=sum(
            1 for candidate in candidates if candidate.eligible_for_proof_reference
        ),
        rule_statement=(
            "Cortex may build connector-backed proof-reference candidates, but candidates are not final proof references, Lifeline receipts, or published evidence."
        ),
        pattern_statement=(
            "Connector inventory becomes proof-reference candidates only after audit blockers and validation posture are clean."
        ),
        failure_mode_statement=(
            "Do not let candidate generation mutate proof-reference packs, publish connector evidence, or bypass Lifeline receipt ownership."
        ),
    )


def render_connector_proof_reference_candidate_summary(
    candidate_set: CortexConnectorProofReferenceCandidateSet,
) -> str:
    lines = [
        "Cortex Connector Proof Reference Candidate Set",
        f"- Run id: {candidate_set.run_id}",
        f"- Owner layer: {candidate_set.owner_layer}",
        f"- Source inventory path: {candidate_set.source_inventory_path}",
        f"- Source inventory run id: {candidate_set.source_inventory_run_id}",
        f"- Lifeline audit index path: {candidate_set.lifeline_audit_index_path or 'none'}",
        f"- Candidate set blocked: {_render_bool(candidate_set.candidate_set_blocked)}",
        (
            "- Candidate set blockers: "
            f"{_render_list(tuple(blocker.code for blocker in candidate_set.candidate_set_blockers))}"
        ),
        f"- Candidate count: {len(candidate_set.candidates)}",
        f"- Eligible candidate count: {candidate_set.eligible_candidate_count}",
        f"- Source counts: {_render_counts(candidate_set.source_counts)}",
        f"- Rule: {candidate_set.rule_statement}",
        f"- Pattern: {candidate_set.pattern_statement}",
        f"- Failure mode: {candidate_set.failure_mode_statement}",
    ]
    return "\n".join(lines) + "\n"


def _write_summary(path: Path, summary: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(summary, encoding="utf-8")


class CortexConnectorProofReferenceCandidateWriter:
    def write(
        self,
        connector_inventory_path: str | Path | None = None,
        *,
        lifeline_audit_index_path: str | Path | None = None,
        root: Path | None = None,
        connector_candidate_root: Path | None = None,
        latest_json_path: Path | None = None,
        latest_summary_path: Path | None = None,
        run_json_path: Path | None = None,
        run_summary_path: Path | None = None,
        write_summary: bool = True,
    ) -> PersistedConnectorProofReferenceCandidateSet:
        base = (root or atlas_root()).resolve()
        output_root = _resolved_candidate_dir(
            root=base,
            connector_candidate_root=connector_candidate_root,
        )
        candidate_set = build_connector_proof_reference_candidates(
            connector_inventory_path,
            lifeline_audit_index_path=lifeline_audit_index_path,
            root=base,
        )
        payload = candidate_set.to_payload()
        summary = render_connector_proof_reference_candidate_summary(candidate_set)

        resolved_latest_json_path = (
            latest_json_path.resolve()
            if latest_json_path is not None
            else default_connector_proof_reference_candidate_latest_json_path(
                base,
                connector_candidate_root=output_root,
            )
        )
        resolved_run_json_path = (
            run_json_path.resolve()
            if run_json_path is not None
            else default_connector_proof_reference_candidate_run_json_path(
                candidate_set.run_id,
                base,
                connector_candidate_root=output_root,
            )
        )
        resolved_latest_summary_path = None
        resolved_run_summary_path = None
        if write_summary:
            resolved_latest_summary_path = (
                latest_summary_path.resolve()
                if latest_summary_path is not None
                else default_connector_proof_reference_candidate_latest_summary_path(
                    base,
                    connector_candidate_root=output_root,
                )
            )
            resolved_run_summary_path = (
                run_summary_path.resolve()
                if run_summary_path is not None
                else default_connector_proof_reference_candidate_run_summary_path(
                    candidate_set.run_id,
                    base,
                    connector_candidate_root=output_root,
                )
            )

        write_json(resolved_latest_json_path, payload)
        write_json(resolved_run_json_path, payload)
        if resolved_latest_summary_path is not None:
            _write_summary(resolved_latest_summary_path, summary)
        if resolved_run_summary_path is not None:
            _write_summary(resolved_run_summary_path, summary)

        return PersistedConnectorProofReferenceCandidateSet(
            latest_artifact_path=resolved_latest_json_path,
            latest_summary_path=resolved_latest_summary_path,
            run_artifact_path=resolved_run_json_path,
            run_summary_path=resolved_run_summary_path,
            payload_digest=stable_json_digest(payload),
            payload=payload,
            summary=summary,
        )


def write_connector_proof_reference_candidates(
    connector_inventory_path: str | Path | None = None,
    *,
    lifeline_audit_index_path: str | Path | None = None,
    root: Path | None = None,
    connector_candidate_root: Path | None = None,
    latest_json_path: Path | None = None,
    latest_summary_path: Path | None = None,
    run_json_path: Path | None = None,
    run_summary_path: Path | None = None,
    write_summary: bool = True,
) -> PersistedConnectorProofReferenceCandidateSet:
    return CortexConnectorProofReferenceCandidateWriter().write(
        connector_inventory_path,
        lifeline_audit_index_path=lifeline_audit_index_path,
        root=root,
        connector_candidate_root=connector_candidate_root,
        latest_json_path=latest_json_path,
        latest_summary_path=latest_summary_path,
        run_json_path=run_json_path,
        run_summary_path=run_summary_path,
        write_summary=write_summary,
    )
