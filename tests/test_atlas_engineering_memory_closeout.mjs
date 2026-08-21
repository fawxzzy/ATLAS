import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { completeEngineeringMemoryJob } from "../ops/atlas/complete_engineering_memory_job.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const EXAMPLE_ROOT = path.join(ROOT, "packages", "atlas-contracts", "fixtures", "examples", "engineering-memory");

async function loadJson(target) {
  return JSON.parse(await fs.readFile(target, "utf8"));
}

async function fixture() {
  const parent = path.join(ROOT, "tmp", "tests");
  await fs.mkdir(parent, { recursive: true });
  const workspaceRoot = await fs.mkdtemp(path.join(parent, "engineering-memory-closeout-"));
  const archiveRef = "docs/archive/fixture-engineering-memory-closeout.md";
  const archivePath = path.join(workspaceRoot, ...archiveRef.split("/"));
  await fs.mkdir(path.dirname(archivePath), { recursive: true });
  await fs.writeFile(archivePath, "# Fixture closeout\n\nFinal status: complete\n", "utf8");
  return {
    workspaceRoot,
    archiveRef,
    job: await loadJson(path.join(EXAMPLE_ROOT, "fitness-pwa-bottom-layout.job-envelope.v2.json")),
    card: await loadJson(path.join(EXAMPLE_ROOT, "fitness-pwa-bottom-layout.card-record.v2.json")),
  };
}

function closeout(job, card, archiveRef, evidence) {
  return {
    contract_version: "atlas.engineering-memory-closeout.v1",
    job_id: job.job_id,
    card_id: card.card_id,
    completed_at: "2026-08-21T18:00:00Z",
    final_status: "complete",
    archive_kind: "repository-docs",
    archive_ref: archiveRef,
    verification: { evidence, unverified: [] },
    blockers: [],
    child_task_ids: [],
  };
}

function runnerVerification(job) {
  return {
    contract_version: "atlas.engineering-memory-runner-verification.v1",
    job_id: job.job_id,
    recorded_at: "2026-08-21T18:00:00Z",
    records: [{ command: "pnpm test", exit_code: 0, stdout_ref: "runtime/test.stdout.log", stderr_ref: "runtime/test.stderr.log" }],
    no_change_proof_ref: null,
  };
}

test("runner reconciliation advances one bound job and card through verify and archive", async (t) => {
  const value = await fixture();
  t.after(() => fs.rm(value.workspaceRoot, { recursive: true, force: true }));
  const evidence = [{
    kind: "screenshot",
    ref: "tmp/visual-proof.json",
    result: "passed",
    surfaces: ["browser:/today:app-shell-bottom", "standalone:/today:app-shell-bottom"],
  }];
  const result = await completeEngineeringMemoryJob({
    job: value.job,
    card: value.card,
    closeout: closeout(value.job, value.card, value.archiveRef, evidence),
    runnerVerification: runnerVerification(value.job),
    workspaceRoot: value.workspaceRoot,
  });
  assert.equal(result.ok, true);
  assert.equal(result.verifyReceipt.status, "passed");
  assert.equal(result.archiveReceipt.status, "passed");
  assert.equal(result.archivedJob.extensions.engineering_memory.phase, "archived");
  assert.equal(result.archivedCard.lifecycle, "archived");
  assert.equal(result.archivedCard.source_ref, value.archiveRef);
});

test("terminal closeout stays blocked when visual parity evidence misses a required surface", async (t) => {
  const value = await fixture();
  t.after(() => fs.rm(value.workspaceRoot, { recursive: true, force: true }));
  const evidence = [{
    kind: "screenshot",
    ref: "tmp/incomplete-visual-proof.json",
    result: "passed",
    surfaces: ["browser:/today:app-shell-bottom"],
  }];
  const result = await completeEngineeringMemoryJob({
    job: value.job,
    card: value.card,
    closeout: closeout(value.job, value.card, value.archiveRef, evidence),
    runnerVerification: runnerVerification(value.job),
    workspaceRoot: value.workspaceRoot,
  });
  assert.equal(result.ok, false);
  assert.equal(result.verifyReceipt.status, "blocked");
  assert.match(result.verifyReceipt.errors.join("\n"), /missing required surface/i);
  assert.equal(result.archiveReceipt.status, "blocked");
});
