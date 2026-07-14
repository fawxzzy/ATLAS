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

function validContextPacket() {
  return {
    contract_version: "atlas.context-packet.v2",
    context_id: "context-native-correlation-001",
    job_id: "job-native-correlation-001",
    component_id: "atlas-root",
    assembled_at: "2026-07-14T04:51:00Z",
    sources: [{ kind: "repository", ref: "AGENTS.md", authority: "authoritative", digest: null }],
    rules: ["Preserve owner-repository authority."],
    decisions: ["Use native execution and backend-neutral Atlas correlation."],
    risks: ["Effective runtime policy may be unavailable from native task reads."],
  };
}

function validEvidenceBundle() {
  return {
    contract_version: "atlas.evidence-bundle.v2",
    bundle_id: "evidence-native-correlation-001",
    job_id: "job-native-correlation-001",
    recorded_at: "2026-07-14T04:52:00Z",
    environment: { component_id: "atlas-root", commit: "0123456789abcdef", branch: "main" },
    evidence: [
      { kind: "test", ref: "native-correlation-tests", status: "passed", digest: null, summary: "Focused tests passed." },
    ],
    classifications: ["verified"],
  };
}

function validWorkerLease() {
  return {
    contract_version: "atlas.worker-lease.v2",
    lease_id: "lease-native-correlation-001",
    job_id: "job-native-correlation-001",
    component_id: "atlas-root",
    status: "released",
    acquired_at: "2026-07-14T04:50:00Z",
    expires_at: "2026-07-14T05:50:00Z",
    renewed_at: null,
    released_at: "2026-07-14T04:53:00Z",
    owner: {
      worker_id: "native-task-019f5ef2",
      thread_id: "019f5ef2-29cb-73b3-a80d-ebe2160d918f",
      turn_id: "019f5ef2-fabe-7d51-8a61-a7d06f23ac27",
    },
    workspace: { root: "<ATLAS_ROOT>", worktree: null, branch: "main" },
    resources: [
      { kind: "custom", resource_id: "atlas-root-read-only-inspection", exclusive: false, metadata: { mode: "read-only" } },
    ],
    recovery: { strategy: "release", checkpoint: "runtime/atlas/native-task-correlations/job-native-correlation-001.json" },
  };
}

function correlationInput(overrides = {}) {
  return {
    job: validJob(),
    taskResult: validTaskResult(),
    contextPacket: validContextPacket(),
    evidenceBundle: validEvidenceBundle(),
    workerLease: validWorkerLease(),
    ...overrides,
  };
}

test("correlates native identities into a schema-valid execution receipt", async () => {
  const receipt = await correlateNativeTask(correlationInput());
  assert.equal(receipt.job_id, "job-native-correlation-001");
  assert.equal(receipt.correlations.thread_id, validTaskResult().thread_id);
  assert.equal(receipt.correlations.turn_id, validTaskResult().turn_id);
  assert.equal(receipt.runtime_effective.model, "unavailable");
  assert.deepEqual(receipt.extensions.runtime_requested, validJob().runtime);
  assert.equal(receipt.extensions.runtime_policy_observed, false);
  assert.equal(receipt.extensions.context_binding.context_id, "context-native-correlation-001");
  assert.equal(receipt.extensions.evidence_binding.bundle_id, "evidence-native-correlation-001");
  assert.equal(receipt.extensions.worker_lease_binding.lease_id, "lease-native-correlation-001");
  assert.ok(receipt.evidence_refs.includes("native-correlation-tests"));
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
  const receipt = await correlateNativeTask(correlationInput({ taskResult }));
  assert.equal(receipt.runtime_effective.model, "gpt-5.6-terra");
  assert.equal(receipt.extensions.runtime_policy_observed, true);
});

test("receipt identity is deterministic", async () => {
  const first = await correlateNativeTask(correlationInput());
  const second = await correlateNativeTask(correlationInput());
  assert.equal(first.receipt_id, second.receipt_id);
});

test("rejects mismatched job correlation", async () => {
  const taskResult = validTaskResult();
  taskResult.job_id = "job-other";
  await assert.rejects(
    correlateNativeTask(correlationInput({ taskResult })),
    (error) => error instanceof NativeTaskCorrelationError && error.message.includes("Job correlation mismatch"),
  );
});

test("rejects missing native turn identity", async () => {
  const taskResult = validTaskResult();
  delete taskResult.turn_id;
  await assert.rejects(
    correlateNativeTask(correlationInput({ taskResult })),
    (error) => error instanceof NativeTaskCorrelationError && error.message.includes("turn_id"),
  );
});

test("rejects invalid job envelopes before correlation", async () => {
  const job = validJob();
  job.authority.production_deploy = "yes";
  await assert.rejects(
    correlateNativeTask(correlationInput({ job })),
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
  const contextPath = path.join(inputDir, "context.json");
  const evidencePath = path.join(inputDir, "evidence.json");
  const leasePath = path.join(inputDir, "lease.json");
  await fs.writeFile(jobPath, JSON.stringify(validJob()), "utf8");
  await fs.writeFile(taskPath, JSON.stringify(validTaskResult()), "utf8");
  await fs.writeFile(contextPath, JSON.stringify(validContextPacket()), "utf8");
  await fs.writeFile(evidencePath, JSON.stringify(validEvidenceBundle()), "utf8");
  await fs.writeFile(leasePath, JSON.stringify(validWorkerLease()), "utf8");
  try {
    const baseArguments = [
      "--job", jobPath,
      "--task-result", taskPath,
      "--context", contextPath,
      "--evidence", evidencePath,
      "--lease", leasePath,
    ];
    const result = await run([...baseArguments, "--output", outputPath]);
    assert.equal(result.status, "written");
    const receipt = JSON.parse(await fs.readFile(outputPath, "utf8"));
    assert.equal(receipt.contract_version, "atlas.execution-receipt.v2");
    await assert.rejects(
      run([...baseArguments, "--output", path.join(root, "docs", `${token}.json`)]),
      (error) => error instanceof NativeTaskCorrelationError && error.message.includes("Output must be under"),
    );
  } finally {
    await fs.rm(inputDir, { recursive: true, force: true });
  }
});

test("rejects sensitive input paths", async () => {
  await assert.rejects(
    run([
      "--job", "secrets/job.json",
      "--task-result", "tmp/task.json",
      "--context", "tmp/context.json",
      "--evidence", "tmp/evidence.json",
      "--lease", "tmp/lease.json",
      "--output", "tmp/out.json",
    ]),
    (error) => error instanceof NativeTaskCorrelationError && error.message.includes("Sensitive input path"),
  );
});

test("rejects context job mismatches", async () => {
  const contextPacket = validContextPacket();
  contextPacket.job_id = "job-other";
  await assert.rejects(
    correlateNativeTask(correlationInput({ contextPacket })),
    (error) => error instanceof NativeTaskCorrelationError && error.message.includes("Context packet job correlation mismatch"),
  );
});

test("rejects evidence component mismatches", async () => {
  const evidenceBundle = validEvidenceBundle();
  evidenceBundle.environment.component_id = "stack";
  await assert.rejects(
    correlateNativeTask(correlationInput({ evidenceBundle })),
    (error) => error instanceof NativeTaskCorrelationError && error.message.includes("Evidence bundle component correlation mismatch"),
  );
});

test("rejects worker lease owner mismatches", async () => {
  const workerLease = validWorkerLease();
  workerLease.owner.thread_id = "thread-other";
  await assert.rejects(
    correlateNativeTask(correlationInput({ workerLease })),
    (error) => error instanceof NativeTaskCorrelationError && error.message.includes("Worker lease owner"),
  );
});

test("rejects released leases without a release timestamp", async () => {
  const workerLease = validWorkerLease();
  workerLease.released_at = null;
  await assert.rejects(
    correlateNativeTask(correlationInput({ workerLease })),
    (error) => error instanceof NativeTaskCorrelationError && error.message.includes("requires released_at"),
  );
});
