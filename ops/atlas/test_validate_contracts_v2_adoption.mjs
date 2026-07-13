import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { validateAdoption } from "./validate_contracts_v2_adoption.mjs";

const canary = "repos/_stack/.codex/logs/20260713T082953822Z-atlas-contracts-v2-stack-producer-no-change-canary-r1/run.json";
const temp = await fs.mkdtemp(path.join(os.tmpdir(), "atlas-contracts-v2-"));
const source = JSON.parse(await fs.readFile(canary, "utf8"));

async function scenario(name, mutate, expected) {
  const run = structuredClone(source);
  mutate(run);
  const file = path.join(temp, `${name}.json`);
  await fs.writeFile(file, JSON.stringify(run));
  const result = await validateAdoption(file);
  assert.equal(result.ok, false, `${name} must be rejected`);
  assert.equal(result.reasonCode, expected, `${name} reason code`);
}

const accepted = await validateAdoption(canary);
assert.equal(accepted.code, "ACCEPTED");
assert.deepEqual(accepted.families, ["componentManifest", "jobEnvelope", "executionReceipt"]);

await scenario("job-mismatch", (run) => { run.atlasContractsV2.identities.jobId = "wrong-job"; }, "JOB_MISMATCH");
await scenario("escaped-path", (run) => { run.atlasContractsV2.artifactPaths.jobEnvelope = "C:/Windows/job.json"; }, "UNSAFE_PATH");
await scenario("failed-run", (run) => { run.status = "failed"; }, "REJECTED");
await scenario("nonterminal-run", (run) => { run.atlasContractsV2.status.terminal = "running"; }, "REJECTED");
await scenario("worker-git", (run) => { run.workerGitState.violations = ["dirty"]; }, "WORKER_GIT_VIOLATION");
await scenario("external-authority", (run) => { run.authorityActions = ["push"]; }, "EXTERNAL_AUTHORITY_ACTION");

const malformed = path.join(temp, "malformed.json");
await fs.writeFile(malformed, "{ malformed JSON rejected");
const malformedResult = await validateAdoption(malformed);
assert.equal(malformedResult.reasonCode, "MALFORMED_JSON");

console.log("real-canary acceptance passed");
console.log("job-mismatch, escaped-path, failed-run, nonterminal-run, worker-git, external-authority, malformed JSON rejected: passed");
