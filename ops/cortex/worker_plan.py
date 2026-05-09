from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ops.cortex.kernel import CortexPosture, CortexRuleRecord, NextAction, RailState

WORKER_PLAN_CONTRACT_VERSION = "atlas.cortex.worker-plan.v1"


@dataclass(frozen=True)
class WorkerPlanTemplate:
    template_id: str
    objective: str
    implementation_plan: tuple[str, ...]
    default_files_to_modify: tuple[str, ...]
    default_files_to_avoid: tuple[str, ...]
    documentation_summary: str
    default_verification_steps: tuple[str, ...]
    default_failure_modes_to_avoid: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkerPlan:
    template_id: str
    owner_layer: str
    objective: str
    prompt: str
    implementation_plan: tuple[str, ...]
    files_to_modify: tuple[str, ...]
    files_to_avoid: tuple[str, ...]
    verification_steps: tuple[str, ...]
    matched_rule_ids: tuple[str, ...]
    failure_modes_to_avoid: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "contract_version": WORKER_PLAN_CONTRACT_VERSION,
            "template_id": self.template_id,
            "owner_layer": self.owner_layer,
            "objective": self.objective,
            "prompt": self.prompt,
            "implementation_plan": list(self.implementation_plan),
            "files_to_modify": list(self.files_to_modify),
            "files_to_avoid": list(self.files_to_avoid),
            "verification_steps": list(self.verification_steps),
            "matched_rule_ids": list(self.matched_rule_ids),
            "failure_modes_to_avoid": list(self.failure_modes_to_avoid),
        }


def _dedupe_strings(values: Iterable[str]) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        stripped = str(value).strip()
        if not stripped or stripped in seen:
            continue
        seen.add(stripped)
        ordered.append(stripped)
    return tuple(ordered)


def _section(title: str, lines: Iterable[str]) -> str:
    items = [str(line).strip() for line in lines if str(line).strip()]
    if not items:
        items = ["None"]
    return "\n".join([title, *[f"- {line}" for line in items]])


def _numbered_section(title: str, lines: Iterable[str]) -> str:
    items = [str(line).strip() for line in lines if str(line).strip()]
    if not items:
        items = ["None"]
    return "\n".join([title, *[f"{index}. {line}" for index, line in enumerate(items, start=1)]])


def _action_text(next_action: NextAction) -> str:
    return " ".join(
        part
        for part in (
            next_action.action_id,
            next_action.owner_layer,
            next_action.title,
            next_action.rationale,
            next_action.receipt_scope or "",
            " ".join(next_action.required_inputs),
        )
        if part
    ).lower()


def _select_rule_record(
    *,
    kind: str,
    rules: list[CortexRuleRecord],
    owner_layer: str,
) -> CortexRuleRecord:
    candidates = [rule for rule in rules if rule.kind == kind]
    if not candidates:
        raise ValueError(f"Cortex worker plan requires at least one {kind} rule record.")

    if owner_layer == "atlas":
        owner_terms = ("atlas root", "atlas")
    elif owner_layer == "fitness":
        owner_terms = ("fitness",)
    elif owner_layer == "cortex":
        owner_terms = ("cortex",)
    else:
        owner_terms = (owner_layer.lower(),)

    def score(rule: CortexRuleRecord) -> tuple[int, str]:
        haystack = " ".join(rule.applies_to).lower()
        match_count = sum(1 for term in owner_terms if term in haystack)
        return (-match_count, rule.rule_id)

    return sorted(candidates, key=score)[0]


def _ensure_same_rail(posture: CortexPosture, rail_state: RailState) -> None:
    if posture.rail_state != rail_state:
        raise ValueError("Cortex posture and rail state must describe the same rail state.")


def _select_template(posture: CortexPosture, next_action: NextAction) -> WorkerPlanTemplate:
    action_text = _action_text(next_action)

    if any(token in action_text for token in ("docs adr", "docs/adr", "adr", "debt slice", "debt-slice")):
        return DOCS_ADR_OR_DEBT_SLICE_TEMPLATE
    if next_action.action_id in {"fitness-owner-adoption", "resume-fitness-owner-adoption"} or any(
        token in action_text for token in ("owner adoption", "owner-adoption")
    ):
        return FITNESS_OWNER_ADOPTION_TEMPLATE
    if next_action.action_id == "atlas-cortex-catch-up" or "catch-up" in action_text:
        return ATLAS_CORTEX_CATCH_UP_TEMPLATE
    if next_action.action_id == "promote-cortex-worker-prompt-contract-wave6":
        return CORTEX_WORKER_PROMPT_CONTRACT_TEMPLATE
    if next_action.action_id == "pilot-cortex-worker-prompt-stack-consumption-wave7":
        return CORTEX_STACK_CONSUMPTION_PILOT_TEMPLATE
    if next_action.action_id == "promote-cortex-stack-consumer-default-routing-wave8":
        return CORTEX_STACK_ADVISORY_HANDOFF_CONTRACT_TEMPLATE
    if next_action.action_id == "promote-cortex-receipt-interpretation-contract-wave9":
        return CORTEX_RECEIPT_INTERPRETATION_CONTRACT_TEMPLATE
    if next_action.owner_layer == "cortex" or "cortex runtime" in action_text or "runtime work" in action_text:
        return CORTEX_RUNTIME_WORK_TEMPLATE

    raise ValueError(
        "Unsupported Cortex NextAction for worker planning: "
        f"action_id={next_action.action_id!r}, owner_layer={next_action.owner_layer!r}, title={next_action.title!r}"
    )


def _format_context(posture: CortexPosture, rail_state: RailState, next_action: NextAction) -> list[str]:
    pivot_active = next_action.owner_layer == "cortex"
    return [
        f"Posture: {posture.posture_id} ({posture.classification})",
        f"Rail: {rail_state.rail_id} owned by {rail_state.owner_layer}",
        f"Latest clean step: {rail_state.latest_clean_step.step_id} ({rail_state.latest_clean_step.owner_layer})",
        f"Selected next action: {next_action.action_id} -> {next_action.owner_layer}",
        f"Next action title: {next_action.title}",
        f"Rationale: {next_action.rationale}",
        f"Required inputs: {'; '.join(next_action.required_inputs) if next_action.required_inputs else 'None'}",
        f"Verification plan: {'; '.join(next_action.verification_plan) if next_action.verification_plan else 'None'}",
        f"Cortex priority override active: {'yes' if pivot_active else 'no'}",
    ]


def _build_prompt(
    *,
    template: WorkerPlanTemplate,
    posture: CortexPosture,
    rail_state: RailState,
    next_action: NextAction,
    rule: CortexRuleRecord,
    pattern: CortexRuleRecord,
    failure_mode: CortexRuleRecord,
    files_to_modify: tuple[str, ...],
    files_to_avoid: tuple[str, ...],
    verification_steps: tuple[str, ...],
) -> str:
    context_lines = _format_context(posture, rail_state, next_action)
    implementation_lines = list(template.implementation_plan)
    if next_action.receipt_scope:
        implementation_lines.append(f"Respect receipt scope: {next_action.receipt_scope}")

    prompt_sections = [
        _section("Objective", [f"{template.objective} Selected next action: {next_action.title}."]),
        _section("Context", context_lines),
        _numbered_section("Implementation plan", implementation_lines),
        _section("Files to modify", files_to_modify),
        _section("Files to avoid", files_to_avoid),
        _section("Verification steps", verification_steps),
        _section(
            "Documentation summary",
            [template.documentation_summary],
        ),
        _section("Rule", [f"{rule.rule_id}: {rule.statement}"]),
        _section("Pattern", [f"{pattern.rule_id}: {pattern.statement}"]),
        _section("Failure Mode", [f"{failure_mode.rule_id}: {failure_mode.statement}"]),
    ]
    return "\n\n".join(prompt_sections)


class WorkerPlanGenerator:
    def generate(
        self,
        posture: CortexPosture,
        rail_state: RailState,
        next_action: NextAction,
        rules: list[CortexRuleRecord],
        *,
        files_to_modify: list[str] | None = None,
        files_to_avoid: list[str] | None = None,
    ) -> WorkerPlan:
        _ensure_same_rail(posture, rail_state)
        template = _select_template(posture, next_action)
        rule = _select_rule_record(kind="rule", rules=rules, owner_layer=next_action.owner_layer)
        pattern = _select_rule_record(kind="pattern", rules=rules, owner_layer=next_action.owner_layer)
        failure_mode = _select_rule_record(kind="failure_mode", rules=rules, owner_layer=next_action.owner_layer)

        resolved_files_to_modify = _dedupe_strings(
            [*template.default_files_to_modify, *(files_to_modify or [])]
        )
        resolved_files_to_avoid = _dedupe_strings(
            [*template.default_files_to_avoid, *(files_to_avoid or [])]
        )
        resolved_verification_steps = _dedupe_strings(
            [*next_action.verification_plan, *template.default_verification_steps]
        )
        implementation_plan = list(template.implementation_plan)
        if next_action.receipt_scope:
            implementation_plan.append(f"Respect receipt scope: {next_action.receipt_scope}")
        resolved_implementation_plan = _dedupe_strings(implementation_plan)
        resolved_failure_modes_to_avoid = _dedupe_strings(
            [failure_mode.statement, *template.default_failure_modes_to_avoid]
        )

        prompt = _build_prompt(
            template=template,
            posture=posture,
            rail_state=rail_state,
            next_action=next_action,
            rule=rule,
            pattern=pattern,
            failure_mode=failure_mode,
            files_to_modify=resolved_files_to_modify,
            files_to_avoid=resolved_files_to_avoid,
            verification_steps=resolved_verification_steps,
        )
        objective = f"{template.objective} Selected next action: {next_action.title}."
        return WorkerPlan(
            template_id=template.template_id,
            owner_layer=next_action.owner_layer,
            objective=objective,
            prompt=prompt,
            implementation_plan=resolved_implementation_plan,
            files_to_modify=resolved_files_to_modify,
            files_to_avoid=resolved_files_to_avoid,
            verification_steps=resolved_verification_steps,
            matched_rule_ids=(rule.rule_id, pattern.rule_id, failure_mode.rule_id),
            failure_modes_to_avoid=resolved_failure_modes_to_avoid,
        )


def build_worker_plan(
    posture: CortexPosture,
    rail_state: RailState,
    next_action: NextAction,
    rules: list[CortexRuleRecord],
    *,
    files_to_modify: list[str] | None = None,
    files_to_avoid: list[str] | None = None,
) -> WorkerPlan:
    return WorkerPlanGenerator().generate(
        posture,
        rail_state,
        next_action,
        rules,
        files_to_modify=files_to_modify,
        files_to_avoid=files_to_avoid,
    )


CORTEX_RUNTIME_WORK_TEMPLATE = WorkerPlanTemplate(
    template_id="cortex_runtime_work",
    objective="Keep the next tranche inside Cortex-owned runtime work.",
    implementation_plan=(
        "Stay inside Cortex runtime modules and their direct tests.",
        "Preserve the active Cortex priority pivot and do not reopen other lanes.",
        "Keep the change PR-sized and deterministic.",
    ),
    default_files_to_modify=("ops/cortex/*.py", "tests/test_cortex_*.py"),
    default_files_to_avoid=("repos/**", "apps/**", "packages/**"),
    documentation_summary="Cortex runtime work stays inside deterministic kernel and planner primitives.",
    default_verification_steps=("python -m unittest tests.test_cortex_worker_plan",),
)


CORTEX_WORKER_PROMPT_CONTRACT_TEMPLATE = WorkerPlanTemplate(
    template_id="cortex_worker_prompt_contract",
    objective="Promote the Cortex worker-prompt contract as a bounded advisory handoff surface.",
    implementation_plan=(
        "Keep the lane inside Cortex root-owned runtime modules and direct tests only.",
        "Emit one _stack-consumable worker-prompt artifact without turning Cortex into an executor.",
        "Preserve planner, context, proof, receipt-draft, and final receipt as separate surfaces linked by refs and digests.",
    ),
    default_files_to_modify=(
        "ops/cortex/worker_plan.py",
        "ops/cortex/worker_prompt.py",
        "tests/test_cortex_worker_plan.py",
        "tests/test_cortex_worker_prompt.py",
    ),
    default_files_to_avoid=(
        "stack.yaml",
        "repos/**",
        "apps/**",
        "packages/**",
        "runtime/lifeline/**",
    ),
    documentation_summary=(
        "The Cortex worker-prompt contract is advisory scaffolding for _stack consumers and does not grant execution, "
        "receipt, or owner-truth authority."
    ),
    default_verification_steps=("python -m unittest tests.test_cortex_worker_prompt tests.test_cortex_worker_plan",),
    default_failure_modes_to_avoid=(
        "Do not treat the worker prompt as execution authority.",
        "Do not collapse planner, context, proof, or receipt surfaces into one mutable truth store.",
    ),
)


CORTEX_STACK_CONSUMPTION_PILOT_TEMPLATE = WorkerPlanTemplate(
    template_id="cortex_stack_consumption_pilot",
    objective="Pilot bounded _stack consumption of Cortex worker-prompt artifacts without widening authority.",
    implementation_plan=(
        "Consume only explicit runtime/cortex worker-prompt, context, operator-surface, and ledger artifacts.",
        "Emit one read-only _stack pilot handoff artifact without dispatching execution or scraping transcripts.",
        "Keep planner, context, proof, receipt-draft, and final receipt separated by refs and digests.",
    ),
    default_files_to_modify=(
        "ops/cortex/stack_consumption_pilot.py",
        "ops/cortex/worker_plan.py",
        "tests/test_cortex_stack_consumption_pilot.py",
        "tests/test_cortex_worker_plan.py",
    ),
    default_files_to_avoid=(
        "stack.yaml",
        "repos/**",
        "apps/**",
        "packages/**",
        "runtime/lifeline/**",
        "runtime/atlas/conversations/**",
        "runtime/atlas/sessions/**",
    ),
    documentation_summary=(
        "The Cortex _stack consumption pilot proves artifact-ref consumption only; it does not dispatch work, "
        "scrape transcripts, change default routing, or grant final receipt authority."
    ),
    default_verification_steps=(
        "python -m unittest tests.test_cortex_stack_consumption_pilot tests.test_cortex_worker_prompt tests.test_cortex_worker_plan",
    ),
    default_failure_modes_to_avoid=(
        "Do not dispatch or execute _stack actions from the pilot.",
        "Do not scrape transcripts or conversations for pilot inputs.",
        "Do not treat the pilot as default consumer routing or receipt authority.",
    ),
)


CORTEX_STACK_ADVISORY_HANDOFF_CONTRACT_TEMPLATE = WorkerPlanTemplate(
    template_id="cortex_stack_advisory_handoff_contract",
    objective="Promote the canonical Cortex -> _stack advisory handoff contract without widening authority.",
    implementation_plan=(
        "Add one canonical advisory handoff envelope that unifies worker-prompt and pilot concerns without becoming execution authority.",
        "Refactor the stack-consumption pilot to reference or validate the canonical handoff instead of owning the handoff shape locally.",
        "Keep planner, context, proof, pilot, receipt-draft, and final receipt surfaces separately referenceable by refs and digests.",
    ),
    default_files_to_modify=(
        "ops/cortex/stack_handoff.py",
        "ops/cortex/stack_consumption_pilot.py",
        "ops/cortex/worker_plan.py",
        "schemas/atlas.cortex.stack-advisory-handoff.v2.json",
        "tests/test_cortex_stack_handoff.py",
        "tests/test_cortex_stack_consumption_pilot.py",
        "tests/test_cortex_worker_plan.py",
    ),
    default_files_to_avoid=(
        "stack.yaml",
        "repos/**",
        "apps/**",
        "packages/**",
        "runtime/lifeline/**",
        "runtime/atlas/conversations/**",
        "runtime/atlas/sessions/**",
    ),
    documentation_summary=(
        "Default routing in Cortex means a promoted advisory artifact-ref handoff contract for _stack, not automatic dispatch, execution, receipt authority, or owner-truth mutation."
    ),
    default_verification_steps=(
        "python -m unittest tests.test_cortex_stack_handoff tests.test_cortex_stack_consumption_pilot tests.test_cortex_worker_prompt tests.test_cortex_worker_plan",
    ),
    default_failure_modes_to_avoid=(
        "Do not enable automatic dispatch or treat the default consumer as execution authority.",
        "Do not collapse worker prompt, context, proof, pilot, or receipt surfaces into one mutable truth store.",
        "Do not give Cortex final receipt authority or scrape transcripts.",
    ),
)


CORTEX_RECEIPT_INTERPRETATION_CONTRACT_TEMPLATE = WorkerPlanTemplate(
    template_id="cortex_receipt_interpretation_contract",
    objective="Promote the Cortex receipt interpretation contract as a read-only proof-summary surface without replacing Lifeline receipt authority.",
    implementation_plan=(
        "Add one read-only receipt interpretation artifact that consumes explicit Cortex, _stack, validation, and Lifeline receipt-like artifacts.",
        "Emit deterministic proof summaries for what changed, what proved, and what remains blocked without issuing final receipts.",
        "Block interpretation when validation, handoff, pilot, or final-receipt authority guards are widened.",
    ),
    default_files_to_modify=(
        "ops/cortex/receipt_interpreter.py",
        "ops/cortex/worker_plan.py",
        "schemas/atlas.cortex.receipt-interpretation.v1.json",
        "tests/test_cortex_receipt_interpreter.py",
        "tests/test_cortex_worker_plan.py",
        "tests/test_cortex_worker_prompt.py",
    ),
    default_files_to_avoid=(
        "stack.yaml",
        "repos/**",
        "apps/**",
        "packages/**",
        "runtime/lifeline/**",
        "runtime/atlas/conversations/**",
        "runtime/atlas/sessions/**",
    ),
    documentation_summary=(
        "Cortex receipt interpretation summarizes explicit receipt and proof posture only; Lifeline remains final receipt authority."
    ),
    default_verification_steps=(
        "python -m unittest tests.test_cortex_receipt_interpreter tests.test_cortex_worker_prompt tests.test_cortex_worker_plan",
    ),
    default_failure_modes_to_avoid=(
        "Do not issue final receipts.",
        "Do not approve work.",
        "Do not mutate Lifeline truth or owner truth.",
        "Do not treat receipt interpretation as execution authority.",
        "Do not scrape transcripts.",
        "Do not collapse receipt candidate, proof summary, final receipt, and interpretation into one mutable truth store.",
    ),
)


ATLAS_CORTEX_CATCH_UP_TEMPLATE = WorkerPlanTemplate(
    template_id="atlas_cortex_catch_up",
    objective="Prepare the root-level ATLAS/Cortex catch-up proof as a narrow stack tranche.",
    implementation_plan=(
        "Keep the work at the ATLAS root and in runtime proof artifacts only.",
        "Treat the lane as coordination and proof, not repo implementation truth.",
        "Avoid pulling product repositories into the change set.",
    ),
    default_files_to_modify=(
        "AGENTS.md",
        "README-STACK.md",
        "stack.yaml",
        "docs/atlas/notes/*.md",
        "runtime/cortex/*.json",
    ),
    default_files_to_avoid=("repos/**", "apps/**", "packages/**", "src/**"),
    documentation_summary="Root proof work should validate stack posture without pulling repo-owned implementation truth upward.",
    default_verification_steps=("python .\\ops\\validation\\validate_stack.py",),
)


FITNESS_OWNER_ADOPTION_TEMPLATE = WorkerPlanTemplate(
    template_id="fitness_owner_adoption",
    objective="Implement the Fitness owner-adoption tranche without crossing back into Cortex ownership.",
    implementation_plan=(
        "Stay inside the Fitness repo and keep the scope repo-owned.",
        "Keep Cortex read-only over product surfaces and avoid stack-wide detours.",
        "Limit the work to the smallest owner-adoption slice that closes the lane.",
    ),
    default_files_to_modify=("repos/fawxzzy-fitness/**",),
    default_files_to_avoid=("ops/cortex/**", "runtime/cortex/**", "AGENTS.md", "stack.yaml", "README-STACK.md"),
    documentation_summary="Fitness owns product adoption work; Cortex only guides and verifies.",
    default_verification_steps=("python -m unittest tests.test_atlas_playbook_contract_consumption",),
)


DOCS_ADR_OR_DEBT_SLICE_TEMPLATE = WorkerPlanTemplate(
    template_id="docs_adr_or_debt_slice",
    objective="Keep the docs/ADR or debt slice narrow and bounded.",
    implementation_plan=(
        "Prefer a single docs or debt artifact and keep the change local.",
        "Treat known debt as context, not as a license for broad stack cleanup.",
        "Do not expand the slice into cross-repo implementation work.",
    ),
    default_files_to_modify=("docs/atlas/notes/*.md", "runtime/cortex/*.json"),
    default_files_to_avoid=("repos/**", "apps/**", "packages/**", "ops/validation/**"),
    documentation_summary="Documentation slices record state and debt without turning into stack-wide remediation.",
    default_verification_steps=("python -m unittest tests.test_cortex_worker_plan",),
)
