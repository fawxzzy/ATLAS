import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { runArtifactValidator } from "../../packages/atlas-contracts/scripts/validate-artifact.mjs";

export const EXPECTED_FAMILIES = Object.freeze([
  "componentManifest",
  "jobEnvelope",
  "executionReceipt",
]);

const SCHEMAS = Object.freeze({
  componentManifest: "atlas.component-manifest.v2",
  jobEnvelope: "atlas.job-envelope.v2",
  executionReceipt: "atlas.execution-receipt.v2",
});
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");

function relative(p) { return path.relative(ROOT, p).split(path.sep).join("/"); }
function fail(reasonCode, errors) { return { ok: false, code: reasonCode, reasonCode, errors }; }
async function readJson(file) { return JSON.parse(await fs.readFile(file, "utf8")); }

async function validateArtifact(family, file) {
  const result = await runArtifactValidator(["--schema", SCHEMAS[family], "--artifact", file, "--json"]);
  return result.result;
}

export async function validateAdoption(runPath) {
  let run;
  try { run = await readJson(path.resolve(runPath)); } catch (error) {
    return fail("MALFORMED_JSON", [error instanceof SyntaxError ? "malformed JSON rejected" : "run input is unreadable"]);
  }
  const errors = [];
  if (!run || typeof run !== "object") return fail("INVALID_RUN", ["run must be an object"]);
  const initialErrors = String(run.status ?? "").startsWith("success") ? [] : ["producer terminal status is not successful"];
  const contracts = run.atlasContractsV2;
  const paths = contracts?.artifactPaths;
  if (!paths || Object.keys(paths).length !== 3 || EXPECTED_FAMILIES.some((key) => typeof paths[key] !== "string")) {
    return fail("ARTIFACT_COUNT_MISMATCH", ["exactly three declared artifacts are required"]);
  }
  const resolved = {};
  for (const family of EXPECTED_FAMILIES) {
    const file = path.resolve(paths[family]);
    resolved[family] = file;
    const inside = file === ROOT || file.startsWith(`${ROOT}${path.sep}`);
    if (!inside) errors.push("escaped artifact path");
    try { if ((await fs.realpath(file)) !== file) errors.push("artifact realpath mismatch"); } catch { errors.push("artifact path does not exist"); }
  }
  if (errors.length) return fail("UNSAFE_PATH", errors);
  errors.push(...initialErrors);
  if (contracts.status?.terminal !== "success_no_changes" && contracts.status?.terminal !== "succeeded") errors.push("producer terminal receipt is not terminal");
  const artifacts = {};
  for (const family of EXPECTED_FAMILIES) {
    try { artifacts[family] = await readJson(resolved[family]); } catch { return fail("MALFORMED_JSON", ["malformed JSON rejected"]); }
    const validation = await validateArtifact(family, resolved[family]);
    if (!validation.ok) errors.push(`${family} canonical schema validation failed`);
  }
  const identity = contracts.identities ?? {};
  const job = artifacts.jobEnvelope;
  const receipt = artifacts.executionReceipt;
  const manifest = artifacts.componentManifest;
  if (identity.componentId !== manifest.component_id || job.component_id !== manifest.component_id || receipt.component_id !== manifest.component_id) errors.push("component correlation mismatch");
  if (job.project_id !== receipt.project_id || job.project_id !== "atlas") errors.push("project correlation mismatch");
  if (identity.jobId !== job.job_id || receipt.job_id !== job.job_id) errors.push("JOB_MISMATCH");
  if (identity.runId !== run.runId) errors.push("RUN_MISMATCH");
  if (job.expected_receipt_version !== "atlas.execution-receipt.v2" || receipt.contract_version !== "atlas.execution-receipt.v2") errors.push("RECEIPT_VERSION_MISMATCH");
  if (receipt.status !== "succeeded") errors.push("receipt is not terminal succeeded");
  const validations = contracts.validation ?? {};
  for (const family of EXPECTED_FAMILIES) {
    const evidence = validations[family];
    if (!evidence?.invoked || evidence.exitCode !== 0 || !evidence.result?.ok || evidence.result.code !== "VALID" || evidence.schemaId !== SCHEMAS[family] || path.resolve(evidence.artifactPath ?? "") !== resolved[family]) errors.push(`${family} producer validation representation missing`);
  }
  if (!run.workerGitState || !Array.isArray(run.workerGitState.violations) || run.workerGitState.violations.length || run.workerGitState.failureCode) errors.push("WORKER_GIT_VIOLATION");
  if (run.authorityActions?.length || run.mutationScopeViolations?.length || run.effectivePolicies?.externalAuthorityAction || receipt.authority_actions?.length) errors.push("EXTERNAL_AUTHORITY_ACTION");
  if (errors.length) return fail(errors.find((e) => e.includes("JOB_MISMATCH") || e.includes("RUN_MISMATCH") || e.includes("RECEIPT_VERSION_MISMATCH") || e.includes("WORKER_GIT_VIOLATION") || e.includes("EXTERNAL_AUTHORITY_ACTION")) ?? "REJECTED", errors);
  const evidence = {};
  for (const family of EXPECTED_FAMILIES) {
    const bytes = await fs.readFile(resolved[family]);
    evidence[family] = { path: relative(resolved[family]), bytes: bytes.length, sha256: `sha256:${crypto.createHash("sha256").update(bytes).digest("hex")}` };
  }
  return { ok: true, code: "ACCEPTED", reasonCode: "ACCEPTED", families: EXPECTED_FAMILIES, runId: run.runId, jobId: job.job_id, evidence };
}

function parseArgs(argv) {
  const runIndex = argv.indexOf("--run");
  return { json: argv.includes("--json"), run: runIndex >= 0 ? argv[runIndex + 1] : null };
}
const args = parseArgs(process.argv.slice(2));
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const result = args.run ? await validateAdoption(args.run) : fail("MISSING_INPUT", ["--run is required"]);
  if (args.json) console.log(JSON.stringify(result));
  else console.log(`${result.code}: ${result.ok ? "Contracts v2 adoption accepted" : result.errors.join(" ")}`);
  process.exitCode = result.ok ? 0 : 1;
}
