from __future__ import annotations

import argparse
import functools
import hashlib
import importlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from time import perf_counter
from types import ModuleType
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops import _atlas as atlas_support
from ops.atlas import awareness
from ops.atlas import build_codex_context as context_builder

cortex_status = importlib.import_module("ops.cortex.render_status")
continuity = importlib.import_module("ops.atlas.continuity")
lockfile_builder = importlib.import_module("ops.stack.generate_lockfile")
repo_inventory_builder = importlib.import_module("ops.stack.export_repo_inventory")


SCHEMA_VERSION = "atlas.codex-context-observability.v1"


class AggregateProbe:
    """Observe one context build without retaining paths, content, or tool output."""

    def __init__(self) -> None:
        self.started_at = perf_counter()
        self.stage_inclusive_seconds: defaultdict[str, float] = defaultdict(float)
        self.stage_exclusive_seconds: defaultdict[str, float] = defaultdict(float)
        self.stage_calls: Counter[str] = Counter()
        self.stage_failures: Counter[str] = Counter()
        self.query_calls: Counter[str] = Counter()
        self.query_result_counts: Counter[str] = Counter()
        self.query_signatures: Counter[str] = Counter()
        self.read_counts: Counter[str] = Counter()
        self.read_suffix_counts: Counter[str] = Counter()
        self.stage_read_counts: defaultdict[str, Counter[str]] = defaultdict(Counter)
        self.stage_read_bytes: Counter[str] = Counter()
        self.read_bytes = 0
        self._stack: list[list[Any]] = []
        self._patches: list[tuple[object, str, Any]] = []

    @staticmethod
    def _signature(operation: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
        def normalized(value: Any) -> Any:
            if isinstance(value, Path):
                return "<path>"
            if isinstance(value, dict):
                return {str(key): normalized(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
            if isinstance(value, (list, tuple)):
                return [normalized(item) for item in value]
            if isinstance(value, (str, int, float, bool)) or value is None:
                return value
            return f"<{type(value).__name__}>"

        encoded = json.dumps(
            {"operation": operation, "args": normalized(args), "kwargs": normalized(kwargs)},
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _result_count(result: Any) -> int:
        if isinstance(result, dict):
            for key in ("results", "items", "records", "entries"):
                records = result.get(key)
                if isinstance(records, list):
                    return len(records)
            return 1
        if isinstance(result, list):
            return len(result)
        return 0

    def call(self, stage: str, function: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        self.stage_calls[stage] += 1
        frame: list[Any] = [stage, perf_counter(), 0.0]
        self._stack.append(frame)
        try:
            return function(*args, **kwargs)
        except Exception:
            self.stage_failures[stage] += 1
            raise
        finally:
            elapsed = perf_counter() - frame[1]
            self._stack.pop()
            self.stage_inclusive_seconds[stage] += elapsed
            self.stage_exclusive_seconds[stage] += max(0.0, elapsed - frame[2])
            if self._stack:
                self._stack[-1][2] += elapsed

    def wrap(self, module: ModuleType, name: str, stage: str, *, query: bool = False) -> None:
        original = getattr(module, name, None)
        if not callable(original):
            return

        @functools.wraps(original)
        def measured(*args: Any, **kwargs: Any) -> Any:
            if query:
                self.query_calls[name] += 1
                self.query_signatures[self._signature(name, args, kwargs)] += 1
            result = self.call(stage, original, *args, **kwargs)
            if query:
                self.query_result_counts[name] += self._result_count(result)
            return result

        self._patches.append((module, name, original))
        setattr(module, name, measured)

    def _patch_path_reads(self) -> None:
        original_read_text = Path.read_text
        original_read_bytes = Path.read_bytes

        @functools.wraps(original_read_text)
        def read_text(path: Path, *args: Any, **kwargs: Any) -> str:
            content = original_read_text(path, *args, **kwargs)
            self._record_read(path, len(content.encode("utf-8")))
            return content

        @functools.wraps(original_read_bytes)
        def read_bytes(path: Path, *args: Any, **kwargs: Any) -> bytes:
            content = original_read_bytes(path, *args, **kwargs)
            self._record_read(path, len(content))
            return content

        self._patches.extend([(Path, "read_text", original_read_text), (Path, "read_bytes", original_read_bytes)])
        Path.read_text = read_text  # type: ignore[assignment]
        Path.read_bytes = read_bytes  # type: ignore[assignment]

    def bind_atlas_root(
        self,
        root: Path,
        *,
        modules: list[ModuleType] | None = None,
        original: Callable[[], Path] | None = None,
    ) -> int:
        original_atlas_root = original or atlas_support.atlas_root
        bound_root = root.resolve()

        def bound_atlas_root() -> Path:
            return bound_root

        patched = 0
        candidates = modules if modules is not None else [
            module for module in sys.modules.values() if isinstance(module, ModuleType)
        ]
        for module in candidates:
            if getattr(module, "atlas_root", None) is not original_atlas_root:
                continue
            self._patches.append((module, "atlas_root", original_atlas_root))
            setattr(module, "atlas_root", bound_atlas_root)
            patched += 1
        return patched

    def _record_read(self, path: Path, size_bytes: int) -> None:
        identity = hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()
        suffix = path.suffix.lower() or "<none>"
        stage = str(self._stack[-1][0]) if self._stack else "unscoped"
        self.read_counts[identity] += 1
        self.read_suffix_counts[suffix] += 1
        self.stage_read_counts[stage][identity] += 1
        self.stage_read_bytes[stage] += size_bytes
        self.read_bytes += size_bytes

    def install(self) -> None:
        self._patch_path_reads()
        for name, stage in (
            ("load_stack_config", "bootstrap_config"),
            ("read_json", "bootstrap_inventory"),
            ("load_working_memory_catalog", "working_memory_catalog"),
            ("_resolve_target_repo_entries", "target_resolution"),
            ("_collect_related_initiatives", "initiative_selection"),
            ("_collect_related_proposals", "proposal_selection"),
            ("_collect_related_working_memory", "working_memory_selection"),
            ("_objective_query", "query_assembly"),
            ("_collect_initiative_attention_records", "attention_selection"),
            ("_collect_knowledge", "knowledge_selection"),
            ("_collect_deferred_repo_refs", "deferred_ref_selection"),
            ("_bootstrap_records", "bootstrap_record_selection"),
            ("stable_json_digest", "payload_digest"),
        ):
            self.wrap(context_builder, name, stage)

        for name, stage in (
            ("_load_snapshot", "status_snapshot_load"),
            ("_load_attention", "status_attention_load"),
            ("render_status_payload", "status_render"),
            ("_load_repo_inventory", "status_repo_inventory_load"),
            ("summarize_repo_inventory", "status_repo_inventory_summary"),
            ("_build_system_guardian_read_model", "status_system_guardian"),
            ("build_playbook_status_slices", "status_playbook_slices"),
            ("build_continuity_status_slices", "status_continuity_slices"),
        ):
            self.wrap(awareness, name, stage)

        for name, stage in (
            ("load_descriptors", "render_load_descriptors"),
            ("load_registry_state", "render_registry_state"),
            ("session_overview", "render_session_overview"),
            ("blocked_workers", "render_blocked_workers"),
            ("classify_merge_requests", "render_merge_requests"),
            ("closure_receipts", "render_closure_receipts"),
            ("execution_receipt_residue_records", "render_receipt_residue"),
            ("governed_writes", "render_governed_writes"),
            ("legacy_compatibility_surfaces", "render_legacy_compatibility"),
            ("trust_surfaces", "render_trust_surfaces"),
            ("trust_posture_summary", "render_trust_posture"),
            ("working_memory_summary", "render_working_memory"),
            ("provenance_alert_summary", "render_provenance_alerts"),
            ("conversation_summary", "render_conversations"),
            ("build_canonical_lockfile_artifacts", "render_canonical_lock"),
            ("repo_inventory_summary_from_lock", "render_repo_inventory"),
            ("lock_worktree_hygiene", "render_lock_hygiene"),
            ("attention_queue", "render_attention_queue"),
            ("proposal_only_state", "render_proposal_only"),
            ("registry_summary", "render_registry_summary"),
            ("artifact_inventory", "render_artifact_inventory"),
        ):
            self.wrap(cortex_status, name, stage)

        for name, stage in (
            ("build_continuity_source_manifest", "continuity_source_manifest"),
            ("build_historical_query_coverage", "continuity_historical_query"),
            ("build_initiative_continuity_manifest_health", "continuity_manifest_health"),
            ("build_open_marker_manifest_coverage", "continuity_marker_coverage"),
            ("build_open_marker_restart_index", "continuity_marker_restart"),
            ("build_maintained_manifest_restart_index", "continuity_maintained_restart"),
        ):
            self.wrap(continuity, name, stage)

        for name, stage in (
            ("_initiative_index", "repo_inventory_initiatives"),
            ("_live_repo_state", "repo_inventory_live_state"),
            ("current_ref", "repo_inventory_current_ref"),
            ("current_remote", "repo_inventory_current_remote"),
            ("_is_repo_dirty", "repo_inventory_dirty"),
            ("summarize_repo_inventory", "repo_inventory_summarize"),
        ):
            self.wrap(repo_inventory_builder, name, stage)

        for name, stage in (
            ("build_lock_payload", "lock_build_payload"),
            ("stack_root_dirty_state", "lock_stack_root_dirty"),
            ("repo_is_git_root", "lock_repo_identity"),
            ("current_ref", "lock_current_ref"),
            ("current_remote", "lock_current_remote"),
            ("git_status_lines", "lock_git_status"),
            ("excluded_surfaces", "lock_excluded_surfaces"),
            ("normalize_lock_payload", "lock_normalize_payload"),
        ):
            self.wrap(lockfile_builder, name, stage)

        query_functions = (
            ("atlas_status", "atlas_status"),
            ("fetch_status_slice", "status_slice_query"),
            ("fetch_memory", "memory_query"),
            ("fetch", "artifact_query"),
            ("list_attention", "attention_query"),
            ("query_knowledge", "knowledge_query"),
        )
        for name, stage in query_functions:
            self.wrap(context_builder, name, stage, query=True)
            self.wrap(awareness, name, stage, query=True)

    def restore(self) -> None:
        while self._patches:
            target, name, original = self._patches.pop()
            setattr(target, name, original)

    def report(self) -> dict[str, Any]:
        repeated_reads = sum(max(0, count - 1) for count in self.read_counts.values())
        repeated_queries = sum(max(0, count - 1) for count in self.query_signatures.values())
        stages = []
        for stage in sorted(self.stage_calls):
            stages.append(
                {
                    "stage": stage,
                    "calls": self.stage_calls[stage],
                    "failures": self.stage_failures[stage],
                    "inclusive_seconds": round(self.stage_inclusive_seconds[stage], 6),
                    "exclusive_seconds": round(self.stage_exclusive_seconds[stage], 6),
                }
            )
        reads_by_stage = []
        for stage in sorted(self.stage_read_counts):
            counts = self.stage_read_counts[stage]
            total = sum(counts.values())
            reads_by_stage.append(
                {
                    "stage": stage,
                    "total": total,
                    "unique_files": len(counts),
                    "repeated_reads": sum(max(0, count - 1) for count in counts.values()),
                    "bytes_returned": self.stage_read_bytes[stage],
                }
            )
        return {
            "wall_seconds": round(perf_counter() - self.started_at, 6),
            "stages": stages,
            "file_reads": {
                "total": sum(self.read_counts.values()),
                "unique_files": len(self.read_counts),
                "repeated_reads": repeated_reads,
                "bytes_returned": self.read_bytes,
                "reads_by_suffix": dict(sorted(self.read_suffix_counts.items())),
                "reads_by_stage": reads_by_stage,
            },
            "queries": {
                "calls_by_operation": dict(sorted(self.query_calls.items())),
                "result_count_by_operation": dict(sorted(self.query_result_counts.items())),
                "total_calls": sum(self.query_calls.values()),
                "unique_signatures": len(self.query_signatures),
                "repeated_calls": repeated_queries,
            },
            "cache_reuse": {
                "explicit_cache_contract_observed": False,
                "cache_hits": 0,
                "cache_misses": 0,
                "unclassified_repeated_query_calls": repeated_queries,
                "repeated_file_reads": repeated_reads,
                "classification": "REUSE_OPPORTUNITIES_OBSERVED_CACHE_CAUSALITY_UNKNOWN",
            },
        }


def _payload_sizes(payload: dict[str, Any], prompt: str, markdown: str) -> dict[str, int]:
    payload_bytes = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return {
        "context_json_bytes": len(payload_bytes),
        "prompt_utf8_bytes": len(prompt.encode("utf-8")),
        "markdown_utf8_bytes": len(markdown.encode("utf-8")),
        "selected_ref_count": sum(len(records) for records in payload.get("selected_refs", {}).values()),
        "ordered_read_count": len(payload.get("bootstrap_contract", {}).get("ordered_reads", [])),
    }


def _payload_identity(payload: dict[str, Any]) -> dict[str, str | None]:
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
    context_digest = payload.get("context_digest")
    return {
        "context_digest": str(context_digest) if isinstance(context_digest, str) else None,
        "payload_sha256": f"sha256:{hashlib.sha256(encoded).hexdigest()}",
    }


def _git_head(root: Path) -> str | None:
    completed = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def _source_hash(module: ModuleType, ref: str) -> dict[str, str]:
    source_path = Path(str(module.__file__)).resolve()
    return {
        "ref": ref,
        "sha256": f"sha256:{hashlib.sha256(source_path.read_bytes()).hexdigest()}",
    }


def profile_context_build(
    *,
    task_id: str,
    objective: str,
    intent_class: str,
    atlas_data_root: Path,
    target_repo_ids: list[str] | None = None,
    target_repo_paths: list[str] | None = None,
    verify_determinism: bool = True,
    build_function: Callable[..., dict[str, Any]] | None = None,
    prompt_renderer: Callable[[dict[str, Any]], str] | None = None,
    markdown_renderer: Callable[[dict[str, Any]], str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    build = build_function or context_builder.build_codex_context
    render_prompt = prompt_renderer or context_builder.render_codex_prompt
    render_markdown = markdown_renderer or context_builder.render_codex_context_markdown
    build_args = {
        "task_id": task_id,
        "objective": objective,
        "intent_class": intent_class,
        "target_repo_ids": target_repo_ids or [],
        "target_repo_paths": target_repo_paths or [],
        "root": atlas_data_root.resolve(),
    }

    probe = AggregateProbe()
    probe.install()
    bound_root_aliases = probe.bind_atlas_root(atlas_data_root)
    try:
        payload = probe.call("context_build", build, **build_args)
        prompt = probe.call("prompt_render", render_prompt, payload)
        markdown = probe.call("markdown_render", render_markdown, payload)
    finally:
        probe.restore()
    measurement_report = probe.report()

    deterministic = {"checked": False, "payload_equal": None, "context_digest_equal": None, "reference_wall_seconds": None}
    if verify_determinism:
        reference_started = perf_counter()
        reference_binding = AggregateProbe()
        reference_binding.bind_atlas_root(atlas_data_root)
        try:
            reference_payload = build(**build_args)
        finally:
            reference_binding.restore()
        deterministic = {
            "checked": True,
            "payload_equal": payload == reference_payload,
            "context_digest_equal": payload.get("context_digest") == reference_payload.get("context_digest"),
            "reference_wall_seconds": round(perf_counter() - reference_started, 6),
        }

    builder_path = Path(context_builder.__file__).resolve()
    report = {
        "schema": SCHEMA_VERSION,
        "source_identity": {
            "source_commit": _git_head(ROOT),
            "scoped_sources": {
                "builder": {
                    "ref": "ops/atlas/build_codex_context.py",
                    "sha256": f"sha256:{hashlib.sha256(builder_path.read_bytes()).hexdigest()}",
                },
                "awareness": _source_hash(awareness, "ops/atlas/awareness.py"),
                "continuity": _source_hash(continuity, "ops/atlas/continuity.py"),
                "measurement_wrapper": {
                    "ref": "ops/atlas/profile_codex_context.py",
                    "sha256": f"sha256:{hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest()}",
                },
            },
        },
        "privacy": {
            "aggregate_only": True,
            "raw_paths_retained": False,
            "raw_content_retained": False,
            "raw_query_text_retained": False,
        },
        "measurement": measurement_report,
        "root_binding": {
            "transitive_aliases_bound": bound_root_aliases,
            "explicit_data_root": True,
            "raw_data_root_retained": False,
        },
        "payload_sizes": _payload_sizes(payload, prompt, markdown),
        "payload_identity": _payload_identity(payload),
        "deterministic_regression": deterministic,
    }
    return payload, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Profile one ATLAS Codex context build with aggregate-only counters.")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--objective", required=True)
    parser.add_argument("--intent-class", required=True)
    parser.add_argument("--atlas-data-root", required=True)
    parser.add_argument("--target-repo", action="append", default=[])
    parser.add_argument("--target-path", action="append", default=[])
    parser.add_argument("--output", required=True)
    parser.add_argument("--skip-determinism-check", action="store_true")
    args = parser.parse_args(argv)

    _payload, report = profile_context_build(
        task_id=args.task_id,
        objective=args.objective,
        intent_class=args.intent_class,
        atlas_data_root=Path(args.atlas_data_root),
        target_repo_ids=args.target_repo,
        target_repo_paths=args.target_path,
        verify_determinism=not args.skip_determinism_check,
    )
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "measured", "schema": SCHEMA_VERSION, "output_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
