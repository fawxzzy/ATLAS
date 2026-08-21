import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { prepareEngineeringMemoryJob } from "../ops/atlas/prepare_engineering_memory_job.mjs";
import { validateEngineeringMemoryGate } from "../ops/atlas/engineering_memory_gate.mjs";

function jobFixture(root, objective = "Make gameplay settings match the main menu") {
  return {
    contract_version: "atlas.job-envelope.v2",
    job_id: "atlas-stack-intake-fixture",
    component_id: "stack",
    project_id: "mazer",
    created_at: "2026-08-21T12:00:00.000Z",
    objective,
    scope: { owner_repository: "mazer", allowed_paths: ["src/**"], forbidden_paths: [".git/**"] },
    runtime: { model: "gpt-5.6-terra", reasoning: "medium", speed: "standard", permissions: "full-access", approval_policy: "never" },
    authority: { external_mutations: [], production_deploy: false, destructive_actions: false },
    verification: { commands: ["npm test"], evidence_required: ["runner-log"] },
    correlations: { card_id: null, parent_job_id: null },
    expected_receipt_version: "atlas.execution-receipt.v2",
    extensions: { run_id: "intake-fixture" },
  };
}

async function fixture(t) {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "atlas-engineering-intake-"));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  const repo = path.join(root, "repo");
  const docs = path.join(root, "docs");
  const log = path.join(root, "runtime", "run");
  await Promise.all([fs.mkdir(path.join(repo, "src"), { recursive: true }), fs.mkdir(docs, { recursive: true }), fs.mkdir(log, { recursive: true })]);
  await fs.writeFile(path.join(repo, "src", "SettingsButton.tsx"), "export const settingsButton = { color: 'green', pulse: true };\n");
  await fs.writeFile(path.join(docs, "visual-contract.md"), "Settings controls share color animation and behavior across gameplay and menu.\n");
  const sourceRef = path.join(log, "engineering-memory.source.md");
  const cardRecordRef = path.join(log, "atlas.card-record.v2.json");
  const searchRecordRef = path.join(log, "engineering-memory.precedent-search.json");
  return { root, repo, sourceRef, cardRecordRef, searchRecordRef };
}

test("normalizes rough parity language and passes the mutation gate", async (t) => {
  const item = await fixture(t);
  const sourceText = "The gameplay settings icon still does not match the main menu settings icon.";
  await fs.writeFile(item.sourceRef, sourceText);
  const result = await prepareEngineeringMemoryJob({
    job: jobFixture(item.root),
    sourceText,
    sourceRef: item.sourceRef,
    workspaceRoot: item.repo,
    cardRecordRef: item.cardRecordRef,
    searchRecordRef: item.searchRecordRef,
    root: item.root,
    checkedAt: "2026-08-21T12:01:00.000Z",
  });

  assert.equal(result.profile.task_type, "ui_parity");
  assert.equal(result.profile.phase, "planned");
  assert.equal(result.card.lifecycle, "ready");
  assert.equal(result.job.correlations.card_id, result.card.card_id);
  assert.equal(result.profile.verification.visual.source_surface, "main-menu:semantic-control");
  assert.deepEqual(result.profile.verification.visual.target_surfaces, ["gameplay:semantic-control"]);
  assert(result.profile.precedent_check.searched_sources.some((source) => source.kind === "current_repo"));
  assert(result.profile.precedent_check.searched_sources.some((source) => source.kind === "atlas_docs"));

  const gate = await validateEngineeringMemoryGate({ job: result.job, card: result.card, gate: "mutation", root: item.root });
  assert.deepEqual(gate, { ok: true, errors: [] });
});

test("records the exact first durable pattern decision when both searches miss", async (t) => {
  const item = await fixture(t);
  const sourceText = "Implement quasarflange zorbulator behavior.";
  await fs.writeFile(item.sourceRef, sourceText);
  const job = jobFixture(item.root, "Implement quasarflange zorbulator behavior");
  job.project_id = "atlas";
  job.scope.owner_repository = "atlas";
  const result = await prepareEngineeringMemoryJob({
    job,
    sourceText,
    sourceRef: item.sourceRef,
    workspaceRoot: item.repo,
    cardRecordRef: item.cardRecordRef,
    searchRecordRef: item.searchRecordRef,
    root: item.root,
    checkedAt: "2026-08-21T12:02:00.000Z",
  });

  assert.equal(result.profile.precedent_check.status, "checked-none");
  assert.equal(result.profile.precedent_check.decision, "first-durable-pattern");
  assert.equal(result.profile.precedent_check.rationale, "No matching precedent found. Creating first durable pattern.");
  assert(result.profile.precedent_check.searched_sources.every((source) => source.evidence_refs.length > 0));
});

test("uses a stable card identity for retries of the same rough note", async (t) => {
  const item = await fixture(t);
  const sourceText = "The gameplay settings icon still does not match the main menu settings icon.";
  await fs.writeFile(item.sourceRef, sourceText);
  const firstJob = jobFixture(item.root);
  const secondJob = jobFixture(item.root);
  secondJob.job_id = "atlas-stack-intake-fixture-retry";
  const first = await prepareEngineeringMemoryJob({
    job: firstJob, sourceText, sourceRef: item.sourceRef, workspaceRoot: item.repo,
    cardRecordRef: item.cardRecordRef, searchRecordRef: item.searchRecordRef, root: item.root,
    checkedAt: "2026-08-21T12:03:00.000Z",
  });
  const second = await prepareEngineeringMemoryJob({
    job: secondJob, sourceText, sourceRef: item.sourceRef, workspaceRoot: item.repo,
    cardRecordRef: item.cardRecordRef, searchRecordRef: item.searchRecordRef, root: item.root,
    checkedAt: "2026-08-21T12:04:00.000Z",
  });
  assert.equal(first.card.card_id, second.card.card_id);
  assert.notEqual(first.profile.task_id, second.profile.task_id);
});
