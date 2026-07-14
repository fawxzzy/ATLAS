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
from ops.cortex.simulation_recommendation_bridge import run as run_bridge

MANIFEST_VERSION = "atlas.cortex.simulation.recommendation-evaluation-manifest.v1"
OUTPUT_VERSION = "atlas.cortex.simulation.recommendation-evaluation.v1"
CLASSIFICATIONS = {"match", "changed", "invalid"}
MANIFEST_FIELDS = {"contract_version", "evaluation_id", "generated_at", "cases"}
CASE_FIELDS = {"case_id", "simulator_manifest_ref", "simulator_manifest_digest", "expected_envelope_id", "expected_classification"}


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


def run(*, root: Path, manifest_path: str, output_path: str | None) -> tuple[OrderedDict[str, object], int]:
    blockers: list[OrderedDict[str, object]] = []
    manifest_ref = _safe_ref(manifest_path, "data/cortex/simulation-evaluations/")
    manifest: dict[str, Any] = {}
    if manifest_ref is None:
        blockers.append(_finding("manifest_path_not_admitted", "Evaluation manifest path is not admitted."))
    else:
        try:
            payload = json.loads((root / manifest_ref).read_text(encoding="utf-8"))
            manifest = payload if isinstance(payload, dict) else {}
        except (OSError, json.JSONDecodeError) as exc:
            blockers.append(_finding("manifest_read_failed", "Evaluation manifest could not be read.", error=str(exc)))
    if manifest:
        unknown = sorted(set(manifest) - MANIFEST_FIELDS)
        missing = sorted(MANIFEST_FIELDS - set(manifest))
        if manifest.get("contract_version") != MANIFEST_VERSION or unknown or missing:
            blockers.append(_finding("manifest_invalid", "Evaluation manifest contract or fields are invalid.", unknown=unknown, missing=missing))
        cases = manifest.get("cases")
        if not isinstance(cases, list) or not 1 <= len(cases) <= 20:
            blockers.append(_finding("cases_invalid", "Evaluation cases must contain 1 through 20 entries."))
        else:
            ids: list[str] = []
            for index, case in enumerate(cases):
                if not isinstance(case, dict) or set(case) != CASE_FIELDS or case.get("expected_classification") not in CLASSIFICATIONS:
                    blockers.append(_finding("case_invalid", "Evaluation case fields or classification are invalid.", index=index))
                    continue
                ids.append(str(case.get("case_id", "")))
            if len(ids) != len(set(ids)) or any(not item for item in ids):
                blockers.append(_finding("case_id_invalid", "Evaluation case IDs must be non-empty and unique."))
    output_ref = None
    if output_path is not None:
        output_ref = _safe_ref(output_path, "tmp/atlas/")
        if output_ref is None:
            blockers.append(_finding("output_path_not_admitted", "Evaluation output path is not admitted."))
    case_results: list[OrderedDict[str, object]] = []
    if not blockers:
        for case in manifest["cases"]:
            simulator_ref = _safe_ref(case["simulator_manifest_ref"], "data/cortex/simulation-replays/")
            envelope_id = None
            invalid_reason = None
            if simulator_ref is None:
                invalid_reason = "simulator_manifest_path_not_admitted"
            else:
                try:
                    digest = "sha256:" + hashlib.sha256((root / simulator_ref).read_bytes()).hexdigest()
                    if digest != case["simulator_manifest_digest"]:
                        invalid_reason = "simulator_manifest_digest_mismatch"
                except OSError:
                    invalid_reason = "simulator_manifest_read_failed"
            if invalid_reason is None and simulator_ref is not None:
                bridge, bridge_code = run_bridge(root=root, simulator_manifest_path=simulator_ref, output_path=None)
                if bridge_code != 0 or bridge.get("status") != "ok" or not isinstance(bridge.get("envelope"), dict):
                    invalid_reason = "recommendation_bridge_blocked"
                else:
                    envelope_id = str(bridge["envelope"]["envelope_id"])
            classification = "invalid" if invalid_reason else ("match" if envelope_id == case["expected_envelope_id"] else "changed")
            case_results.append(OrderedDict([
                ("case_id", case["case_id"]), ("simulator_manifest_ref", simulator_ref or case["simulator_manifest_ref"]),
                ("expected_envelope_id", case["expected_envelope_id"]), ("observed_envelope_id", envelope_id),
                ("expected_classification", case["expected_classification"]), ("classification", classification),
                ("expectation_met", classification == case["expected_classification"]), ("invalid_reason", invalid_reason),
                ("mutation_authorized", False),
            ]))
    evaluation = None
    if not blockers:
        counts = Counter(str(item["classification"]) for item in case_results)
        threshold = all(counts[name] > 0 for name in ("match", "changed", "invalid")) and all(bool(item["expectation_met"]) for item in case_results)
        basis = {"manifest": manifest, "case_results": case_results}
        evaluation = OrderedDict([
            ("contract_version", OUTPUT_VERSION), ("evaluation_run_id", _stable(basis)),
            ("evaluation_id", manifest["evaluation_id"]), ("generated_at", manifest["generated_at"]),
            ("source_ref", manifest_ref), ("case_results", case_results),
            ("classification_counts", OrderedDict((name, counts[name]) for name in ("match", "changed", "invalid"))),
            ("threshold_eligible", threshold),
            ("termination", OrderedDict([("terminated", True), ("reason", "all_cases_evaluated"), ("cases_evaluated", len(case_results))])),
            ("authority", OrderedDict([("advisory_only", True), ("execution_authorized", False), ("dispatch_authorized", False), ("doctrine_promotion_authorized", False), ("owner_repo_mutation_authorized", False), ("platform_mutation_authorized", False), ("discord_write_authorized", False), ("board_write_authorized", False), ("deployment_authorized", False), ("approval_authorized", False), ("final_receipt_authorized", False), ("marker_movement_authorized", False)])),
        ])
    status = "blocker" if blockers else ("ok" if evaluation and evaluation["threshold_eligible"] else "advisory_gap")
    result = OrderedDict([("status", status), ("safe_to_use", status == "ok"), ("manifest_ref", manifest_ref), ("output_ref", output_ref), ("evaluation", evaluation), ("warnings", [] if status != "advisory_gap" else [_finding("evaluation_threshold_incomplete", "Evaluation did not prove all three expected classes.")]), ("blockers", blockers)])
    if evaluation is not None and output_ref is not None and not blockers:
        destination = root / output_ref
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(evaluation, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return result, 0 if status == "ok" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay and evaluate deterministic Cortex simulation recommendation envelopes.")
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
