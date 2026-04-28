from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, normalize_slashes
from ops.cortex._artifacts import stable_json_digest, write_json
from ops.cortex.loop import CortexRunResult, load_and_run_cortex_loop


def default_run_artifact_dir(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "cortex" / "runs"


def default_run_artifact_path(root: Path | None = None) -> Path:
    return default_run_artifact_dir(root) / "cortex-run-result.latest.json"


def default_run_summary_path(root: Path | None = None) -> Path:
    return default_run_artifact_dir(root) / "cortex-run-result.latest.txt"


def _require_seed_path(path: Path, label: str) -> Path:
    resolved = path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Cortex {label} seed not found: {normalize_slashes(str(resolved))}")
    return resolved


@dataclass(frozen=True)
class PersistedCortexRunArtifact:
    artifact_path: Path
    summary_path: Path | None
    payload_digest: str
    payload: dict[str, object]
    summary: str

    def to_payload(self, *, root: Path | None = None) -> dict[str, object]:
        base = (root or atlas_root()).resolve()
        return {
            "artifact_path": atlas_relative(self.artifact_path, root=base),
            "summary_path": atlas_relative(self.summary_path, root=base) if self.summary_path is not None else None,
            "payload_digest": self.payload_digest,
            "summary": self.summary,
        }


def render_run_summary(result: CortexRunResult) -> str:
    trace = result.applied_rule_trace
    lines = [
        "Cortex Run Result",
        f"- Selected next action: {result.selected_next_action['action_id']} ({result.selected_next_action['owner_layer']})",
        f"- Worker plan template: {result.worker_plan.template_id}",
        f"- Receipt ready: {'yes' if result.receipt_ready else 'no'}",
        f"- Next required layer: {result.next_required_layer or 'none'}",
        f"- Ambient debt count: {len(result.known_ambient_debt)}",
        f"- Decision rules: {', '.join(trace.decision_rule_ids) if trace.decision_rule_ids else 'none'}",
        f"- Plan rules: {', '.join(trace.plan_rule_ids) if trace.plan_rule_ids else 'none'}",
        f"- Patterns applied: {', '.join(trace.pattern_ids) if trace.pattern_ids else 'none'}",
        f"- Failure modes avoided: {', '.join(trace.failure_mode_ids) if trace.failure_mode_ids else 'none'}",
        f"- Why selected: {' | '.join(trace.why_selected) if trace.why_selected else 'none'}",
    ]
    return "\n".join(lines) + "\n"


def persist_cortex_run_artifact(
    *,
    root: Path | None = None,
    output_json_path: Path | None = None,
    output_summary_path: Path | None = None,
    write_summary: bool = True,
    state_model_path: Path | None = None,
    rule_registry_path: Path | None = None,
    proof_summary_examples_path: Path | None = None,
) -> PersistedCortexRunArtifact:
    base = (root or atlas_root()).resolve()
    artifact_path = (output_json_path or default_run_artifact_path(base)).resolve()
    summary_path = (output_summary_path or default_run_summary_path(base)).resolve() if write_summary else None
    resolved_state_model_path = _require_seed_path(
        state_model_path if state_model_path is not None else base / "runtime" / "cortex" / "kernel.state-model.seed.v1.json",
        "state model",
    )
    resolved_rule_registry_path = _require_seed_path(
        rule_registry_path if rule_registry_path is not None else base / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json",
        "rule registry",
    )
    resolved_proof_summary_examples_path = _require_seed_path(
        (
            proof_summary_examples_path
            if proof_summary_examples_path is not None
            else base / "runtime" / "cortex" / "kernel.proof-summary.examples.v1.json"
        ),
        "proof summary examples",
    )

    result = load_and_run_cortex_loop(
        root=base,
        state_model_path=resolved_state_model_path,
        rule_registry_path=resolved_rule_registry_path,
        proof_summary_examples_path=resolved_proof_summary_examples_path,
    )
    payload = result.to_payload()
    summary = render_run_summary(result)
    write_json(artifact_path, payload)
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(summary, encoding="utf-8")

    return PersistedCortexRunArtifact(
        artifact_path=artifact_path,
        summary_path=summary_path,
        payload_digest=stable_json_digest(payload),
        payload=payload,
        summary=summary,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Persist a deterministic CortexRunResult artifact and summary.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--state-model-path", type=Path)
    parser.add_argument("--rule-registry-path", type=Path)
    parser.add_argument("--proof-summary-examples-path", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-summary", type=Path)
    parser.add_argument("--no-write-summary", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    base = args.root.resolve()
    try:
        artifact = persist_cortex_run_artifact(
            root=base,
            output_json_path=args.output_json.resolve() if args.output_json else None,
            output_summary_path=args.output_summary.resolve() if args.output_summary else None,
            write_summary=not args.no_write_summary,
            state_model_path=args.state_model_path.resolve() if args.state_model_path else None,
            rule_registry_path=args.rule_registry_path.resolve() if args.rule_registry_path else None,
            proof_summary_examples_path=(
                args.proof_summary_examples_path.resolve() if args.proof_summary_examples_path else None
            ),
        )
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.print_json:
        print(json.dumps(artifact.payload, indent=2))
    elif not args.quiet:
        print(artifact.summary, end="")
        print(f"JSON artifact: {normalize_slashes(str(artifact.artifact_path))}")
        if artifact.summary_path is not None:
            print(f"Summary report: {normalize_slashes(str(artifact.summary_path))}")
        print(f"Payload digest: {artifact.payload_digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
