from __future__ import annotations

import unittest
from dataclasses import replace

from ops._atlas import atlas_root
from ops.cortex.kernel import CortexPosture, NextAction, RailState, load_kernel_state_model, load_rule_registry
from ops.cortex.worker_plan import build_worker_plan


class CortexWorkerPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = atlas_root()
        cls.posture = load_kernel_state_model(root=cls.root)
        cls.rules = load_rule_registry(root=cls.root)

    def _with_state(
        self,
        *,
        posture: CortexPosture | None = None,
        rail_state: RailState | None = None,
        next_action: NextAction | None = None,
    ) -> tuple[CortexPosture, RailState, NextAction]:
        base_posture = posture or self.posture
        base_rail_state = rail_state or base_posture.rail_state
        if base_posture.rail_state != base_rail_state:
            base_posture = replace(base_posture, rail_state=base_rail_state)
        base_next_action = next_action or base_rail_state.next_action
        return base_posture, base_rail_state, base_next_action

    def test_cortex_runtime_next_action_produces_cortex_runtime_prompt(self) -> None:
        posture, rail_state, next_action = self._with_state(
            posture=replace(self.posture, classification="steady"),
            rail_state=replace(
                self.posture.rail_state,
                owner_layer="cortex",
                latest_clean_step=replace(self.posture.rail_state.latest_clean_step, owner_layer="atlas"),
                next_action=replace(
                    self.posture.rail_state.next_action,
                    action_id="cortex-runtime-work",
                    owner_layer="cortex",
                    title="Continue Cortex runtime work.",
                    rationale="Cortex remains active and should stay on the runtime lane.",
                    verification_plan=("python -m unittest tests.test_cortex_worker_plan",),
                ),
            ),
        )

        plan = build_worker_plan(posture, rail_state, next_action, self.rules)

        self.assertEqual("cortex_runtime_work", plan.template_id)
        self.assertEqual("cortex", plan.owner_layer)
        self.assertIn("Objective", plan.prompt)
        self.assertIn("Context", plan.prompt)
        self.assertIn("Implementation plan", plan.prompt)
        self.assertIn("Files to modify", plan.prompt)
        self.assertIn("Files to avoid", plan.prompt)
        self.assertIn("Verification steps", plan.prompt)
        self.assertIn("Documentation summary", plan.prompt)
        self.assertIn("Rule", plan.prompt)
        self.assertIn("Pattern", plan.prompt)
        self.assertIn("Failure Mode", plan.prompt)
        self.assertIn("Cortex priority override active: yes", plan.prompt)
        self.assertTrue(any(path.startswith("ops/cortex/") for path in plan.files_to_modify))
        self.assertTrue(plan.implementation_plan)
        self.assertTrue(plan.failure_modes_to_avoid)

    def test_worker_prompt_contract_next_action_produces_dedicated_prompt_template(self) -> None:
        posture, rail_state, next_action = self._with_state(
            posture=replace(self.posture, classification="pivoted"),
            rail_state=replace(
                self.posture.rail_state,
                owner_layer="cortex",
                next_action=replace(
                    self.posture.rail_state.next_action,
                    action_id="promote-cortex-worker-prompt-contract-wave6",
                    owner_layer="cortex",
                    title="Promote the Cortex worker-prompt contract.",
                    rationale="Cortex needs one _stack-consumable worker prompt while staying advisory.",
                    receipt_scope="Keep receipt authority outside Cortex.",
                    verification_plan=(
                        "python -m unittest tests.test_cortex_worker_prompt tests.test_cortex_worker_plan",
                    ),
                ),
            ),
        )

        plan = build_worker_plan(posture, rail_state, next_action, self.rules)

        self.assertEqual("cortex_worker_prompt_contract", plan.template_id)
        self.assertIn("worker-prompt contract", plan.prompt.lower())
        self.assertIn("Respect receipt scope: Keep receipt authority outside Cortex.", plan.implementation_plan)
        self.assertIn("Do not treat the worker prompt as execution authority.", plan.failure_modes_to_avoid)
        self.assertIn("ops/cortex/worker_prompt.py", plan.files_to_modify)
        self.assertIn("stack.yaml", plan.files_to_avoid)

    def test_stack_consumption_pilot_next_action_produces_bounded_pilot_template(self) -> None:
        posture, rail_state, next_action = self._with_state(
            posture=replace(self.posture, classification="pivoted"),
            rail_state=replace(
                self.posture.rail_state,
                owner_layer="cortex",
                next_action=replace(
                    self.posture.rail_state.next_action,
                    action_id="pilot-cortex-worker-prompt-stack-consumption-wave7",
                    owner_layer="cortex",
                    title="Pilot bounded _stack consumption of the Cortex worker-prompt contract.",
                    rationale="Cortex needs one _stack pilot that consumes artifacts without transcript scraping.",
                    receipt_scope="Keep receipt authority outside Cortex and do not enable default routing.",
                    verification_plan=(
                        "python -m unittest tests.test_cortex_stack_consumption_pilot tests.test_cortex_worker_prompt",
                    ),
                ),
            ),
        )

        plan = build_worker_plan(posture, rail_state, next_action, self.rules)

        self.assertEqual("cortex_stack_consumption_pilot", plan.template_id)
        self.assertIn("without transcript scraping", plan.prompt.lower())
        self.assertIn("ops/cortex/stack_consumption_pilot.py", plan.files_to_modify)
        self.assertIn("runtime/atlas/conversations/**", plan.files_to_avoid)
        self.assertIn("Do not scrape transcripts or conversations for pilot inputs.", plan.failure_modes_to_avoid)
        self.assertIn(
            "Respect receipt scope: Keep receipt authority outside Cortex and do not enable default routing.",
            plan.implementation_plan,
        )

    def test_stack_consumer_default_routing_next_action_produces_canonical_handoff_template(self) -> None:
        posture, rail_state, next_action = self._with_state(
            posture=replace(self.posture, classification="pivoted"),
            rail_state=replace(
                self.posture.rail_state,
                owner_layer="cortex",
                next_action=replace(
                    self.posture.rail_state.next_action,
                    action_id="promote-cortex-stack-consumer-default-routing-wave8",
                    owner_layer="cortex",
                    title="Promote Cortex _stack consumer default routing.",
                    rationale="Cortex needs one canonical advisory handoff envelope for _stack consumption.",
                    receipt_scope="Keep execution, routing, owner-truth mutation, and Lifeline receipt authority outside Cortex.",
                    verification_plan=(
                        "python -m unittest tests.test_cortex_stack_handoff tests.test_cortex_stack_consumption_pilot",
                    ),
                ),
            ),
        )

        plan = build_worker_plan(posture, rail_state, next_action, self.rules)

        self.assertEqual("cortex_stack_advisory_handoff_contract", plan.template_id)
        self.assertIn("canonical", plan.prompt.lower())
        self.assertIn("ops/cortex/stack_handoff.py", plan.files_to_modify)
        self.assertIn("schemas/atlas.cortex.stack-advisory-handoff.v2.json", plan.files_to_modify)
        self.assertIn("runtime/atlas/conversations/**", plan.files_to_avoid)
        self.assertTrue(any("automatic dispatch" in item for item in plan.failure_modes_to_avoid))
        self.assertIn(
            "Respect receipt scope: Keep execution, routing, owner-truth mutation, and Lifeline receipt authority outside Cortex.",
            plan.implementation_plan,
        )

    def test_receipt_interpretation_next_action_produces_dedicated_template(self) -> None:
        posture, rail_state, next_action = self._with_state(
            posture=replace(self.posture, classification="pivoted"),
            rail_state=replace(
                self.posture.rail_state,
                owner_layer="cortex",
                next_action=replace(
                    self.posture.rail_state.next_action,
                    action_id="promote-cortex-receipt-interpretation-contract-wave9",
                    owner_layer="cortex",
                    title="Promote Cortex receipt interpretation contract.",
                    rationale="Cortex needs one read-only receipt interpretation surface.",
                    receipt_scope=(
                        "Cortex may interpret explicit receipt artifacts and summarize proof posture only. "
                        "Cortex must not issue final receipts, approve work, mutate owner truth, or replace Lifeline receipt authority."
                    ),
                    verification_plan=(
                        "python -m unittest tests.test_cortex_receipt_interpreter tests.test_cortex_worker_plan",
                    ),
                ),
            ),
        )

        plan = build_worker_plan(posture, rail_state, next_action, self.rules)

        self.assertEqual("cortex_receipt_interpretation_contract", plan.template_id)
        self.assertIn("receipt interpretation", plan.prompt.lower())
        self.assertIn("ops/cortex/receipt_interpreter.py", plan.files_to_modify)
        self.assertIn("schemas/atlas.cortex.receipt-interpretation.v1.json", plan.files_to_modify)
        self.assertIn("runtime/lifeline/**", plan.files_to_avoid)
        self.assertIn("Do not issue final receipts.", plan.failure_modes_to_avoid)
        self.assertIn("Do not scrape transcripts.", plan.failure_modes_to_avoid)

    def test_receipt_interpretation_stack_consumption_seed_next_action_produces_seed_only_template(self) -> None:
        posture, rail_state, next_action = self._with_state(
            posture=replace(self.posture, classification="pivoted"),
            rail_state=replace(
                self.posture.rail_state,
                owner_layer="cortex",
                next_action=replace(
                    self.posture.rail_state.next_action,
                    action_id="promote-cortex-receipt-interpretation-stack-consumption-wave10",
                    owner_layer="cortex",
                    title="Advance the Cortex rail seed after receipt interpretation.",
                    rationale="Ratchet the seeded next lane without implementing new stack-consumption behavior yet.",
                    receipt_scope=(
                        "Cortex may interpret explicit receipt artifacts and summarize proof posture only. "
                        "final_receipt_authorized=false, approval_authorized=false, execution_authorized=false, "
                        "dispatch_authorized=false, owner_truth_mutation_authorized=false, "
                        "lifeline_truth_mutation_authorized=false, transcript_scraping_allowed=false."
                    ),
                    verification_plan=(
                        "python -m unittest tests.test_cortex_worker_plan tests.test_cortex_current_state",
                    ),
                ),
            ),
        )

        plan = build_worker_plan(posture, rail_state, next_action, self.rules)

        self.assertEqual("cortex_receipt_interpretation_stack_consumption_seed", plan.template_id)
        self.assertIn("seed-only", plan.prompt.lower())
        self.assertIn("runtime/cortex/receipt-interpretation/latest.json", plan.files_to_modify)
        self.assertIn("runtime/lifeline/**", plan.files_to_avoid)
        self.assertIn("Do not implement new receipt-interpretation stack consumption yet.", plan.failure_modes_to_avoid)
        self.assertIn("Do not widen final receipt, approval, execution, dispatch, owner-truth, Lifeline-truth, or transcript authority.", plan.failure_modes_to_avoid)

    def test_fitness_owner_adoption_next_action_produces_fitness_scoped_prompt(self) -> None:
        posture, rail_state, next_action = self._with_state(
            posture=replace(self.posture, classification="steady"),
            rail_state=replace(
                self.posture.rail_state,
                owner_layer="fitness",
                latest_clean_step=replace(self.posture.rail_state.latest_clean_step, owner_layer="atlas"),
                next_action=replace(
                    self.posture.rail_state.next_action,
                    action_id="fitness-owner-adoption",
                    owner_layer="fitness",
                    title="Resume Fitness owner adoption.",
                    rationale="Fitness owns the lane and should continue adoption work.",
                    verification_plan=("python -m unittest tests.test_atlas_playbook_contract_consumption",),
                ),
            ),
        )

        plan = build_worker_plan(posture, rail_state, next_action, self.rules)

        self.assertEqual("fitness_owner_adoption", plan.template_id)
        self.assertIn("Fitness", plan.prompt)
        self.assertTrue(any(path.startswith("repos/fawxzzy-fitness") for path in plan.files_to_modify))
        self.assertIn("ops/cortex/**", plan.prompt)

    def test_atlas_cortex_catch_up_next_action_produces_root_only_proof_prompt(self) -> None:
        posture, rail_state, next_action = self._with_state(
            posture=replace(self.posture, classification="steady"),
            rail_state=replace(
                self.posture.rail_state,
                owner_layer="atlas",
                latest_clean_step=replace(self.posture.rail_state.latest_clean_step, owner_layer="fitness"),
                next_action=replace(
                    self.posture.rail_state.next_action,
                    action_id="atlas-cortex-catch-up",
                    owner_layer="atlas",
                    title="Perform the matching ATLAS/Cortex catch-up.",
                    rationale="The root proof lane should stay at the ATLAS boundary.",
                    verification_plan=("python .\\ops\\validation\\validate_stack.py",),
                ),
            ),
        )

        plan = build_worker_plan(posture, rail_state, next_action, self.rules)

        self.assertEqual("atlas_cortex_catch_up", plan.template_id)
        self.assertTrue(all(not path.startswith("repos/") for path in plan.files_to_modify))
        self.assertIn("AGENTS.md", plan.prompt)
        self.assertIn("stack.yaml", plan.prompt)
        self.assertIn("Root proof work should validate stack posture", plan.prompt)

    def test_docs_adr_next_action_avoids_broad_stack_cleanup(self) -> None:
        posture, rail_state, next_action = self._with_state(
            posture=replace(self.posture, classification="steady"),
            rail_state=replace(
                self.posture.rail_state,
                owner_layer="cortex",
                next_action=replace(
                    self.posture.rail_state.next_action,
                    action_id="docs-adr-or-debt-slice",
                    owner_layer="cortex",
                    title="Draft the Cortex docs ADR slice.",
                    rationale="Capture the narrow docs slice without broad stack cleanup.",
                    verification_plan=("python -m unittest tests.test_cortex_worker_plan",),
                ),
            ),
        )

        plan = build_worker_plan(posture, rail_state, next_action, self.rules)

        self.assertEqual("docs_adr_or_debt_slice", plan.template_id)
        self.assertTrue(all(not path.startswith("repos/") for path in plan.files_to_modify))
        self.assertIn("broad stack cleanup", plan.prompt.lower())

    def test_generated_prompt_includes_files_to_avoid_when_provided(self) -> None:
        posture, rail_state, next_action = self._with_state(
            rail_state=replace(
                self.posture.rail_state,
                next_action=replace(
                    self.posture.rail_state.next_action,
                    action_id="cortex-runtime-work",
                    owner_layer="cortex",
                    title="Continue Cortex runtime work.",
                    rationale="Keep the runtime lane active.",
                ),
            ),
        )

        plan = build_worker_plan(
            posture,
            rail_state,
            next_action,
            self.rules,
            files_to_avoid=["tmp/**", "repos/**"],
        )

        self.assertIn("tmp/**", plan.prompt)
        self.assertIn("repos/**", plan.prompt)
        self.assertIn("tmp/**", plan.files_to_avoid)
        self.assertIn("repos/**", plan.files_to_avoid)

    def test_invalid_next_action_fails_clearly(self) -> None:
        posture, rail_state, _ = self._with_state(
            rail_state=replace(
                self.posture.rail_state,
                next_action=replace(
                    self.posture.rail_state.next_action,
                    action_id="open-connector-work",
                    owner_layer="connector",
                    title="Open connector work.",
                    rationale="This lane is outside the supported Cortex prompt templates.",
                ),
            ),
        )
        unsupported_next_action = replace(
            rail_state.next_action,
            action_id="open-connector-work",
            owner_layer="connector",
            title="Open connector work.",
            rationale="This lane is outside the supported Cortex prompt templates.",
        )

        with self.assertRaisesRegex(ValueError, "Unsupported Cortex NextAction"):
            build_worker_plan(posture, rail_state, unsupported_next_action, self.rules)


if __name__ == "__main__":
    unittest.main()
