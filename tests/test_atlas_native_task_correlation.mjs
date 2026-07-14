import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  NativeTaskCorrelationError,
  correlateNativeTask,
  run,
} from "../ops/atlas/native_task_correlation.mjs";
import {
  loadKnownSchema,
  validateJsonSchema,
} from "../packages/atlas-contracts/scripts/lib/validate-json-schema.mjs";

function validJob() {
  return {
    contract_version: "atlas.job-envelope.v2",
    job_id: "job-native-correlation-001",
    component_id: "atlas-root",
    project_id: "atlas",
    created_at: "2026-07-14T04:50:00Z",
    objective: "Correlate one bounded native task result.",
    scope: {
      owner_repository: "atlas",
      allowed_paths: ["ops/atlas/native_task_correlation.mjs"],
      forbidden_paths: ["secrets/**", "repos/**"],
    },
    runtime: {
      model: "gpt-5.6-terra",
      reasoning: "high",
      speed: "standard",
      permissions: "full-access",
      approval_policy: "never",
    },
    authority: {
      external_mutations: [],
      production_deploy: false,
      destructive_actions: false,
    },
    verification: {
      commands: ["node --test tests/test_atlas_native_task_correlation.mjs"],
      evidence_required: ["schema-valid execution receipt"],
    },
    correlations: { card_id: null, parent_job_id: null },
    expected_receipt_version: "atlas.execution-receipt.v2",
  };
}

function validTaskResult() {
  return {
    job_id: "job-native-correlation-001",
    thread_id: "019f5ef2-29cb-73b3-a80d-ebe2160d918f",
    turn_id: "019f5ef2-fabe-7d51-8a61-a7d06f23ac27",
    terminal_status: "completed",
    recorded_at: "2026-07-14T04:47:00Z",
    final_response: "Read-only native continuation completed.",
    changed_paths: [],
    commits: [],
    evidence_refs: ["docs/ops/native-task-spike.md"],
    blockers: [],
    follow_up: [],
    authority_actions: [],
    verification: [
      { command: "git rev-parse HEAD", status: "passed", evidence_refs: ["docs/ops/native-task-spike.md"] },
    ],
    branch: "main",
    worktree: null,
  };
}

test("correlates native identities into a schema-valid execution receipt", async () => {
  const receipt = await correlateNativeTask({ job: validJob(), taskResult: validTaskResult() });
  assert.equal(receipt.job_id, "job-native-correlation-001");
  assert.equal(receipt.correlations.thread_id, validTaskResult().thread_id);
  assert.equal(receipt.correlations.turn_id, validTaskResult().turn_id);
  assert.equal(receipt.runtime_effective.model, "unavailable");
  assert.deepEqual(receipt.extensions.runtime_requested, validJob().runtime);
  assert.equal(receipt.extensions.runtime_policy_observed, false);
  const loaded = await loadKnownSchema("atlas.execution-receipt.v2");
  assert.equal(loaded.ok, true);
  assert.deepEqual(validateJsonSchema(receipt, loaded.schema), []);
});

test("uses supplied effective runtime without confusing requested policy", async () => {
  const taskResult = validTaskResult();
  taskResult.runtime_effective = {
    model: "gpt-5.6-terra",
    reasoning: "high",
    speed: "standard",
    permissions: "full-access",
    approval_policy: "never",
  };
  const receipt = await correlateNativeTask({ job: validJob(), taskResult });
  assert.equal(receipt.runtime_effective.model, "gpt-5.6-terra");
  assert.equal(receipt.extensions.runtime_policy_observed, true);
});

test("receipt identity is deterministic", async () => {
  const first = await correlateNativeTask({ job: validJob(), taskResult: validTaskResult() });
  const second = await correlateNativeTask({ job: validJob(), taskResult: validTaskResult() });
  assert.equal(first.receipt_id, second.receipt_id);
});

test("rejects mismatched job correlation", async () => {
  const taskResult = validTaskResult();
  taskResult.job_id = "job-other";
  await assert.rejects(
    correlateNativeTask({ job: validJob(), taskResult }),
    (error) => error instanceof NativeTaskCorrelationError && error.message.includes("Job correlation mismatch"),
  );
});

test("rejects missing native turn identity", async () => {
  const taskResult = validTaskResult();
  delete taskResult.turn_id;
  await assert.rejects(
    correlateNativeTask({ job: validJob(), taskResult }),
    (error) => error instanceof NativeTaskCorrelationError && error.message.includes("turn_id"),
  );
});

test("rejects invalid job envelopes before correlation", async () => {
  const job = validJob();
  job.authority.production_deploy = "yes";
  await assert.rejects(
    correlateNativeTask({ job, taskResult: validTaskResult() }),
    (error) => error instanceof NativeTaskCorrelationError && error.message.includes("Job envelope failed"),
  );
});

test("CLI writes only to admitted runtime or tmp paths", async () => {
  const token = `native-task-correlation-${process.pid}-${Date.now()}`;
  const root = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/(.:)/, "$1")), "..");
  const inputDir = path.join(root, "tmp", token);
  await fs.mkdir(inputDir, { recursive: true });
  const jobPath = path.join(inputDir, "job.json");
  const taskPath = path.join(inputDir, "task.json");
  const outputPath = path.join(inputDir, "receipt.json");
  await fs.writeFile(jobPath, JSON.stringify(validJob()), "utf8");
  await fs.writeFile(taskPath, JSON.stringify(validTaskResult()), "utf8");
  try {
    const result = await run(["--job", jobPath, "--task-result", taskPath, "--output", outputPath]);
    assert.equal(result.status, "written");
    const receipt = JSON.parse(await fs.readFile(outputPath, "utf8"));
    assert.equal(receipt.contract_version, "atlas.execution-receipt.v2");
    await assert.rejects(
      run(["--job", jobPath, "--task-result", taskPath, "--output", path.join(root, "docs", `${token}.json`)]),
      (error) => error instanceof NativeTaskCorrelationError && error.message.includes("Output must be under"),
    );
  } finally {
    await fs.rm(inputDir, { recursive: true, force: true });
  }
});

test("rejects sensitive input paths", async () => {
  await assert.rejects(
    run(["--job", "secrets/job.json", "--task-result", "tmp/task.json", "--output", "tmp/out.json"]),
    (error) => error instanceof NativeTaskCorrelationError && error.message.includes("Sensitive input path"),
  );
});
