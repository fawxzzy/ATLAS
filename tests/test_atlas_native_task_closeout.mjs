import assert from "node:assert/strict";
import test from "node:test";

import { NativeTaskCloseoutError, buildCloseout } from "../ops/atlas/native_task_closeout.mjs";

const receipt = {
  contract_version: "atlas.execution-receipt.v2",
  receipt_id: "atr_closeout_001",
  job_id: "job-closeout-001",
  recorded_at: "2026-07-14T05:30:00Z",
  status: "succeeded",
  component_id: "atlas-root",
  project_id: "atlas",
  runtime_effective: { model: "unavailable", reasoning: "unavailable", speed: "unavailable", permissions: "unavailable", approval_policy: "unavailable" },
  changed_paths: [],
  commits: [],
  verification: [],
  evidence_refs: ["docs/ops/execution-proof.md"],
  blockers: [],
  follow_up: [],
  correlations: { card_id: null, thread_id: "thread-001", turn_id: "turn-001", branch: "main", worktree: null },
  authority_actions: [],
  summary: "Closeout proof succeeded.",
  extensions: {},
};

const base = {
  receipt,
  markerId: "owner-lane-agent-service-bus-and-discordos-ops-readiness",
  markerScope: "ten binary native-first orchestration units",
  numerator: 8,
  denominator: 10,
  previousPercentage: 70,
  measuredAt: "2026-07-14T05:31:00Z",
  validUntil: "2026-07-21T05:31:00Z",
  transitionReason: "Unit 9 produced validated marker and knowledge closeout artifacts.",
  evidenceRefs: ["tests/test_atlas_native_task_closeout.mjs"],
  knowledgeKind: "failure-mode",
  knowledgeName: "Readback Format Assumption Drift",
  knowledgeStatement: "A board readback validator can report false failure when its message-shape assumption lags the current journal format.",
  knowledgeScope: "Atlas and DiscordOS board integration",
  suggestedDestination: "Playbook failure-mode registry",
  provenanceRefs: ["ops/atlas/native_task_closeout.mjs"],
};

test("builds schema-valid marker evidence and knowledge candidate", async () => {
  const result = await buildCloseout(base);
  assert.equal(result.markerEvidence.percentage, 80);
  assert.equal(result.markerEvidence.transition.previous_percentage, 70);
  assert.equal(result.knowledgeCandidate.kind, "failure-mode");
  assert.equal(result.knowledgeCandidate.review.status, "candidate");
});

test("produces deterministic knowledge identity", async () => {
  const first = await buildCloseout(base);
  const second = await buildCloseout(base);
  assert.equal(first.knowledgeCandidate.candidate_id, second.knowledgeCandidate.candidate_id);
});

test("deduplicates marker evidence references", async () => {
  const result = await buildCloseout({ ...base, evidenceRefs: ["docs/ops/execution-proof.md"] });
  assert.equal(result.markerEvidence.evidence_refs.filter((ref) => ref === "docs/ops/execution-proof.md").length, 1);
});

test("rejects non-terminal receipt", async () => {
  await assert.rejects(
    buildCloseout({ ...base, receipt: { ...receipt, status: "failed" } }),
    (error) => error instanceof NativeTaskCloseoutError && error.message.includes("succeeded"),
  );
});

test("rejects numerator above denominator", async () => {
  await assert.rejects(
    buildCloseout({ ...base, numerator: 11 }),
    (error) => error instanceof NativeTaskCloseoutError && error.message.includes("bounded integers"),
  );
});

test("rejects fractional denominator units", async () => {
  await assert.rejects(
    buildCloseout({ ...base, numerator: 7.5 }),
    (error) => error instanceof NativeTaskCloseoutError && error.message.includes("bounded integers"),
  );
});

test("rejects backward freshness window", async () => {
  await assert.rejects(
    buildCloseout({ ...base, validUntil: "2026-07-13T05:31:00Z" }),
    (error) => error instanceof NativeTaskCloseoutError && error.message.includes("validUntil"),
  );
});

test("allows historical evidence without a validity deadline", async () => {
  const result = await buildCloseout({ ...base, validUntil: null });
  assert.equal(result.markerEvidence.freshness.valid_until, null);
});
