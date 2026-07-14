import assert from "node:assert/strict";
import test from "node:test";

import { NativeBoardCorrelationError, buildBoardEvent } from "../ops/atlas/native_board_correlation.mjs";

const job = {
  contract_version: "atlas.job-envelope.v2",
  job_id: "job-board-001",
  project_id: "atlas",
  created_at: "2026-07-14T05:20:00Z",
  component_id: "atlas-root",
  objective: "Prove board correlation without mutation.",
  scope: { owner_repository: "atlas", allowed_paths: ["runtime/atlas/native-board-correlations/**"], forbidden_paths: ["secrets/**", "repos/**"] },
  runtime: { model: "configured-default", reasoning: "medium", speed: "standard", permissions: "full-access", approval_policy: "never" },
  authority: { external_mutations: [], production_deploy: false, destructive_actions: false },
  verification: { commands: ["validate contracts"], evidence_required: ["schema-valid BoardEvent"] },
  correlations: { card_id: "atlas-card-001", parent_job_id: null },
  expected_receipt_version: "atlas.execution-receipt.v2",
  extensions: {},
};

const receipt = {
  contract_version: "atlas.execution-receipt.v2",
  receipt_id: "atr_board_001",
  job_id: job.job_id,
  recorded_at: "2026-07-14T05:22:00Z",
  status: "succeeded",
  component_id: "atlas-root",
  project_id: "atlas",
  runtime_effective: { model: "unavailable", reasoning: "unavailable", speed: "unavailable", permissions: "unavailable", approval_policy: "unavailable" },
  changed_paths: [],
  commits: [],
  verification: [],
  evidence_refs: [],
  blockers: [],
  follow_up: [],
  correlations: { card_id: "atlas-card-001", thread_id: "thread-001", turn_id: "turn-001", branch: "main", worktree: null },
  authority_actions: [],
  summary: "Read-only board correlation proof.",
  extensions: {},
};

const card = {
  contract_version: "atlas.card-record.v2",
  card_id: "atlas-card-001",
  project_id: "atlas",
  board_id: "atlas-planning",
  title: "Atlas board correlation canary",
  description: "No-send contract canary.",
  card_type: "governance",
  lifecycle: "review",
  priority: "medium",
  owner: "atlas-root",
  dependencies: [],
  board_version: 4,
  updated_at: "2026-07-14T05:21:00Z",
  source_ref: "docs/ops/canary.md",
  extensions: {},
};

const base = { job, receipt, card, eventType: "transition", occurredAt: "2026-07-14T05:23:00Z", fromState: "review", toState: "completed", reason: "verification passed" };

test("builds deterministic pending intent with DiscordOS writer authority", async () => {
  const first = await buildBoardEvent(base);
  const second = await buildBoardEvent(base);
  assert.equal(first.event_id, second.event_id);
  assert.equal(first.idempotency_key, second.idempotency_key);
  assert.equal(first.extensions.writer_authority, "discordos");
  assert.equal(first.extensions.external_mutation, "not_performed");
});

test("binds verified readback to the same idempotency identity", async () => {
  const intent = await buildBoardEvent(base);
  const readback = await buildBoardEvent({
    ...base,
    eventType: "readback",
    occurredAt: "2026-07-14T05:24:00Z",
    status: "verified",
    observedVersion: 4,
    readbackAt: "2026-07-14T05:24:00Z",
    readbackReceiptRef: "discordos-readback-001",
  });
  assert.equal(readback.idempotency_key, intent.idempotency_key);
  assert.notEqual(readback.event_id, intent.event_id);
  assert.equal(readback.extensions.external_mutation, "observed_only");
});

test("rejects project identity drift", async () => {
  await assert.rejects(
    buildBoardEvent({ ...base, card: { ...card, project_id: "mazer" } }),
    (error) => error instanceof NativeBoardCorrelationError && error.message.includes("Project identity"),
  );
});

test("rejects job identity drift", async () => {
  await assert.rejects(
    buildBoardEvent({ ...base, receipt: { ...receipt, job_id: "job-other" } }),
    (error) => error instanceof NativeBoardCorrelationError && error.message.includes("job identity"),
  );
});

test("rejects card identity drift", async () => {
  await assert.rejects(
    buildBoardEvent({ ...base, receipt: { ...receipt, correlations: { ...receipt.correlations, card_id: "card-other" } } }),
    (error) => error instanceof NativeBoardCorrelationError && error.message.includes("Card identity"),
  );
});

test("rejects stale expected version", async () => {
  await assert.rejects(
    buildBoardEvent({ ...base, expectedVersion: 3 }),
    (error) => error instanceof NativeBoardCorrelationError && error.message.includes("expected_version"),
  );
});

test("rejects lifecycle drift", async () => {
  await assert.rejects(
    buildBoardEvent({ ...base, fromState: "ready" }),
    (error) => error instanceof NativeBoardCorrelationError && error.message.includes("from state"),
  );
});

test("rejects pending intent that claims readback", async () => {
  await assert.rejects(
    buildBoardEvent({ ...base, observedVersion: 4 }),
    (error) => error instanceof NativeBoardCorrelationError && error.message.includes("Pending"),
  );
});

test("requires readback evidence for observed result", async () => {
  await assert.rejects(
    buildBoardEvent({ ...base, status: "verified" }),
    (error) => error instanceof NativeBoardCorrelationError && error.message.includes("requires version"),
  );
});

test("requires an error code for conflict result", async () => {
  await assert.rejects(
    buildBoardEvent({ ...base, status: "conflict", observedVersion: 4, readbackAt: "2026-07-14T05:24:00Z", readbackReceiptRef: "discordos-readback-001" }),
    (error) => error instanceof NativeBoardCorrelationError && error.message.includes("error_code"),
  );
});
