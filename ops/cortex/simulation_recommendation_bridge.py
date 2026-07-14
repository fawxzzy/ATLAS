from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root, normalize_slashes
from ops.cortex.workflow_resilience_simulator import run as run_simulator

OUTPUT_VERSION = "atlas.cortex.simulation.recommendation-envelope.v1"
PLAYBOOK_ADOPTION_REF = "docs/registry/ATLAS-PLAYBOOK-DOCTRINE-ADOPTION.json"
PLAYBOOK_CONTRACT = "atlas.playbook_doctrine_adoption.v1"


def _stable(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _finding(code: str, message: str, **details: object) -> OrderedDict[str, object]:
    item: OrderedDict[str, object] = OrderedDict([("code", code), ("message", message)])
    if details:
        item["details"] = OrderedDict(sorted(details.items()))
    return item


def _safe_output(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip() or Path(value).is_absolute():
        return None
    ref = normalize_slashes(value).strip("/")
    if ref.startswith("../") or "/../" in f"/{ref}/" or not ref.startswith("tmp/atlas/") or not ref.endswith(".json"):
        return None
    return ref


def _load_playbook_adoption(root: Path) -> tuple[dict[str, Any], str | None, list[OrderedDict[str, object]]]:
    try:
        raw = (root / PLAYBOOK_ADOPTION_REF).read_bytes()
        payload = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        return {}, None, [_finding("playbook_adoption_read_failed", "Playbook adoption record could not be read.", error=str(exc))]
    blockers: list[OrderedDict[str, object]] = []
    if not isinstance(payload, dict) or payload.get("contract_version") != PLAYBOOK_CONTRACT:
        blockers.append(_finding("playbook_adoption_contract_invalid", "Playbook adoption contract is invalid."))
    source = payload.get("source") if isinstance(payload, dict) else None
    registry = source.get("artifacts", {}).get("registry") if isinstance(source, dict) else None
    adopted = payload.get("registry", {}).get("adopted_record_ids") if isinstance(payload, dict) else None
    if not isinstance(registry, dict) or not isinstance(registry.get("path"), str) or not isinstance(registry.get("sha256"), str):
        blockers.append(_finding("playbook_registry_source_invalid", "Playbook registry source metadata is invalid."))
    if not isinstance(adopted, dict) or not isinstance(adopted.get("promoted"), list):
        blockers.append(_finding("playbook_adopted_records_invalid", "Playbook adopted record IDs are invalid."))
    return payload, _digest(raw), blockers


def _candidate(simulation_id: str, record_type: str, statement: str, source_refs: list[str]) -> OrderedDict[str, object]:
    basis = {"simulation_id": simulation_id, "record_type": record_type, "statement": statement}
    return OrderedDict([
        ("candidate_id", _stable(basis)), ("record_type", record_type), ("statement", statement),
        ("source_refs", source_refs), ("promotion_state", "candidate_only"),
        ("owner_review_required", True), ("promotion_authorized", False),
    ])


def run(*, root: Path, simulator_manifest_path: str, output_path: str | None) -> tuple[OrderedDict[str, object], int]:
    blockers: list[OrderedDict[str, object]] = []
    output_ref = None
    if output_path is not None:
        output_ref = _safe_output(output_path)
        if output_ref is None:
            blockers.append(_finding("output_path_not_admitted", "Recommendation output path is not admitted."))
    simulator_result, simulator_code = run_simulator(root=root, manifest_path=simulator_manifest_path, output_path=None)
    if simulator_code != 0 or simulator_result.get("status") != "ok" or not isinstance(simulator_result.get("simulation"), dict):
        blockers.append(_finding("simulation_not_eligible", "Simulator did not produce an eligible recommendation source."))
    adoption, adoption_digest, adoption_blockers = _load_playbook_adoption(root)
    blockers.extend(adoption_blockers)
    envelope = None
    if not blockers:
        simulation = simulator_result["simulation"]
        manifest_ref = str(simulator_result["manifest_ref"])
        manifest_digest = _digest((root / manifest_ref).read_bytes())
        source_refs = [manifest_ref, PLAYBOOK_ADOPTION_REF]
        candidate_refs = [*source_refs, *list(simulation["source_refs"])]
        candidates = [
            _candidate(str(simulation["simulation_id"]), "rule_candidate", "Require real execution, verification, and readback receipts before operational state changes.", candidate_refs),
            _candidate(str(simulation["simulation_id"]), "pattern_candidate", "Use a receipt-bound bounded rehearsal to identify recovery proof before selecting execution.", candidate_refs),
            _candidate(str(simulation["simulation_id"]), "failure_mode_candidate", "Simulated recovery is promoted as completed work without real execution proof.", candidate_refs),
        ]
        proof_required = sorted({str(proof) for step in simulation["steps"] for proof in step["proof_required"]})
        recommendations = [OrderedDict([
            ("recommendation_id", _stable({"simulation_id": simulation["simulation_id"], "sequence": index + 1, "text": text})),
            ("priority", index + 1), ("action", text), ("observed_state", simulation["observed_state"]),
            ("evidence_required", proof_required), ("source_refs", list(simulation["source_refs"])),
            ("advisory_only", True), ("execution_authorized", False), ("dispatch_authorized", False),
        ]) for index, text in enumerate(simulation["recommendations"])]
        basis = {"simulation_id": simulation["simulation_id"], "adoption_digest": adoption_digest, "candidates": candidates, "recommendations": recommendations}
        envelope = OrderedDict([
            ("contract_version", OUTPUT_VERSION), ("envelope_id", _stable(basis)),
            ("simulation_id", simulation["simulation_id"]), ("generated_at", simulation["generated_at"]),
            ("source_refs", source_refs),
            ("source_digests", [OrderedDict([("ref", manifest_ref), ("digest", manifest_digest)]), OrderedDict([("ref", PLAYBOOK_ADOPTION_REF), ("digest", adoption_digest)])]),
            ("playbook_projection", OrderedDict([
                ("doctrine_source", f"git:{adoption['source']['repository_path']}@{adoption['source']['accepted_commit']}:{adoption['source']['artifacts']['registry']['path']}"),
                ("doctrine_is_not_implementation_proof", True), ("candidates", candidates),
            ])),
            ("cortex_projection", OrderedDict([("observed_state", simulation["observed_state"]), ("recommendations", recommendations)])),
            ("authority", OrderedDict([("advisory_only", True), ("execution_authorized", False), ("dispatch_authorized", False), ("doctrine_promotion_authorized", False), ("owner_repo_mutation_authorized", False), ("platform_mutation_authorized", False), ("discord_write_authorized", False), ("board_write_authorized", False), ("deployment_authorized", False), ("approval_authorized", False), ("final_receipt_authorized", False), ("marker_movement_authorized", False)])),
        ])
    status = "blocker" if blockers else "ok"
    result = OrderedDict([("status", status), ("safe_to_use", status == "ok"), ("output_ref", output_ref), ("envelope", envelope), ("warnings", []), ("blockers", blockers)])
    if envelope is not None and output_ref is not None:
        destination = root / output_ref
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(envelope, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return result, 0 if status == "ok" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Project Cortex simulation output into Playbook candidates and Cortex recommendations.")
    parser.add_argument("--simulator-manifest", required=True)
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    result, code = run(root=atlas_root(), simulator_manifest_path=args.simulator_manifest, output_path=args.output)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return code if args.strict else (1 if result["status"] == "blocker" else 0)


if __name__ == "__main__":
    raise SystemExit(main())
