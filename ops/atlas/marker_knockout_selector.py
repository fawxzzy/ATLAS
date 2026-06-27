from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root
from ops.atlas.continuity import build_open_marker_restart_index

MARKER_LINE_PATTERN = re.compile(r"^- ([^:]+): `(\d+)%`$")
ACTIVE_LANE_PATTERNS = (
    re.compile(r"the current active ATLAS-side lane is now `([^`]+)`", re.IGNORECASE),
    re.compile(r"the next durable ATLAS-side active lane is now `([^`]+)`", re.IGNORECASE),
    re.compile(r"the current immediate control-plane family is now `([^`]+)`", re.IGNORECASE),
)
SECTION_HEADERS = {
    "## Active Front-Page Marker Table": "active_front_page",
    "## Supporting Open Markers": "supporting_open",
    "## Closed / Locked Ratchets": "closed_locked",
}

CAMPAIGN_PRIORITY = (
    "AI Repetition-to-Automation Pipeline",
    "AI Long-Run Batch Orchestration",
    "Sandbox Simulation Readiness",
    "Feedback Loop Readiness",
    "Durable Context Externalization",
    "Knowledge Capture & Transfer",
    "Truth Map & ATLAS Book",
    "Inventory & Truth Map",
    "Playbook Everywhere + Cortex Interface",
    "Cortex Readiness",
    "Core Pattern Convergence",
    "Discord Workflow, Publication & Docs Reliability",
    "DiscordOS Runtime & Product Hardening",
    "Discord OS Feedback Workflow Canonicalization",
    "Discord OS Infrastructure Separation",
    "Local Data Gateway",
    "Dependency Untangling",
    "Atlas-owned Repo Naming Canonicalization",
    "Preview Cache & Surface Consistency",
    "Vercel Hobby Cost Governance",
    "Operator Secret Path Hygiene",
    "Manual Deploy Exception Burn-Down",
    "Post-Convergence Lane Split Readiness",
    "Vision & Future Alignment",
)

ALLOWED_CATEGORIES = {
    "admissible now",
    "admissible after current lane",
    "protected/Fitness hold",
    "owner-repo hold",
    "archive/delete hold",
    "deploy/publication hold",
    "secret/.env hold",
    "insufficient evidence / needs selector only",
    "already closed / locked",
}


@dataclass(frozen=True)
class MarkerPolicy:
    category: str
    rationale: str
    expected_evidence: str


@dataclass(frozen=True)
class MarkerRecord:
    marker: str
    percentage: int
    section: str
    category: str
    rationale: str
    expected_evidence: str
    priority: int


@dataclass(frozen=True)
class PacketDescriptor:
    packet: str
    basis_receipt_ref: str
    mode: str | None = None
    scope: str | None = None


@dataclass(frozen=True)
class PacketReceiptContext:
    basis_receipt_ref: str
    mode: str
    scope: str


POLICY_REGISTRY: dict[str, MarkerPolicy] = {
    "_stack Readiness": MarkerPolicy(
        category="already closed / locked",
        rationale="The lane is already proof-closed at 100% and the operator packet explicitly says not to reopen it.",
        expected_evidence="none; preserve 100% and do not reopen without a genuinely new blocker class or authority change",
    ),
    "Atlas-owned Repo Naming Canonicalization": MarkerPolicy(
        category="insufficient evidence / needs selector only",
        rationale="Current truth says the lane is held unless one direct naming or path dependency is actually admitted later.",
        expected_evidence="one direct live naming/path dependency that creates a bounded root-owned packet",
    ),
    "Local Data Gateway": MarkerPolicy(
        category="insufficient evidence / needs selector only",
        rationale="The process-and-placement threshold is materially held and no direct new adoptable-now packet is active from current truth.",
        expected_evidence="one new reusable proof family or a direct dependency that reopens the lane as root-owned work",
    ),
    "Dependency Untangling": MarkerPolicy(
        category="insufficient evidence / needs selector only",
        rationale="Current root truth does not expose one exact non-destructive root-only packet from this marker.",
        expected_evidence="one bounded dependency inventory or contract packet that does not widen into owner-repo mutation",
    ),
    "Truth Map & ATLAS Book": MarkerPolicy(
        category="admissible after current lane",
        rationale="The lane is root-owned and close to saturation, but current truth says docs-only follow-on should come after more execution-facing evidence rather than ahead of it.",
        expected_evidence="one new execution-backed state change that the Book must absorb into canonical restart truth",
    ),
    "Inventory & Truth Map": MarkerPolicy(
        category="admissible after current lane",
        rationale="The inventory spine is root-owned and durable, but current truth does not make it the first honest execution-facing packet.",
        expected_evidence="one new decisive receipt cluster that materially changes the live cross-system inventory map",
    ),
    "Knowledge Capture & Transfer": MarkerPolicy(
        category="admissible after current lane",
        rationale="The marker is root-owned and restart-relevant, but it remains downstream of fresh execution evidence rather than the first packet to reopen.",
        expected_evidence="one additional reusable evidence cluster that widens transfer-ready truth beyond the current bundle",
    ),
    "Durable Context Externalization": MarkerPolicy(
        category="admissible after current lane",
        rationale="The lane is root-owned and healthy, but current truth says it should reopen from real adjacent execution-state change rather than projection upkeep alone.",
        expected_evidence="one broadened manifest-backed or restart-backed externalization that survives refresh",
    ),
    "Discord OS Infrastructure Separation": MarkerPolicy(
        category="owner-repo hold",
        rationale="Current receipts allow only bridge-independent follow-on while runtime, schema, and cutover work remain outside this root-only packet.",
        expected_evidence="one explicit new DiscordOS scope that stays owner-admitted and avoids runtime/schema/deploy authority",
    ),
    "Discord OS Feedback Workflow Canonicalization": MarkerPolicy(
        category="deploy/publication hold",
        rationale="The remaining evidence classes still lean on live workflow and publication proof rather than one root-only documentation packet.",
        expected_evidence="one bounded non-runtime proof or routing question that can be answered without deploy/publication authority",
    ),
    "Verta Absorption": MarkerPolicy(
        category="insufficient evidence / needs selector only",
        rationale="The dedicated Verta trust-gate boundary is still required, so this root campaign cannot treat it as an ordinary closeout marker.",
        expected_evidence="one dedicated Verta-scoped trust-gate or closeout packet in the correct lane",
    ),
    "ATLAS Core Phase": MarkerPolicy(
        category="insufficient evidence / needs selector only",
        rationale="Current surfaces expose broad capstone posture, not one exact bounded root-owned execution packet.",
        expected_evidence="one narrow, evidence-backed capstone packet that does not rely on owner or protected surfaces",
    ),
    "Lifeline Readiness": MarkerPolicy(
        category="owner-repo hold",
        rationale="Book truth explicitly says no immediate root-only Lifeline mutation packet is open by default; repo-local truth owns the next execution-facing work.",
        expected_evidence="one Lifeline-scoped owner packet or a root-only routing seam explicitly admitted by Lifeline truth",
    ),
    "Playbook Maturity": MarkerPolicy(
        category="owner-repo hold",
        rationale="The remaining work depends on Playbook-owned doctrine and repo-local surfaces rather than one immediate ATLAS-root packet.",
        expected_evidence="one root-routable Playbook contract or verification seam that does not require doctrine admission",
    ),
    "Cortex Readiness": MarkerPolicy(
        category="admissible after current lane",
        rationale="The lane is root-owned and the read-model surfaces are real, but the first reopen should still favor the more execution-facing AI pipeline lane.",
        expected_evidence="one new authority-false consumption or routing surface that widens bounded runtime breadth without shifting truth ownership",
    ),
    "Fitness QA/LLEL Workflow": MarkerPolicy(
        category="protected/Fitness hold",
        rationale="The operator packet keeps Fitness protected and this marker is explicitly held.",
        expected_evidence="explicit operator release of Fitness plus a bounded owner-side packet",
    ),
    "Fitness Branch Cleanup / Main-Only Governance": MarkerPolicy(
        category="protected/Fitness hold",
        rationale="The operator packet keeps Fitness protected and this marker is explicitly held.",
        expected_evidence="explicit operator release of Fitness plus a bounded owner-side packet",
    ),
    "Fitness Recovery Preservation": MarkerPolicy(
        category="protected/Fitness hold",
        rationale="The operator packet keeps Fitness protected and this marker is explicitly held.",
        expected_evidence="explicit operator release of Fitness plus a bounded owner-side packet",
    ),
    "Tmp Dependency Elimination": MarkerPolicy(
        category="archive/delete hold",
        rationale="The remaining work still leans on retained residue, archive timing, or deletion authority that this session does not have.",
        expected_evidence="one bounded non-destructive proof family or explicit archive/delete authority",
    ),
    "Duplicate Surface Decommission": MarkerPolicy(
        category="archive/delete hold",
        rationale="The lane still routes through unique-state verification and later archive/delete decisions, so it is not eligible for this non-destructive root packet.",
        expected_evidence="one non-destructive proof packet or explicit archive/delete authority",
    ),
    "Brand Asset Canonicalization": MarkerPolicy(
        category="owner-repo hold",
        rationale="The remaining work still depends on owner-side asset or deploy authority rather than one root-only packet.",
        expected_evidence="one root-owned asset-governance seam that stays outside owner/deploy authority",
    ),
    "Preview Cache & Surface Consistency": MarkerPolicy(
        category="deploy/publication hold",
        rationale="Preview-surface truth still depends on deploy/runtime-facing evidence rather than a root-only lane.",
        expected_evidence="one non-deploy cache/projection contract or explicit preview authority",
    ),
    "Vercel Hobby Cost Governance": MarkerPolicy(
        category="admissible after current lane",
        rationale="The marker is now durably admitted, but current truth still keeps the AI and queue-or-registry execution-facing lanes ahead of a cost-governance follow-on by default.",
        expected_evidence="one root-owned usage-snapshot or threshold-governance receipt that preserves Hobby posture without requiring Vercel setting mutation",
    ),
    "Operator Secret Path Hygiene": MarkerPolicy(
        category="secret/.env hold",
        rationale="The marker may only reopen on non-secret docs/checks or new secret-path ambiguity, and the active campaign explicitly forbids secret work.",
        expected_evidence="one non-secret classification packet or a fresh ambiguity proof that stays out of secrets themselves",
    ),
    "Manual Deploy Exception Burn-Down": MarkerPolicy(
        category="deploy/publication hold",
        rationale="The remaining work is exception accounting around deploy authority, not an immediate root-only capability packet.",
        expected_evidence="one documentation-only exception packet that stays outside deploy execution",
    ),
    "Unified Workflow Convergence": MarkerPolicy(
        category="insufficient evidence / needs selector only",
        rationale="The workflow spine is materially held and does not expose a fresh immediate packet from current truth.",
        expected_evidence="one distinct new workflow-boundary question that materially changes lane routing",
    ),
    "Vision & Future Alignment": MarkerPolicy(
        category="insufficient evidence / needs selector only",
        rationale="The marker remains exploratory and does not currently expose one bounded execution-facing root packet.",
        expected_evidence="one concrete strategy-to-execution slice with bounded files and local verification",
    ),
    "Core Pattern Convergence": MarkerPolicy(
        category="insufficient evidence / needs selector only",
        rationale="The provisional doctrine threshold remains materially held and not ready for another root packet by default.",
        expected_evidence="one new repeatable cross-repo pattern with bounded evidence and no doctrine-admission jump",
    ),
    "Discord Workflow, Publication & Docs Reliability": MarkerPolicy(
        category="deploy/publication hold",
        rationale="The lane still lacks the missing live publication/parity evidence class and is not root-only from current truth.",
        expected_evidence="one new non-runtime publication/docs proof seam that does not require live publication authority",
    ),
    "DiscordOS Runtime & Product Hardening": MarkerPolicy(
        category="owner-repo hold",
        rationale="The live hardening lane is real, but the open work still sits in DiscordOS owner-repo runtime, cron, alert, and audit surfaces rather than one immediate ATLAS-root packet.",
        expected_evidence="one explicit root-routable contract or restart seam that improves the lane without mutating DiscordOS runtime or deploy surfaces",
    ),
    "Playbook Everywhere + Cortex Interface": MarkerPolicy(
        category="admissible after current lane",
        rationale="The current exportable-now family set is materially held, but it can reopen if the current AI lane creates a new bounded exportable family.",
        expected_evidence="one new exportable contract family or one real contract drift that widens the interface safely",
    ),
    "AI Repetition-to-Automation Pipeline": MarkerPolicy(
        category="admissible now",
        rationale="Fresh operator authorization explicitly reopens root-owned non-Fitness work, and this lane still owns the strongest execution-facing automation opportunity at ATLAS root.",
        expected_evidence="one real root-owned operator surface with repeatable proof and safe fallback that classifies or advances the non-Fitness marker field without touching protected surfaces",
    ),
    "AI Long-Run Batch Orchestration": MarkerPolicy(
        category="admissible after current lane",
        rationale="The lane is a plausible next automation beneficiary, but current truth still needs a first repeatable selector surface before queue or batch semantics become honest.",
        expected_evidence="one queue/registry or batch-scaffold contract that is clearly downstream of the first selector landing",
    ),
    "Feedback Loop Readiness": MarkerPolicy(
        category="insufficient evidence / needs selector only",
        rationale="Current truth explicitly says deterministic replayable proof capture is still missing.",
        expected_evidence="one replayable end-to-end proof loop without hidden operator stitching",
    ),
    "Sandbox Simulation Readiness": MarkerPolicy(
        category="insufficient evidence / needs selector only",
        rationale="The marker is still at 0% and lacks one admitted root-owned starter packet in current truth.",
        expected_evidence="one bounded simulation-scope contract or harness design receipt",
    ),
    "Workstation Resource Hygiene": MarkerPolicy(
        category="insufficient evidence / needs selector only",
        rationale="The lane now has a baseline and one-hot-chat guard, but current truth still lacks one repeated relief cycle or broader adoption packet.",
        expected_evidence="one replayed hygiene relief cycle or one bounded operator-surface improvement that proves broader reuse",
    ),
    "Post-Convergence Lane Split Readiness": MarkerPolicy(
        category="admissible after current lane",
        rationale="The lane is root-owned and restart-safe, but current truth says there is no immediate docs-only follow-on packet from it right now.",
        expected_evidence="one distinct restart-truth, marker, approval, or execution-surface change that reopens the split lane",
    ),
}

PACKET_REGISTRY: dict[str, PacketDescriptor] = {
    "AI Repetition-to-Automation Pipeline": PacketDescriptor(
        packet="AI Repetition-to-Automation Pipeline non-Fitness marker knockout selector surface",
        basis_receipt_ref=(
            "docs/ops/"
            "AI-REPETITION-TO-AUTOMATION-PIPELINE-NON-FITNESS-MARKER-KNOCKOUT-SELECTOR-"
            "ACTIVE-LANE-FOLLOW-ON-DISAMBIGUATION-2026-06-17.md"
        ),
    ),
    "AI Long-Run Batch Orchestration": PacketDescriptor(
        packet=(
            "AI Long-Run Batch Orchestration "
            "post-stack-command-implementation-actual-owner-side-mutation-authority-class-value "
            "downstream hold recheck"
        ),
        basis_receipt_ref=(
            "docs/ops/"
            "AI-LONG-RUN-BATCH-ORCHESTRATION-POST-STACK-COMMAND-IMPLEMENTATION-"
            "ACTUAL-OWNER-SIDE-MUTATION-AUTHORITY-CLASS-VALUE-DOWNSTREAM-HOLD-RECHECK-"
            "2026-06-26.md"
        ),
    ),
    "Sandbox Simulation Readiness": PacketDescriptor(
        packet="Sandbox Simulation Readiness local-only first validator-boundary contract freeze",
        basis_receipt_ref=(
            "docs/ops/"
            "SANDBOX-SIMULATION-READINESS-LOCAL-ONLY-FIRST-EXPECTED-OUTPUT-FIXTURE-"
            "STUB-ADMISSION-2026-06-27.md"
        ),
        mode="root-owned docs-only validator-boundary follow-on",
        scope=(
            "freeze how a future local-only validator may read the admitted scenario, fixture-pack, note, input, "
            "and expected-output stubs without admitting validator execution, runner behavior, no-_stack widening, "
            "or mutation behavior"
        ),
    ),
}


class MarkerSelectorError(RuntimeError):
    pass


def _normalize_marker_name(value: str) -> str:
    return value.replace("`", "").strip()


def load_marker_sections(*, root: Path) -> dict[str, dict[str, int]]:
    marker_path = root / "docs" / "atlas-book" / "02-lanes-and-markers.md"
    if not marker_path.exists():
        raise MarkerSelectorError(f"Missing marker table source: {atlas_relative(marker_path, root=root)}")

    sections = {value: {} for value in SECTION_HEADERS.values()}
    active_section: str | None = None

    for raw_line in marker_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if line in SECTION_HEADERS:
            active_section = SECTION_HEADERS[line]
            continue
        if line.startswith("## "):
            active_section = None
            continue
        if active_section is None:
            continue
        match = MARKER_LINE_PATTERN.match(line)
        if not match:
            continue
        marker, percentage = _normalize_marker_name(match.group(1)), int(match.group(2))
        sections[active_section][marker] = percentage

    if not sections["active_front_page"]:
        raise MarkerSelectorError("Active front-page marker table could not be parsed from durable Book truth.")
    if not sections["supporting_open"]:
        raise MarkerSelectorError("Supporting open markers could not be parsed from durable Book truth.")

    return sections


def _priority_order(marker: str) -> int:
    try:
        return CAMPAIGN_PRIORITY.index(marker)
    except ValueError:
        return len(CAMPAIGN_PRIORITY) + sorted(POLICY_REGISTRY).index(marker)


def load_active_lane(*, root: Path) -> str | None:
    source_refs = (
        root / "docs" / "atlas-book" / "01-current-state.md",
        root / "docs" / "atlas-book" / "12-restart-and-handoff-guide.md",
    )
    discovered: dict[str, set[str]] = {}

    for source_ref in source_refs:
        if not source_ref.exists():
            continue
        text = source_ref.read_text(encoding="utf-8")
        for pattern in ACTIVE_LANE_PATTERNS:
            for match in pattern.finditer(text):
                lane = _normalize_marker_name(match.group(1))
                discovered.setdefault(lane, set()).add(atlas_relative(source_ref, root=root))

    if not discovered:
        return None

    if len(discovered) > 1:
        details = ", ".join(
            f"{lane} ({', '.join(sorted(source_refs))})"
            for lane, source_refs in sorted(discovered.items())
        )
        raise MarkerSelectorError(f"Durable active-lane sources disagree: {details}")

    return next(iter(discovered))


def effective_policy(*, marker: str, percentage: int, active_lane: str | None) -> MarkerPolicy:
    policy = POLICY_REGISTRY[marker]
    if marker == "Sandbox Simulation Readiness" and percentage > 0:
        policy = MarkerPolicy(
            category="admissible after current lane",
            rationale=(
                "The lane now has one admitted root-owned starter packet plus durable scenario, runtime, and fixture-pack contract freezes, one admitted example pair, one note-only leaf fixture, one input fixture stub, and one expected-output fixture stub, "
                "but current durable restart truth still keeps the active ATLAS-root lane ahead of it."
            ),
            expected_evidence=(
                "one bounded local-only first validator-boundary contract freeze that preserves "
                "no owner-repo, deploy, secret, or live-data widening"
            ),
        )
    if not active_lane:
        return policy
    if marker == active_lane:
        return MarkerPolicy(
            category="admissible now",
            rationale=(
                "Current durable restart truth already names this as the active immediate ATLAS-root lane, "
                "so it remains the first honest bounded execution-facing packet until its present subfamily exhausts or blocks."
            ),
            expected_evidence=(
                "one bounded follow-on inside the active lane that preserves current root-owned proof discipline and does not widen "
                "into owner-repo, deploy, secret, or protected-surface mutation"
            ),
        )
    if policy.category == "admissible now":
        return MarkerPolicy(
            category="admissible after current lane",
            rationale=(
                f"Current durable restart truth now routes the immediate ATLAS-root lane through {active_lane}, "
                "so this earlier selector family stays durable carry-forward truth rather than the first reopen."
            ),
            expected_evidence=policy.expected_evidence,
        )
    return policy


def _explicit_no_immediate_hold_markers(*, root: Path) -> set[str]:
    payload = build_open_marker_restart_index(root=root)
    items = payload.get("items") if isinstance(payload.get("items"), list) else []
    held_markers: set[str] = set()

    for item in items:
        if not isinstance(item, dict):
            continue
        marker = str(item.get("marker") or "").strip()
        if not marker:
            continue
        if str(item.get("restart_status") or "").strip() != "restart_ready":
            continue
        next_package = item.get("next_package") if isinstance(item.get("next_package"), dict) else {}
        package_name = str(next_package.get("package") or "").strip()
        if package_name.startswith("No immediate "):
            held_markers.add(marker)

    return held_markers


def packet_for_marker(marker: str) -> str | None:
    descriptor = PACKET_REGISTRY.get(marker)
    if descriptor is None:
        return None
    return descriptor.packet


def packet_basis_ref_for_marker(marker: str) -> str | None:
    descriptor = PACKET_REGISTRY.get(marker)
    if descriptor is None:
        return None
    return descriptor.basis_receipt_ref


def packet_mode_for_marker(*, root: Path, marker: str) -> str | None:
    descriptor = PACKET_REGISTRY.get(marker)
    if descriptor is None:
        return None
    if descriptor.mode is not None:
        return descriptor.mode
    basis_ref = descriptor.basis_receipt_ref
    if not basis_ref:
        return None
    return load_packet_receipt_context(root=root, basis_receipt_ref=basis_ref).mode


def packet_scope_for_marker(*, root: Path, marker: str) -> str | None:
    descriptor = PACKET_REGISTRY.get(marker)
    if descriptor is None:
        return None
    if descriptor.scope is not None:
        return descriptor.scope
    basis_ref = descriptor.basis_receipt_ref
    if not basis_ref:
        return None
    return load_packet_receipt_context(root=root, basis_receipt_ref=basis_ref).scope


def load_packet_receipt_context(*, root: Path, basis_receipt_ref: str) -> PacketReceiptContext:
    receipt_path = (root / basis_receipt_ref).resolve()
    if not receipt_path.exists():
        raise MarkerSelectorError(
            f"Missing packet basis receipt: {atlas_relative(receipt_path, root=root)}"
        )

    mode: str | None = None
    scope: str | None = None
    for raw_line in receipt_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("- Mode: `") and line.endswith("`"):
            mode = line[len("- Mode: `") : -1]
        elif line.startswith("- Scope: `") and line.endswith("`"):
            scope = line[len("- Scope: `") : -1]
        if mode and scope:
            break

    if not mode or not scope:
        raise MarkerSelectorError(
            "Packet basis receipt is missing required Mode/Scope metadata: "
            + atlas_relative(receipt_path, root=root)
        )

    return PacketReceiptContext(
        basis_receipt_ref=basis_receipt_ref,
        mode=mode,
        scope=scope,
    )


def build_campaign(*, root: Path) -> dict[str, object]:
    sections = load_marker_sections(root=root)
    active_lane = load_active_lane(root=root)
    explicit_hold_markers = _explicit_no_immediate_hold_markers(root=root)
    open_markers = {**sections["active_front_page"], **sections["supporting_open"]}

    unknown_markers = sorted(set(open_markers) - set(POLICY_REGISTRY))
    if unknown_markers:
        raise MarkerSelectorError(
            "Marker selector is missing policy entries for: " + ", ".join(unknown_markers)
        )
    if active_lane and active_lane not in open_markers:
        raise MarkerSelectorError(
            f"Durable active lane is not present in the open marker field: {active_lane}"
        )

    records: list[MarkerRecord] = []
    for marker, percentage in open_markers.items():
        policy = effective_policy(marker=marker, percentage=percentage, active_lane=active_lane)
        if policy.category not in ALLOWED_CATEGORIES:
            raise MarkerSelectorError(f"Unsupported category for {marker}: {policy.category}")
        section = "active front-page" if marker in sections["active_front_page"] else "supporting open"
        records.append(
            MarkerRecord(
                marker=marker,
                percentage=percentage,
                section=section,
                category=policy.category,
                rationale=policy.rationale,
                expected_evidence=policy.expected_evidence,
                priority=_priority_order(marker),
            )
        )

    records.sort(key=lambda item: (item.priority, item.marker.lower()))

    if active_lane:
        selected = next((record for record in records if record.marker == active_lane), None)
    else:
        selected = next(
            (
                record
                for record in records
                if record.category == "admissible now" and record.marker not in explicit_hold_markers
            ),
            None,
        )
    next_after_current = next(
        (
            record
            for record in records
            if record.category == "admissible after current lane"
            and record.marker not in explicit_hold_markers
        ),
        None,
    )
    category_counts: dict[str, int] = {}
    for record in records:
        category_counts[record.category] = category_counts.get(record.category, 0) + 1

    closed_markers = [
        MarkerRecord(
            marker=marker,
            percentage=percentage,
            section="closed / locked",
            category="already closed / locked",
            rationale="Closed ratchet carried for restart context only.",
            expected_evidence="none",
            priority=len(CAMPAIGN_PRIORITY) + len(POLICY_REGISTRY),
        )
        for marker, percentage in sorted(sections["closed_locked"].items())
    ]

    active_lane_is_held = bool(selected and selected.marker in explicit_hold_markers)

    operator_action = None
    operator_action_reason = None
    if selected and active_lane and active_lane_is_held:
        operator_action = "hold_current_lane"
        operator_action_reason = (
            "Durable restart truth still names the active ATLAS-root lane, but its own manifest-backed "
            "next-package ladder explicitly says no immediate same-lane packet is open."
        )
    elif selected and active_lane:
        operator_action = "continue_current_lane"
        operator_action_reason = (
            "Durable restart truth already names the active ATLAS-root lane, so continue the current packet "
            "before falling through to the first downstream admissible lane."
        )
    elif selected:
        operator_action = "open_selected_lane"
        operator_action_reason = (
            "No active lane is already named in durable restart truth, so open the first admissible selected lane."
        )

    return {
        "campaign_id": "root-non-fitness-marker-knockout",
        "source_ref": "docs/atlas-book/02-lanes-and-markers.md",
        "source_digest_count": len(open_markers),
        "active_lane": active_lane,
        "open_markers": [asdict(record) for record in records],
        "closed_markers": [asdict(record) for record in closed_markers],
        "category_counts": category_counts,
        "selected_marker": selected.marker if selected else None,
        "selected_percentage": selected.percentage if selected else None,
        "selected_expected_evidence": selected.expected_evidence if selected else None,
        "selected_reason": selected.rationale if selected else None,
        "operator_action": operator_action,
        "operator_action_reason": operator_action_reason,
        "selected_current_packet": packet_for_marker(selected.marker) if selected else None,
        "selected_current_packet_basis_ref": packet_basis_ref_for_marker(selected.marker) if selected else None,
        "selected_current_packet_mode": (
            packet_mode_for_marker(root=root, marker=selected.marker) if selected else None
        ),
        "selected_current_packet_scope": (
            packet_scope_for_marker(root=root, marker=selected.marker) if selected else None
        ),
        "next_after_current_marker": next_after_current.marker if next_after_current else None,
        "next_after_current_percentage": next_after_current.percentage if next_after_current else None,
        "next_after_current_expected_evidence": next_after_current.expected_evidence if next_after_current else None,
        "next_after_current_reason": next_after_current.rationale if next_after_current else None,
        "next_after_current_packet": packet_for_marker(next_after_current.marker) if next_after_current else None,
        "next_after_current_packet_basis_ref": (
            packet_basis_ref_for_marker(next_after_current.marker) if next_after_current else None
        ),
        "next_after_current_packet_mode": (
            packet_mode_for_marker(root=root, marker=next_after_current.marker) if next_after_current else None
        ),
        "next_after_current_packet_scope": (
            packet_scope_for_marker(root=root, marker=next_after_current.marker) if next_after_current else None
        ),
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Root Non-Fitness Marker Knockout Selector",
        "",
        f"- Campaign id: `{payload['campaign_id']}`",
        f"- Source ref: `{payload['source_ref']}`",
        "",
        "## Category Counts",
        "",
    ]
    for category, count in sorted(dict(payload["category_counts"]).items()):
        lines.append(f"- `{category}`: `{count}`")

    lines += ["", "## Open Marker Table", "", "| Priority | Marker | Current | Category | Why | Expected evidence |", "| --- | --- | --- | --- | --- | --- |"]
    for record in payload["open_markers"]:
        lines.append(
            f"| `{record['priority'] + 1}` | `{record['marker']}` | `{record['percentage']}%` | "
            f"`{record['category']}` | {record['rationale']} | {record['expected_evidence']} |"
        )

    if payload.get("operator_action"):
        lines += [
            "",
            "## Operator Action",
            "",
            f"- action: `{payload['operator_action']}`",
            f"- why: {payload['operator_action_reason']}",
        ]
        if payload.get("selected_current_packet"):
            lines.append(f"- do now: `{payload['selected_current_packet']}`")
        if payload.get("selected_current_packet_basis_ref"):
            lines.append(f"- current packet basis receipt: `{payload['selected_current_packet_basis_ref']}`")
        if payload.get("selected_current_packet_mode"):
            lines.append(f"- current packet mode: `{payload['selected_current_packet_mode']}`")
        if payload.get("selected_current_packet_scope"):
            lines.append(f"- current packet scope: `{payload['selected_current_packet_scope']}`")
        if payload.get("next_after_current_packet"):
            lines.append(f"- fallback after current lane: `{payload['next_after_current_packet']}`")
        if payload.get("next_after_current_packet_basis_ref"):
            lines.append(
                f"- fallback packet basis receipt: `{payload['next_after_current_packet_basis_ref']}`"
            )
        if payload.get("next_after_current_packet_mode"):
            lines.append(f"- fallback packet mode: `{payload['next_after_current_packet_mode']}`")
        if payload.get("next_after_current_packet_scope"):
            lines.append(f"- fallback packet scope: `{payload['next_after_current_packet_scope']}`")

    if payload.get("selected_marker"):
        section_title = "## Current Active Marker" if payload.get("active_lane") else "## First Admissible Marker"
        lines += [
            "",
            section_title,
            "",
            f"- marker: `{payload['selected_marker']}`",
            f"- current percentage: `{payload['selected_percentage']}%`",
            f"- why: {payload['selected_reason']}",
            f"- expected evidence: {payload['selected_expected_evidence']}",
        ]
        if payload.get("selected_current_packet"):
            lines.append(f"- current packet: `{payload['selected_current_packet']}`")
        if payload.get("selected_current_packet_basis_ref"):
            lines.append(f"- current packet basis receipt: `{payload['selected_current_packet_basis_ref']}`")
        if payload.get("selected_current_packet_mode"):
            lines.append(f"- current packet mode: `{payload['selected_current_packet_mode']}`")
        if payload.get("selected_current_packet_scope"):
            lines.append(f"- current packet scope: `{payload['selected_current_packet_scope']}`")

    if payload.get("next_after_current_marker"):
        lines += [
            "",
            "## First Admissible After Current Lane",
            "",
            f"- marker: `{payload['next_after_current_marker']}`",
            f"- current percentage: `{payload['next_after_current_percentage']}%`",
            f"- why: {payload['next_after_current_reason']}",
            f"- expected evidence: {payload['next_after_current_expected_evidence']}",
        ]
        if payload.get("next_after_current_packet"):
            lines.append(f"- next packet after current lane: `{payload['next_after_current_packet']}`")
        if payload.get("next_after_current_packet_basis_ref"):
            lines.append(
                f"- next packet basis receipt: `{payload['next_after_current_packet_basis_ref']}`"
            )
        if payload.get("next_after_current_packet_mode"):
            lines.append(f"- next packet mode: `{payload['next_after_current_packet_mode']}`")
        if payload.get("next_after_current_packet_scope"):
            lines.append(f"- next packet scope: `{payload['next_after_current_packet_scope']}`")

    return "\n".join(lines).rstrip() + "\n"


def write_output(*, payload: dict[str, object], output_path: Path, format_name: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if format_name == "json":
        output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return
    output_path.write_text(render_markdown(payload), encoding="utf-8")


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Classify the current non-Fitness marker field for the ATLAS root campaign.")
    parser.add_argument("--root", default=str(atlas_root()))
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--output")
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    try:
        payload = build_campaign(root=root)
        if args.output:
            write_output(payload=payload, output_path=(root / args.output).resolve(), format_name=args.format)
        elif args.format == "json":
            print(json.dumps(payload, indent=2))
        else:
            print(render_markdown(payload), end="")
    except MarkerSelectorError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


