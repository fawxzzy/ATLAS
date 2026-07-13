import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import {
  compileGithubEventAdmission,
  DEFAULT_POLICY_PATH,
  loadPolicy,
  selfCheckGithubEventAdmission,
  stableStringify,
  validatePolicyDocument,
} from "../ops/atlas/github_event_admission.mjs";
import {
  loadKnownSchema,
  validateJsonSchema,
} from "../packages/atlas-contracts/scripts/lib/validate-json-schema.mjs";

const testsDir = path.dirname(fileURLToPath(import.meta.url));
const atlasRoot = path.resolve(testsDir, "..");
const cliPath = path.join(atlasRoot, "ops", "atlas", "github_event_admission.mjs");
const baseReceiptPath = path.join(
  atlasRoot,
  "packages",
  "atlas-contracts",
  "fixtures",
  "valid",
  "github.event-receipt.v1.json",
);
const compilerSourcePath = path.join(atlasRoot, "ops", "atlas", "github_event_admission.mjs");

const EVENT_FAMILIES = [
  "repository",
  "branch",
  "pull_request",
  "issue",
  "workflow_run",
  "release",
  "security_alert",
];
const FACT_STATES = [
  "observed",
  "empty",
  "unknown",
  "access_denied",
  "disabled",
  "conflicting",
  "not_applicable",
];

const baseReceipt = JSON.parse(await fs.readFile(baseReceiptPath, "utf8"));

function digestHex(value) {
  return createHash("sha256").update(value).digest("hex");
}

function makeReceipt({
  eventFamily = "repository",
  factState = "observed",
  idSeed = `${eventFamily}-${factState}`,
  digestSeed = `${eventFamily}-${factState}`,
  observedAt = "2026-07-13T14:16:10Z",
  sourceIdempotencyKey = null,
} = {}) {
  const receipt = structuredClone(baseReceipt);
  const digest = digestHex(digestSeed);
  const slug = `${eventFamily}-${factState}-${idSeed}`
    .replace(/[^a-z0-9]+/gu, "_")
    .replace(/^_+|_+$/gu, "")
    .slice(0, 40);

  receipt.event_id = `ghr_${slug}_${digest.slice(0, 12)}`;
  receipt.idempotency_key = sourceIdempotencyKey ?? `ghk_${slug}`;
  receipt.observed_at = observedAt;
  receipt.event_family = eventFamily;
  receipt.fact_state = factState;
  receipt.source.endpoint = `repos/fawxzzy/ATLAS/${eventFamily}/${slug}`;
  receipt.subject.entity_type = eventFamily;
  receipt.subject.entity_id = slug;
  receipt.subject.entity_ref = `ref/${slug}`;
  receipt.subject.title = `${eventFamily} ${factState}`;
  receipt.subject.url = `https://github.com/fawxzzy/ATLAS/${eventFamily}/${slug}`;
  receipt.evidence_refs = [`tests/fixtures/${slug}.json`];
  receipt.digest.value = digest;
  receipt.digest.source_event_identity = `${eventFamily}:${slug}:${digest.slice(0, 16)}`;
  receipt.digest.fact_payload_identity = `atlas-github:${slug}`;
  receipt.normalized_facts = [
    {
      fact_key: `${eventFamily}.state`,
      note: factState === "observed" ? null : `${eventFamily} reported ${factState}.`,
      source_path: `${eventFamily}.${factState}`,
      state: factState,
      value: factState === "observed" ? slug : null,
    },
  ];

  return receipt;
}

async function assertValidArtifact(schemaId, artifact) {
  const loadedSchema = await loadKnownSchema(schemaId);
  assert.equal(loadedSchema.ok, true);
  const errors = validateJsonSchema(artifact, loadedSchema.schema);
  assert.deepEqual(errors, []);
}

function invokeCli(args) {
  const child = spawnSync(process.execPath, [cliPath, ...args], {
    cwd: atlasRoot,
    encoding: "utf8",
  });

  const output = child.stdout.trim();
  return {
    json: output ? JSON.parse(output) : null,
    status: child.status,
    stderr: child.stderr.trim(),
    stdout: output,
  };
}

async function writeJson(dirPath, fileName, payload) {
  const targetPath = path.join(dirPath, fileName);
  await fs.writeFile(targetPath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
  return targetPath;
}

test("self-check validates the registered schemas and canonical policy", async () => {
  const result = await selfCheckGithubEventAdmission();
  assert.equal(result.ok, true);
  assert.equal(result.code, "SELF_CHECK_OK");
  assert.equal(typeof result.policy_digest, "string");
  assert.equal(result.policy_digest.length, 64);
});

test("first-seen acceptance preserves source identity and validates admission plus ledger intent", async () => {
  const { policy } = await loadPolicy(DEFAULT_POLICY_PATH);
  const receipt = makeReceipt({
    eventFamily: "pull_request",
    factState: "observed",
    idSeed: "first-seen",
  });

  const result = await compileGithubEventAdmission({
    policy,
    receipt,
  });

  assert.equal(result.ok, true);
  assert.equal(result.admission.decision, "accepted");
  assert.equal(result.admission.admitted_at, receipt.observed_at);
  assert.equal(result.admission.source_event.event_id, receipt.event_id);
  assert.equal(result.admission.source_event.idempotency_key, receipt.idempotency_key);
  assert.equal(result.admission.source_event.event_family, receipt.event_family);
  assert.equal(result.admission.source_event.fact_state, receipt.fact_state);
  assert.equal(result.admission.source_event.digest_value, receipt.digest.value);
  assert.equal(result.admission.ledger_disposition.meaning, "record_only");
  assert.equal(result.projection_intents.length, 1);
  assert.equal(result.projection_intents[0].destination, "atlas_ledger");
  assert.equal(result.projection_intents[0].operation, "record");
  assert.equal(result.projection_intents[0].decision, "admitted");
  assert.equal(result.projection_intents[0].external_mutation, "denied");
  assert.deepEqual(result.projection_intents[0].route, {
    board_id: null,
    card_id: null,
    channel_id: null,
    project_id: null,
    thread_id: null,
  });
  assert.deepEqual(
    result.projection_intents[0].normalized_fact_refs,
    receipt.normalized_facts.map((fact) => fact.fact_key),
  );

  await assertValidArtifact("atlas.github.event-admission.v1", result.admission);
  await assertValidArtifact("atlas.github.projection-intent.v1", result.projection_intents[0]);
});

test("replay of identical receipt, policy, and prior evidence is byte-stable", async () => {
  const { policy } = await loadPolicy(DEFAULT_POLICY_PATH);
  const receipt = makeReceipt({
    eventFamily: "issue",
    factState: "empty",
    idSeed: "stable-replay",
  });

  const first = await compileGithubEventAdmission({ policy, receipt });
  const second = await compileGithubEventAdmission({ policy, receipt });

  assert.equal(stableStringify(first), stableStringify(second));
});

test("same digest prior evidence is classified as duplicate and suppresses new projections", async () => {
  const { policy } = await loadPolicy(DEFAULT_POLICY_PATH);
  const receipt = makeReceipt({
    eventFamily: "workflow_run",
    factState: "observed",
    idSeed: "duplicate",
  });

  const firstSeen = await compileGithubEventAdmission({ policy, receipt });
  const duplicate = await compileGithubEventAdmission({
    policy,
    priorAdmissions: [firstSeen.admission],
    receipt,
  });

  assert.equal(duplicate.admission.decision, "duplicate");
  assert.equal(duplicate.admission.ledger_disposition.meaning, "noop_duplicate");
  assert.deepEqual(duplicate.projection_intents, []);
  assert.deepEqual(duplicate.admission.projection_intent_refs, []);
  assert.ok(duplicate.admission.reason_codes.includes("admission.duplicate.same_digest"));
  await assertValidArtifact("atlas.github.event-admission.v1", duplicate.admission);
});

test("different digest prior evidence is quarantined with stable conflict reason", async () => {
  const { policy } = await loadPolicy(DEFAULT_POLICY_PATH);
  const sourceIdempotencyKey = "ghk_digest_conflict_case";
  const firstReceipt = makeReceipt({
    eventFamily: "repository",
    factState: "observed",
    idSeed: "digest-a",
    digestSeed: "digest-a",
    sourceIdempotencyKey,
  });
  const secondReceipt = makeReceipt({
    eventFamily: "repository",
    factState: "observed",
    idSeed: "digest-b",
    digestSeed: "digest-b",
    sourceIdempotencyKey,
  });

  const firstSeen = await compileGithubEventAdmission({ policy, receipt: firstReceipt });
  const quarantined = await compileGithubEventAdmission({
    policy,
    priorAdmissions: [firstSeen.admission],
    receipt: secondReceipt,
  });

  assert.equal(quarantined.admission.decision, "quarantined");
  assert.equal(quarantined.admission.ledger_disposition.meaning, "quarantine_hold");
  assert.deepEqual(quarantined.projection_intents, []);
  assert.ok(quarantined.admission.reason_codes.includes("admission.quarantine.digest_conflict"));
  await assertValidArtifact("atlas.github.event-admission.v1", quarantined.admission);
});

test("policy covers every event family and fact state explicitly", async () => {
  const { policy } = await loadPolicy(DEFAULT_POLICY_PATH);
  const validation = validatePolicyDocument(policy);
  assert.equal(validation.ok, true);

  for (const family of EVENT_FAMILIES) {
    assert.ok(policy.event_families[family]);
    for (const state of FACT_STATES) {
      assert.ok(policy.event_families[family].states[state]);
    }
  }
});

test("release and security-alert observations emit review intents with null routes and denied mutation", async () => {
  const { policy } = await loadPolicy(DEFAULT_POLICY_PATH);
  const releaseResult = await compileGithubEventAdmission({
    policy,
    receipt: makeReceipt({
      eventFamily: "release",
      factState: "observed",
      idSeed: "release-review",
    }),
  });
  const securityResult = await compileGithubEventAdmission({
    policy,
    receipt: makeReceipt({
      eventFamily: "security_alert",
      factState: "observed",
      idSeed: "security-review",
    }),
  });

  assert.equal(releaseResult.admission.ledger_disposition.meaning, "record_and_project");
  assert.deepEqual(
    releaseResult.projection_intents.map((intent) => intent.destination).sort(),
    ["atlas_ledger", "discordos_update"],
  );
  const releaseReview = releaseResult.projection_intents.find(
    (intent) => intent.destination === "discordos_update",
  );
  assert.equal(releaseReview.decision, "requires_review");
  assert.equal(releaseReview.operation, "publish");
  assert.equal(releaseReview.external_mutation, "denied");
  assert.deepEqual(releaseReview.route, {
    board_id: null,
    card_id: null,
    channel_id: null,
    project_id: null,
    thread_id: null,
  });

  assert.equal(securityResult.admission.ledger_disposition.meaning, "record_and_project");
  assert.deepEqual(
    securityResult.projection_intents.map((intent) => intent.destination).sort(),
    ["atlas_ledger", "discordos_alerts"],
  );
  const securityReview = securityResult.projection_intents.find(
    (intent) => intent.destination === "discordos_alerts",
  );
  assert.equal(securityReview.decision, "requires_review");
  assert.equal(securityReview.operation, "alert");
  assert.equal(securityReview.external_mutation, "denied");
  assert.deepEqual(securityReview.route, {
    board_id: null,
    card_id: null,
    channel_id: null,
    project_id: null,
    thread_id: null,
  });
});

test("malformed, schema-invalid, unknown-policy, and contradictory prior inputs fail closed without secret echo", async () => {
  const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), "atlas-github-admission-errors-"));
  try {
    const validReceipt = makeReceipt({
      eventFamily: "branch",
      factState: "observed",
      idSeed: "error-cases",
    });
    const receiptPath = await writeJson(tempDir, "receipt.json", validReceipt);

    const malformedReceiptPath = path.join(tempDir, "malformed-receipt.json");
    const malformedSecret = "ghp_secret_like_token_should_not_echo";
    await fs.writeFile(
      malformedReceiptPath,
      `{"token":"${malformedSecret}"`,
      "utf8",
    );

    const malformedOutcome = invokeCli(["--receipt", malformedReceiptPath]);
    assert.equal(malformedOutcome.status, 3);
    assert.equal(malformedOutcome.json.code, "MALFORMED_RECEIPT_JSON");
    assert.ok(!malformedOutcome.stdout.includes(malformedSecret));

    const invalidReceipt = structuredClone(validReceipt);
    const invalidSecret = "super_secret_external_mutation_value";
    invalidReceipt.authority.external_mutation = invalidSecret;
    const invalidReceiptPath = await writeJson(tempDir, "invalid-receipt.json", invalidReceipt);
    const invalidOutcome = invokeCli(["--receipt", invalidReceiptPath]);
    assert.equal(invalidOutcome.status, 1);
    assert.equal(invalidOutcome.json.code, "INVALID_RECEIPT");
    assert.ok(!invalidOutcome.stdout.includes(invalidSecret));

    const { policy } = await loadPolicy(DEFAULT_POLICY_PATH);
    const invalidPolicy = structuredClone(policy);
    invalidPolicy.event_families.repository.states.observed.intent_template_ids = [
      "secret_like_template_should_not_echo",
    ];
    const invalidPolicyPath = await writeJson(tempDir, "invalid-policy.json", invalidPolicy);
    const invalidPolicyOutcome = invokeCli(["--receipt", receiptPath, "--policy", invalidPolicyPath]);
    assert.equal(invalidPolicyOutcome.status, 2);
    assert.equal(invalidPolicyOutcome.json.code, "INVALID_POLICY");
    assert.ok(!invalidPolicyOutcome.stdout.includes("secret_like_template_should_not_echo"));

    const accepted = await compileGithubEventAdmission({ policy, receipt: validReceipt });
    const contradictoryPrior = structuredClone(accepted.admission);
    contradictoryPrior.decision = "duplicate";
    const contradictoryPriorPath = await writeJson(
      tempDir,
      "contradictory-prior.json",
      contradictoryPrior,
    );
    const contradictoryOutcome = invokeCli([
      "--receipt",
      receiptPath,
      "--prior-admission",
      contradictoryPriorPath,
    ]);
    assert.equal(contradictoryOutcome.status, 1);
    assert.equal(contradictoryOutcome.json.code, "CONTRADICTORY_PRIOR_ADMISSION");
  } finally {
    await fs.rm(tempDir, { force: true, recursive: true });
  }
});

test("output directory mode writes exact admission and intent artifacts without backend selection", async () => {
  const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), "atlas-github-admission-output-"));
  try {
    const receipt = makeReceipt({
      eventFamily: "release",
      factState: "observed",
      idSeed: "output-dir",
    });
    const receiptPath = await writeJson(tempDir, "receipt.json", receipt);
    const outputDir = path.join(tempDir, "artifacts");

    const outcome = invokeCli(["--receipt", receiptPath, "--output-dir", outputDir]);
    assert.equal(outcome.status, 0);
    assert.equal(outcome.json.code, "ADMISSION_COMPILED");

    const writtenFiles = (await fs.readdir(outputDir)).sort();
    const expectedFiles = [
      `${outcome.json.admission.admission_id}.json`,
      ...outcome.json.projection_intents.map((intent) => `${intent.projection_id}.json`),
    ].sort();
    assert.deepEqual(writtenFiles, expectedFiles);

    for (const fileName of writtenFiles) {
      const fileContent = await fs.readFile(path.join(outputDir, fileName), "utf8");
      const parsed = JSON.parse(fileContent);
      const expectedArtifact = fileName.startsWith("gha_")
        ? outcome.json.admission
        : outcome.json.projection_intents.find(
            (intent) => `${intent.projection_id}.json` === fileName,
          );
      assert.equal(fileContent, `${stableStringify(expectedArtifact, { pretty: true })}\n`);
      assert.equal(stableStringify(parsed), stableStringify(expectedArtifact));
    }
  } finally {
    await fs.rm(tempDir, { force: true, recursive: true });
  }
});

test("compiler implementation stays local-only and contains no network or mutation adapters", async () => {
  const source = await fs.readFile(compilerSourcePath, "utf8");
  const forbiddenPatterns = [
    /child_process/u,
    /\bfetch\s*\(/u,
    /\bhttps?:\/\//u,
    /\bspawn\s*\(/u,
    /\bexec\s*\(/u,
    /\bgit\s+(push|commit|reset|checkout|switch|rebase|merge)\b/u,
    /@supabase\//u,
    /\bcreateClient\s*\(/u,
    /\bvercel\b/iu,
    /\bdiscord\.js\b/u,
  ];

  for (const pattern of forbiddenPatterns) {
    assert.equal(pattern.test(source), false, `Forbidden pattern matched: ${pattern}`);
  }
});
