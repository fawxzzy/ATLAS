from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root, normalize_slashes
from ops.atlas.continuity import build_initiative_continuity_manifest_health, build_open_marker_manifest_coverage
from ops.cortex.receipt_replay import run as run_replay
from ops.cortex.simulation_recommendation_bridge import run as run_bridge
from ops.cortex.simulation_recommendation_evaluator import run as run_evaluator
from ops.cortex.workflow_resilience_simulator import run as run_simulator

SIMULATOR_MANIFEST = "data/cortex/simulation-replays/first-mixed-replay/workflow-resilience-manifest.json"
REPLAY_MANIFEST = "data/cortex/simulation-replays/first-mixed-replay/manifest.json"
EVALUATION_MANIFEST = "data/cortex/simulation-evaluations/first-recommendation-loop/manifest.json"
REVIEW_VERSION = "atlas.cortex.simulation.independent-governance-review.v1"
REQUIRED_FILES = [
    "docs/registry/CORTEX-SIMULATION-SUBSTRATE-RESEARCH-CONTRACT.v1.json",
    "schemas/atlas.cortex.simulation.agent-state.v1.json",
    "ops/cortex/read_only_scenario_helper.py",
    "ops/cortex/receipt_replay.py",
    "docs/registry/CORTEX-SIMULATION-PROJECT-ADAPTER-SELECTION.v1.json",
    "ops/cortex/workflow_resilience_simulator.py",
    "ops/cortex/simulation_recommendation_bridge.py",
    "ops/cortex/simulation_recommendation_evaluator.py",
]
TEST_FILES = [
    "tests/test_cortex_simulation_substrate_requirements.py",
    "tests/test_cortex_simulation_agent_state_schema.py",
    "tests/test_cortex_read_only_scenario_helper.py",
    "tests/test_cortex_receipt_replay.py",
    "tests/test_cortex_workflow_resilience_simulator.py",
    "tests/test_cortex_simulation_recommendation_bridge.py",
    "tests/test_cortex_simulation_recommendation_evaluator.py",
]


def _safe_review_ref(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip() or Path(value).is_absolute():
        return None
    ref = normalize_slashes(value).strip("/")
    if ref.startswith("../") or "/../" in f"/{ref}/" or not ref.startswith("data/cortex/simulation-audits/") or not ref.endswith(".json"):
        return None
    return ref


def _all_authority_false(payload: object) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key.endswith("_authorized") and value is not False:
                return False
            if key == "advisory_only" and value is not True:
                return False
            if not _all_authority_false(value):
                return False
    elif isinstance(payload, list):
        return all(_all_authority_false(item) for item in payload)
    return True


def _gate(gate_id: str, name: str, passed: bool, evidence: list[str], detail: str) -> OrderedDict[str, object]:
    return OrderedDict([("gate_id", gate_id), ("name", name), ("passed", passed), ("evidence_refs", evidence), ("detail", detail)])


def run(*, root: Path, independent_review_path: str | None, output_path: str | None) -> tuple[OrderedDict[str, object], int]:
    blockers: list[OrderedDict[str, object]] = []
    output_ref = None
    if output_path is not None:
        output_ref = normalize_slashes(output_path).strip("/") if isinstance(output_path, str) else None
        if not output_ref or Path(output_ref).is_absolute() or output_ref.startswith("../") or "/../" in f"/{output_ref}/" or not output_ref.startswith("tmp/atlas/") or not output_ref.endswith(".json"):
            blockers.append(OrderedDict([("code", "output_path_not_admitted"), ("message", "Audit output path is not admitted.")]))
    replay, replay_code = run_replay(root=root, manifest_path=REPLAY_MANIFEST, output_path=None)
    simulator, simulator_code = run_simulator(root=root, manifest_path=SIMULATOR_MANIFEST, output_path=None)
    bridge, bridge_code = run_bridge(root=root, simulator_manifest_path=SIMULATOR_MANIFEST, output_path=None)
    evaluator, evaluator_code = run_evaluator(root=root, manifest_path=EVALUATION_MANIFEST, output_path=None)
    continuity = build_initiative_continuity_manifest_health(root=root)
    coverage = build_open_marker_manifest_coverage(root=root)
    try:
        validation = json.loads((root / "runtime/receipts/validation/stack-validation.latest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        validation = {}
    try:
        adapters = json.loads((root / "docs/registry/CORTEX-SIMULATION-PROJECT-ADAPTER-SELECTION.v1.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        adapters = {}
    gates: list[OrderedDict[str, object]] = []
    gates.append(_gate("G01", "research_requirements", all((root / ref).is_file() for ref in REQUIRED_FILES[:1]), REQUIRED_FILES[:1], "Research contract is present."))
    gates.append(_gate("G02", "agent_state_and_helper", all((root / ref).is_file() for ref in REQUIRED_FILES[1:3]), REQUIRED_FILES[1:3], "Agent-state schema and read-only helper are present."))
    gates.append(_gate("G03", "receipt_replay", replay_code == 0 and replay.get("status") == "ok" and bool(replay.get("replay", {}).get("threshold_eligible")), [REPLAY_MANIFEST], "Digest-bound mixed receipt replay is eligible."))
    adapter_rows = adapters.get("adapters", []) if isinstance(adapters, dict) else []
    adapters_ok = len(adapter_rows) == 4 and adapter_rows[0].get("status") == "selected_for_first_prototype" and all(row.get("status") == "selected_held" for row in adapter_rows[1:])
    gates.append(_gate("G04", "adapter_selection", adapters_ok, ["docs/registry/CORTEX-SIMULATION-PROJECT-ADAPTER-SELECTION.v1.json"], "Four adapters are selected and owner adapters remain held."))
    sim = simulator.get("simulation", {}) if isinstance(simulator, dict) else {}
    sim_ok = simulator_code == 0 and simulator.get("status") == "ok" and sim.get("termination", {}).get("terminated") is True and len(sim.get("steps", [])) <= sim.get("termination", {}).get("max_steps", 0)
    gates.append(_gate("G05", "safe_simulator", sim_ok, [SIMULATOR_MANIFEST], "Simulator is bounded, terminating, and eligible."))
    envelope = bridge.get("envelope", {}) if isinstance(bridge, dict) else {}
    bridge_ok = bridge_code == 0 and bridge.get("status") == "ok" and len(envelope.get("playbook_projection", {}).get("candidates", [])) >= 3 and len(envelope.get("cortex_projection", {}).get("recommendations", [])) >= 1
    gates.append(_gate("G06", "recommendation_consumption", bridge_ok, [SIMULATOR_MANIFEST, "docs/registry/ATLAS-PLAYBOOK-DOCTRINE-ADOPTION.json"], "Playbook and Cortex projections are populated."))
    evaluation = evaluator.get("evaluation", {}) if isinstance(evaluator, dict) else {}
    eval_ok = evaluator_code == 0 and evaluator.get("status") == "ok" and evaluation.get("classification_counts") == {"match": 1, "changed": 1, "invalid": 1} and evaluation.get("termination", {}).get("terminated") is True
    gates.append(_gate("G07", "recommendation_evaluation", eval_ok, [EVALUATION_MANIFEST], "Evaluation proves match, changed, invalid, and termination."))
    authority_ok = all(_all_authority_false(item) for item in (sim, envelope, evaluation))
    gates.append(_gate("G08", "permanent_authority_denial", authority_ok, [SIMULATOR_MANIFEST, EVALUATION_MANIFEST], "All nested authorization fields remain false and advisory flags remain true."))
    summary = validation.get("summary", {}) if isinstance(validation, dict) else {}
    operational_ok = all((root / ref).is_file() for ref in TEST_FILES) and continuity.get("error_count") == 0 and continuity.get("warning_count") == 0 and coverage.get("status") == "ok" and summary.get("critical") == 0 and summary.get("error") == 0
    gates.append(_gate("G09", "operational_health", operational_ok, [*TEST_FILES, "runtime/receipts/validation/stack-validation.latest.json"], "Focused proof files, continuity, coverage, and blocking validation are clean."))
    review_ref = _safe_review_ref(independent_review_path) if independent_review_path is not None else None
    review_ok = False
    if review_ref is not None:
        try:
            review = json.loads((root / review_ref).read_text(encoding="utf-8"))
            review_ok = review.get("contract_version") == REVIEW_VERSION and review.get("decision") == "RATIFY_100" and review.get("unresolved_blockers") == [] and review.get("independent") is True
        except (OSError, json.JSONDecodeError):
            review_ok = False
    gates.append(_gate("G10", "independent_ratification", review_ok, [review_ref] if review_ref else [], "Independent RATIFY_100 review is required."))
    passed_count = sum(1 for gate in gates if gate["passed"])
    eligible = passed_count == 10 and not blockers
    audit = OrderedDict([("contract_version", "atlas.cortex.simulation.governance-audit.v1"), ("decision", "RATIFY_100" if eligible else "AWAIT_INDEPENDENT_REVIEW" if passed_count == 9 else "HOLD"), ("passed_count", passed_count), ("gate_count", 10), ("eligible_for_100", eligible), ("gates", gates), ("authority", OrderedDict([("advisory_only", True), ("execution_authorized", False), ("dispatch_authorized", False), ("doctrine_promotion_authorized", False), ("owner_repo_mutation_authorized", False), ("platform_mutation_authorized", False), ("discord_write_authorized", False), ("board_write_authorized", False), ("deployment_authorized", False), ("approval_authorized", False), ("final_receipt_authorized", False), ("marker_movement_authorized", False)]))])
    status = "blocker" if blockers or passed_count < 9 else ("ok" if eligible else "awaiting_review")
    result = OrderedDict([("status", status), ("safe_to_use", status in {"ok", "awaiting_review"}), ("output_ref", output_ref), ("audit", audit), ("blockers", blockers)])
    if output_ref is not None and not blockers:
        destination = root / output_ref
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(audit, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return result, 0 if status == "ok" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit the Cortex simulation substrate against its fixed governance-safe closeout gates.")
    parser.add_argument("--independent-review")
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    result, code = run(root=atlas_root(), independent_review_path=args.independent_review, output_path=args.output)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return code if args.strict else (1 if result["status"] == "blocker" else 0)


if __name__ == "__main__":
    raise SystemExit(main())
