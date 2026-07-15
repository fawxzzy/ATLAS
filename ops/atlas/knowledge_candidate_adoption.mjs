import crypto from "node:crypto";
import { spawnSync } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const PLAYBOOK_ROOT = path.join(ROOT, "repos", "playbook");
const ATLAS_CONTRACTS_ROOT = path.join(ROOT, "packages", "atlas-contracts");
const VALID_FIXTURE = path.join(ATLAS_CONTRACTS_ROOT, "fixtures", "valid", "knowledge-candidate.v2.json");
const QUEUE_REF = ".playbook/memory/atlas-knowledge-candidates.json";
const PLAYBOOK_PR = 25;
const PLAYBOOK_FEATURE_HEAD = "14fce44268084bcaaab6d189b6ef18eb7a992faf";
const PLAYBOOK_MERGE_COMMIT = "f39dbac27d9a1c706ad11dbefe7f37feeebd5c3d";
const PLAYBOOK_BUILD_COMMAND = "pnpm -r build";
const PLAYBOOK_INSTALL_COMMAND = "pnpm install --frozen-lockfile --offline";
const TRUSTED_BUILD_PREFIX = "atlas-playbook-trusted-build-";
const TRUSTED_ARCHIVE_PATHS = Object.freeze([
  ".npmrc",
  "AGENTS.md",
  "package.json",
  "pnpm-lock.yaml",
  "pnpm-workspace.yaml",
  "packages",
  "scripts",
  "templates",
]);
const PLAYBOOK_CONSUMER_PATHS = Object.freeze([
  "packages/cli/src/commands/knowledge/atlasCandidate.ts",
  "packages/cli/src/commands/knowledge/atlasCandidate.test.ts",
  "packages/cli/src/commands/knowledge/index.ts",
  "packages/cli/src/commands/knowledge/shared.ts",
  "packages/engine/src/memory/atlasCandidateAdmission.ts",
  "packages/engine/src/memory/atlasCandidateAdmission.test.ts",
  "package.json",
]);
const DOCTRINE_PATHS = Object.freeze([
  ".playbook/memory/candidates.json",
  ".playbook/memory/knowledge/decisions.json",
  ".playbook/memory/knowledge/patterns.json",
  ".playbook/memory/knowledge/failure-modes.json",
  ".playbook/memory/knowledge/invariants.json",
  ".playbook/patterns.json",
  ".playbook/patterns-promoted.json",
  ".playbook/story-candidates.json",
  ".playbook/stories.json",
  "docs/PLAYBOOK_NOTES.md",
]);
const RECORDED_AT = "2026-07-15T17:25:00Z";

export const KNOWLEDGE_CANDIDATE_REASON_CODES = Object.freeze([
  "KNOWLEDGE_ATLAS_SCHEMA_REJECTED",
  "KNOWLEDGE_IDENTITY_LOSS",
  "KNOWLEDGE_PROVENANCE_MISMATCH",
  "KNOWLEDGE_DESTINATION_UNSUPPORTED",
  "KNOWLEDGE_CONSUMER_RECEIPT_MISSING",
  "KNOWLEDGE_CONSUMER_RECEIPT_MISMATCH",
  "KNOWLEDGE_AUTO_PROMOTION_DETECTED",
  "KNOWLEDGE_CONSUMER_REVISION_UNTRUSTED",
  "KNOWLEDGE_DOCTRINE_MUTATION",
]);

export class KnowledgeCandidateAdoptionError extends Error {
  constructor(reasonCode, errors) {
    super(errors.join("; "));
    this.name = "KnowledgeCandidateAdoptionError";
    this.reasonCode = reasonCode;
    this.errors = errors;
  }
}

function reject(reasonCode, error) {
  throw new KnowledgeCandidateAdoptionError(reasonCode, [error]);
}

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, canonicalize(value[key])]));
  }
  return value;
}

export function stableStringify(value) {
  return JSON.stringify(canonicalize(value));
}

function deterministicBytes(value) {
  return Buffer.from(`${JSON.stringify(canonicalize(value), null, 2)}\n`, "utf8");
}

function digest(bytes) {
  return `sha256:${crypto.createHash("sha256").update(bytes).digest("hex")}`;
}

function identity(prefix, value) {
  return `${prefix}_${digest(Buffer.from(stableStringify(value))).slice("sha256:".length, "sha256:".length + 32)}`;
}

function sameValue(left, right) {
  return stableStringify(left) === stableStringify(right);
}

async function exists(file) {
  try {
    await fs.access(file);
    return true;
  } catch {
    return false;
  }
}

function runGit(playbookRoot, args) {
  return spawnSync("git", ["-C", playbookRoot, ...args], { encoding: "utf8", windowsHide: true });
}

function runCommand(command, args, options = {}) {
  return spawnSync(command, args, {
    encoding: "utf8",
    windowsHide: true,
    maxBuffer: 50 * 1024 * 1024,
    ...options,
  });
}

function commandFailure(result) {
  return result.error?.message ?? result.stderr?.trim() ?? result.stdout?.trim() ?? "command failed";
}

function trackedStatus(playbookRoot) {
  const result = runGit(playbookRoot, ["status", "--short", "--untracked-files=no"]);
  if (result.status !== 0) reject("KNOWLEDGE_CONSUMER_REVISION_UNTRUSTED", commandFailure(result));
  return result.stdout.trim();
}

function isPathWithin(parent, child) {
  const relative = path.relative(path.resolve(parent), path.resolve(child));
  return relative !== "" && !relative.startsWith("..") && !path.isAbsolute(relative);
}

async function fileDigest(file) {
  if (!(await exists(file))) reject("KNOWLEDGE_CONSUMER_REVISION_UNTRUSTED", `Trusted build output is missing: ${file}`);
  return digest(await fs.readFile(file));
}

async function optionalFileDigest(file) {
  return (await exists(file)) ? digest(await fs.readFile(file)) : null;
}

export function verifyPlaybookConsumerRevision({
  playbookRoot = PLAYBOOK_ROOT,
  featureHead = PLAYBOOK_FEATURE_HEAD,
  mergeCommit = PLAYBOOK_MERGE_COMMIT,
} = {}) {
  const head = runGit(playbookRoot, ["rev-parse", "HEAD"]);
  const originMain = runGit(playbookRoot, ["rev-parse", "origin/main"]);
  const featureMerged = runGit(playbookRoot, ["merge-base", "--is-ancestor", featureHead, "origin/main"]);
  const mergeRetained = runGit(playbookRoot, ["merge-base", "--is-ancestor", mergeCommit, "origin/main"]);
  const checkoutDescendsFromFeature = runGit(playbookRoot, ["merge-base", "--is-ancestor", featureHead, "HEAD"]);
  const checkoutConsumerUnchanged = runGit(playbookRoot, ["diff", "--quiet", `${featureHead}..HEAD`, "--", ...PLAYBOOK_CONSUMER_PATHS]);
  const trackedStatus = runGit(playbookRoot, ["status", "--short", "--untracked-files=no"]);
  const headValue = head.stdout?.trim();
  const originMainValue = originMain.stdout?.trim();
  if (
    head.status !== 0
    || originMain.status !== 0
    || featureMerged.status !== 0
    || mergeRetained.status !== 0
    || checkoutDescendsFromFeature.status !== 0
    || checkoutConsumerUnchanged.status !== 0
    || trackedStatus.status !== 0
    || trackedStatus.stdout.trim()
  ) {
    reject("KNOWLEDGE_CONSUMER_REVISION_UNTRUSTED", "Playbook consumer checkout, merge ancestry, merged tree, or tracked-clean proof is untrusted.");
  }
  return {
    repository: "fawxzzy/playbook",
    pr: PLAYBOOK_PR,
    feature_head: featureHead,
    merge_commit: mergeCommit,
    checkout_head: headValue,
    origin_main: originMainValue,
    feature_is_ancestor_of_origin_main: true,
    merge_is_ancestor_of_origin_main: true,
    observed_checkout_descends_from_feature: true,
    observed_checkout_consumer_paths_unchanged_from_feature: true,
    tracked_clean: true,
  };
}

export async function assertTrustedPlaybookExecutable(consumerBuild) {
  const expectedSourceTree = runGit(PLAYBOOK_ROOT, ["rev-parse", `${PLAYBOOK_FEATURE_HEAD}^{tree}`]);
  const expectedTemporaryParent = path.join(ROOT, "tmp");
  const expectedCli = path.join(consumerBuild?.source_root ?? "", "packages", "cli", "dist", "main.js");
  const expectedEngine = path.join(consumerBuild?.source_root ?? "", "packages", "engine", "dist", "memory", "atlasCandidateAdmission.js");
  if (
    consumerBuild?.status !== "trusted_disposable_build"
    || consumerBuild?.source_revision !== PLAYBOOK_FEATURE_HEAD
    || expectedSourceTree.status !== 0
    || consumerBuild?.source_tree !== expectedSourceTree.stdout.trim()
    || consumerBuild?.build_command !== PLAYBOOK_BUILD_COMMAND
    || consumerBuild?.dependency_install_command !== PLAYBOOK_INSTALL_COMMAND
    || !consumerBuild?.build_root
    || path.basename(consumerBuild.build_root).startsWith(TRUSTED_BUILD_PREFIX) !== true
    || !isPathWithin(expectedTemporaryParent, consumerBuild.build_root)
    || !isPathWithin(consumerBuild.build_root, consumerBuild.source_root)
    || path.resolve(consumerBuild.cli_path ?? "") !== path.resolve(expectedCli)
    || path.resolve(consumerBuild.engine_path ?? "") !== path.resolve(expectedEngine)
    || consumerBuild.owner_checkout_dist_used !== false
    || consumerBuild.owner_checkout_cli_sha256_before !== consumerBuild.owner_checkout_cli_sha256_after
    || consumerBuild.owner_checkout_engine_sha256_before !== consumerBuild.owner_checkout_engine_sha256_after
  ) {
    reject("KNOWLEDGE_CONSUMER_REVISION_UNTRUSTED", "Playbook executable was not produced in the disposable exact-revision build boundary.");
  }
  const [cliSha256, engineSha256] = await Promise.all([
    fileDigest(consumerBuild.cli_path),
    fileDigest(consumerBuild.engine_path),
  ]);
  if (cliSha256 !== consumerBuild.cli_sha256 || engineSha256 !== consumerBuild.engine_sha256) {
    reject("KNOWLEDGE_CONSUMER_REVISION_UNTRUSTED", "Trusted Playbook build output changed after the canonical build.");
  }
  return true;
}

export async function buildTrustedPlaybookConsumer({ playbookRoot = PLAYBOOK_ROOT } = {}) {
  const consumerRevision = verifyPlaybookConsumerRevision({ playbookRoot });
  const ownerTrackedBefore = trackedStatus(playbookRoot);
  const ownerCliPath = path.join(playbookRoot, "packages", "cli", "dist", "main.js");
  const ownerEnginePath = path.join(playbookRoot, "packages", "engine", "dist", "memory", "atlasCandidateAdmission.js");
  const [ownerCliBefore, ownerEngineBefore] = await Promise.all([
    optionalFileDigest(ownerCliPath),
    optionalFileDigest(ownerEnginePath),
  ]);
  const sourceTreeResult = runGit(playbookRoot, ["rev-parse", `${PLAYBOOK_FEATURE_HEAD}^{tree}`]);
  if (sourceTreeResult.status !== 0) reject("KNOWLEDGE_CONSUMER_REVISION_UNTRUSTED", commandFailure(sourceTreeResult));
  const buildRoot = await fs.mkdtemp(path.join(ROOT, "tmp", TRUSTED_BUILD_PREFIX));
  const sourceRoot = path.join(buildRoot, "source");
  const archivePath = path.join(buildRoot, "trusted-source.tar");
  try {
    await fs.mkdir(sourceRoot, { recursive: true });
    const archive = runGit(playbookRoot, [
      "archive",
      "--format=tar",
      `--output=${archivePath}`,
      PLAYBOOK_FEATURE_HEAD,
      "--",
      ...TRUSTED_ARCHIVE_PATHS,
    ]);
    if (archive.status !== 0) reject("KNOWLEDGE_CONSUMER_REVISION_UNTRUSTED", commandFailure(archive));
    const extract = runCommand("tar", ["-xf", archivePath, "-C", sourceRoot]);
    if (extract.status !== 0) reject("KNOWLEDGE_CONSUMER_REVISION_UNTRUSTED", commandFailure(extract));
    await fs.rm(archivePath, { force: true });

    const pnpm = process.platform === "win32" ? "pnpm.cmd" : "pnpm";
    const install = runCommand(pnpm, ["install", "--frozen-lockfile", "--offline"], { cwd: sourceRoot, shell: process.platform === "win32" });
    if (install.status !== 0) reject("KNOWLEDGE_CONSUMER_REVISION_UNTRUSTED", `Trusted Playbook dependency install failed: ${commandFailure(install)}`);
    const build = runCommand(pnpm, ["-r", "build"], { cwd: sourceRoot, shell: process.platform === "win32" });
    if (build.status !== 0) reject("KNOWLEDGE_CONSUMER_REVISION_UNTRUSTED", `Canonical Playbook build failed: ${commandFailure(build)}`);

    const cliPath = path.join(sourceRoot, "packages", "cli", "dist", "main.js");
    const enginePath = path.join(sourceRoot, "packages", "engine", "dist", "memory", "atlasCandidateAdmission.js");
    const ownerTrackedAfter = trackedStatus(playbookRoot);
    const [ownerCliAfter, ownerEngineAfter] = await Promise.all([
      optionalFileDigest(ownerCliPath),
      optionalFileDigest(ownerEnginePath),
    ]);
    if (ownerTrackedBefore !== ownerTrackedAfter || ownerTrackedAfter !== "") {
      reject("KNOWLEDGE_CONSUMER_REVISION_UNTRUSTED", "Canonical disposable build changed the Playbook owner's tracked state.");
    }
    if (ownerCliBefore !== ownerCliAfter || ownerEngineBefore !== ownerEngineAfter) {
      reject("KNOWLEDGE_CONSUMER_REVISION_UNTRUSTED", "Canonical disposable build changed the Playbook owner's ignored dist state.");
    }
    const consumerBuild = {
      status: "trusted_disposable_build",
      source_revision: PLAYBOOK_FEATURE_HEAD,
      source_tree: sourceTreeResult.stdout.trim(),
      source_materialization: "git archive <trusted-feature-head>",
      dependency_install_command: PLAYBOOK_INSTALL_COMMAND,
      build_command: PLAYBOOK_BUILD_COMMAND,
      build_root: buildRoot,
      source_root: sourceRoot,
      cli_path: cliPath,
      engine_path: enginePath,
      cli_sha256: await fileDigest(cliPath),
      engine_sha256: await fileDigest(enginePath),
      owner_tracked_status_before: ownerTrackedBefore,
      owner_tracked_status_after: ownerTrackedAfter,
      owner_checkout_cli_sha256_before: ownerCliBefore,
      owner_checkout_cli_sha256_after: ownerCliAfter,
      owner_checkout_engine_sha256_before: ownerEngineBefore,
      owner_checkout_engine_sha256_after: ownerEngineAfter,
      owner_checkout_dist_used: false,
      consumer_revision: consumerRevision,
    };
    await assertTrustedPlaybookExecutable(consumerBuild);
    return consumerBuild;
  } catch (error) {
    await fs.rm(buildRoot, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
    throw error;
  }
}

export async function disposeTrustedPlaybookConsumer(consumerBuild) {
  if (
    consumerBuild?.build_root
    && path.basename(consumerBuild.build_root).startsWith(TRUSTED_BUILD_PREFIX)
    && isPathWithin(path.join(ROOT, "tmp"), consumerBuild.build_root)
  ) {
    await fs.rm(consumerBuild.build_root, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
  }
}

function mapPlaybookReason(reasonCode) {
  const mapping = {
    KNOWLEDGE_ATLAS_VALIDATION_FAILED: "KNOWLEDGE_ATLAS_SCHEMA_REJECTED",
    KNOWLEDGE_ATLAS_VALIDATOR_UNAVAILABLE: "KNOWLEDGE_ATLAS_SCHEMA_REJECTED",
    KNOWLEDGE_IDENTITY_LOST: "KNOWLEDGE_IDENTITY_LOSS",
    KNOWLEDGE_PROVENANCE_MISMATCH: "KNOWLEDGE_PROVENANCE_MISMATCH",
    KNOWLEDGE_DESTINATION_UNSUPPORTED: "KNOWLEDGE_DESTINATION_UNSUPPORTED",
    KNOWLEDGE_CONSUMER_RECEIPT_MISSING: "KNOWLEDGE_CONSUMER_RECEIPT_MISSING",
    KNOWLEDGE_AUTO_PROMOTION_FORBIDDEN: "KNOWLEDGE_AUTO_PROMOTION_DETECTED",
  };
  return mapping[reasonCode] ?? "KNOWLEDGE_ATLAS_SCHEMA_REJECTED";
}

function parseCommandPayload(stdout) {
  try {
    return JSON.parse(stdout);
  } catch {
    reject("KNOWLEDGE_CONSUMER_RECEIPT_MISSING", "Playbook public command did not emit one readable JSON result.");
  }
}

export async function runPlaybookAdmissionCommand({
  projectRoot,
  artifactPath,
  promote = false,
  consumerBuild,
  atlasContractsRoot = ATLAS_CONTRACTS_ROOT,
}) {
  await assertTrustedPlaybookExecutable(consumerBuild);
  const cli = consumerBuild.cli_path;
  const args = [
    cli,
    "knowledge",
    "atlas-admit",
    "--artifact",
    path.resolve(artifactPath),
    "--atlas-contracts-root",
    path.resolve(atlasContractsRoot),
    "--json",
  ];
  if (promote) args.push("--promote");
  const command = spawnSync(process.execPath, args, {
    cwd: path.resolve(projectRoot),
    encoding: "utf8",
    windowsHide: true,
    maxBuffer: 10 * 1024 * 1024,
  });
  const payload = parseCommandPayload(command.stdout.trim());
  if (command.status !== 0 || payload.status === "rejected") {
    reject(mapPlaybookReason(payload.reason_code), payload.error ?? "Playbook rejected KnowledgeCandidate admission.");
  }
  return payload;
}

export async function snapshotDoctrine(projectRoot) {
  const snapshot = {};
  for (const relativePath of DOCTRINE_PATHS) {
    const target = path.join(projectRoot, relativePath);
    snapshot[relativePath] = await exists(target) ? digest(await fs.readFile(target)) : null;
  }
  return snapshot;
}

export function assertDoctrineUnchanged(before, after) {
  if (!sameValue(before, after)) reject("KNOWLEDGE_DOCTRINE_MUTATION", "Canonical Rule, Pattern, Failure Mode, story, memory, or notes doctrine changed during candidate admission.");
  return true;
}

export function verifyKnowledgeCandidateConsumerReceipt(receipt, expectedReceipt) {
  if (!receipt) reject("KNOWLEDGE_CONSUMER_RECEIPT_MISSING", "The correlated Playbook consumer receipt is missing.");
  if (!expectedReceipt || !sameValue(receipt, expectedReceipt)) {
    reject("KNOWLEDGE_CONSUMER_RECEIPT_MISMATCH", "The Playbook consumer receipt changed identity, digest, decision, or candidate correlation.");
  }
  return true;
}

function validateCandidateRecord(candidate, record, commandResult) {
  if (!record || record.external_candidate_id !== candidate.candidate_id || record.candidate?.candidate_id !== candidate.candidate_id) {
    reject("KNOWLEDGE_IDENTITY_LOSS", "Playbook did not preserve Atlas candidate_id as the exact external and stored identity.");
  }
  if (!sameValue(record.candidate?.provenance, candidate.provenance)) {
    reject("KNOWLEDGE_PROVENANCE_MISMATCH", "Playbook changed a provenance reference or classification.");
  }
  if (!sameValue(record.candidate, candidate)) {
    reject("KNOWLEDGE_IDENTITY_LOSS", "Playbook changed one or more Atlas candidate fields.");
  }
  if (
    candidate.review?.status !== "candidate"
    || record.admission?.state !== "review-candidate"
    || record.admission?.promotion_authority !== "none"
    || record.admission?.suggested_destination_authority !== "proposal-only"
  ) {
    reject("KNOWLEDGE_AUTO_PROMOTION_DETECTED", "Candidate admission granted doctrine, story, Rule, Pattern, or Failure Mode promotion authority.");
  }
  verifyKnowledgeCandidateConsumerReceipt(record.consumer_receipt, commandResult?.receipt);
  const receipt = record.consumer_receipt;
  if (
    receipt.candidate_id !== candidate.candidate_id
    || receipt.candidate_record_id !== record.record_id
    || receipt.candidate_content_sha256 !== record.candidate_content_sha256
    || receipt.suggested_destination !== candidate.suggested_destination
    || receipt.decision !== "candidate-only-admitted"
    || receipt.review_status !== "candidate"
    || receipt.promotion_authority !== "none"
    || receipt.correlation?.candidate_id !== candidate.candidate_id
    || receipt.correlation?.candidate_record_id !== record.record_id
    || commandResult?.candidate_record_id !== record.record_id
  ) {
    reject("KNOWLEDGE_CONSUMER_RECEIPT_MISMATCH", "The Playbook consumer receipt lost candidate identity, digest, destination, decision, or record correlation.");
  }
  const recordDigest = digest(deterministicBytes(record)).slice("sha256:".length);
  if (commandResult?.proof?.candidate_record_sha256 !== recordDigest) {
    reject("KNOWLEDGE_CONSUMER_RECEIPT_MISMATCH", "The public command candidate-record digest disagreed with the admitted queue record.");
  }
  return record;
}

export function validateKnowledgeCandidateQueue({ queue, expectedCandidates, commandResults }) {
  if (queue?.schema_version !== "1.0" || queue?.kind !== "playbook.atlas-knowledge-candidate.queue.v1" || !Array.isArray(queue?.candidates)) {
    reject("KNOWLEDGE_IDENTITY_LOSS", "The Playbook candidate-only queue shape is invalid.");
  }
  if (queue.candidates.length !== expectedCandidates.length) {
    reject("KNOWLEDGE_IDENTITY_LOSS", "The Playbook queue contains a missing or duplicate Atlas candidate identity.");
  }
  const expectedOrder = [...expectedCandidates].sort((left, right) => left.candidate_id.localeCompare(right.candidate_id));
  return expectedOrder.map((candidate) => {
    const records = queue.candidates.filter((record) => record?.external_candidate_id === candidate.candidate_id);
    if (records.length !== 1) reject("KNOWLEDGE_IDENTITY_LOSS", `Atlas candidate ${candidate.candidate_id} is missing or duplicated.`);
    const commandResult = commandResults.find((result) => result?.candidate_id === candidate.candidate_id);
    return validateCandidateRecord(candidate, records[0], commandResult);
  });
}

function secondCandidate(first) {
  return {
    ...structuredClone(first),
    candidate_id: "knowledge-002",
    kind: "pattern",
    name: "Exact candidate-only intake",
    statement: "An independent consumer preserves Atlas identity and classified provenance while emitting a deterministic receipt without doctrine promotion.",
    scope: "Atlas Contracts v2 adoption",
    provenance: [
      { source_type: "repository", ref: "packages/atlas-contracts/fixtures/valid/knowledge-candidate.v2.json", classification: "verified" },
      { source_type: "receipt", ref: "github:fawxzzy/playbook#25", classification: "verified" },
    ],
    suggested_destination: "Playbook/patterns",
    created_at: RECORDED_AT,
  };
}

async function queueState(projectRoot, expectedCandidates, commandResults) {
  const queuePath = path.join(projectRoot, QUEUE_REF);
  const queueBytes = await fs.readFile(queuePath);
  const queue = JSON.parse(queueBytes);
  const records = validateKnowledgeCandidateQueue({ queue, expectedCandidates, commandResults });
  const queueDigest = digest(queueBytes);
  const latestResult = commandResults.at(-1);
  if (latestResult?.proof?.queue_bytes_sha256 !== queueDigest.slice("sha256:".length)) {
    reject("KNOWLEDGE_CONSUMER_RECEIPT_MISMATCH", "The public command queue digest disagreed with exact queue bytes.");
  }
  return { queue, queueBytes, queueDigest, records };
}

export async function buildKnowledgeCandidateAdoptionReceipt({ projectRoot = null, consumerBuild = null } = {}) {
  const ownsConsumerBuild = consumerBuild === null;
  const trustedConsumer = ownsConsumerBuild ? await buildTrustedPlaybookConsumer() : consumerBuild;
  await assertTrustedPlaybookExecutable(trustedConsumer);
  const consumerRevision = trustedConsumer.consumer_revision;
  const ownsTemp = projectRoot === null;
  const admittedRoot = ownsTemp
    ? await fs.mkdtemp(path.join(ROOT, "tmp", "atlas-knowledge-candidate-adoption-"))
    : path.resolve(projectRoot);
  try {
    await fs.mkdir(admittedRoot, { recursive: true });
    const firstCandidate = JSON.parse(await fs.readFile(VALID_FIXTURE, "utf8"));
    const second = secondCandidate(firstCandidate);
    const secondPath = path.join(admittedRoot, "knowledge-candidate-002.json");
    await fs.writeFile(secondPath, deterministicBytes(second));
    const doctrineBefore = await snapshotDoctrine(admittedRoot);

    const firstAdmission = await runPlaybookAdmissionCommand({ projectRoot: admittedRoot, artifactPath: VALID_FIXTURE, consumerBuild: trustedConsumer });
    const firstState = await queueState(admittedRoot, [firstCandidate], [firstAdmission]);
    const firstReplay = await runPlaybookAdmissionCommand({ projectRoot: admittedRoot, artifactPath: VALID_FIXTURE, consumerBuild: trustedConsumer });
    const firstReplayState = await queueState(admittedRoot, [firstCandidate], [firstReplay]);
    if (
      firstReplay.status !== "replayed"
      || !firstReplayState.queueBytes.equals(firstState.queueBytes)
      || !sameValue(firstReplay.receipt, firstAdmission.receipt)
    ) {
      reject("KNOWLEDGE_CONSUMER_RECEIPT_MISMATCH", "First candidate replay changed queue bytes or its correlated consumer receipt.");
    }

    const secondAdmission = await runPlaybookAdmissionCommand({ projectRoot: admittedRoot, artifactPath: secondPath, consumerBuild: trustedConsumer });
    const appendState = await queueState(admittedRoot, [firstCandidate, second], [firstAdmission, secondAdmission]);
    const secondReplay = await runPlaybookAdmissionCommand({ projectRoot: admittedRoot, artifactPath: secondPath, consumerBuild: trustedConsumer });
    const replayState = await queueState(admittedRoot, [firstCandidate, second], [firstAdmission, secondReplay]);
    if (
      secondReplay.status !== "replayed"
      || !replayState.queueBytes.equals(appendState.queueBytes)
      || !sameValue(secondReplay.receipt, secondAdmission.receipt)
    ) {
      reject("KNOWLEDGE_CONSUMER_RECEIPT_MISMATCH", "Second candidate replay changed queue bytes or its correlated consumer receipt.");
    }

    const doctrineAfter = await snapshotDoctrine(admittedRoot);
    assertDoctrineUnchanged(doctrineBefore, doctrineAfter);
    const candidateInputs = [firstCandidate, second].map((candidate) => ({
      candidate_id: candidate.candidate_id,
      candidate_sha256: digest(deterministicBytes(candidate)),
      provenance_sha256: digest(deterministicBytes(candidate.provenance)),
    }));
    const admissions = appendState.records.map((record) => ({
      candidate_id: record.candidate.candidate_id,
      candidate_record_id: record.record_id,
      consumer_receipt_id: record.consumer_receipt.receipt_id,
      candidate_content_sha256: `sha256:${record.candidate_content_sha256}`,
      candidate_record_sha256: digest(deterministicBytes(record)),
    }));
    const basis = {
      contract_version: "atlas.knowledge-candidate-adoption-receipt.v1",
      status: "accepted_candidate_only",
      reason_code: "ACCEPTED",
      recorded_at: RECORDED_AT,
      consumer_revision: consumerRevision,
      github_evidence: {
        pr: PLAYBOOK_PR,
        head: PLAYBOOK_FEATURE_HEAD,
        merge: PLAYBOOK_MERGE_COMMIT,
        successful_workflows: 7,
      },
      public_surface: {
        command: "playbook knowledge atlas-admit --artifact <candidate> --atlas-contracts-root <package> --json",
        source_revision: trustedConsumer.source_revision,
        source_tree: trustedConsumer.source_tree,
        source_materialization: trustedConsumer.source_materialization,
        dependency_install_command: trustedConsumer.dependency_install_command,
        canonical_build_command: trustedConsumer.build_command,
        cli_sha256: trustedConsumer.cli_sha256,
        engine_admission_sha256: trustedConsumer.engine_sha256,
        owner_tracked_status_before: trustedConsumer.owner_tracked_status_before,
        owner_tracked_status_after: trustedConsumer.owner_tracked_status_after,
        owner_checkout_cli_sha256_before: trustedConsumer.owner_checkout_cli_sha256_before,
        owner_checkout_cli_sha256_after: trustedConsumer.owner_checkout_cli_sha256_after,
        owner_checkout_engine_sha256_before: trustedConsumer.owner_checkout_engine_sha256_before,
        owner_checkout_engine_sha256_after: trustedConsumer.owner_checkout_engine_sha256_after,
        owner_checkout_dist_used: false,
      },
      inputs: candidateInputs,
      admissions,
      queue: {
        relative_path: QUEUE_REF,
        candidate_count: appendState.queue.candidates.length,
        queue_bytes_sha256: appendState.queueDigest,
        first_replay_byte_identical: true,
        second_replay_byte_identical: true,
        duplicate_candidate_ids: 0,
      },
      conformance: {
        atlas_schema_authority: true,
        candidate_identity_exact: true,
        provenance_refs_and_classifications_exact: true,
        all_candidate_fields_exact: true,
        consumer_receipts_correlated: true,
        append_order_deterministic: true,
        candidate_only: true,
        auto_promotion: false,
        doctrine_unchanged: true,
        doctrine_snapshot_sha256: digest(Buffer.from(stableStringify(doctrineAfter))),
      },
      authority: {
        playbook_owns_consumer_semantics: true,
        atlas_owns_contract_semantics: true,
        promotion_authority: "none",
        external_mutation: false,
        owner_repository_mutation: false,
        doctrine_mutation: false,
      },
    };
    return { receipt_id: identity("akcar", basis), ...basis };
  } finally {
    if (ownsTemp) await fs.rm(admittedRoot, { recursive: true, force: true });
    if (ownsConsumerBuild) await disposeTrustedPlaybookConsumer(trustedConsumer);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    if (process.argv.slice(2).some((argument) => ["--apply", "--live", "--write", "--promote", "--deploy", "--production", "--prod"].includes(argument))) {
      reject("KNOWLEDGE_AUTO_PROMOTION_DETECTED", "KnowledgeCandidate adoption accepts no mutation or promotion flag.");
    }
    const receipt = await buildKnowledgeCandidateAdoptionReceipt();
    console.log(process.argv.includes("--json") ? JSON.stringify(receipt) : `ACCEPTED: ${receipt.receipt_id}`);
  } catch (error) {
    console.log(JSON.stringify({ ok: false, reasonCode: error?.reasonCode ?? "KNOWLEDGE_ADOPTION_FAILED", errors: error?.errors ?? [error?.message ?? "KnowledgeCandidate adoption failed"] }));
    process.exitCode = 1;
  }
}
