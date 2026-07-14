from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root, normalize_slashes
from ops.cortex.read_only_scenario_helper import build_state

MANIFEST_VERSION = "atlas.cortex.simulation.receipt-replay-manifest.v1"
OUTPUT_VERSION = "atlas.cortex.simulation.receipt-replay.v1"
RECEIPT_STATUSES = {"accepted", "rejected", "passed", "failed", "skipped", "warning"}
EXECUTION_STATUSES = {"succeeded", "failed", "blocked", "cancelled", "awaiting-review", "partial"}
TRUST_PREFIXES = {
    "atlas_runtime_receipt": "runtime/receipts/",
    "committed_replay_fixture": "data/cortex/simulation-replays/",
    "contract_fixture": "packages/atlas-contracts/fixtures/valid/",
}


def _stable(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _finding(code: str, message: str, **details: object) -> OrderedDict[str, object]:
    item: OrderedDict[str, object] = OrderedDict([("code", code), ("message", message)])
    if details:
        item["details"] = OrderedDict(sorted(details.items()))
    return item


def _safe_ref(value: object, prefix: str) -> str | None:
    if not isinstance(value, str) or not value.strip() or Path(value).is_absolute():
        return None
    ref = normalize_slashes(value).strip("/")
    if ref.startswith("../") or "/../" in f"/{ref}/" or not ref.startswith(prefix) or not ref.endswith(".json"):
        return None
    return ref


def _validate_receipt(payload: object, ref: str) -> list[OrderedDict[str, object]]:
    if not isinstance(payload, dict):
        return [_finding("receipt_not_object", "Receipt must be a JSON object.", ref=ref)]
    version = payload.get("contract_version")
    required = {"receipt_id", "recorded_at", "status"}
    missing = sorted(field for field in required if not isinstance(payload.get(field), str) or not payload[field].strip())
    blockers = [_finding("receipt_field_missing", "Receipt required fields are missing.", ref=ref, fields=missing)] if missing else []
    if version == "atlas.receipt.v1":
        if payload.get("status") not in RECEIPT_STATUSES:
            blockers.append(_finding("receipt_status_invalid", "Receipt status is invalid.", ref=ref))
    elif version == "atlas.execution-receipt.v2":
        if payload.get("status") not in EXECUTION_STATUSES:
            blockers.append(_finding("receipt_status_invalid", "Execution receipt status is invalid.", ref=ref))
        verification = payload.get("verification")
        if not isinstance(verification, list) or any(not isinstance(item, dict) or item.get("status") not in {"passed", "failed", "skipped", "blocked"} for item in verification):
            blockers.append(_finding("verification_invalid", "Execution receipt verification entries are invalid.", ref=ref))
    else:
        blockers.append(_finding("receipt_contract_not_admitted", "Receipt contract is not admitted.", ref=ref, contract_version=version))
    return blockers


def _classify(payload: dict[str, Any]) -> str:
    verification = payload.get("verification", [])
    if any(item.get("status") == "blocked" for item in verification if isinstance(item, dict)):
        return "blocked"
    if any(item.get("status") == "failed" for item in verification if isinstance(item, dict)):
        return "failure"
    status = payload["status"]
    if status in {"accepted", "passed", "succeeded"}:
        return "success"
    if status in {"warning", "skipped", "awaiting-review", "partial"}:
        return "advisory"
    if status in {"blocked", "cancelled"}:
        return "blocked"
    return "failure"


def run(*, root: Path, manifest_path: str, output_path: str | None) -> tuple[OrderedDict[str, object], int]:
    blockers: list[OrderedDict[str, object]] = []
    manifest_ref = _safe_ref(manifest_path, "data/cortex/simulation-replays/")
    if manifest_ref is None:
        blockers.append(_finding("manifest_path_not_admitted", "Replay manifest path is not admitted."))
        manifest: dict[str, Any] = {}
    else:
        try:
            manifest = json.loads((root / manifest_ref).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            blockers.append(_finding("manifest_read_failed", "Replay manifest could not be read.", error=str(exc)))
            manifest = {}
    if manifest and (manifest.get("contract_version") != MANIFEST_VERSION or not isinstance(manifest.get("receipts"), list) or not manifest["receipts"]):
        blockers.append(_finding("manifest_invalid", "Replay manifest contract or receipt list is invalid."))
    output_ref = None
    if output_path is not None:
        output_ref = _safe_ref(output_path, "tmp/atlas/")
        if output_ref is None:
            blockers.append(_finding("output_path_not_admitted", "Replay output path is not admitted."))
    observations: list[OrderedDict[str, object]] = []
    seen_ids: set[str] = set()
    if not blockers:
        for index, entry in enumerate(manifest["receipts"]):
            if not isinstance(entry, dict) or entry.get("trust_class") not in TRUST_PREFIXES:
                blockers.append(_finding("receipt_entry_invalid", "Receipt entry or trust class is invalid.", index=index))
                continue
            trust = str(entry["trust_class"])
            ref = _safe_ref(entry.get("ref"), TRUST_PREFIXES[trust])
            if ref is None:
                blockers.append(_finding("receipt_path_not_admitted", "Receipt path is not admitted for its trust class.", index=index))
                continue
            try:
                raw = (root / ref).read_bytes()
                payload = json.loads(raw)
            except (OSError, json.JSONDecodeError) as exc:
                blockers.append(_finding("receipt_read_failed", "Receipt could not be read.", ref=ref, error=str(exc)))
                continue
            digest = "sha256:" + hashlib.sha256(raw).hexdigest()
            if entry.get("digest") != digest:
                blockers.append(_finding("receipt_digest_mismatch", "Receipt byte digest does not match.", ref=ref))
                continue
            receipt_blockers = _validate_receipt(payload, ref)
            blockers.extend(receipt_blockers)
            if receipt_blockers:
                continue
            receipt_id = str(payload["receipt_id"])
            if receipt_id in seen_ids:
                blockers.append(_finding("duplicate_receipt_id", "Receipt ID is duplicated.", receipt_id=receipt_id))
                continue
            seen_ids.add(receipt_id)
            observations.append(OrderedDict([
                ("receipt_id", receipt_id), ("contract_version", payload["contract_version"]),
                ("recorded_at", payload["recorded_at"]), ("source_status", payload["status"]),
                ("failure_class", _classify(payload)), ("source_ref", ref), ("source_digest", digest),
                ("trust_class", trust), ("summary", payload.get("summary") or f"{payload['contract_version']} {payload['status']}"),
            ]))
    observations.sort(key=lambda item: (str(item["recorded_at"]), str(item["receipt_id"]), str(item["source_ref"])))
    counts = Counter(str(item["failure_class"]) for item in observations)
    versions = {str(item["contract_version"]) for item in observations}
    eligible_source = any(item["trust_class"] != "contract_fixture" for item in observations)
    threshold_eligible = eligible_source and versions == {"atlas.receipt.v1", "atlas.execution-receipt.v2"} and counts["success"] > 0 and (counts["failure"] + counts["blocked"] > 0)
    replay = None
    if not blockers and observations:
        transitions = [OrderedDict([("sequence", index + 1), ("receipt_id", item["receipt_id"]), ("recorded_at", item["recorded_at"]), ("classification", item["failure_class"]), ("source_ref", item["source_ref"])]) for index, item in enumerate(observations)]
        fixture = {
            "scenario_id": manifest["scenario_id"], "agent_id": manifest["agent_id"], "generated_at": manifest["generated_at"],
            "objective": manifest["objective"], "minimum_confidence": 0.5,
            "scoring": {"recency_weight": 0.3, "importance_weight": 0.3, "relevance_weight": 0.4},
            "observations": [{"observed_at": item["recorded_at"], "content_summary": item["summary"], "source_ref": item["source_ref"], "source_digest": item["source_digest"], "importance": 0.8, "confidence": 1.0, "retention_class": "project", "rights_class": "operator_owned", "privacy_class": "internal", "injection_state": "neutralized"} for item in observations],
        }
        state = build_state(fixture=fixture, input_ref=manifest_ref)
        basis = {"manifest": manifest_ref, "observations": observations}
        replay = OrderedDict([
            ("contract_version", OUTPUT_VERSION), ("replay_id", _stable(basis)), ("generated_at", manifest["generated_at"]),
            ("scenario_id", manifest["scenario_id"]), ("agent_id", manifest["agent_id"]), ("objective", manifest["objective"]),
            ("source_refs", [manifest_ref, *[str(item["source_ref"]) for item in observations]]),
            ("receipt_observations", observations), ("transitions", transitions),
            ("failure_mode_counts", OrderedDict((name, counts[name]) for name in ("success", "advisory", "failure", "blocked"))),
            ("threshold_eligible", threshold_eligible), ("agent_state", state),
            ("authority", OrderedDict([("advisory_only", True), ("execution_authorized", False), ("dispatch_authorized", False), ("owner_repo_mutation_authorized", False), ("platform_mutation_authorized", False), ("discord_write_authorized", False), ("board_write_authorized", False), ("deployment_authorized", False), ("approval_authorized", False), ("final_receipt_authorized", False), ("marker_movement_authorized", False)])),
        ])
    status = "blocker" if blockers else ("ok" if threshold_eligible else "advisory_gap")
    result = OrderedDict([("status", status), ("safe_to_use", status == "ok"), ("manifest_ref", manifest_ref), ("output_ref", output_ref), ("replay", replay), ("warnings", [] if threshold_eligible or blockers else [_finding("threshold_evidence_incomplete", "Replay does not satisfy mixed-source threshold evidence.")]), ("blockers", blockers)])
    if replay is not None and output_ref is not None and not blockers:
        destination = root / output_ref
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(replay, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return result, 0 if status == "ok" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay admitted ATLAS receipts into deterministic advisory Cortex state.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    result, code = run(root=atlas_root(), manifest_path=args.manifest, output_path=args.output)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return code if args.strict else (1 if result["status"] == "blocker" else 0)


if __name__ == "__main__":
    raise SystemExit(main())
