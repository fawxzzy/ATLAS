from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root, normalize_slashes

SCHEMA_VERSION = "atlas.cortex.chatgpt_codex_role_inventory.v1"
STATUS_OK = "ok"
STATUS_ADVISORY = "advisory_gap"
STATUS_BLOCKER = "blocker"
STATUS_INTERNAL_ERROR = "internal_error"

DEFAULT_SOURCE_REFS = (
    "AGENTS.md",
    "docs/PLAYBOOK_NOTES.md",
    "docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md",
    "docs/atlas-book/05-receipt-index.md",
    "docs/memory/profiles/zachariah_workflow_profile.md",
    "docs/ops/CORTEX-DUAL-MODE-AND-SIMULATION-SUBSTRATE-MARKER-ADMISSION-2026-07-09.md",
    "docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-OPERATING-MODE-CONTRACT-FREEZE-2026-07-09.md",
    "docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHATGPT-CODEX-ROLE-INVENTORY-FIRST-IMPLEMENTATION-ADMISSION-2026-07-09.md",
    "docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHATGPT-CODEX-ROLE-INVENTORY-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-09.md",
    "docs/registry/STACK-REPO-INVENTORY.json",
)

ALLOWED_EXACT_SOURCE_REFS = set(DEFAULT_SOURCE_REFS)
CORE_REQUIRED_SOURCE_REFS = {
    "docs/memory/profiles/zachariah_workflow_profile.md",
    "docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-OPERATING-MODE-CONTRACT-FREEZE-2026-07-09.md",
    "docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHATGPT-CODEX-ROLE-INVENTORY-FIRST-IMPLEMENTATION-ADMISSION-2026-07-09.md",
    "docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHATGPT-CODEX-ROLE-INVENTORY-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-09.md",
}
PROTECTED_PREFIXES = (
    ".github/workflows",
    ".playwright-mcp",
    ".vercel",
    "archive",
    "repos",
    "secrets",
)
DEPLOY_OR_PLATFORM_PREFIXES = (
    "deploy",
    "deployment",
    "platform",
    "vercel",
)
HIDDEN_CONTEXT_PREFIXES = (
    ".codex",
    "runtime/chats",
    "runtime/session",
    "runtime/sessions",
    "runtime/transcripts",
    "runtime/atlas/conversations",
    "runtime/atlas/sessions",
    "tmp/chats",
    "tmp/transcripts",
)
AUTHORITY_DENIALS = (
    "execution",
    "approval",
    "owner-truth",
    "final-receipt",
    "deploy",
    "secret-handling",
    "transcript-scraping",
    "automatic-_stack-dispatch",
    "repo-mutation",
    "platform-mutation",
    "owner-repo-mutation",
    "protected-surface-mutation",
    "workflow-dispatch",
    "marker-movement",
)
FORBIDDEN_SURFACES = (
    "repos/**",
    "archive/**",
    ".vercel/**",
    ".playwright-mcp/**",
    "secrets/**",
    ".env*",
    ".github/workflows/**",
    "deployment outputs",
    "deploy/platform outputs",
    "owner-repo receipts as truth inputs",
    "runtime latest files by default",
    "final Lifeline receipts",
    "hidden transcript/chat/session state",
)
ALLOWED_ROLE_CLASSES = {
    "synthesis_strategy",
    "research_synthesis",
    "packet_framing",
    "operator_facing_tradeoff_compression",
    "execution_mutation",
    "verification_and_tests",
    "proof_and_receipt_capture",
    "execution_reconciliation",
}
ALLOWED_FUTURE_TARGETS = (
    "cortex_synthesis_interface",
    "cortex_execution_interface",
    "cortex_bridge",
    "shared_atlas_substrate",
    "shared_playbook_doctrine_substrate",
)
SHARED_SUBSTRATE_DEPENDENCIES = (
    "shared_atlas_substrate",
    "shared_playbook_doctrine_substrate",
)
RISK_CODES = (
    "memory_truth_split",
    "doctrine_truth_split",
    "execution_truth_split",
    "marker_authority_split",
    "bridge_scope_ambiguity",
)


def _finding(code: str, message: str, **details: Any) -> OrderedDict[str, Any]:
    payload: OrderedDict[str, Any] = OrderedDict([("code", code), ("message", message)])
    if details:
        payload["details"] = details
    return payload


def _git_stdout(root: Path, *args: str) -> str | None:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def collect_git_state(root: Path) -> tuple[str | None, str | None]:
    return _git_stdout(root, "branch", "--show-current"), _git_stdout(root, "rev-parse", "HEAD")


def _has_env_component(ref: str) -> bool:
    return any(part.startswith(".env") for part in ref.split("/"))


def _is_prefix_match(ref: str, prefixes: tuple[str, ...]) -> bool:
    return any(ref == prefix or ref.startswith(f"{prefix}/") for prefix in prefixes)


def _normalize_ref(candidate: str | Path, root: Path) -> tuple[str | None, OrderedDict[str, Any] | None]:
    value = Path(candidate)
    if value.is_absolute():
        return None, _finding("absolute_path_forbidden", "Path must be root-relative.", path=normalize_slashes(str(value)))
    ref = normalize_slashes(str(value)).strip("/")
    if not ref or ref.startswith("../") or "/../" in f"/{ref}/":
        return None, _finding("parent_traversal_forbidden", "Path must not use parent traversal.", path=ref)
    if _has_env_component(ref):
        return None, _finding("secret_path_forbidden", "Path targets an .env secret surface.", path=ref)
    if _is_prefix_match(ref, PROTECTED_PREFIXES):
        return None, _finding("owner_repo_source_forbidden", "Owner or protected repo surfaces are not admitted.", path=ref)
    if _is_prefix_match(ref, DEPLOY_OR_PLATFORM_PREFIXES):
        return None, _finding("deploy_platform_path_forbidden", "Deploy and platform surfaces are not admitted.", path=ref)
    parts = tuple(part.lower() for part in ref.split("/"))
    hidden_tokens = {"transcript", "transcripts", "chat", "chats", "session", "sessions"}
    if _is_prefix_match(ref, HIDDEN_CONTEXT_PREFIXES) or any(part in hidden_tokens for part in parts):
        return None, _finding("hidden_context_path_forbidden", "Hidden transcript, chat, or session state is not admitted.", path=ref)
    resolved = (root / ref).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding("outside_root_path", "Path must stay inside the ATLAS root.", path=ref)
    return ref, None


def is_allowed_source_ref(ref: str) -> bool:
    return ref in ALLOWED_EXACT_SOURCE_REFS


def resolve_sources(root: Path, requested_sources: list[str] | None = None) -> tuple[list[str], list[OrderedDict[str, Any]]]:
    errors: list[OrderedDict[str, Any]] = []
    refs: list[str] = []
    seen: set[str] = set()
    candidates = requested_sources or list(DEFAULT_SOURCE_REFS)
    for source in candidates:
        ref, error = _normalize_ref(source, root)
        if error is not None:
            errors.append(error)
            continue
        if ref is None:
            continue
        if not is_allowed_source_ref(ref):
            errors.append(_finding("source_not_admitted", "Source path is outside the admitted role-inventory doctrine set.", path=ref))
            continue
        if ref not in seen:
            refs.append(ref)
            seen.add(ref)
    return refs, errors


def validate_output_path(root: Path, output: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    ref, error = _normalize_ref(output, root)
    if error is not None or ref is None:
        return None, error
    if not ref.startswith("tmp/") or not ref.endswith(".json"):
        return None, _finding("non_tmp_json_output_path", "Output path must be under tmp/** and end with .json.", path=ref)
    return (root / ref).resolve(), None


def read_validation(root: Path) -> tuple[OrderedDict[str, int], OrderedDict[str, Any] | None]:
    path = root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json"
    counts = OrderedDict([("critical", 0), ("error", 0), ("warning", 0), ("info", 0)])
    if not path.exists():
        return counts, _finding("validation_missing", "Stack validation receipt is unavailable.", path="runtime/receipts/validation/stack-validation.latest.json")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return counts, _finding("validation_malformed", "Stack validation receipt is not valid JSON.", exception=str(exc))
    summary = payload.get("summary") if isinstance(payload, dict) else {}
    if not isinstance(summary, dict):
        return counts, _finding("validation_summary_missing", "Stack validation summary is unavailable.")
    for key in counts:
        counts[key] = int(summary.get(key, 0) or 0)
    return counts, None


def _read_sources(root: Path, source_refs: list[str]) -> tuple[OrderedDict[str, str], list[OrderedDict[str, Any]]]:
    texts: OrderedDict[str, str] = OrderedDict()
    blockers: list[OrderedDict[str, Any]] = []
    for ref in source_refs:
        path = (root / ref).resolve()
        if not path.exists() or not path.is_file():
            blockers.append(_finding("source_missing", "Admitted source path is missing.", path=ref))
            continue
        try:
            texts[ref] = path.read_text(encoding="utf-8")
        except OSError as exc:
            blockers.append(_finding("source_read_failed", "Admitted source path could not be read.", path=ref, exception=str(exc)))
    return texts, blockers


def _evidence_phrase_present(texts: dict[str, str], phrases: tuple[str, ...]) -> bool:
    lowered_texts = [value.lower() for value in texts.values()]
    lowered_phrases = [phrase.lower() for phrase in phrases]
    return any(phrase in text for phrase in lowered_phrases for text in lowered_texts)


def _role(
    *,
    role_id: str,
    role_class: str,
    current_system: str,
    role_summary: str,
    future_target: str,
    shared_substrate_dependency: str,
    authority_requirements: list[str],
    migration_notes: str,
) -> OrderedDict[str, Any]:
    if role_class not in ALLOWED_ROLE_CLASSES:
        raise ValueError(f"Unadmitted role class: {role_class}")
    if future_target not in ALLOWED_FUTURE_TARGETS:
        raise ValueError(f"Unadmitted future target: {future_target}")
    if shared_substrate_dependency not in SHARED_SUBSTRATE_DEPENDENCIES:
        raise ValueError(f"Unadmitted shared substrate dependency: {shared_substrate_dependency}")
    return OrderedDict(
        [
            ("role_id", role_id),
            ("current_role_class", role_class),
            ("current_system", current_system),
            ("role_summary", role_summary),
            ("future_target", future_target),
            ("shared_substrate_dependency", shared_substrate_dependency),
            ("authority_requirements", authority_requirements),
            ("migration_notes", migration_notes),
        ]
    )


def build_role_inventory(*, texts: dict[str, str], source_refs: list[str]) -> tuple[list[OrderedDict[str, Any]], list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    warnings: list[OrderedDict[str, Any]] = []
    blockers: list[OrderedDict[str, Any]] = []
    roles: list[OrderedDict[str, Any]] = []

    missing_core_refs = sorted(CORE_REQUIRED_SOURCE_REFS - set(source_refs))
    if missing_core_refs:
        blockers.append(_finding("core_source_missing", "Core doctrine sources are required for role inventory classification.", refs=missing_core_refs))
        return roles, warnings, blockers

    has_chatgpt = _evidence_phrase_present(texts, ("chatgpt-style", "current chatgpt mapping", "chatgpt: quick decisions"))
    has_codex = _evidence_phrase_present(texts, ("codex-style", "current codex mapping", "codex: implementation work"))
    has_deep_research = _evidence_phrase_present(texts, ("deep research",))
    has_pro_chat = _evidence_phrase_present(texts, ("pro chat",))
    has_normal_chat = _evidence_phrase_present(texts, ("chatgpt: quick decisions",))
    has_atlas = _evidence_phrase_present(texts, ("atlas", "atlas root"))
    has_playbook = _evidence_phrase_present(texts, ("playbook", "playbook cli"))
    has_cortex = _evidence_phrase_present(texts, ("cortex synthesis interface", "cortex execution interface", "cortex bridge"))

    if has_chatgpt:
        roles.append(
            _role(
                role_id="chatgpt_synthesis",
                role_class="synthesis_strategy",
                current_system="ChatGPT",
                role_summary="Questions, ideas, explaining concepts, drafting, option comparison, and decision framing stay on the synthesis side.",
                future_target="cortex_synthesis_interface",
                shared_substrate_dependency="shared_playbook_doctrine_substrate",
                authority_requirements=["no repo mutation", "no marker movement", "no owner-truth authority"],
                migration_notes="Derived from workflow-profile ChatGPT routing plus the dual-mode operating-model current ChatGPT mapping.",
            )
        )
        roles.append(
            _role(
                role_id="chatgpt_packet_framing",
                role_class="packet_framing",
                current_system="ChatGPT",
                role_summary="Packet framing and tradeoff compression stay explicit rather than leaking into free-form execution authority.",
                future_target="cortex_bridge",
                shared_substrate_dependency="shared_playbook_doctrine_substrate",
                authority_requirements=["bridge preserves doctrine", "bridge denies deploy authority", "bridge denies final receipt authority"],
                migration_notes="Bridge-facing synthesis posture is frozen in the operating-model and prompt-pack receipts.",
            )
        )
    if has_deep_research:
        roles.append(
            _role(
                role_id="deep_research_synthesis",
                role_class="research_synthesis",
                current_system="Deep Research",
                role_summary="Current external research lane supplies high-stakes or current-fact synthesis without mutating stack truth directly.",
                future_target="cortex_synthesis_interface",
                shared_substrate_dependency="shared_playbook_doctrine_substrate",
                authority_requirements=["no owner-truth authority", "no hidden transcript dependence"],
                migration_notes="Present in the workflow profile reasoning-depth routes and preserved as optional external scaffolding.",
            )
        )
    if has_pro_chat:
        roles.append(
            _role(
                role_id="pro_chat_tradeoff_compression",
                role_class="operator_facing_tradeoff_compression",
                current_system="Pro Chat",
                role_summary="Deeper technical reasoning and architecture review remain synthesis-facing but operator-visible.",
                future_target="cortex_synthesis_interface",
                shared_substrate_dependency="shared_playbook_doctrine_substrate",
                authority_requirements=["no repo mutation", "no deploy authority"],
                migration_notes="Present in the workflow profile reasoning-depth routes as the deeper synthesis lane.",
            )
        )
    if has_normal_chat:
        roles.append(
            _role(
                role_id="normal_chat_quick_framing",
                role_class="packet_framing",
                current_system="Normal Chat",
                role_summary="Quick decisions and lightweight planning remain the lightweight synthesis entrypoint.",
                future_target="cortex_synthesis_interface",
                shared_substrate_dependency="shared_playbook_doctrine_substrate",
                authority_requirements=["no owner-truth authority", "no repo mutation"],
                migration_notes="Inferred from the workflow profile ChatGPT route as the normal-chat counterpart of the external synthesis scaffold.",
            )
        )
    if has_codex:
        roles.append(
            _role(
                role_id="codex_execution",
                role_class="execution_mutation",
                current_system="Codex",
                role_summary="Codebase understanding, bounded implementation, and reviewable edits remain execution-facing responsibilities.",
                future_target="cortex_execution_interface",
                shared_substrate_dependency="shared_atlas_substrate",
                authority_requirements=["bounded file scope", "no owner-truth authority", "no marker authority"],
                migration_notes="Derived from workflow-profile Codex routing plus the dual-mode operating-model current Codex mapping.",
            )
        )
        roles.append(
            _role(
                role_id="codex_verification",
                role_class="verification_and_tests",
                current_system="Codex",
                role_summary="Tests, linters, typecheckers, and terminal evidence stay bound to execution proof rather than synthesis claims.",
                future_target="cortex_execution_interface",
                shared_substrate_dependency="shared_atlas_substrate",
                authority_requirements=["test evidence only", "no final receipt authority", "no deploy authority"],
                migration_notes="Proof posture is frozen in the workflow profile and operating-model execution mapping.",
            )
        )
        roles.append(
            _role(
                role_id="codex_receipt_capture",
                role_class="proof_and_receipt_capture",
                current_system="Codex",
                role_summary="Execution closeout evidence must flow back into ATLAS receipts rather than creating private worker truth.",
                future_target="shared_atlas_substrate",
                shared_substrate_dependency="shared_atlas_substrate",
                authority_requirements=["receipt-backed truth only", "no marker movement", "no owner-truth authority"],
                migration_notes="Codex remains the execution worker while ATLAS stays the durable proof substrate.",
            )
        )
    if has_atlas:
        roles.append(
            _role(
                role_id="atlas_governance",
                role_class="execution_reconciliation",
                current_system="ATLAS",
                role_summary="Governance, receipts, manifests, restart truth, and reconciliation stay owned by ATLAS rather than by external scaffolding.",
                future_target="shared_atlas_substrate",
                shared_substrate_dependency="shared_atlas_substrate",
                authority_requirements=["owner of canonical memory", "owner of receipt truth", "no silent execution widening"],
                migration_notes="ATLAS remains the durable source of truth in AGENTS, workflow profile, and architecture doctrine.",
            )
        )
    if has_playbook:
        roles.append(
            _role(
                role_id="playbook_doctrine",
                role_class="packet_framing",
                current_system="Playbook",
                role_summary="Reusable doctrine, patterns, and failure modes stay shared contract truth across synthesis and execution.",
                future_target="shared_playbook_doctrine_substrate",
                shared_substrate_dependency="shared_playbook_doctrine_substrate",
                authority_requirements=["doctrine-first routing", "no stack-truth replacement"],
                migration_notes="Architecture and notes doctrine keep Playbook as the repo-runtime and doctrine layer, not the stack root.",
            )
        )
    if has_cortex:
        roles.append(
            _role(
                role_id="cortex_bridge",
                role_class="packet_framing",
                current_system="Cortex",
                role_summary="The Cortex bridge must translate synthesis outputs into bounded execution packets without widening authority.",
                future_target="cortex_bridge",
                shared_substrate_dependency="shared_playbook_doctrine_substrate",
                authority_requirements=["bridge denies deploy authority", "bridge denies marker authority", "bridge preserves shared doctrine"],
                migration_notes="The operating-model contract freezes Cortex as one substrate with synthesis, execution, and bridge interfaces.",
            )
        )
        roles.append(
            _role(
                role_id="cortex_future_execution",
                role_class="execution_reconciliation",
                current_system="Cortex",
                role_summary="Future Cortex execution must consume bounded packets, return proof, and stay subordinate to ATLAS governance.",
                future_target="cortex_execution_interface",
                shared_substrate_dependency="shared_atlas_substrate",
                authority_requirements=["no owner-truth authority", "no final receipt authority", "proof-backed execution only"],
                migration_notes="Future execution-interface posture is frozen in the operating-model contract and architecture notes.",
            )
        )

    required_systems = ("ChatGPT", "Codex", "ATLAS", "Playbook", "Cortex")
    present_systems = {role["current_system"] for role in roles}
    missing_systems = [system for system in required_systems if system not in present_systems]
    if missing_systems:
        blockers.append(_finding("required_role_system_missing", "One or more required role systems could not be classified safely.", systems=missing_systems))

    return roles, warnings, blockers


def build_role_inventory_report(*, root: Path | None = None, sources: list[str] | None = None) -> OrderedDict[str, Any]:
    base = (root or atlas_root()).resolve()
    branch, head = collect_git_state(base)
    warnings: list[OrderedDict[str, Any]] = []
    blockers: list[OrderedDict[str, Any]] = []

    source_refs, source_errors = resolve_sources(base, requested_sources=sources)
    blockers.extend(source_errors)
    texts, source_blockers = _read_sources(base, source_refs)
    blockers.extend(source_blockers)

    validation_counts, validation_error = read_validation(base)
    if validation_error is not None:
        warnings.append(validation_error)
    if validation_counts["critical"] or validation_counts["error"]:
        blockers.append(
            _finding(
                "validation_not_safe",
                "Stack validation has critical or error findings; role inventory is not safe to use.",
                critical=validation_counts["critical"],
                error=validation_counts["error"],
            )
        )

    role_inventory: list[OrderedDict[str, Any]] = []
    if not blockers:
        role_inventory, inventory_warnings, inventory_blockers = build_role_inventory(texts=texts, source_refs=source_refs)
        warnings.extend(inventory_warnings)
        blockers.extend(inventory_blockers)

    synthesis_roles = [role for role in role_inventory if role["future_target"] == "cortex_synthesis_interface"]
    execution_roles = [role for role in role_inventory if role["future_target"] == "cortex_execution_interface"]
    bridge_roles = [role for role in role_inventory if role["future_target"] == "cortex_bridge"]
    simulation_roles: list[OrderedDict[str, Any]] = []
    replacement_targets = list(OrderedDict.fromkeys(role["future_target"] for role in role_inventory))
    external_dependencies = list(
        OrderedDict.fromkeys(
            role["current_system"]
            for role in role_inventory
            if role["current_system"] in {"ChatGPT", "Codex", "Deep Research", "Pro Chat", "Normal Chat"}
        )
    )
    split_brain_risks = list(RISK_CODES)
    shared_substrate_dependencies = list(
        OrderedDict.fromkeys(role["shared_substrate_dependency"] for role in role_inventory)
    )

    status = STATUS_OK
    if blockers:
        status = STATUS_BLOCKER
    elif warnings:
        status = STATUS_ADVISORY

    safe_to_use = status == STATUS_OK
    mapped_role_count = sum(1 for role in role_inventory if role["future_target"] in ALLOWED_FUTURE_TARGETS)

    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("root", normalize_slashes(str(base))),
            ("branch", branch),
            ("head", head),
            ("source_refs", source_refs),
            ("role_inventory", role_inventory),
            ("synthesis_roles", synthesis_roles),
            ("execution_roles", execution_roles),
            ("bridge_roles", bridge_roles),
            ("simulation_roles", simulation_roles),
            ("replacement_targets", replacement_targets),
            ("external_dependencies", external_dependencies),
            ("current_role_count", len(role_inventory)),
            ("mapped_role_count", mapped_role_count),
            ("unmapped_role_count", len(role_inventory) - mapped_role_count),
            ("current_roles", role_inventory),
            ("future_interface_targets", replacement_targets),
            ("shared_substrate_dependencies", shared_substrate_dependencies),
            ("authority_denials", list(AUTHORITY_DENIALS)),
            ("forbidden_surfaces", list(FORBIDDEN_SURFACES)),
            ("split_brain_risks", split_brain_risks),
            ("warnings", warnings),
            ("blockers", blockers),
            ("safe_to_use", safe_to_use),
        ]
    )


def render_summary(report: OrderedDict[str, Any]) -> str:
    return "\n".join(
        [
            "ChatGPT/Codex Role Inventory",
            f"Status: {report['status']}",
            f"Branch: {report.get('branch') or 'unknown'}",
            f"Head: {report.get('head') or 'unknown'}",
            f"Sources consumed: {len(report.get('source_refs', []))}",
            f"Current roles: {report.get('current_role_count', 0)}",
            f"Safe to use: {str(report.get('safe_to_use')).lower()}",
            "Authority: advisory only; no execution, approval, owner-truth, deploy, secret, workflow dispatch, _stack dispatch, mutation, or marker movement authority.",
        ]
    ) + "\n"


def exit_code(status: str, *, strict: bool) -> int:
    if status == STATUS_OK:
        return 0
    if status == STATUS_ADVISORY:
        return 1 if strict else 0
    if status == STATUS_BLOCKER:
        return 2
    return 3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a read-only ChatGPT/Codex role inventory for the Cortex dual-mode lane.")
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON only.")
    parser.add_argument("--source", action="append", default=[], help="Optional repeatable admitted root-relative source ref.")
    parser.add_argument("--output", help="Optional root-relative tmp/**.json output path.")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    root = atlas_root().resolve()
    try:
        report = build_role_inventory_report(root=root, sources=list(args.source or []))
        if args.output:
            resolved_output, output_error = validate_output_path(root, args.output)
            if output_error is not None:
                report["status"] = STATUS_BLOCKER
                report["blockers"] = list(report.get("blockers", [])) + [output_error]
                report["safe_to_use"] = False
            elif resolved_output is not None:
                resolved_output.parent.mkdir(parents=True, exist_ok=True)
                resolved_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(render_summary(report), end="")
        return exit_code(str(report.get("status") or STATUS_INTERNAL_ERROR), strict=args.strict)
    except Exception as exc:
        report = OrderedDict(
            [
                ("schema_version", SCHEMA_VERSION),
                ("status", STATUS_INTERNAL_ERROR),
                ("root", normalize_slashes(str(root))),
                ("branch", None),
                ("head", None),
                ("source_refs", []),
                ("role_inventory", []),
                ("synthesis_roles", []),
                ("execution_roles", []),
                ("bridge_roles", []),
                ("simulation_roles", []),
                ("replacement_targets", []),
                ("external_dependencies", []),
                ("current_role_count", 0),
                ("mapped_role_count", 0),
                ("unmapped_role_count", 0),
                ("current_roles", []),
                ("future_interface_targets", []),
                ("shared_substrate_dependencies", []),
                ("authority_denials", list(AUTHORITY_DENIALS)),
                ("forbidden_surfaces", list(FORBIDDEN_SURFACES)),
                ("split_brain_risks", list(RISK_CODES)),
                ("warnings", []),
                ("blockers", [_finding("internal_error", "Role inventory failed before completion.", exception=str(exc))]),
                ("safe_to_use", False),
            ]
        )
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(render_summary(report), end="")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
