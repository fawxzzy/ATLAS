import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import {
  loadKnownSchema,
  validateJsonSchema,
} from "../../packages/atlas-contracts/scripts/lib/validate-json-schema.mjs";

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
export const SOURCE_PACKET_REF = "docs/ops/ATLAS-CREATION-OS-PLAYBOOK-PROMOTION-CANDIDATES-2026-07-16.md";
export const ARTIFACT_ROOT_REF = "data/knowledge-candidates/creation-os";
export const MANIFEST_REF = `${ARTIFACT_ROOT_REF}/manifest.v1.json`;
export const PLAYBOOK_HANDOFF_REF = "docs/ops/ATLAS-CREATION-OS-PLAYBOOK-CANDIDATE-INTAKE-HANDOFF-2026-07-16.md";
export const CORTEX_HANDOFF_REF = "docs/ops/ATLAS-CREATION-OS-CORTEX-ADVISORY-REFRESH-HANDOFF-2026-07-16.md";

const CONTRACT_ID = "atlas.knowledge-candidate.v2";
const SCHEMA_REF = "packages/atlas-contracts/schemas/atlas.knowledge-candidate.v2.schema.json";
const SOURCE_PACKET_FIRST_COMMIT = "2407b0e656775d040099e5618eb194c5c06ee0e7";
const SOURCE_PACKET_CORRECTED_REVISION = "c376810ec75066fb6b21d950f56fcdf986421889";
const SOURCE_PACKET_CORRECTED_SHA256 = "sha256:e2946fcc95f2b1aa5d871767446e97a0e69da6c66d72c90e53855313c4cf2ca2";
const SOURCE_ADOPTION_MERGE_COMMIT = "1d79d4ac3191dade11a2aa7c40352a5f210d35e2";
const CREATED_AT = "2026-07-16T06:31:44Z";
const PLAYBOOK_REPOSITORY = "fawxzzy/playbook";
const PLAYBOOK_CONSUMER_REVISION = "8aa912b492e689fca4c296d59a438c2813cba4fc";
const PLAYBOOK_CONSUMER_PATH = "packages/engine/src/memory/atlasCandidateAdmission.ts";
const RAW_RESEARCH_REF = "data/imports/creation-os/deep-research-2026-07-16/deep-research-report.md";
const DECISION_ID = "creation-os-software-repo-voice-first-wedge";

export const SUPPORTED_PLAYBOOK_DESTINATIONS = Object.freeze({
  rule: "Playbook/rules",
  pattern: "Playbook/patterns",
  "failure-mode": "Playbook/failure-modes",
});

const CONTRACT_KINDS = Object.freeze([
  "rule",
  "pattern",
  "failure-mode",
  "automation-opportunity",
  "governance-gap",
]);

export const EXPECTED_RECORDS = Object.freeze([
  {
    id: "creation-os-human-directed-authority",
    name: "Human-Directed Authority",
    sourceKind: "RULE",
    kind: "rule",
    statement: "Atlas remains human-directed; autonomy does not imply external or production authority.",
    scope: "Atlas jobs, tools, agents, voice surfaces, planner roles, deployments, publications, purchases, and device actions.",
    destination: "Playbook/rules",
    evidenceRefs: [
      "docs/architecture/ATLAS-CONTRACTS-V2-SCOPE.md#authority-boundaries",
      "docs/architecture/ATLAS-CREATION-OS-TARGET-ARCHITECTURE.md#policy-permission-and-approval",
    ],
    rawLines: "5,19,68,365-370",
    sourceRawLines: "5, 19, 68, and 365-370",
  },
  {
    id: "creation-os-bootstrap-pointer-not-memory",
    name: "Bootstrap Pointer, Not Memory",
    sourceKind: "RULE",
    kind: "rule",
    statement: "The bootstrap artifact is a pointer into governed truth, never the entire memory system.",
    scope: "recovery, profile/context bootstrap, memory, indexes, storage, and cross-machine restore.",
    destination: "Playbook/rules",
    evidenceRefs: [
      "docs/atlas/decisions/adr-signed-versioned-atlas-bootstrap-manifest.md",
      "docs/architecture/STATE-AND-MEMORY-BOUNDARIES.md",
    ],
    rawLines: "7,218",
    sourceRawLines: "7 and 218",
  },
  {
    id: "creation-os-builder-creative-loop-separation",
    name: "Builder and Creative Loop Separation",
    sourceKind: "PATTERN",
    kind: "pattern",
    statement: "Separate the deterministic builder loop from the conversational creative loop and require explicit admission from creative output into governed execution.",
    scope: "voice/text exploration, plans, code edits, tests, previews, receipts, merge, deploy, and publication.",
    destination: "Playbook/patterns",
    evidenceRefs: [
      "docs/architecture/ATLAS-CREATION-OS-TARGET-ARCHITECTURE.md#interaction-loops",
      "docs/architecture/ATLAS-CHATGPT-CODEX-WORKFLOW.md",
    ],
    rawLines: "9,246",
    sourceRawLines: "9 and 246",
  },
  {
    id: "creation-os-platform-surface-vertical-contracts",
    name: "Platform, Surface, and Vertical Contracts",
    sourceKind: "PATTERN",
    kind: "pattern",
    statement: "Core platform, surfaces, and verticals evolve independently through explicit versioned contracts and owner boundaries.",
    scope: "Atlas root, Playbook, Contracts, Cortex, `_stack`, DiscordOS, owner repositories, user surfaces, and domain products.",
    destination: "Playbook/patterns",
    evidenceRefs: [
      "docs/architecture/ATLAS-CREATION-OS-TARGET-ARCHITECTURE.md#current-truth-and-target-ownership",
      "docs/atlas-book/06-system-ownership.md",
      "docs/atlas-book/07-contracts-and-seams.md",
    ],
    rawLines: "23-27",
    sourceRawLines: "23-27",
  },
  {
    id: "creation-os-infrastructure-shopping-before-wedge",
    name: "Infrastructure Shopping Before the Wedge",
    sourceKind: "FAILURE MODE",
    kind: "failure-mode",
    statement: "Infrastructure shopping before the native-first wedge is proven turns a vendor list into architecture, creates operational burden, and hides the product-learning loop.",
    scope: "databases, vector/graph stores, caches, object stores, workflow engines, realtime transports, policy engines, signing systems, and provider routers.",
    destination: "Playbook/failure-modes",
    evidenceRefs: [
      "docs/audits/ATLAS-CREATION-OS-RESEARCH-RECONCILIATION-2026-07-16.md#recommendation-mapping",
      "docs/architecture/ATLAS-CREATION-OS-TARGET-ARCHITECTURE.md#phase-one-non-goals",
    ],
    rawLines: "222-228,260-271",
    sourceRawLines: "222-228 and 260-271",
  },
  {
    id: "creation-os-xr-device-novelty-trap",
    name: "XR and Device Novelty Trap",
    sourceKind: "FAILURE MODE",
    kind: "failure-mode",
    statement: "XR or device novelty consumes the software-builder roadmap before the first wedge has repeatable value, trust, and safe execution evidence.",
    scope: "spatial viewers, headsets, scene standards, smart-home protocols, robotics, sensors, actuators, and hardware support.",
    destination: "Playbook/failure-modes",
    evidenceRefs: [
      "docs/architecture/ATLAS-CREATION-OS-TARGET-ARCHITECTURE.md#staged-roadmap",
      "docs/architecture/ATLAS-CREATION-OS-TARGET-ARCHITECTURE.md#success-metrics-and-kill-criteria",
    ],
    rawLines: "11,248-250,355-356,369-370",
    sourceRawLines: "11, 248-250, 355-356, and 369-370",
  },
  {
    id: DECISION_ID,
    name: "Software Repository and Voice First Wedge",
    sourceKind: "DECISION",
    kind: "decision",
    statement: "Software creation with repository ingestion and voice is the first Creation OS product wedge, subject to operator ratification of success and kill metrics.",
    scope: "product definition, repository classes, artifact types, previews, voice interaction, human approval, product-market fit, and monetization.",
    destination: null,
    evidenceRefs: [
      "docs/architecture/ATLAS-CREATION-OS-TARGET-ARCHITECTURE.md#phase-one-wedge",
      "docs/architecture/ATLAS-CREATION-OS-TARGET-ARCHITECTURE.md#success-metrics-and-kill-criteria",
    ],
    rawLines: "13,27,415",
    sourceRawLines: "13, 27, and 415",
  },
]);

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.keys(value).sort().map((key) => [key, canonicalize(value[key])]),
    );
  }
  return value;
}

function deterministicJson(value) {
  return `${JSON.stringify(value, null, 2)}\n`;
}

export function normalizeSourceBytes(sourceBytes) {
  const text = sourceBytes.toString("utf8");
  if (/\r(?!\n)/.test(text)) fail("source packet contains an unsupported lone CR line ending");
  return Buffer.from(text.replaceAll("\r\n", "\n"), "utf8");
}

function canonicalJson(value) {
  return JSON.stringify(canonicalize(value));
}

function digestBytes(bytes) {
  return `sha256:${crypto.createHash("sha256").update(bytes).digest("hex")}`;
}

function digestText(text) {
  return digestBytes(Buffer.from(text, "utf8"));
}

function recordWithHash(record) {
  return {
    ...record,
    record_sha256: digestText(canonicalJson(record)),
  };
}

function fail(errors) {
  const list = Array.isArray(errors) ? errors : [errors];
  const error = new Error(list.join("; "));
  error.errors = list;
  throw error;
}

function fieldFromSection(body, label) {
  const lines = body.split(/\r?\n/);
  const prefix = `- ${label}:`;
  const start = lines.findIndex((line) => line.startsWith(prefix));
  if (start === -1) return null;
  const parts = [lines[start].slice(prefix.length).trim()];
  for (let index = start + 1; index < lines.length; index += 1) {
    const line = lines[index];
    if (line.startsWith("- ") || line.trim() === "") break;
    parts.push(line.trim());
  }
  return parts.filter(Boolean).join(" ");
}

function evidenceFromSection(body) {
  const evidence = fieldFromSection(body, "Evidence") ?? "";
  const refs = [...evidence.matchAll(/\]\(([^)]+)\)/g)].map((match) => {
    const [relative, fragment] = match[1].split("#", 2);
    const resolved = path.posix.normalize(
      path.posix.join(path.posix.dirname(SOURCE_PACKET_REF), relative),
    );
    return fragment ? `${resolved}#${fragment}` : resolved;
  });
  const rawLines = evidence.match(/raw research lines? (.+)\.$/)?.[1] ?? null;
  return { refs, rawLines };
}

export function parseSourcePacket(sourceText) {
  const sections = new Map();
  const expression = /^### `([^`]+)`\r?\n([\s\S]*?)(?=^### `|^## Promotion gate)/gm;
  for (const match of sourceText.matchAll(expression)) {
    const id = match[1];
    const body = match[2];
    const evidence = evidenceFromSection(body);
    sections.set(id, {
      id,
      kind: fieldFromSection(body, "Kind"),
      statement: fieldFromSection(body, "Statement"),
      scope: fieldFromSection(body, "Scope"),
      destination: fieldFromSection(body, "Intended Playbook destination"),
      reviewState: fieldFromSection(body, "Review state"),
      evidenceRefs: evidence.refs,
      rawLines: evidence.rawLines,
    });
  }
  return sections;
}

export function assertSourcePacket(sourceText) {
  const parsed = parseSourcePacket(sourceText);
  const errors = [];
  if (parsed.size !== EXPECTED_RECORDS.length) {
    errors.push(`source packet must contain exactly ${EXPECTED_RECORDS.length} records; found ${parsed.size}`);
  }
  for (const expected of EXPECTED_RECORDS) {
    const actual = parsed.get(expected.id);
    if (!actual) {
      errors.push(`source record is missing: ${expected.id}`);
      continue;
    }
    for (const key of ["statement", "scope"]) {
      if (actual[key] !== expected[key]) {
        errors.push(`${expected.id} ${key} drifted from its locked source text`);
      }
    }
    if (actual.kind !== expected.sourceKind) {
      errors.push(`${expected.id} source kind must remain ${expected.sourceKind}`);
    }
    if (!actual.reviewState?.toLowerCase().startsWith("candidate;")) {
      errors.push(`${expected.id} source review state must remain candidate`);
    }
    if (expected.destination && actual.destination !== `\`${expected.destination}\`.`) {
      errors.push(`${expected.id} source destination must be ${expected.destination}`);
    }
    if (!expected.destination && !actual.destination?.startsWith("none.")) {
      errors.push(`${expected.id} must explicitly record no Playbook destination`);
    }
    if (canonicalJson(actual.evidenceRefs) !== canonicalJson(expected.evidenceRefs)) {
      errors.push(`${expected.id} evidence references drifted from the source packet`);
    }
    if (actual.rawLines !== expected.sourceRawLines) {
      errors.push(`${expected.id} raw research line evidence drifted from the source packet`);
    }
  }
  const unexpected = [...parsed.keys()].filter(
    (id) => !EXPECTED_RECORDS.some((record) => record.id === id),
  );
  if (unexpected.length > 0) errors.push(`unexpected source records: ${unexpected.join(", ")}`);
  if (errors.length > 0) fail(errors);
  return parsed;
}

function atlasRepositoryRef(ref, revision = SOURCE_ADOPTION_MERGE_COMMIT) {
  return {
    source_type: "repository",
    ref: `git:fawxzzy/ATLAS@${revision}:${ref}`,
    classification: "verified",
  };
}

function candidateProvenance(spec) {
  return [
    atlasRepositoryRef(`${SOURCE_PACKET_REF}#${spec.id}`, SOURCE_PACKET_CORRECTED_REVISION),
    ...spec.evidenceRefs.map((ref) => atlasRepositoryRef(ref)),
    {
      source_type: "external-source",
      ref: `git:fawxzzy/ATLAS@${SOURCE_ADOPTION_MERGE_COMMIT}:${RAW_RESEARCH_REF}#lines=${spec.rawLines}`,
      classification: "reported",
    },
    {
      source_type: "repository",
      ref: `git:${PLAYBOOK_REPOSITORY}@${PLAYBOOK_CONSUMER_REVISION}:${PLAYBOOK_CONSUMER_PATH}`,
      classification: "verified",
    },
  ];
}

function buildCandidate(spec) {
  return {
    contract_version: CONTRACT_ID,
    candidate_id: spec.id,
    kind: spec.kind,
    name: spec.name,
    statement: spec.statement,
    scope: spec.scope,
    provenance: candidateProvenance(spec),
    review: {
      status: "candidate",
      reviewer: null,
      reviewed_at: null,
      decision_note: null,
    },
    suggested_destination: spec.destination,
    created_at: CREATED_AT,
    extensions: {
      atlas_projection: {
        source_packet_ref: SOURCE_PACKET_REF,
        source_packet_first_commit: SOURCE_PACKET_FIRST_COMMIT,
        source_packet_corrected_revision: SOURCE_PACKET_CORRECTED_REVISION,
        source_adoption_merge_commit: SOURCE_ADOPTION_MERGE_COMMIT,
        source_statement_sha256: digestText(spec.statement),
        source_scope_sha256: digestText(spec.scope),
        created_at_basis: "First durable Git commit containing the source candidate packet.",
      },
      playbook_consumer_contract: {
        repository: PLAYBOOK_REPOSITORY,
        observed_revision: PLAYBOOK_CONSUMER_REVISION,
        contract_path: PLAYBOOK_CONSUMER_PATH,
        accepted_mapping: {
          kind: spec.kind,
          destination: spec.destination,
        },
      },
    },
  };
}

function candidateArtifactRef(id) {
  return `${ARTIFACT_ROOT_REF}/${id}.knowledge-candidate.v2.json`;
}

export function resolveProjectionOutput(root, ref) {
  if (typeof ref !== "string" || ref === "" || ref.includes("\\")) {
    fail(`projection output is not a portable relative path: ${ref}`);
  }
  const segments = ref.split("/");
  if (path.posix.isAbsolute(ref)
    || path.win32.isAbsolute(ref)
    || path.posix.normalize(ref) !== ref
    || segments.some((segment) => segment === "" || segment === "." || segment === "..")) {
    fail(`projection output is not a portable relative path: ${ref}`);
  }
  const artifactRelative = path.posix.relative(ARTIFACT_ROOT_REF, ref);
  const insideArtifactRoot = artifactRelative !== ""
    && !artifactRelative.startsWith("../")
    && artifactRelative !== ".."
    && !path.posix.isAbsolute(artifactRelative);
  const allowed = insideArtifactRoot
    || ref === PLAYBOOK_HANDOFF_REF
    || ref === CORTEX_HANDOFF_REF;
  if (!allowed) fail(`projection output escapes the root-owned boundary: ${ref}`);

  const resolvedRoot = path.resolve(root);
  const target = path.resolve(resolvedRoot, ...segments);
  const rootRelative = path.relative(resolvedRoot, target);
  if (rootRelative === ""
    || rootRelative.startsWith("..")
    || path.isAbsolute(rootRelative)) {
    fail(`projection output escapes the Atlas root: ${ref}`);
  }
  return target;
}

function buildCandidateManifestRecord(spec, artifactBytes) {
  const basis = {
    record_id: spec.id,
    classification: "knowledge-candidate-v2",
    kind: spec.kind,
    source_statement_sha256: digestText(spec.statement),
    source_scope_sha256: digestText(spec.scope),
    contract_eligible: true,
    artifact_path: candidateArtifactRef(spec.id),
    artifact_sha256: digestBytes(artifactBytes),
    suggested_destination: spec.destination,
    disposition: "playbook-candidate-only-intake",
  };
  return recordWithHash(basis);
}

function buildDecisionManifestRecord(spec) {
  const basis = {
    record_id: spec.id,
    classification: "atlas-product-decision",
    kind: "decision",
    name: spec.name,
    statement: spec.statement,
    scope: spec.scope,
    source_statement_sha256: digestText(spec.statement),
    source_scope_sha256: digestText(spec.scope),
    provenance: [
      atlasRepositoryRef(`${SOURCE_PACKET_REF}#${spec.id}`, SOURCE_PACKET_CORRECTED_REVISION),
      ...spec.evidenceRefs.map((ref) => atlasRepositoryRef(ref)),
      {
        source_type: "external-source",
        ref: `git:fawxzzy/ATLAS@${SOURCE_ADOPTION_MERGE_COMMIT}:${RAW_RESEARCH_REF}#lines=${spec.rawLines}`,
        classification: "reported",
      },
    ],
    contract_eligible: false,
    artifact_path: null,
    artifact_sha256: null,
    suggested_destination: null,
    disposition: "deferred-atlas-product-decision",
    contract_exclusion_reason: "Decision is not one of the five atlas.knowledge-candidate.v2 kinds, and the current Playbook consumer has no Decision destination.",
    later_authority: {
      decision_ratification: "Operator ratification of the target architecture success thresholds and kill criteria is required before this product Decision can authorize execution.",
      contract_migration: "A separately approved Atlas Contracts and Playbook consumer migration is required before any Decision can flow through the KnowledgeCandidate contract; relabeling is forbidden.",
    },
    target_architecture_refs: spec.evidenceRefs,
  };
  return recordWithHash(basis);
}

function buildManifest(sourceBytes, candidateRecords, decisionRecord) {
  return {
    manifest_version: "atlas.creation-os.knowledge-candidate-index.v1",
    generated_at: CREATED_AT,
    layout: {
      root: ARTIFACT_ROOT_REF,
      candidate_filename_contract: "<candidate_id>.knowledge-candidate.v2.json",
      manifest: MANIFEST_REF,
      owner_repository_output_allowed: false,
    },
    source: {
      packet_ref: SOURCE_PACKET_REF,
      packet_sha256: digestBytes(sourceBytes),
      packet_sha256_semantics: "Canonical LF-normalized Git blob bytes used to build this projection.",
      packet_first_commit: SOURCE_PACKET_FIRST_COMMIT,
      packet_first_commit_at: CREATED_AT,
      corrected_packet_revision: SOURCE_PACKET_CORRECTED_REVISION,
      adoption_merge_commit: SOURCE_ADOPTION_MERGE_COMMIT,
      created_at_semantics: "Each candidate created_at is the UTC time of the first durable Git commit containing the source candidate packet, not generation or owner-review time.",
    },
    contract: {
      contract_id: CONTRACT_ID,
      schema_ref: SCHEMA_REF,
      allowed_kinds: CONTRACT_KINDS,
      playbook_consumer: {
        repository: PLAYBOOK_REPOSITORY,
        observed_revision: PLAYBOOK_CONSUMER_REVISION,
        contract_path: PLAYBOOK_CONSUMER_PATH,
        accepted_destinations: SUPPORTED_PLAYBOOK_DESTINATIONS,
      },
    },
    hash_policy: {
      algorithm: "sha256",
      artifact_sha256: "Exact committed UTF-8 bytes including the terminal LF.",
      source_field_sha256: "Exact normalized Markdown paragraph text encoded as UTF-8.",
      record_sha256: "Recursive key-sorted UTF-8 JSON without whitespace, excluding record_sha256 itself.",
    },
    counts: {
      total_source_records: 7,
      knowledge_candidates: 6,
      deferred_decisions: 1,
    },
    records: [...candidateRecords, decisionRecord],
    authority: {
      atlas_projection_only: true,
      playbook_doctrine_mutation: false,
      cortex_policy_authority: false,
      owner_repository_mutation: false,
      bulk_copy: false,
      automatic_promotion: false,
    },
  };
}

function buildPlaybookHandoff(manifest) {
  const candidates = manifest.records.filter((record) => record.contract_eligible);
  const rows = candidates.map((record) =>
    `| \`${record.record_id}\` | \`${record.artifact_path}\` | \`${record.artifact_sha256}\` | \`${record.suggested_destination}\` |`,
  );
  return `# Playbook Creation OS Candidate Intake Handoff - 2026-07-16

## Authority

This is an exact six-artifact, candidate-only owner intake. Atlas supplies
review candidates and immutable evidence; Atlas does not mutate Playbook,
promote doctrine, bulk-copy prose, or grant automatic promotion authority.

Playbook consumer truth was inspected read-only at
\`${PLAYBOOK_REPOSITORY}@${PLAYBOOK_CONSUMER_REVISION}\`, path
\`${PLAYBOOK_CONSUMER_PATH}\`. Its accepted mapping is exactly:

- \`rule -> Playbook/rules\`
- \`pattern -> Playbook/patterns\`
- \`failure-mode -> Playbook/failure-modes\`

## Exact intake

| Candidate ID | Atlas artifact | Exact artifact SHA-256 | Supported destination |
| --- | --- | --- | --- |
${rows.join("\n")}

The source of truth for this set is
\`${MANIFEST_REF}\`. Intake must reject any identity, byte hash, provenance,
review status, kind, or destination mismatch.

## Owner disposition contract

Playbook must return one correlated candidate-only owner receipt per input:

- **accept** - admit the exact artifact into governed candidate review only;
  this is not doctrine promotion;
- **revise** - preserve the Atlas source identity and hash while returning the
  proposed owner revision as a new review record;
- **split** - preserve the Atlas source identity and hash and correlate every
  derived review candidate;
- **reject** - preserve the Atlas source identity and hash and state the
  evidence-backed rejection reason.

No bulk-copy or auto-promotion is allowed. Any later doctrine mutation belongs
to a separately authorized Playbook owner decision and validation path, never
to Atlas projection.

## Excluded Decision

\`${DECISION_ID}\` is intentionally absent from this intake. It remains an
Atlas product Decision in the manifest because \`decision\` is not a current
\`atlas.knowledge-candidate.v2\` kind and Playbook has no Decision destination.
Do not relabel it.

## Required owner receipt

The receipt must report the observed Playbook head, all six candidate IDs,
Atlas paths and hashes, exact destinations, one accept/revise/split/reject
disposition per candidate, candidate-only truth, validation results, and zero
Atlas-authored Playbook doctrine mutation.

## Next sequence

1. Playbook Creation OS candidate-only owner adoption.
2. Cortex Creation OS advisory read-model refresh after the Playbook receipt is reconciled.
3. DiscordOS reliability continuation only after both owner receipts are reconciled.
`;
}

function buildCortexHandoff(manifest) {
  const candidates = manifest.records.filter((record) => record.contract_eligible);
  const decision = manifest.records.find((record) => record.record_id === DECISION_ID);
  const rows = candidates.map((record) =>
    `| \`${record.record_id}\` | \`${record.artifact_path}\` | \`${record.artifact_sha256}\` |`,
  );
  return `# Cortex Creation OS Advisory Refresh Handoff - 2026-07-16

## Authority

This is a read-only advisory ingestion packet. Cortex may refresh derived
context, routing, synthesis, retrieval, and read models. Cortex does not gain
policy, doctrine, scheduling, execution, deployment, owner-mutation, board, or
final approval authority.

## Governed inputs

- Architecture: \`docs/architecture/ATLAS-CREATION-OS-TARGET-ARCHITECTURE.md\`
- Reconciliation: \`docs/audits/ATLAS-CREATION-OS-RESEARCH-RECONCILIATION-2026-07-16.md\`
- Candidate and Decision index: \`${MANIFEST_REF}\`
- Playbook receipt: required before this refresh is accepted

| Candidate ID | Atlas artifact | Exact artifact SHA-256 |
| --- | --- | --- |
${rows.join("\n")}

## Deferred product Decision

- Identity: \`${decision.record_id}\`
- Classification: \`${decision.classification}\`
- Manifest record SHA-256: \`${decision.record_sha256}\`
- Contract eligibility: \`false\`
- Disposition: \`${decision.disposition}\`
- Required truth: success thresholds and kill criteria remain unresolved and
  require operator ratification.

Cortex must represent this record as an Atlas product Decision, not as a
KnowledgeCandidate, Rule, Pattern, Failure Mode, policy, or execution order.

## Refresh contract

1. Read the merged architecture, reconciliation, manifest, exact six candidate
   artifacts, and reconciled Playbook owner receipt.
2. Preserve IDs, classifications, source refs, artifact hashes, the Decision
   exclusion reason, and unresolved success/kill criteria.
3. Rebuild only derived advisory read models; keep every projection traceable
   to the governed inputs above.
4. Return a receipt with source revisions, all seven record IDs, the six exact
   artifact hashes, the deferred Decision record hash, refreshed read-model
   paths and hashes, and zero policy, execution, or owner-repository mutation.

## Next sequence

1. Playbook Creation OS candidate-only owner adoption.
2. Cortex Creation OS advisory read-model refresh after the Playbook receipt is reconciled.
3. DiscordOS reliability continuation only after both owner receipts are reconciled.
`;
}

export async function assertProjectionInvariants(projection) {
  const errors = [];
  const loadedSchema = await loadKnownSchema(CONTRACT_ID);
  if (!loadedSchema.ok) fail([loadedSchema.code, loadedSchema.error]);

  if (projection.candidates.length !== 6) {
    errors.push(`projection must contain six candidates; found ${projection.candidates.length}`);
  }
  const ids = new Set();
  for (const candidate of projection.candidates) {
    const schemaErrors = validateJsonSchema(candidate, loadedSchema.schema);
    errors.push(...schemaErrors.map((error) => `${candidate.candidate_id}: ${error}`));
    const expected = EXPECTED_RECORDS.find((record) => record.id === candidate.candidate_id);
    if (!expected || expected.kind === "decision") {
      errors.push(`unexpected candidate artifact identity: ${candidate.candidate_id}`);
      continue;
    }
    if (ids.has(candidate.candidate_id)) errors.push(`duplicate candidate identity: ${candidate.candidate_id}`);
    ids.add(candidate.candidate_id);
    if (candidate.kind !== expected.kind) errors.push(`${candidate.candidate_id} kind drifted`);
    if (candidate.statement !== expected.statement) errors.push(`${candidate.candidate_id} statement drifted`);
    if (candidate.scope !== expected.scope) errors.push(`${candidate.candidate_id} scope drifted`);
    if (candidate.created_at !== CREATED_AT) errors.push(`${candidate.candidate_id} created_at semantics drifted`);
    if (candidate.review?.status !== "candidate") errors.push(`${candidate.candidate_id} review status must be candidate`);
    const expectedPacketRef = `git:fawxzzy/ATLAS@${SOURCE_PACKET_CORRECTED_REVISION}:${SOURCE_PACKET_REF}#${candidate.candidate_id}`;
    if (candidate.provenance?.[0]?.ref !== expectedPacketRef
      || candidate.provenance?.[0]?.classification !== "verified") {
      errors.push(`${candidate.candidate_id} corrected packet provenance drifted`);
    }
    const projectionMetadata = candidate.extensions?.atlas_projection;
    if (projectionMetadata?.source_packet_first_commit !== SOURCE_PACKET_FIRST_COMMIT
      || projectionMetadata?.source_packet_corrected_revision !== SOURCE_PACKET_CORRECTED_REVISION
      || projectionMetadata?.created_at_basis !== "First durable Git commit containing the source candidate packet.") {
      errors.push(`${candidate.candidate_id} packet history semantics drifted`);
    }
    const supported = SUPPORTED_PLAYBOOK_DESTINATIONS[candidate.kind];
    if (!supported || candidate.suggested_destination !== supported) {
      errors.push(`${candidate.candidate_id} has unsupported kind/destination mapping`);
    }
    const expectedRef = candidateArtifactRef(candidate.candidate_id);
    if (!projection.outputs.has(expectedRef)) errors.push(`${candidate.candidate_id} filename/path contract drifted`);
  }

  const manifest = projection.manifest;
  if (manifest.source?.packet_first_commit !== SOURCE_PACKET_FIRST_COMMIT
    || manifest.source?.packet_first_commit_at !== CREATED_AT
    || manifest.source?.corrected_packet_revision !== SOURCE_PACKET_CORRECTED_REVISION
    || manifest.source?.packet_sha256 !== SOURCE_PACKET_CORRECTED_SHA256) {
    errors.push("manifest packet history and corrected provenance drifted");
  }
  if (manifest.counts?.total_source_records !== 7
    || manifest.counts?.knowledge_candidates !== 6
    || manifest.counts?.deferred_decisions !== 1
    || manifest.records?.length !== 7) {
    errors.push("manifest count contract drifted");
  }
  const manifestIds = manifest.records.map((record) => record.record_id);
  if (new Set(manifestIds).size !== 7) errors.push("manifest contains duplicate record identities");
  for (const record of manifest.records) {
    const { record_sha256: actualRecordHash, ...basis } = record;
    if (actualRecordHash !== digestText(canonicalJson(basis))) {
      errors.push(`${record.record_id} manifest record hash drifted`);
    }
    const expected = EXPECTED_RECORDS.find((candidate) => candidate.id === record.record_id);
    if (!expected) {
      errors.push(`manifest contains unexpected record ${record.record_id}`);
      continue;
    }
    if (record.source_statement_sha256 !== digestText(expected.statement)
      || record.source_scope_sha256 !== digestText(expected.scope)) {
      errors.push(`${record.record_id} source field hash drifted`);
    }
    if (expected.kind !== "decision") {
      const bytes = projection.outputs.get(candidateArtifactRef(expected.id));
      if (!bytes || record.artifact_sha256 !== digestBytes(bytes)) {
        errors.push(`${record.record_id} artifact hash drifted`);
      }
      if (record.artifact_path !== candidateArtifactRef(expected.id)
        || record.suggested_destination !== expected.destination
        || record.contract_eligible !== true) {
        errors.push(`${record.record_id} manifest contract mapping drifted`);
      }
    }
  }
  const decision = manifest.records.find((record) => record.record_id === DECISION_ID);
  if (!decision
    || decision.kind !== "decision"
    || decision.classification !== "atlas-product-decision"
    || decision.contract_eligible !== false
    || decision.artifact_path !== null
    || decision.artifact_sha256 !== null
    || decision.suggested_destination !== null) {
    errors.push("deferred Decision must remain manifest-only and contract-ineligible");
  }
  const expectedDecisionPacketRef = `git:fawxzzy/ATLAS@${SOURCE_PACKET_CORRECTED_REVISION}:${SOURCE_PACKET_REF}#${DECISION_ID}`;
  if (decision?.provenance?.[0]?.ref !== expectedDecisionPacketRef
    || decision?.provenance?.[0]?.classification !== "verified") {
    errors.push("deferred Decision corrected packet provenance drifted");
  }
  if (projection.outputs.has(candidateArtifactRef(DECISION_ID))) {
    errors.push("deferred Decision cannot have a KnowledgeCandidate artifact");
  }
  for (const ref of projection.outputs.keys()) {
    try {
      resolveProjectionOutput(ROOT, ref);
    } catch (error) {
      errors.push(...(error.errors ?? [error.message]));
    }
  }
  if (errors.length > 0) fail(errors);
  return true;
}

export async function buildProjection({ root = ROOT } = {}) {
  const sourcePath = path.join(root, SOURCE_PACKET_REF);
  const sourceBytes = normalizeSourceBytes(await fs.readFile(sourcePath));
  const sourceDigest = digestBytes(sourceBytes);
  if (sourceDigest !== SOURCE_PACKET_CORRECTED_SHA256) {
    fail(`source packet bytes drifted from corrected revision ${SOURCE_PACKET_CORRECTED_REVISION}`);
  }
  const sourceText = sourceBytes.toString("utf8");
  assertSourcePacket(sourceText);

  const candidateSpecs = EXPECTED_RECORDS.filter((record) => record.kind !== "decision");
  const decisionSpec = EXPECTED_RECORDS.find((record) => record.kind === "decision");
  const candidates = candidateSpecs.map(buildCandidate);
  const outputs = new Map();
  const candidateManifestRecords = candidates.map((candidate, index) => {
    const bytes = Buffer.from(deterministicJson(candidate), "utf8");
    outputs.set(candidateArtifactRef(candidate.candidate_id), bytes);
    return buildCandidateManifestRecord(candidateSpecs[index], bytes);
  });
  const decisionRecord = buildDecisionManifestRecord(decisionSpec);
  const manifest = buildManifest(sourceBytes, candidateManifestRecords, decisionRecord);
  outputs.set(MANIFEST_REF, Buffer.from(deterministicJson(manifest), "utf8"));
  outputs.set(PLAYBOOK_HANDOFF_REF, Buffer.from(buildPlaybookHandoff(manifest), "utf8"));
  outputs.set(CORTEX_HANDOFF_REF, Buffer.from(buildCortexHandoff(manifest), "utf8"));
  const projection = { candidates, manifest, outputs };
  await assertProjectionInvariants(projection);
  return projection;
}

export function projectionDigest(projection) {
  const records = [...projection.outputs.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([ref, bytes]) => `${ref}\t${digestBytes(bytes)}`);
  return digestText(records.join("\n"));
}

export async function writeProjection(projection, { root = ROOT } = {}) {
  for (const [ref, bytes] of projection.outputs) {
    const target = resolveProjectionOutput(root, ref);
    await fs.mkdir(path.dirname(target), { recursive: true });
    await fs.writeFile(target, bytes);
  }
}

export async function checkProjection(projection, { root = ROOT } = {}) {
  const errors = [];
  for (const [ref, expectedBytes] of projection.outputs) {
    let target;
    try {
      target = resolveProjectionOutput(root, ref);
    } catch (error) {
      errors.push(...(error.errors ?? [error.message]));
      continue;
    }
    let actualBytes;
    try {
      actualBytes = await fs.readFile(target);
    } catch (error) {
      errors.push(`generated output is missing: ${ref}: ${error.message}`);
      continue;
    }
    if (!actualBytes.equals(expectedBytes)) errors.push(`generated output drifted: ${ref}`);
  }
  const expectedCandidates = new Set(
    EXPECTED_RECORDS.filter((record) => record.kind !== "decision")
      .map((record) => `${record.id}.knowledge-candidate.v2.json`),
  );
  let actualCandidates = [];
  try {
    actualCandidates = (await fs.readdir(path.join(root, ARTIFACT_ROOT_REF)))
      .filter((name) => name.endsWith(".knowledge-candidate.v2.json"));
  } catch (error) {
    errors.push(`candidate artifact root is unavailable: ${error.message}`);
  }
  for (const name of actualCandidates) {
    if (!expectedCandidates.has(name)) errors.push(`unexpected KnowledgeCandidate artifact: ${name}`);
  }
  for (const name of expectedCandidates) {
    if (!actualCandidates.includes(name)) errors.push(`expected KnowledgeCandidate artifact is missing: ${name}`);
  }
  const decisionArtifact = path.join(root, candidateArtifactRef(DECISION_ID));
  try {
    await fs.access(decisionArtifact);
    errors.push("deferred Decision exists as a forbidden KnowledgeCandidate artifact");
  } catch (error) {
    if (error.code !== "ENOENT") errors.push(`cannot prove Decision artifact absence: ${error.message}`);
  }
  const replay = await buildProjection({ root });
  if (projectionDigest(replay) !== projectionDigest(projection)) {
    errors.push("repeated generation is not byte-stable");
  }
  if (errors.length > 0) fail(errors);
  return {
    status: "ok",
    candidate_count: 6,
    deferred_decision_count: 1,
    schema: CONTRACT_ID,
    playbook_consumer_revision: PLAYBOOK_CONSUMER_REVISION,
    output_set_sha256: projectionDigest(projection),
    byte_stable: true,
    owner_repository_outputs: 0,
  };
}

async function main() {
  const argumentsList = process.argv.slice(2);
  const write = argumentsList.includes("--write");
  const check = argumentsList.includes("--check") || !write;
  if (write && argumentsList.includes("--check")) fail("choose either --write or --check");
  const unknown = argumentsList.filter((argument) => !["--write", "--check", "--json"].includes(argument));
  if (unknown.length > 0) fail(`unknown arguments: ${unknown.join(", ")}`);
  const projection = await buildProjection();
  if (write) await writeProjection(projection);
  const result = await checkProjection(projection);
  if (argumentsList.includes("--json")) {
    console.log(JSON.stringify({ ...result, mode: write ? "write" : "check" }));
  } else {
    console.log(`ACCEPTED: ${result.candidate_count} candidates, ${result.deferred_decision_count} deferred Decision, ${result.output_set_sha256}`);
  }
  return check;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(JSON.stringify({ status: "error", errors: error.errors ?? [error.message] }, null, 2));
    process.exitCode = 1;
  });
}
