import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { runArtifactValidator } from "../../packages/atlas-contracts/scripts/validate-artifact.mjs";

export const EXPECTED_FAMILIES = Object.freeze([
  "componentManifest",
  "jobEnvelope",
  "contextPacket",
  "approvalRecord",
  "evidenceBundle",
  "executionReceipt",
]);

const SCHEMAS = Object.freeze({
  componentManifest: "atlas.component-manifest.v2",
  jobEnvelope: "atlas.job-envelope.v2",
  contextPacket: "atlas.context-packet.v2",
  approvalRecord: "atlas.approval-record.v2",
  evidenceBundle: "atlas.evidence-bundle.v2",
  executionReceipt: "atlas.execution-receipt.v2",
});
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const VALIDATOR = path.join(ROOT, "packages", "atlas-contracts", "scripts", "validate-artifact.mjs");
const EXTERNAL_ACTIONS = Object.freeze(["push", "deploy", "production", "discord", "board", "data_mutation"]);

function relative(file) { return path.relative(ROOT, file).split(path.sep).join("/"); }
function fail(reasonCode, errors) { return { ok: false, code: reasonCode, reasonCode, errors }; }
async function readJson(file) { return JSON.parse(await fs.readFile(file, "utf8")); }
function isRecord(value) { return Boolean(value) && typeof value === "object" && !Array.isArray(value); }
function resolvedPath(value) { return typeof value === "string" ? path.resolve(value) : null; }

async function validateArtifact(family, file) {
  return runArtifactValidator(["--schema", SCHEMAS[family], "--artifact", file, "--json"]);
}

function producerValidationMatches(evidence, expected, file) {
  if (!isRecord(evidence) || evidence.invoked !== true || resolvedPath(evidence.cliPath) !== VALIDATOR) return false;
  if (evidence.schemaId !== SCHEMAS[expected.family] || resolvedPath(evidence.artifactPath) !== file) return false;
  if (evidence.exitCode !== expected.exitCode || evidence.ok !== expected.result.ok || evidence.reasonCode !== null) return false;
  if (JSON.stringify(evidence.result) !== JSON.stringify(expected.result)) return false;
  try { return JSON.stringify(JSON.parse(evidence.stdout)) === JSON.stringify(expected.result) && evidence.stderr === "" && evidence.parseError === null; } catch { return false; }
}

function artifactReferencesMatch(receipt, resolved) {
  const refs = receipt.extensions?.artifact_refs;
  if (!isRecord(refs) || !Array.isArray(receipt.evidence_refs)) return false;
  const expected = {
    context_packet: resolved.contextPacket,
    approval_record: resolved.approvalRecord,
    evidence_bundle: resolved.evidenceBundle,
  };
  return Object.entries(expected).every(([key, file]) => resolvedPath(refs[key]) === file && receipt.evidence_refs.some((reference) => resolvedPath(reference) === file));
}

function hasTerminalVerificationEvidence(receipt, evidenceBundle) {
  const verificationRefs = new Set((receipt.verification ?? []).flatMap((entry) => entry?.status === "passed" ? entry.evidence_refs ?? [] : []).map(resolvedPath));
  return evidenceBundle.classifications?.includes("verified")
    && evidenceBundle.evidence?.some((entry) => entry?.status === "passed" && verificationRefs.has(resolvedPath(entry.ref)));
}

function authorityDenied(run, job, approval, receipt) {
  const denied = job.extensions?.external_authority;
  const notExercised = receipt.extensions?.external_authority;
  return job.authority?.external_mutations?.length === 0
    && job.authority?.production_deploy === false
    && job.authority?.destructive_actions === false
    && EXTERNAL_ACTIONS.every((action) => denied?.[action] === "denied" && notExercised?.[action] === "not-exercised")
    && approval.action?.kind === "external-mutation"
    && approval.decision === "rejected"
    && approval.extensions?.external_authority === "denied"
    && !run.authorityActions?.length
    && !run.mutationScopeViolations?.length
    && !run.effectivePolicies?.externalAuthorityAction
    && !receipt.authority_actions?.length;
}

export async function validateAdoption(runPath) {
  let run;
  try { run = await readJson(path.resolve(runPath)); } catch (error) {
    return fail("MALFORMED_JSON", [error instanceof SyntaxError ? "malformed JSON rejected" : "run input is unreadable"]);
  }
  if (!isRecord(run)) return fail("INVALID_RUN", ["run must be an object"]);

  const contracts = run.atlasContractsV2;
  const paths = contracts?.artifactPaths;
  const declaredFamilies = isRecord(paths) ? Object.keys(paths).sort() : [];
  if (declaredFamilies.length !== EXPECTED_FAMILIES.length || declaredFamilies.join(",") !== [...EXPECTED_FAMILIES].sort().join(",") || EXPECTED_FAMILIES.some((family) => typeof paths[family] !== "string")) {
    return fail("ARTIFACT_COUNT_MISMATCH", ["exactly six declared artifacts are required"]);
  }

  const resolved = {};
  const pathErrors = [];
  for (const family of EXPECTED_FAMILIES) {
    const file = path.resolve(paths[family]);
    resolved[family] = file;
    if (!(file === ROOT || file.startsWith(`${ROOT}${path.sep}`))) pathErrors.push("escaped artifact path");
    try { if (await fs.realpath(file) !== file) pathErrors.push("artifact realpath mismatch"); } catch { pathErrors.push("artifact path does not exist"); }
  }
  if (new Set(Object.values(resolved)).size !== EXPECTED_FAMILIES.length) pathErrors.push("duplicate artifact path");
  if (pathErrors.length) return fail("UNSAFE_PATH", pathErrors);

  const artifacts = {};
  const validations = {};
  for (const family of EXPECTED_FAMILIES) {
    try { artifacts[family] = await readJson(resolved[family]); } catch { return fail("MALFORMED_JSON", ["malformed JSON rejected"]); }
    validations[family] = await validateArtifact(family, resolved[family]);
    if (!validations[family].result.ok) return fail("CANONICAL_SCHEMA_INVALID", [`${family} canonical schema validation failed`]);
  }
  for (const family of EXPECTED_FAMILIES) {
    if (!producerValidationMatches(contracts.validation?.[family], { family, ...validations[family] }, resolved[family])) {
      return fail("PRODUCER_VALIDATION_MISMATCH", [`${family} producer validation representation does not match canonical validation`]);
    }
  }

  const manifest = artifacts.componentManifest;
  const job = artifacts.jobEnvelope;
  const context = artifacts.contextPacket;
  const approval = artifacts.approvalRecord;
  const evidenceBundle = artifacts.evidenceBundle;
  const receipt = artifacts.executionReceipt;
  const identity = contracts.identities ?? {};

  if (identity.componentId !== manifest.component_id || job.component_id !== manifest.component_id || receipt.component_id !== manifest.component_id) return fail("COMPONENT_MISMATCH", ["component correlation mismatch"]);
  if (job.project_id !== receipt.project_id || job.project_id !== "atlas") return fail("PROJECT_MISMATCH", ["project correlation mismatch"]);
  if (identity.jobId !== job.job_id || receipt.job_id !== job.job_id) return fail("JOB_MISMATCH", ["job correlation mismatch"]);
  if (identity.runId !== run.runId || job.extensions?.run_id !== run.runId) return fail("RUN_MISMATCH", ["run correlation mismatch"]);
  if (context.job_id !== job.job_id || context.component_id !== manifest.component_id || context.extensions?.run_id !== run.runId) return fail("CONTEXT_CORRELATION_MISMATCH", ["ContextPacket job, component, or run correlation mismatch"]);
  if (approval.job_id !== job.job_id || approval.extensions?.component_id !== manifest.component_id || approval.extensions?.run_id !== run.runId) return fail("APPROVAL_CORRELATION_MISMATCH", ["ApprovalRecord job, component, or run correlation mismatch"]);
  if (evidenceBundle.job_id !== job.job_id || evidenceBundle.environment?.component_id !== manifest.component_id || evidenceBundle.extensions?.run_id !== run.runId) return fail("EVIDENCE_CORRELATION_MISMATCH", ["EvidenceBundle job, component, or run correlation mismatch"]);
  if (!artifactReferencesMatch(receipt, resolved)) return fail("RECEIPT_ARTIFACT_REFERENCE_MISMATCH", ["ExecutionReceipt artifact references must exactly match declared artifacts"]);

  if (approval.decision !== "rejected") return fail("APPROVAL_DENIAL_MISMATCH", ["external mutation approval must be rejected"]);
  if (!authorityDenied(run, job, approval, receipt)) return fail("EXTERNAL_AUTHORITY_ACTION", ["external authority denial or no-action proof is missing"]);
  if (job.expected_receipt_version !== "atlas.execution-receipt.v2" || receipt.contract_version !== "atlas.execution-receipt.v2") return fail("RECEIPT_VERSION_MISMATCH", ["receipt version mismatch"]);
  if (!String(run.status ?? "").startsWith("success") || contracts.status?.preflight !== "validated" || !["success_no_changes", "succeeded"].includes(contracts.status?.terminal) || contracts.status?.receiptValidated !== true || receipt.status !== "succeeded" || run.verification?.some((entry) => entry?.exitCode !== 0)) return fail("TERMINAL_STATUS_MISMATCH", ["producer terminal status is not accepted"]);
  if (!hasTerminalVerificationEvidence(receipt, evidenceBundle) || !receipt.verification?.length || receipt.verification.some((entry) => entry?.status !== "passed")) return fail("TERMINAL_EVIDENCE_MISMATCH", ["terminal verification evidence is missing or failed"]);
  if (receipt.blockers?.length || run.proofGateFailureReason || run.runtimePolicy?.blockers?.length || contracts.status?.reasonCode) return fail("BLOCKER_PRESENT", ["producer or receipt blocker is present"]);
  if (!run.workerGitState || !Array.isArray(run.workerGitState.violations) || run.workerGitState.violations.length || run.workerGitState.failureCode) return fail("WORKER_GIT_VIOLATION", ["worker Git violation"]);

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
