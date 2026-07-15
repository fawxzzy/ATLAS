import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  KnowledgeCandidateAdoptionError,
  assertDoctrineUnchanged,
  buildKnowledgeCandidateAdoptionReceipt,
  buildTrustedPlaybookConsumer,
  disposeTrustedPlaybookConsumer,
  runPlaybookAdmissionCommand,
  snapshotDoctrine,
  stableStringify,
  validateKnowledgeCandidateQueue,
  verifyPlaybookConsumerRevision,
} from "../ops/atlas/knowledge_candidate_adoption.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const CONTRACTS = path.join(ROOT, "packages", "atlas-contracts");
const VALID = path.join(CONTRACTS, "fixtures", "valid", "knowledge-candidate.v2.json");
const BAD_KIND = path.join(CONTRACTS, "fixtures", "invalid", "knowledge-candidate.v2.bad-kind.json");
const QUEUE_REF = ".playbook/memory/atlas-knowledge-candidates.json";
const temp = await fs.mkdtemp(path.join(ROOT, "tmp", "knowledge-candidate-adoption-test-"));
let consumerBuild;

async function project(name) {
  const target = path.join(temp, name);
  await fs.mkdir(target, { recursive: true });
  return target;
}

async function writeCandidate(projectRoot, mutate, name = "candidate.json") {
  const candidate = JSON.parse(await fs.readFile(VALID, "utf8"));
  mutate(candidate);
  const target = path.join(projectRoot, name);
  await fs.writeFile(target, `${JSON.stringify(candidate, null, 2)}\n`, "utf8");
  return { candidate, target };
}

async function readQueue(projectRoot) {
  return JSON.parse(await fs.readFile(path.join(projectRoot, QUEUE_REF), "utf8"));
}

async function writeQueue(projectRoot, queue) {
  await fs.writeFile(path.join(projectRoot, QUEUE_REF), `${JSON.stringify(queue, null, 2)}\n`, "utf8");
}

async function expectReason(action, reasonCode) {
  await assert.rejects(
    action,
    (error) => error instanceof KnowledgeCandidateAdoptionError && error.reasonCode === reasonCode,
  );
}

function git(root, args) {
  const result = spawnSync("git", ["-C", root, ...args], { encoding: "utf8", windowsHide: true });
  assert.equal(result.status, 0, result.stderr || result.stdout);
  return result.stdout.trim();
}

test.before(async () => {
  consumerBuild = await buildTrustedPlaybookConsumer();
});

test.after(async () => {
  await disposeTrustedPlaybookConsumer(consumerBuild);
  await fs.rm(temp, { recursive: true, force: true });
});

test("proves exact two-candidate public admission, byte-identical replay, and deterministic receipt", async () => {
  const first = await buildKnowledgeCandidateAdoptionReceipt({ consumerBuild });
  const second = await buildKnowledgeCandidateAdoptionReceipt({ consumerBuild });
  assert.equal(stableStringify(first), stableStringify(second));
  assert.match(first.receipt_id, /^akcar_[a-f0-9]{32}$/);
  assert.equal(first.consumer_revision.pr, 25);
  assert.equal(first.consumer_revision.feature_head, "14fce44268084bcaaab6d189b6ef18eb7a992faf");
  assert.equal(first.consumer_revision.merge_commit, "f39dbac27d9a1c706ad11dbefe7f37feeebd5c3d");
  assert.equal(first.github_evidence.successful_workflows, 7);
  assert.equal(first.public_surface.source_revision, "14fce44268084bcaaab6d189b6ef18eb7a992faf");
  assert.equal(first.public_surface.canonical_build_command, "pnpm -r build");
  assert.equal(first.public_surface.owner_checkout_dist_used, false);
  assert.equal(first.public_surface.owner_tracked_status_before, "");
  assert.equal(first.public_surface.owner_tracked_status_after, "");
  assert.equal(first.public_surface.owner_checkout_cli_sha256_before, first.public_surface.owner_checkout_cli_sha256_after);
  assert.equal(first.public_surface.owner_checkout_engine_sha256_before, first.public_surface.owner_checkout_engine_sha256_after);
  assert.equal(first.admissions.length, 2);
  assert.deepEqual(first.admissions.map((entry) => entry.candidate_id), ["knowledge-001", "knowledge-002"]);
  assert.equal(new Set(first.admissions.map((entry) => entry.consumer_receipt_id)).size, 2);
  assert.equal(first.queue.candidate_count, 2);
  assert.equal(first.queue.first_replay_byte_identical, true);
  assert.equal(first.queue.second_replay_byte_identical, true);
  assert.equal(first.queue.duplicate_candidate_ids, 0);
  assert.equal(first.conformance.candidate_identity_exact, true);
  assert.equal(first.conformance.provenance_refs_and_classifications_exact, true);
  assert.equal(first.conformance.all_candidate_fields_exact, true);
  assert.equal(first.conformance.consumer_receipts_correlated, true);
  assert.equal(first.conformance.auto_promotion, false);
  assert.equal(first.conformance.doctrine_unchanged, true);
  assert.equal(first.authority.promotion_authority, "none");
  assert.equal(first.authority.owner_repository_mutation, false);
});

test("rejects the Atlas bad-kind fixture through the public Playbook consumer", async () => {
  const root = await project("bad-kind");
  await expectReason(
    () => runPlaybookAdmissionCommand({ projectRoot: root, artifactPath: BAD_KIND, consumerBuild }),
    "KNOWLEDGE_ATLAS_SCHEMA_REJECTED",
  );
});

test("rejects unsupported destination tampering", async () => {
  const root = await project("destination");
  const { target } = await writeCandidate(root, (candidate) => { candidate.suggested_destination = "playbook/failure-modes"; });
  await expectReason(
    () => runPlaybookAdmissionCommand({ projectRoot: root, artifactPath: target, consumerBuild }),
    "KNOWLEDGE_DESTINATION_UNSUPPORTED",
  );
});

test("rejects explicit auto-promotion", async () => {
  const root = await project("promotion");
  await expectReason(
    () => runPlaybookAdmissionCommand({ projectRoot: root, artifactPath: VALID, promote: true, consumerBuild }),
    "KNOWLEDGE_AUTO_PROMOTION_DETECTED",
  );
});

test("rejects stored candidate identity loss on replay", async () => {
  const root = await project("identity");
  await runPlaybookAdmissionCommand({ projectRoot: root, artifactPath: VALID, consumerBuild });
  const queue = await readQueue(root);
  queue.candidates[0].candidate.candidate_id = "tampered-identity";
  await writeQueue(root, queue);
  await expectReason(
    () => runPlaybookAdmissionCommand({ projectRoot: root, artifactPath: VALID, consumerBuild }),
    "KNOWLEDGE_IDENTITY_LOSS",
  );
});

test("rejects provenance reference and classification tampering", async () => {
  const root = await project("provenance");
  await runPlaybookAdmissionCommand({ projectRoot: root, artifactPath: VALID, consumerBuild });
  const queue = await readQueue(root);
  queue.candidates[0].candidate.provenance[0].ref = "tampered/ref";
  queue.candidates[0].candidate.provenance[0].classification = "unknown";
  await writeQueue(root, queue);
  await expectReason(
    () => runPlaybookAdmissionCommand({ projectRoot: root, artifactPath: VALID, consumerBuild }),
    "KNOWLEDGE_PROVENANCE_MISMATCH",
  );
});

test("rejects missing and mismatched correlated consumer receipts", async () => {
  const root = await project("receipt");
  const result = await runPlaybookAdmissionCommand({ projectRoot: root, artifactPath: VALID, consumerBuild });
  const candidate = JSON.parse(await fs.readFile(VALID, "utf8"));
  const queue = await readQueue(root);
  const missing = structuredClone(queue);
  delete missing.candidates[0].consumer_receipt;
  await writeQueue(root, missing);
  await expectReason(
    () => runPlaybookAdmissionCommand({ projectRoot: root, artifactPath: VALID, consumerBuild }),
    "KNOWLEDGE_CONSUMER_RECEIPT_MISSING",
  );

  const mismatched = structuredClone(queue);
  mismatched.candidates[0].consumer_receipt.receipt_id = "playbook-akc-receipt-tampered";
  assert.throws(
    () => validateKnowledgeCandidateQueue({ queue: mismatched, expectedCandidates: [candidate], commandResults: [result] }),
    (error) => error instanceof KnowledgeCandidateAdoptionError && error.reasonCode === "KNOWLEDGE_CONSUMER_RECEIPT_MISMATCH",
  );
});

test("rejects deliberate canonical doctrine mutation", async () => {
  const root = await project("doctrine");
  const before = await snapshotDoctrine(root);
  const doctrine = path.join(root, ".playbook", "patterns.json");
  await fs.mkdir(path.dirname(doctrine), { recursive: true });
  await fs.writeFile(doctrine, "{\"tampered\":true}\n", "utf8");
  const after = await snapshotDoctrine(root);
  assert.throws(
    () => assertDoctrineUnchanged(before, after),
    (error) => error instanceof KnowledgeCandidateAdoptionError && error.reasonCode === "KNOWLEDGE_DOCTRINE_MUTATION",
  );
});

test("rejects a non-merged or untrusted Playbook consumer revision", async () => {
  const root = await project("untrusted-playbook");
  assert.throws(
    () => verifyPlaybookConsumerRevision({ playbookRoot: root }),
    (error) => error instanceof KnowledgeCandidateAdoptionError && error.reasonCode === "KNOWLEDGE_CONSUMER_REVISION_UNTRUSTED",
  );
});

test("rejects stale or pre-existing owner-checkout dist instead of reusing it", async () => {
  const root = await project("stale-owner-dist");
  const ownerRoot = path.join(ROOT, "repos", "playbook");
  const staleOwnerBuild = {
    ...consumerBuild,
    build_root: ownerRoot,
    source_root: ownerRoot,
    cli_path: path.join(ownerRoot, "packages", "cli", "dist", "main.js"),
    engine_path: path.join(ownerRoot, "packages", "engine", "dist", "memory", "atlasCandidateAdmission.js"),
    owner_checkout_dist_used: true,
  };
  await expectReason(
    () => runPlaybookAdmissionCommand({ projectRoot: root, artifactPath: VALID, consumerBuild: staleOwnerBuild }),
    "KNOWLEDGE_CONSUMER_REVISION_UNTRUSTED",
  );
});

test("accepts a trusted descendant and rejects non-ancestor or consumer-path drift", async () => {
  const root = await project("monotonic-trust");
  git(root, ["init"]);
  git(root, ["config", "user.name", "Atlas Test"]);
  git(root, ["config", "user.email", "atlas-test@example.invalid"]);
  await fs.writeFile(path.join(root, "README.md"), "initial\n", "utf8");
  git(root, ["add", "README.md"]);
  git(root, ["commit", "-m", "initial"]);
  const nonAncestor = git(root, ["rev-parse", "HEAD"]);

  const consumerPath = path.join(root, "packages", "cli", "src", "commands", "knowledge", "atlasCandidate.ts");
  await fs.mkdir(path.dirname(consumerPath), { recursive: true });
  await fs.writeFile(consumerPath, "export const trusted = true;\n", "utf8");
  git(root, ["add", "packages/cli/src/commands/knowledge/atlasCandidate.ts"]);
  git(root, ["commit", "-m", "trusted feature"]);
  const featureHead = git(root, ["rev-parse", "HEAD"]);

  await fs.writeFile(path.join(root, "DESCENDANT.md"), "later unrelated change\n", "utf8");
  git(root, ["add", "DESCENDANT.md"]);
  git(root, ["commit", "-m", "trusted descendant"]);
  const descendant = git(root, ["rev-parse", "HEAD"]);
  git(root, ["update-ref", "refs/remotes/origin/main", descendant]);
  const accepted = verifyPlaybookConsumerRevision({ playbookRoot: root, featureHead, mergeCommit: featureHead });
  assert.equal(accepted.checkout_head, descendant);
  assert.equal(accepted.origin_main, descendant);
  assert.equal(accepted.observed_checkout_consumer_paths_unchanged_from_feature, true);

  git(root, ["update-ref", "refs/remotes/origin/main", nonAncestor]);
  assert.throws(
    () => verifyPlaybookConsumerRevision({ playbookRoot: root, featureHead, mergeCommit: featureHead }),
    (error) => error instanceof KnowledgeCandidateAdoptionError && error.reasonCode === "KNOWLEDGE_CONSUMER_REVISION_UNTRUSTED",
  );

  await fs.writeFile(consumerPath, "export const trusted = false;\n", "utf8");
  git(root, ["add", "packages/cli/src/commands/knowledge/atlasCandidate.ts"]);
  git(root, ["commit", "-m", "consumer path drift"]);
  git(root, ["update-ref", "refs/remotes/origin/main", "HEAD"]);
  assert.throws(
    () => verifyPlaybookConsumerRevision({ playbookRoot: root, featureHead, mergeCommit: featureHead }),
    (error) => error instanceof KnowledgeCandidateAdoptionError && error.reasonCode === "KNOWLEDGE_CONSUMER_REVISION_UNTRUSTED",
  );
});
