from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ops._atlas import atlas_relative, atlas_root, normalize_slashes, resolve_atlas_path
from ops.cortex._artifacts import read_json, stable_json_digest, write_json
from ops.cortex.lifeline_audit_index import (
    CortexLifelineAuditIndexSummary,
    default_lifeline_audit_index_path,
    summarize_lifeline_audit_index,
)
from ops.cortex.proof_reference_pack import default_proof_reference_pack_latest_json_path

CONNECTOR_EVIDENCE_INVENTORY_CONTRACT_VERSION = (
    "atlas.cortex.connector-evidence-inventory.v1"
)


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


@dataclass(frozen=True)
class ConnectorPublicationBlocker:
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
class ConnectorEvidenceCandidate:
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

    def to_payload(self) -> dict[str, object]:
        return {
            "source": self.source,
            "kind": self.kind,
            "reference_id": self.reference_id,
            "claim": self.claim,
            "status": self.status,
            "observed_at": self.observed_at,
            "artifact_or_url": self.artifact_or_url,
            "owner_layer": self.owner_layer,
            "eligible_for_proof_reference": self.eligible_for_proof_reference,
            "blockers": list(self.blockers),
        }


@dataclass(frozen=True)
class CortexConnectorEvidenceInventory:
    run_id: str
    owner_layer: str
    inventory_only: bool
    connector_observations_are_final_proof_references: bool
    connector_publication_blocked: bool
    connector_publication_blockers: tuple[ConnectorPublicationBlocker, ...]
    lifeline_audit_index_path: str | None
    proof_reference_pack_path: str | None
    evidence: tuple[ConnectorEvidenceCandidate, ...]
    source_counts: dict[str, int]
    eligible_candidate_count: int
    rule_statement: str
    pattern_statement: str
    failure_mode_statement: str

    def to_payload(self) -> dict[str, object]:
        return {
            "contract_version": CONNECTOR_EVIDENCE_INVENTORY_CONTRACT_VERSION,
            "run_id": self.run_id,
            "owner_layer": self.owner_layer,
            "inventory_only": self.inventory_only,
            "connector_observations_are_final_proof_references": self.connector_observations_are_final_proof_references,
            "connector_publication_blocked": self.connector_publication_blocked,
            "connector_publication_blockers": [
                blocker.to_payload() for blocker in self.connector_publication_blockers
            ],
            "lifeline_audit_index_path": self.lifeline_audit_index_path,
            "proof_reference_pack_path": self.proof_reference_pack_path,
            "evidence_count": len(self.evidence),
            "source_counts": dict(sorted(self.source_counts.items())),
            "eligible_candidate_count": self.eligible_candidate_count,
            "evidence": [candidate.to_payload() for candidate in self.evidence],
            "rule_statement": self.rule_statement,
            "pattern_statement": self.pattern_statement,
            "failure_mode_statement": self.failure_mode_statement,
            "lifeline_receipt_truth_owner": "lifeline",
        }


@dataclass(frozen=True)
class PersistedConnectorEvidenceInventory:
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


def _resolved_connector_evidence_dir(
    *,
    root: Path | None = None,
    connector_evidence_root: Path | None = None,
) -> Path:
    base = (root or atlas_root()).resolve()
    return (
        connector_evidence_root.resolve()
        if connector_evidence_root is not None
        else base / "runtime" / "cortex" / "connector-evidence"
    )


def default_connector_evidence_latest_json_path(
    root: Path | None = None,
    *,
    connector_evidence_root: Path | None = None,
) -> Path:
    return _resolved_connector_evidence_dir(
        root=root,
        connector_evidence_root=connector_evidence_root,
    ) / "latest.json"


def default_connector_evidence_latest_summary_path(
    root: Path | None = None,
    *,
    connector_evidence_root: Path | None = None,
) -> Path:
    return _resolved_connector_evidence_dir(
        root=root,
        connector_evidence_root=connector_evidence_root,
    ) / "latest.txt"


def default_connector_evidence_run_dir(
    root: Path | None = None,
    *,
    connector_evidence_root: Path | None = None,
) -> Path:
    return _resolved_connector_evidence_dir(
        root=root,
        connector_evidence_root=connector_evidence_root,
    ) / "runs"


def default_connector_evidence_run_json_path(
    run_id: str,
    root: Path | None = None,
    *,
    connector_evidence_root: Path | None = None,
) -> Path:
    return default_connector_evidence_run_dir(
        root=root,
        connector_evidence_root=connector_evidence_root,
    ) / f"{_run_artifact_stem(run_id)}.json"


def default_connector_evidence_run_summary_path(
    run_id: str,
    root: Path | None = None,
    *,
    connector_evidence_root: Path | None = None,
) -> Path:
    return default_connector_evidence_run_dir(
        root=root,
        connector_evidence_root=connector_evidence_root,
    ) / f"{_run_artifact_stem(run_id)}.txt"


def _candidate_sort_key(candidate: ConnectorEvidenceCandidate) -> tuple[str, ...]:
    return (
        candidate.source,
        candidate.kind,
        candidate.reference_id,
        candidate.artifact_or_url or "",
        candidate.status,
        candidate.claim,
        candidate.owner_layer,
        candidate.observed_at or "",
    )


def _sorted_unique_blockers(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if value}))


def _eligible_for_candidate(*, base_status: str, blockers: tuple[str, ...]) -> bool:
    return base_status not in {"blocked", "failed", "invalid", "error"} and not blockers


def _candidate(
    *,
    source: str,
    kind: str,
    reference_id: str,
    claim: str,
    status: str,
    observed_at: str | None,
    artifact_or_url: str | None,
    owner_layer: str,
    blockers: tuple[str, ...] = (),
    eligible_for_proof_reference: bool | None = None,
) -> ConnectorEvidenceCandidate:
    normalized_status = _require_non_empty_string(status, "status").lower()
    normalized_blockers = _sorted_unique_blockers(blockers)
    eligible = (
        _eligible_for_candidate(base_status=normalized_status, blockers=normalized_blockers)
        if eligible_for_proof_reference is None
        else _require_bool(eligible_for_proof_reference, "eligible_for_proof_reference")
    )
    return ConnectorEvidenceCandidate(
        source=_require_non_empty_string(source, "source").lower(),
        kind=_require_non_empty_string(kind, "kind").lower(),
        reference_id=_require_non_empty_string(reference_id, "reference_id"),
        claim=_require_non_empty_string(claim, "claim"),
        status=normalized_status,
        observed_at=_optional_string(observed_at, "observed_at"),
        artifact_or_url=_optional_path_or_url(artifact_or_url, "artifact_or_url"),
        owner_layer=_require_non_empty_string(owner_layer, "owner_layer").lower(),
        eligible_for_proof_reference=eligible,
        blockers=normalized_blockers,
    )


def _global_connector_blocker_codes(
    blockers: tuple[ConnectorPublicationBlocker, ...],
) -> tuple[str, ...]:
    return tuple(blocker.code for blocker in blockers)


def _coerce_named_items(
    payload: dict[str, Any],
    *,
    singular_name: str,
    plural_name: str,
    field_prefix: str,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    singular = payload.get(singular_name)
    if singular is not None:
        items.append(_require_object(singular, f"{field_prefix}.{singular_name}"))
    plural = payload.get(plural_name)
    if plural is not None:
        items.extend(
            _require_object(item, f"{field_prefix}.{plural_name}[{index}]")
            for index, item in enumerate(_require_list(plural, f"{field_prefix}.{plural_name}"))
        )
    return items


def _build_github_candidates(
    payload: dict[str, Any],
    *,
    global_blockers: tuple[str, ...],
) -> tuple[ConnectorEvidenceCandidate, ...]:
    evidence = _require_object(payload, "github_evidence")
    default_observed_at = _optional_string(
        evidence.get("observed_at"),
        "github_evidence.observed_at",
    )
    candidates: list[ConnectorEvidenceCandidate] = []

    for item in _coerce_named_items(
        evidence,
        singular_name="pull_request",
        plural_name="pull_requests",
        field_prefix="github_evidence",
    ):
        number = item.get("number")
        if isinstance(number, bool) or not isinstance(number, int):
            raise ValueError("Expected integer for github_evidence.pull_request.number.")
        url = _optional_path_or_url(item.get("url"), "github_evidence.pull_request.url")
        head_sha = _optional_string(item.get("head_sha"), "github_evidence.pull_request.head_sha")
        claim = (
            "GitHub pull request metadata records a read-only review surface and observed head "
            "SHA for a future proof-reference candidate."
        )
        if head_sha is not None:
            claim = f"{claim} Observed head SHA={head_sha}."
        candidates.append(
            _candidate(
                source="github",
                kind="pull_request",
                reference_id=f"github-pr-{number}",
                claim=claim,
                status=_optional_string(item.get("status"), "github_evidence.pull_request.status")
                or "observed",
                observed_at=_optional_string(
                    item.get("observed_at"),
                    "github_evidence.pull_request.observed_at",
                )
                or default_observed_at,
                artifact_or_url=url,
                owner_layer="github",
                blockers=global_blockers,
            )
        )

    for item in _coerce_named_items(
        evidence,
        singular_name="workflow_run",
        plural_name="workflow_runs",
        field_prefix="github_evidence",
    ):
        run_id = item.get("run_id")
        if isinstance(run_id, bool) or not isinstance(run_id, int):
            raise ValueError("Expected integer for github_evidence.workflow_run.run_id.")
        workflow_name = _optional_string(
            item.get("workflow"),
            "github_evidence.workflow_run.workflow",
        )
        status = _optional_string(item.get("status"), "github_evidence.workflow_run.status")
        conclusion = _optional_string(
            item.get("conclusion"),
            "github_evidence.workflow_run.conclusion",
        )
        normalized_status = (conclusion or status or "observed").lower()
        item_blockers = list(global_blockers)
        if normalized_status in {"failure", "failed", "timed_out", "cancelled", "error"}:
            item_blockers.append("workflow_run_not_successful")
        claim = (
            "GitHub workflow run metadata records a read-only CI evidence surface for a "
            "future proof-reference candidate."
        )
        if workflow_name is not None:
            claim = f"{claim} Workflow={workflow_name}."
        candidates.append(
            _candidate(
                source="github",
                kind="workflow_run",
                reference_id=f"github-workflow-run-{run_id}",
                claim=claim,
                status=normalized_status,
                observed_at=_optional_string(
                    item.get("observed_at"),
                    "github_evidence.workflow_run.observed_at",
                )
                or default_observed_at,
                artifact_or_url=_optional_path_or_url(
                    item.get("url"),
                    "github_evidence.workflow_run.url",
                ),
                owner_layer="github",
                blockers=tuple(item_blockers),
            )
        )

    for item in _coerce_named_items(
        evidence,
        singular_name="commit",
        plural_name="commits",
        field_prefix="github_evidence",
    ):
        sha = _require_non_empty_string(item.get("sha"), "github_evidence.commit.sha")
        candidates.append(
            _candidate(
                source="github",
                kind="commit",
                reference_id=f"github-commit-{sha[:12]}",
                claim=(
                    "GitHub commit metadata records an observed head SHA for a future "
                    "proof-reference candidate."
                ),
                status=_optional_string(item.get("status"), "github_evidence.commit.status")
                or "observed",
                observed_at=_optional_string(
                    item.get("observed_at"),
                    "github_evidence.commit.observed_at",
                )
                or default_observed_at,
                artifact_or_url=_optional_path_or_url(
                    item.get("url"),
                    "github_evidence.commit.url",
                ),
                owner_layer="github",
                blockers=global_blockers,
            )
        )

    return tuple(sorted(candidates, key=_candidate_sort_key))


def _build_vercel_candidates(
    payload: dict[str, Any],
    *,
    global_blockers: tuple[str, ...],
) -> tuple[ConnectorEvidenceCandidate, ...]:
    evidence = _require_object(payload, "vercel_evidence")
    default_observed_at = _optional_string(
        evidence.get("observed_at"),
        "vercel_evidence.observed_at",
    )
    candidates: list[ConnectorEvidenceCandidate] = []

    project = evidence.get("project")
    if project is not None:
        item = _require_object(project, "vercel_evidence.project")
        project_id = _require_non_empty_string(item.get("id"), "vercel_evidence.project.id")
        project_name = _optional_string(item.get("name"), "vercel_evidence.project.name")
        claim = (
            "Vercel project metadata records a read-only deployment surface for a future "
            "proof-reference candidate."
        )
        if project_name is not None:
            claim = f"{claim} Project={project_name}."
        candidates.append(
            _candidate(
                source="vercel",
                kind="project",
                reference_id=f"vercel-project-{project_id}",
                claim=claim,
                status=_optional_string(item.get("status"), "vercel_evidence.project.status")
                or "observed",
                observed_at=_optional_string(
                    item.get("observed_at"),
                    "vercel_evidence.project.observed_at",
                )
                or default_observed_at,
                artifact_or_url=_optional_path_or_url(
                    item.get("url"),
                    "vercel_evidence.project.url",
                ),
                owner_layer="vercel",
                blockers=global_blockers,
            )
        )

    deployment = evidence.get("deployment")
    if deployment is not None:
        item = _require_object(deployment, "vercel_evidence.deployment")
        deployment_id = _require_non_empty_string(
            item.get("id"),
            "vercel_evidence.deployment.id",
        )
        state = (
            _optional_string(item.get("status"), "vercel_evidence.deployment.status")
            or _optional_string(item.get("state"), "vercel_evidence.deployment.state")
            or "observed"
        ).lower()
        item_blockers = list(global_blockers)
        if state not in {"ready", "success", "succeeded", "observed"}:
            item_blockers.append("deployment_not_ready")
        commit_sha = _optional_string(
            item.get("commit_sha"),
            "vercel_evidence.deployment.commit_sha",
        )
        claim = (
            "Vercel deployment metadata records a read-only deployment outcome for a future "
            "proof-reference candidate."
        )
        if commit_sha is not None:
            claim = f"{claim} Observed commit SHA={commit_sha}."
        candidates.append(
            _candidate(
                source="vercel",
                kind="deployment",
                reference_id=f"vercel-deployment-{deployment_id}",
                claim=claim,
                status=state,
                observed_at=_optional_string(
                    item.get("observed_at"),
                    "vercel_evidence.deployment.observed_at",
                )
                or default_observed_at,
                artifact_or_url=_optional_path_or_url(
                    item.get("url"),
                    "vercel_evidence.deployment.url",
                ),
                owner_layer="vercel",
                blockers=tuple(item_blockers),
            )
        )

    return tuple(sorted(candidates, key=_candidate_sort_key))


def _lifeline_blockers(
    summary: CortexLifelineAuditIndexSummary,
) -> tuple[ConnectorPublicationBlocker, ...]:
    return tuple(
        ConnectorPublicationBlocker(
            source="lifeline",
            code=blocker.code,
            message=blocker.message,
            reference_ids=blocker.receipt_paths,
        )
        for blocker in summary.connector_publication_blockers
    )


def _audit_summary_candidate(
    summary: CortexLifelineAuditIndexSummary,
) -> ConnectorEvidenceCandidate:
    blocker_codes = tuple(blocker.code for blocker in summary.connector_publication_blockers)
    return _candidate(
        source="lifeline",
        kind="audit_index_summary",
        reference_id="lifeline-audit-index-summary",
        claim=(
            "Lifeline audit-index summary is read-only receipt truth and can block "
            "connector-backed publication without mutating Lifeline."
        ),
        status="blocked" if blocker_codes else "observed",
        observed_at=None,
        artifact_or_url=summary.lifeline_audit_index_path,
        owner_layer="lifeline",
        blockers=blocker_codes,
        eligible_for_proof_reference=False,
    )


def _load_optional_lifeline_summary(
    lifeline_audit_index_path: str | Path | None,
    *,
    root: Path,
) -> CortexLifelineAuditIndexSummary | None:
    if lifeline_audit_index_path is None:
        default_path = default_lifeline_audit_index_path(root)
        if not default_path.exists():
            return None
        return summarize_lifeline_audit_index(default_path, root=root)
    return summarize_lifeline_audit_index(lifeline_audit_index_path, root=root)


def _load_optional_proof_reference_pack_payload(
    proof_reference_pack_path: str | Path | None,
    *,
    root: Path,
) -> tuple[dict[str, Any], Path] | None:
    candidate = (
        resolve_atlas_path(proof_reference_pack_path, root=root)
        if proof_reference_pack_path is not None
        else default_proof_reference_pack_latest_json_path(root)
    )
    if not candidate.exists():
        if proof_reference_pack_path is None:
            return None
        raise FileNotFoundError(
            f"Cortex proof reference pack not found at {normalize_slashes(str(candidate))}."
        )
    payload = read_json(candidate)
    _require_list(payload.get("references"), "proof_reference_pack.references")
    return payload, candidate


def _proof_reference_candidates(
    payload: dict[str, Any],
    *,
    global_blockers: tuple[str, ...],
) -> tuple[ConnectorEvidenceCandidate, ...]:
    references = _require_list(payload.get("references"), "proof_reference_pack.references")
    candidates: list[ConnectorEvidenceCandidate] = []
    for index, item in enumerate(references):
        reference = _require_object(item, f"proof_reference_pack.references[{index}]")
        candidates.append(
            _candidate(
                source="cortex",
                kind=_require_non_empty_string(
                    reference.get("kind"),
                    f"proof_reference_pack.references[{index}].kind",
                ),
                reference_id=_require_non_empty_string(
                    reference.get("reference_id"),
                    f"proof_reference_pack.references[{index}].reference_id",
                ),
                claim=_require_non_empty_string(
                    reference.get("claim"),
                    f"proof_reference_pack.references[{index}].claim",
                ),
                status=_require_non_empty_string(
                    reference.get("status"),
                    f"proof_reference_pack.references[{index}].status",
                ),
                observed_at=None,
                artifact_or_url=_optional_path_or_url(
                    reference.get("artifact_path") or reference.get("command"),
                    f"proof_reference_pack.references[{index}] artifact",
                ),
                owner_layer=_require_non_empty_string(
                    reference.get("owner_layer"),
                    f"proof_reference_pack.references[{index}].owner_layer",
                ),
                blockers=global_blockers,
            )
        )
    return tuple(sorted(candidates, key=_candidate_sort_key))


def _source_counts(evidence: tuple[ConnectorEvidenceCandidate, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in evidence:
        counts[item.source] = counts.get(item.source, 0) + 1
    return dict(sorted(counts.items()))


def _dedupe_candidates(
    candidates: tuple[ConnectorEvidenceCandidate, ...],
) -> tuple[ConnectorEvidenceCandidate, ...]:
    ordered: list[ConnectorEvidenceCandidate] = []
    seen: set[tuple[str, str, str]] = set()
    for candidate in sorted(candidates, key=_candidate_sort_key):
        key = (candidate.source, candidate.kind, candidate.reference_id)
        if key in seen:
            raise ValueError(
                "Expected unique source/kind/reference_id combinations in connector evidence inventory."
            )
        seen.add(key)
        ordered.append(candidate)
    return tuple(ordered)


def build_connector_evidence_inventory(
    *,
    github_evidence: dict[str, Any] | None = None,
    vercel_evidence: dict[str, Any] | None = None,
    lifeline_audit_index_path: str | Path | None = None,
    proof_reference_pack_path: str | Path | None = None,
    run_id: str | None = None,
    root: Path | None = None,
) -> CortexConnectorEvidenceInventory:
    base = (root or atlas_root()).resolve()
    lifeline_summary = _load_optional_lifeline_summary(
        lifeline_audit_index_path,
        root=base,
    )
    publication_blockers = (
        _lifeline_blockers(lifeline_summary) if lifeline_summary is not None else ()
    )
    global_connector_blockers = _global_connector_blocker_codes(publication_blockers)

    evidence: list[ConnectorEvidenceCandidate] = []
    if lifeline_summary is not None:
        evidence.append(_audit_summary_candidate(lifeline_summary))
    if github_evidence is not None:
        evidence.extend(
            _build_github_candidates(
                github_evidence,
                global_blockers=global_connector_blockers,
            )
        )
    if vercel_evidence is not None:
        evidence.extend(
            _build_vercel_candidates(
                vercel_evidence,
                global_blockers=global_connector_blockers,
            )
        )

    proof_reference_pack_path_display: str | None = None
    proof_reference_run_id: str | None = None
    proof_reference_pack = _load_optional_proof_reference_pack_payload(
        proof_reference_pack_path,
        root=base,
    )
    if proof_reference_pack is not None:
        proof_reference_payload, proof_reference_path = proof_reference_pack
        proof_reference_pack_path_display = atlas_relative(proof_reference_path, root=base)
        proof_reference_run_id = _optional_string(
            proof_reference_payload.get("run_id"),
            "proof_reference_pack.run_id",
        )
        evidence.extend(
            _proof_reference_candidates(
                proof_reference_payload,
                global_blockers=global_connector_blockers,
            )
        )

    normalized_evidence = _dedupe_candidates(tuple(evidence))
    resolved_run_id = run_id or proof_reference_run_id or "connector-evidence.latest"

    return CortexConnectorEvidenceInventory(
        run_id=_require_non_empty_string(resolved_run_id, "run_id"),
        owner_layer="cortex",
        inventory_only=True,
        connector_observations_are_final_proof_references=False,
        connector_publication_blocked=bool(publication_blockers),
        connector_publication_blockers=publication_blockers,
        lifeline_audit_index_path=(
            lifeline_summary.lifeline_audit_index_path if lifeline_summary is not None else None
        ),
        proof_reference_pack_path=proof_reference_pack_path_display,
        evidence=normalized_evidence,
        source_counts=_source_counts(normalized_evidence),
        eligible_candidate_count=sum(
            1 for item in normalized_evidence if item.eligible_for_proof_reference
        ),
        rule_statement=(
            "Cortex may inventory connector-backed evidence candidates, but connector "
            "observations are not final proof references or Lifeline receipts."
        ),
        pattern_statement=(
            "After Cortex can read Lifeline audit truth, inventory read-only connector "
            "surfaces before building any connector-backed proof-reference candidates."
        ),
        failure_mode_statement=(
            "Do not let read-only connector inventory become GitHub or Vercel mutation, "
            "proof publication, or hidden receipt promotion."
        ),
    )


def render_connector_evidence_inventory_summary(
    inventory: CortexConnectorEvidenceInventory,
) -> str:
    lines = [
        "Cortex Connector Evidence Inventory",
        f"- Run id: {inventory.run_id}",
        f"- Owner layer: {inventory.owner_layer}",
        f"- Inventory only: {_render_bool(inventory.inventory_only)}",
        (
            "- Connector observations are final proof references: "
            f"{_render_bool(inventory.connector_observations_are_final_proof_references)}"
        ),
        f"- Connector publication blocked: {_render_bool(inventory.connector_publication_blocked)}",
        (
            "- Connector publication blockers: "
            f"{_render_list(tuple(blocker.code for blocker in inventory.connector_publication_blockers))}"
        ),
        f"- Lifeline audit index path: {inventory.lifeline_audit_index_path or 'none'}",
        f"- Proof reference pack path: {inventory.proof_reference_pack_path or 'none'}",
        f"- Evidence count: {len(inventory.evidence)}",
        f"- Eligible candidate count: {inventory.eligible_candidate_count}",
        f"- Source counts: {_render_counts(inventory.source_counts)}",
        f"- Rule: {inventory.rule_statement}",
        f"- Pattern: {inventory.pattern_statement}",
        f"- Failure mode: {inventory.failure_mode_statement}",
    ]
    return "\n".join(lines) + "\n"


def _write_summary(path: Path, summary: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(summary, encoding="utf-8")


class CortexConnectorEvidenceInventoryWriter:
    def write(
        self,
        *,
        github_evidence: dict[str, Any] | None = None,
        vercel_evidence: dict[str, Any] | None = None,
        lifeline_audit_index_path: str | Path | None = None,
        proof_reference_pack_path: str | Path | None = None,
        run_id: str | None = None,
        root: Path | None = None,
        connector_evidence_root: Path | None = None,
        latest_json_path: Path | None = None,
        latest_summary_path: Path | None = None,
        run_json_path: Path | None = None,
        run_summary_path: Path | None = None,
        write_summary: bool = True,
    ) -> PersistedConnectorEvidenceInventory:
        base = (root or atlas_root()).resolve()
        output_root = _resolved_connector_evidence_dir(
            root=base,
            connector_evidence_root=connector_evidence_root,
        )
        inventory = build_connector_evidence_inventory(
            github_evidence=github_evidence,
            vercel_evidence=vercel_evidence,
            lifeline_audit_index_path=lifeline_audit_index_path,
            proof_reference_pack_path=proof_reference_pack_path,
            run_id=run_id,
            root=base,
        )
        payload = inventory.to_payload()
        summary = render_connector_evidence_inventory_summary(inventory)

        resolved_latest_json_path = (
            latest_json_path.resolve()
            if latest_json_path is not None
            else default_connector_evidence_latest_json_path(
                base,
                connector_evidence_root=output_root,
            )
        )
        resolved_run_json_path = (
            run_json_path.resolve()
            if run_json_path is not None
            else default_connector_evidence_run_json_path(
                inventory.run_id,
                base,
                connector_evidence_root=output_root,
            )
        )
        resolved_latest_summary_path = None
        resolved_run_summary_path = None
        if write_summary:
            resolved_latest_summary_path = (
                latest_summary_path.resolve()
                if latest_summary_path is not None
                else default_connector_evidence_latest_summary_path(
                    base,
                    connector_evidence_root=output_root,
                )
            )
            resolved_run_summary_path = (
                run_summary_path.resolve()
                if run_summary_path is not None
                else default_connector_evidence_run_summary_path(
                    inventory.run_id,
                    base,
                    connector_evidence_root=output_root,
                )
            )

        write_json(resolved_latest_json_path, payload)
        write_json(resolved_run_json_path, payload)
        if resolved_latest_summary_path is not None:
            _write_summary(resolved_latest_summary_path, summary)
        if resolved_run_summary_path is not None:
            _write_summary(resolved_run_summary_path, summary)

        return PersistedConnectorEvidenceInventory(
            latest_artifact_path=resolved_latest_json_path,
            latest_summary_path=resolved_latest_summary_path,
            run_artifact_path=resolved_run_json_path,
            run_summary_path=resolved_run_summary_path,
            payload_digest=stable_json_digest(payload),
            payload=payload,
            summary=summary,
        )


def write_connector_evidence_inventory(
    *,
    github_evidence: dict[str, Any] | None = None,
    vercel_evidence: dict[str, Any] | None = None,
    lifeline_audit_index_path: str | Path | None = None,
    proof_reference_pack_path: str | Path | None = None,
    run_id: str | None = None,
    root: Path | None = None,
    connector_evidence_root: Path | None = None,
    latest_json_path: Path | None = None,
    latest_summary_path: Path | None = None,
    run_json_path: Path | None = None,
    run_summary_path: Path | None = None,
    write_summary: bool = True,
) -> PersistedConnectorEvidenceInventory:
    return CortexConnectorEvidenceInventoryWriter().write(
        github_evidence=github_evidence,
        vercel_evidence=vercel_evidence,
        lifeline_audit_index_path=lifeline_audit_index_path,
        proof_reference_pack_path=proof_reference_pack_path,
        run_id=run_id,
        root=root,
        connector_evidence_root=connector_evidence_root,
        latest_json_path=latest_json_path,
        latest_summary_path=latest_summary_path,
        run_json_path=run_json_path,
        run_summary_path=run_summary_path,
        write_summary=write_summary,
    )
