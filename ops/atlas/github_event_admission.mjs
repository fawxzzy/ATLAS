import { createHash } from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import {
  loadKnownSchema,
  validateJsonSchema,
} from "../../packages/atlas-contracts/scripts/lib/validate-json-schema.mjs";

const modulePath = fileURLToPath(import.meta.url);
const moduleDir = path.dirname(modulePath);
const atlasRoot = path.resolve(moduleDir, "..", "..");

export const DEFAULT_POLICY_PATH = path.join(
  atlasRoot,
  "docs",
  "registry",
  "GITHUB-EVENT-ADMISSION-POLICY.v1.json",
);

const RECEIPT_SCHEMA_ID = "atlas.github.event-receipt.v1";
const ADMISSION_SCHEMA_ID = "atlas.github.event-admission.v1";
const PROJECTION_INTENT_SCHEMA_ID = "atlas.github.projection-intent.v1";

const EVENT_FAMILIES = Object.freeze([
  "repository",
  "branch",
  "pull_request",
  "issue",
  "workflow_run",
  "release",
  "security_alert",
]);

const FACT_STATES = Object.freeze([
  "observed",
  "empty",
  "unknown",
  "access_denied",
  "disabled",
  "conflicting",
  "not_applicable",
]);

const POLICY_DECISIONS = Object.freeze(["accepted", "duplicate", "rejected", "quarantined"]);
const LEDGER_MEANINGS = Object.freeze([
  "record_only",
  "record_and_project",
  "noop_duplicate",
  "reject_record",
  "quarantine_hold",
]);
const PROJECTION_DECISIONS = Object.freeze([
  "admitted",
  "suppressed",
  "requires_review",
  "blocked",
]);
const DESTINATIONS = Object.freeze([
  "atlas_ledger",
  "discordos_board",
  "discordos_update",
  "discordos_alerts",
]);
const OPERATIONS = Object.freeze([
  "record",
  "create",
  "update",
  "transition",
  "publish",
  "alert",
  "none",
]);
const ROUTE_KEYS = Object.freeze(["project_id", "card_id", "board_id", "channel_id", "thread_id"]);

const exitCodes = Object.freeze({
  OK: 0,
  INVALID_INPUT: 1,
  INVALID_POLICY: 2,
  MALFORMED_JSON: 3,
  MISSING_INPUT: 4,
  SELF_CHECK_FAILED: 5,
});

class AdmissionCompilerError extends Error {
  constructor(code, message, { errors = [], exitCode = exitCodes.INVALID_INPUT } = {}) {
    super(message);
    this.name = "AdmissionCompilerError";
    this.code = code;
    this.errors = errors.length > 0 ? [...errors] : [message];
    this.exitCode = exitCode;
  }
}

function isPlainObject(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function stableValue(value) {
  if (Array.isArray(value)) {
    return value.map((entry) => stableValue(entry));
  }

  if (!isPlainObject(value)) {
    return value;
  }

  return Object.fromEntries(
    Object.keys(value)
      .sort()
      .map((key) => [key, stableValue(value[key])]),
  );
}

export function stableStringify(value, { pretty = false } = {}) {
  return JSON.stringify(stableValue(value), null, pretty ? 2 : 0);
}

function sha256Hex(value) {
  return createHash("sha256").update(value).digest("hex");
}

export function policyDigest(policy) {
  return sha256Hex(stableStringify(policy));
}

function prefixedIdentity(prefix, payload) {
  return `${prefix}${sha256Hex(stableStringify(payload))}`;
}

function uniqueSortedStrings(values) {
  return [...new Set(values)].sort();
}

async function readJsonArtifact(filePath, { malformedCode, missingCode, label }) {
  let raw;
  try {
    raw = await fs.readFile(filePath, "utf8");
  } catch (error) {
    if (error?.code === "ENOENT" || error?.code === "ENOTDIR") {
      throw new AdmissionCompilerError(
        missingCode,
        `${label} JSON path does not exist.`,
        {
          errors: [`${label} JSON path does not exist.`],
          exitCode: exitCodes.MISSING_INPUT,
        },
      );
    }
    throw error;
  }

  try {
    return JSON.parse(raw);
  } catch {
    throw new AdmissionCompilerError(
      malformedCode,
      `${label} JSON could not be parsed.`,
      {
        errors: [`${label} JSON could not be parsed.`],
        exitCode: exitCodes.MALFORMED_JSON,
      },
    );
  }
}

async function loadRegisteredSchema(reference) {
  const loadedSchema = await loadKnownSchema(reference);
  if (!loadedSchema.ok) {
    throw new AdmissionCompilerError(
      loadedSchema.code,
      loadedSchema.error,
      {
        errors: [loadedSchema.error],
        exitCode: exitCodes.SELF_CHECK_FAILED,
      },
    );
  }

  return loadedSchema;
}

async function validateRegisteredArtifact(artifact, schemaId, code, label) {
  const loadedSchema = await loadRegisteredSchema(schemaId);
  const errors = validateJsonSchema(artifact, loadedSchema.schema);
  if (errors.length > 0) {
    throw new AdmissionCompilerError(code, `${label} is schema-invalid.`, {
      errors,
      exitCode: exitCodes.INVALID_INPUT,
    });
  }

  return loadedSchema;
}

function validateRoute(route, label, errors) {
  if (!isPlainObject(route)) {
    errors.push(`${label} must be an object.`);
    return;
  }

  const keys = Object.keys(route).sort();
  if (stableStringify(keys) !== stableStringify([...ROUTE_KEYS].sort())) {
    errors.push(`${label} must contain only ${ROUTE_KEYS.join(", ")}.`);
  }

  for (const key of ROUTE_KEYS) {
    if (!(key in route)) {
      errors.push(`${label}.${key} is required.`);
      continue;
    }

    if (route[key] !== null) {
      errors.push(`${label}.${key} must remain null until DiscordOS resolves routing.`);
    }
  }
}

function validateReasonCodes(reasonCodes, label, errors) {
  if (!Array.isArray(reasonCodes) || reasonCodes.length === 0) {
    errors.push(`${label} must be a non-empty array.`);
    return;
  }

  for (const reasonCode of reasonCodes) {
    if (
      typeof reasonCode !== "string"
      || !/^[a-z0-9][a-z0-9._-]*$/.test(reasonCode)
    ) {
      errors.push(`${label} must contain stable lowercase reason codes.`);
      return;
    }
  }
}

function validatePolicyOutcome(outcome, family, state, policy, errors) {
  const label = `event_families.${family}.states.${state}`;
  const intentTemplates = isPlainObject(policy.intent_templates) ? policy.intent_templates : {};
  if (!isPlainObject(outcome)) {
    errors.push(`${label} must be an object.`);
    return;
  }

  if (!POLICY_DECISIONS.includes(outcome.decision)) {
    errors.push(`${label}.decision must be one of ${POLICY_DECISIONS.join(", ")}.`);
  }

  if (!LEDGER_MEANINGS.includes(outcome.ledger_meaning)) {
    errors.push(`${label}.ledger_meaning must be one of ${LEDGER_MEANINGS.join(", ")}.`);
  }

  validateReasonCodes(outcome.reason_codes, `${label}.reason_codes`, errors);

  if (!Array.isArray(outcome.intent_template_ids)) {
    errors.push(`${label}.intent_template_ids must be an array.`);
    return;
  }

  for (const templateId of outcome.intent_template_ids) {
    if (typeof templateId !== "string" || !(templateId in intentTemplates)) {
      errors.push(`${label}.intent_template_ids must reference known templates.`);
    }
  }

  const templateIds = uniqueSortedStrings(outcome.intent_template_ids);
  const hasLedgerIntent = templateIds.includes("ledger_record");
  const hasExternalIntent = templateIds.some((templateId) => templateId !== "ledger_record");

  if (state === "conflicting") {
    if (outcome.decision !== "quarantined") {
      errors.push(`${label}.decision must quarantine conflicting source facts.`);
    }
    if (outcome.ledger_meaning !== "quarantine_hold") {
      errors.push(`${label}.ledger_meaning must be quarantine_hold for conflicting source facts.`);
    }
    if (templateIds.length > 0) {
      errors.push(`${label}.intent_template_ids must be empty for conflicting source facts.`);
    }
    return;
  }

  if (outcome.decision === "accepted") {
    if (!hasLedgerIntent) {
      errors.push(`${label}.intent_template_ids must include ledger_record for accepted outcomes.`);
    }

    const expectedMeaning = hasExternalIntent ? "record_and_project" : "record_only";
    if (outcome.ledger_meaning !== expectedMeaning) {
      errors.push(`${label}.ledger_meaning must be ${expectedMeaning}.`);
    }
    return;
  }

  if (outcome.decision === "quarantined") {
    if (outcome.ledger_meaning !== "quarantine_hold") {
      errors.push(`${label}.ledger_meaning must be quarantine_hold for quarantined outcomes.`);
    }
    if (templateIds.length > 0) {
      errors.push(`${label}.intent_template_ids must be empty for quarantined outcomes.`);
    }
    return;
  }

  if (outcome.decision === "rejected") {
    if (outcome.ledger_meaning !== "reject_record") {
      errors.push(`${label}.ledger_meaning must be reject_record for rejected outcomes.`);
    }
    if (templateIds.length > 0) {
      errors.push(`${label}.intent_template_ids must be empty for rejected outcomes.`);
    }
  }
}

export function validatePolicyDocument(policy) {
  const errors = [];

  if (!isPlainObject(policy)) {
    return {
      ok: false,
      errors: ["Policy document must be a JSON object."],
    };
  }

  if (policy.contract_version !== "atlas.github.event-admission-policy.v1") {
    errors.push("contract_version must equal atlas.github.event-admission-policy.v1.");
  }

  if (policy.policy_id !== "github-event-admission-policy") {
    errors.push("policy_id must equal github-event-admission-policy.");
  }

  if (policy.version !== 1) {
    errors.push("version must equal 1.");
  }

  if (!isPlainObject(policy.deduplication)) {
    errors.push("deduplication must be an object.");
  } else {
    for (const key of ["same_digest", "digest_conflict"]) {
      const rule = policy.deduplication[key];
      if (!isPlainObject(rule)) {
        errors.push(`deduplication.${key} must be an object.`);
        continue;
      }

      if (!POLICY_DECISIONS.includes(rule.decision)) {
        errors.push(`deduplication.${key}.decision must be a known admission decision.`);
      }
      if (!LEDGER_MEANINGS.includes(rule.ledger_meaning)) {
        errors.push(`deduplication.${key}.ledger_meaning must be a known ledger meaning.`);
      }
      validateReasonCodes(rule.reason_codes, `deduplication.${key}.reason_codes`, errors);
    }

    if (policy.deduplication?.same_digest?.decision !== "duplicate") {
      errors.push("deduplication.same_digest.decision must be duplicate.");
    }
    if (policy.deduplication?.same_digest?.ledger_meaning !== "noop_duplicate") {
      errors.push("deduplication.same_digest.ledger_meaning must be noop_duplicate.");
    }
    if (policy.deduplication?.digest_conflict?.decision !== "quarantined") {
      errors.push("deduplication.digest_conflict.decision must be quarantined.");
    }
    if (policy.deduplication?.digest_conflict?.ledger_meaning !== "quarantine_hold") {
      errors.push("deduplication.digest_conflict.ledger_meaning must be quarantine_hold.");
    }
  }

  if (!isPlainObject(policy.routes)) {
    errors.push("routes must be an object.");
  } else {
    const expectedRouteKeys = ["atlas_ledger", "discordos_alerts", "discordos_update"];
    const actualRouteKeys = Object.keys(policy.routes).sort();
    if (stableStringify(actualRouteKeys) !== stableStringify(expectedRouteKeys)) {
      errors.push(`routes must contain only ${expectedRouteKeys.join(", ")}.`);
    }

    for (const routeKey of expectedRouteKeys) {
      validateRoute(policy.routes[routeKey], `routes.${routeKey}`, errors);
    }
  }

  if (!isPlainObject(policy.intent_templates)) {
    errors.push("intent_templates must be an object.");
  } else {
    const expectedTemplateIds = [
      "ledger_record",
      "release_publish_requires_review",
      "security_alert_requires_review",
    ];
    const actualTemplateIds = Object.keys(policy.intent_templates).sort();
    if (stableStringify(actualTemplateIds) !== stableStringify(expectedTemplateIds)) {
      errors.push(`intent_templates must contain only ${expectedTemplateIds.join(", ")}.`);
    }

    for (const templateId of expectedTemplateIds) {
      const template = policy.intent_templates[templateId];
      const label = `intent_templates.${templateId}`;
      if (!isPlainObject(template)) {
        errors.push(`${label} must be an object.`);
        continue;
      }
      if (!PROJECTION_DECISIONS.includes(template.decision)) {
        errors.push(`${label}.decision must be a known projection decision.`);
      }
      if (!DESTINATIONS.includes(template.destination)) {
        errors.push(`${label}.destination must be a known destination.`);
      }
      if (!OPERATIONS.includes(template.operation)) {
        errors.push(`${label}.operation must be a known operation.`);
      }
      if (typeof template.route_key !== "string" || !(template.route_key in (policy.routes ?? {}))) {
        errors.push(`${label}.route_key must reference a known route.`);
      }
      validateReasonCodes(template.reason_codes, `${label}.reason_codes`, errors);
    }

    const ledgerTemplate = policy.intent_templates.ledger_record;
    if (ledgerTemplate?.decision !== "admitted") {
      errors.push("intent_templates.ledger_record.decision must be admitted.");
    }
    if (ledgerTemplate?.destination !== "atlas_ledger") {
      errors.push("intent_templates.ledger_record.destination must be atlas_ledger.");
    }
    if (ledgerTemplate?.operation !== "record") {
      errors.push("intent_templates.ledger_record.operation must be record.");
    }

    const releaseTemplate = policy.intent_templates.release_publish_requires_review;
    if (releaseTemplate?.decision !== "requires_review") {
      errors.push("intent_templates.release_publish_requires_review.decision must be requires_review.");
    }
    if (releaseTemplate?.destination !== "discordos_update") {
      errors.push("intent_templates.release_publish_requires_review.destination must be discordos_update.");
    }
    if (releaseTemplate?.operation !== "publish") {
      errors.push("intent_templates.release_publish_requires_review.operation must be publish.");
    }

    const securityTemplate = policy.intent_templates.security_alert_requires_review;
    if (securityTemplate?.decision !== "requires_review") {
      errors.push("intent_templates.security_alert_requires_review.decision must be requires_review.");
    }
    if (securityTemplate?.destination !== "discordos_alerts") {
      errors.push("intent_templates.security_alert_requires_review.destination must be discordos_alerts.");
    }
    if (securityTemplate?.operation !== "alert") {
      errors.push("intent_templates.security_alert_requires_review.operation must be alert.");
    }
  }

  if (!isPlainObject(policy.event_families)) {
    errors.push("event_families must be an object.");
  } else {
    const actualFamilies = Object.keys(policy.event_families).sort();
    if (stableStringify(actualFamilies) !== stableStringify([...EVENT_FAMILIES].sort())) {
      errors.push(`event_families must contain only ${EVENT_FAMILIES.join(", ")}.`);
    }

    for (const family of EVENT_FAMILIES) {
      const familyPolicy = policy.event_families[family];
      const label = `event_families.${family}`;
      if (!isPlainObject(familyPolicy)) {
        errors.push(`${label} must be an object.`);
        continue;
      }

      if (!isPlainObject(familyPolicy.states)) {
        errors.push(`${label}.states must be an object.`);
        continue;
      }

      const actualStates = Object.keys(familyPolicy.states).sort();
      if (stableStringify(actualStates) !== stableStringify([...FACT_STATES].sort())) {
        errors.push(`${label}.states must contain only ${FACT_STATES.join(", ")}.`);
      }

      for (const state of FACT_STATES) {
        validatePolicyOutcome(familyPolicy.states[state], family, state, policy, errors);
      }

      const observedOutcome = familyPolicy.states.observed;
      const observedTemplateIds = uniqueSortedStrings(observedOutcome?.intent_template_ids ?? []);
      if (family === "release") {
        if (!observedTemplateIds.includes("release_publish_requires_review")) {
          errors.push("event_families.release.states.observed must emit release review intent.");
        }
      } else if (observedTemplateIds.includes("release_publish_requires_review")) {
        errors.push(`event_families.${family}.states.observed must not emit release review intent.`);
      }

      if (family === "security_alert") {
        if (!observedTemplateIds.includes("security_alert_requires_review")) {
          errors.push("event_families.security_alert.states.observed must emit security review intent.");
        }
      } else if (observedTemplateIds.includes("security_alert_requires_review")) {
        errors.push(`event_families.${family}.states.observed must not emit security review intent.`);
      }
    }
  }

  if (errors.length > 0) {
    return { ok: false, errors: uniqueSortedStrings(errors) };
  }

  return {
    ok: true,
    digest: policyDigest(policy),
  };
}

function validateReceiptSemantics(receipt) {
  const errors = [];

  if (receipt.source?.provider !== "github") {
    errors.push("source.provider must remain github.");
  }
  if (receipt.source?.producer !== "_stack") {
    errors.push("source.producer must remain _stack.");
  }
  if (receipt.subject?.entity_type !== receipt.event_family) {
    errors.push("subject.entity_type must match event_family.");
  }
  if (receipt.authority?.producer !== "_stack") {
    errors.push("authority.producer must remain _stack.");
  }
  if (receipt.authority?.atlas_contract_owner !== "Atlas Contracts") {
    errors.push("authority.atlas_contract_owner must remain Atlas Contracts.");
  }
  if (receipt.authority?.owner_repository_truth !== "preserved") {
    errors.push("authority.owner_repository_truth must remain preserved.");
  }
  if (receipt.authority?.read_only_first !== true) {
    errors.push("authority.read_only_first must remain true.");
  }
  if (receipt.authority?.external_mutation !== "denied") {
    errors.push("authority.external_mutation must remain denied.");
  }

  if (errors.length > 0) {
    throw new AdmissionCompilerError("INVALID_RECEIPT", "Receipt immutable facts are invalid.", {
      errors,
      exitCode: exitCodes.INVALID_INPUT,
    });
  }
}

function validatePriorAdmissionSemantics(admission) {
  const errors = [];

  if (
    admission.decision === "duplicate"
    && (
      admission.ledger_disposition?.meaning !== "noop_duplicate"
      || admission.projection_intent_refs.length !== 0
    )
  ) {
    errors.push("Duplicate prior admissions must use noop_duplicate and no projection refs.");
  }

  if (
    admission.decision === "quarantined"
    && (
      admission.ledger_disposition?.meaning !== "quarantine_hold"
      || admission.projection_intent_refs.length !== 0
    )
  ) {
    errors.push("Quarantined prior admissions must use quarantine_hold and no projection refs.");
  }

  if (
    admission.decision === "rejected"
    && (
      admission.ledger_disposition?.meaning !== "reject_record"
      || admission.projection_intent_refs.length !== 0
    )
  ) {
    errors.push("Rejected prior admissions must use reject_record and no projection refs.");
  }

  if (
    admission.decision === "accepted"
    && !["record_only", "record_and_project"].includes(admission.ledger_disposition?.meaning)
  ) {
    errors.push("Accepted prior admissions must use record_only or record_and_project.");
  }

  if (errors.length > 0) {
    throw new AdmissionCompilerError(
      "CONTRADICTORY_PRIOR_ADMISSION",
      "Prior admission evidence is semantically contradictory.",
      {
        errors,
        exitCode: exitCodes.INVALID_INPUT,
      },
    );
  }
}

function relevantPriorAdmissions(priorAdmissions, receipt) {
  return priorAdmissions.filter(
    (admission) => admission.source_event.idempotency_key === receipt.idempotency_key,
  );
}

function detectContradictoryPriorAdmissions(priorAdmissions) {
  const byAdmissionId = new Map();
  for (const admission of priorAdmissions) {
    const normalized = stableStringify(admission);
    const existing = byAdmissionId.get(admission.admission_id);
    if (!existing) {
      byAdmissionId.set(admission.admission_id, normalized);
      continue;
    }
    if (existing !== normalized) {
      throw new AdmissionCompilerError(
        "CONTRADICTORY_PRIOR_ADMISSION",
        "Prior admission evidence contains multiple payloads for one admission_id.",
        {
          errors: ["Prior admission evidence contains multiple payloads for one admission_id."],
          exitCode: exitCodes.INVALID_INPUT,
        },
      );
    }
  }

  const byDigestKey = new Map();
  for (const admission of priorAdmissions) {
    const digestKey = [
      admission.source_event.idempotency_key,
      admission.source_event.digest_value,
    ].join("|");

    const snapshot = {
      digest_algorithm: admission.source_event.digest_algorithm,
      event_family: admission.source_event.event_family,
      event_id: admission.source_event.event_id,
      fact_state: admission.source_event.fact_state,
    };

    const existing = byDigestKey.get(digestKey);
    if (!existing) {
      byDigestKey.set(digestKey, snapshot);
      continue;
    }

    if (stableStringify(existing) !== stableStringify(snapshot)) {
      throw new AdmissionCompilerError(
        "CONTRADICTORY_PRIOR_ADMISSION",
        "Prior admission evidence disagrees about source identity for the same digest.",
        {
          errors: ["Prior admission evidence disagrees about source identity for the same digest."],
          exitCode: exitCodes.INVALID_INPUT,
        },
      );
    }
  }
}

function ledgerDisposition(decision, ledgerMeaning) {
  if (!POLICY_DECISIONS.includes(decision)) {
    throw new Error(`Unsupported decision ${decision}`);
  }

  return {
    backend: "backend_neutral",
    meaning: ledgerMeaning,
    terminal: true,
  };
}

function sourceEventFromReceipt(receipt) {
  return {
    digest_algorithm: receipt.digest.algorithm,
    digest_value: receipt.digest.value,
    event_family: receipt.event_family,
    event_id: receipt.event_id,
    fact_state: receipt.fact_state,
    idempotency_key: receipt.idempotency_key,
  };
}

function projectionSourceEventFromReceipt(receipt) {
  return {
    digest_algorithm: receipt.digest.algorithm,
    digest_value: receipt.digest.value,
    event_family: receipt.event_family,
    event_id: receipt.event_id,
  };
}

function admissionAuthority() {
  return {
    admission_owner: "Atlas",
    external_mutation: "denied",
    projection_writer: "DiscordOS",
    source_producer: "_stack",
  };
}

function projectionAuthority() {
  return {
    external_writer: "DiscordOS",
    intent_producer: "Atlas",
  };
}

function matchedPriorEvidenceRefs(receipt, priorAdmissions, policy) {
  const priorRefs = priorAdmissions.map((admission) => `admission:${admission.admission_id}`);
  return uniqueSortedStrings([
    ...receipt.evidence_refs,
    ...priorRefs,
    `policy:${policy.policy_id}:${policyDigest(policy)}`,
  ]);
}

function buildProjectionIntent({
  admissionDecision,
  admissionId,
  policy,
  receipt,
  templateId,
  template,
}) {
  const projectionId = prefixedIdentity("ghp_", {
    admission_id: admissionId,
    receipt: {
      digest_value: receipt.digest.value,
      event_family: receipt.event_family,
      event_id: receipt.event_id,
      observed_at: receipt.observed_at,
    },
    template_id: templateId,
  });

  const projectionIdempotencyKey = prefixedIdentity("ghpk_", {
    receipt: {
      digest_value: receipt.digest.value,
      source_idempotency_key: receipt.idempotency_key,
    },
    template_id: templateId,
  });

  return {
    admission_ref: {
      admission_id: admissionId,
      decision: admissionDecision,
    },
    authority: projectionAuthority(),
    contract_version: PROJECTION_INTENT_SCHEMA_ID,
    created_at: receipt.observed_at,
    decision: template.decision,
    destination: template.destination,
    evidence_refs: uniqueSortedStrings([
      ...receipt.evidence_refs,
      `policy:${policy.policy_id}:${policyDigest(policy)}`,
    ]),
    external_mutation: "denied",
    idempotency_key: projectionIdempotencyKey,
    normalized_fact_refs: receipt.normalized_facts.map((fact) => fact.fact_key),
    operation: template.operation,
    projection_id: projectionId,
    reason_codes: [...template.reason_codes],
    route: stableValue(policy.routes[template.route_key]),
    source_event: projectionSourceEventFromReceipt(receipt),
  };
}

function classifyReceipt({ policy, priorAdmissions, receipt }) {
  const familyPolicy = policy.event_families[receipt.event_family];
  const outcome = familyPolicy.states[receipt.fact_state];
  const sameDigestPriors = priorAdmissions.filter(
    (admission) => admission.source_event.digest_value === receipt.digest.value,
  );
  const conflictingDigestPriors = priorAdmissions.filter(
    (admission) => admission.source_event.digest_value !== receipt.digest.value,
  );

  if (conflictingDigestPriors.length > 0) {
    return {
      decision: "quarantined",
      evidenceRefs: matchedPriorEvidenceRefs(receipt, conflictingDigestPriors, policy),
      ledgerMeaning: policy.deduplication.digest_conflict.ledger_meaning,
      reasonCodes: [...policy.deduplication.digest_conflict.reason_codes],
      templateIds: [],
    };
  }

  if (sameDigestPriors.length > 0) {
    return {
      decision: "duplicate",
      evidenceRefs: matchedPriorEvidenceRefs(receipt, sameDigestPriors, policy),
      ledgerMeaning: policy.deduplication.same_digest.ledger_meaning,
      reasonCodes: [...policy.deduplication.same_digest.reason_codes],
      templateIds: [],
    };
  }

  return {
    decision: outcome.decision,
    evidenceRefs: uniqueSortedStrings([
      ...receipt.evidence_refs,
      `policy:${policy.policy_id}:${policyDigest(policy)}`,
    ]),
    ledgerMeaning: outcome.ledger_meaning,
    reasonCodes: [...outcome.reason_codes],
    templateIds: [...outcome.intent_template_ids],
  };
}

export async function loadPolicy(policyPath = DEFAULT_POLICY_PATH) {
  const policy = await readJsonArtifact(policyPath, {
    label: "Policy",
    malformedCode: "MALFORMED_POLICY_JSON",
    missingCode: "MISSING_POLICY",
  });

  const validation = validatePolicyDocument(policy);
  if (!validation.ok) {
    throw new AdmissionCompilerError("INVALID_POLICY", "Policy document is invalid.", {
      errors: validation.errors,
      exitCode: exitCodes.INVALID_POLICY,
    });
  }

  return {
    digest: validation.digest,
    policy,
  };
}

export async function selfCheckGithubEventAdmission({ policyPath = DEFAULT_POLICY_PATH } = {}) {
  await loadRegisteredSchema(RECEIPT_SCHEMA_ID);
  await loadRegisteredSchema(ADMISSION_SCHEMA_ID);
  await loadRegisteredSchema(PROJECTION_INTENT_SCHEMA_ID);
  const { digest, policy } = await loadPolicy(policyPath);
  return {
    code: "SELF_CHECK_OK",
    ok: true,
    policy_digest: digest,
    policy_id: policy.policy_id,
    schema_ids: [
      RECEIPT_SCHEMA_ID,
      ADMISSION_SCHEMA_ID,
      PROJECTION_INTENT_SCHEMA_ID,
    ],
  };
}

export async function compileGithubEventAdmission({
  policy,
  priorAdmissions = [],
  receipt,
} = {}) {
  if (!receipt) {
    throw new AdmissionCompilerError("MISSING_INPUT", "A receipt JSON artifact is required.", {
      errors: ["A receipt JSON artifact is required."],
      exitCode: exitCodes.MISSING_INPUT,
    });
  }

  await validateRegisteredArtifact(receipt, RECEIPT_SCHEMA_ID, "INVALID_RECEIPT", "Receipt");
  validateReceiptSemantics(receipt);

  if (!policy) {
    throw new AdmissionCompilerError("INVALID_POLICY", "A policy document is required.", {
      errors: ["A policy document is required."],
      exitCode: exitCodes.INVALID_POLICY,
    });
  }

  const policyValidation = validatePolicyDocument(policy);
  if (!policyValidation.ok) {
    throw new AdmissionCompilerError("INVALID_POLICY", "Policy document is invalid.", {
      errors: policyValidation.errors,
      exitCode: exitCodes.INVALID_POLICY,
    });
  }

  for (const admission of priorAdmissions) {
    await validateRegisteredArtifact(
      admission,
      ADMISSION_SCHEMA_ID,
      "INVALID_PRIOR_ADMISSION",
      "Prior admission",
    );
    validatePriorAdmissionSemantics(admission);
  }

  detectContradictoryPriorAdmissions(priorAdmissions);

  const relevantPriors = relevantPriorAdmissions(priorAdmissions, receipt).sort((left, right) =>
    stableStringify(left.source_event).localeCompare(stableStringify(right.source_event))
    || left.admission_id.localeCompare(right.admission_id),
  );

  const classification = classifyReceipt({
    policy,
    priorAdmissions: relevantPriors,
    receipt,
  });

  const atlasIdempotencyKey = prefixedIdentity("ghak_", {
    policy_digest: policyValidation.digest,
    receipt: {
      digest_value: receipt.digest.value,
      event_id: receipt.event_id,
      source_idempotency_key: receipt.idempotency_key,
    },
  });

  const admissionId = prefixedIdentity("gha_", {
    policy_digest: policyValidation.digest,
    prior_admissions: relevantPriors.map((admission) => ({
      admission_id: admission.admission_id,
      decision: admission.decision,
      digest_value: admission.source_event.digest_value,
      source_idempotency_key: admission.source_event.idempotency_key,
    })),
    receipt,
  });

  const projectionIntents = classification.templateIds
    .map((templateId) => buildProjectionIntent({
      admissionDecision: classification.decision,
      admissionId,
      policy,
      receipt,
      template: policy.intent_templates[templateId],
      templateId,
    }))
    .sort((left, right) => left.projection_id.localeCompare(right.projection_id));

  for (const projectionIntent of projectionIntents) {
    await validateRegisteredArtifact(
      projectionIntent,
      PROJECTION_INTENT_SCHEMA_ID,
      "INVALID_PROJECTION_INTENT",
      "Projection intent",
    );
  }

  const admission = {
    admitted_at: receipt.observed_at,
    admission_id: admissionId,
    authority: admissionAuthority(),
    contract_version: ADMISSION_SCHEMA_ID,
    decision: classification.decision,
    evidence_refs: classification.evidenceRefs,
    idempotency_key: atlasIdempotencyKey,
    ledger_disposition: ledgerDisposition(classification.decision, classification.ledgerMeaning),
    projection_intent_refs: projectionIntents.map((projectionIntent) => projectionIntent.projection_id),
    reason_codes: classification.reasonCodes,
    source_event: sourceEventFromReceipt(receipt),
  };

  await validateRegisteredArtifact(
    admission,
    ADMISSION_SCHEMA_ID,
    "INVALID_ADMISSION",
    "Admission",
  );

  return {
    admission,
    code: "ADMISSION_COMPILED",
    ok: true,
    policy_digest: policyValidation.digest,
    projection_intents: projectionIntents,
  };
}

async function writeArtifacts(outputDir, result) {
  await fs.mkdir(outputDir, { recursive: true });

  const artifacts = [
    {
      fileName: `${result.admission.admission_id}.json`,
      payload: result.admission,
    },
    ...result.projection_intents.map((projectionIntent) => ({
      fileName: `${projectionIntent.projection_id}.json`,
      payload: projectionIntent,
    })),
  ];

  for (const artifact of artifacts) {
    await fs.writeFile(
      path.join(outputDir, artifact.fileName),
      `${stableStringify(artifact.payload, { pretty: true })}\n`,
      "utf8",
    );
  }
}

function parseArguments(argv) {
  const options = {
    priorAdmissions: [],
    selfCheck: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];

    if (argument === "--self-check") {
      options.selfCheck = true;
      continue;
    }

    const equalsMatch = argument.match(
      /^--(receipt|prior-admission|policy|output-dir)=(.*)$/u,
    );
    if (equalsMatch) {
      const [, key, value] = equalsMatch;
      if (key === "prior-admission") {
        options.priorAdmissions.push(value);
      } else if (key === "output-dir") {
        options.outputDir = value;
      } else {
        options[key.replace(/-([a-z])/gu, (_, letter) => letter.toUpperCase())] = value;
      }
      continue;
    }

    if (["--receipt", "--prior-admission", "--policy", "--output-dir"].includes(argument)) {
      const value = argv[index + 1];
      if (!value || value.startsWith("--")) {
        throw new AdmissionCompilerError(
          "MISSING_INPUT",
          `${argument} requires a value.`,
          {
            errors: [`${argument} requires a value.`],
            exitCode: exitCodes.MISSING_INPUT,
          },
        );
      }

      if (argument === "--prior-admission") {
        options.priorAdmissions.push(value);
      } else if (argument === "--output-dir") {
        options.outputDir = value;
      } else {
        const key = argument.slice(2).replace(/-([a-z])/gu, (_, letter) => letter.toUpperCase());
        options[key] = value;
      }
      index += 1;
      continue;
    }

    throw new AdmissionCompilerError(
      "INVALID_ARGUMENT",
      `Unsupported argument: ${argument}`,
      {
        errors: [`Unsupported argument: ${argument}`],
        exitCode: exitCodes.INVALID_INPUT,
      },
    );
  }

  return options;
}

function failureResult(error) {
  if (error instanceof AdmissionCompilerError) {
    return {
      exitCode: error.exitCode,
      result: {
        code: error.code,
        errors: error.errors,
        ok: false,
      },
    };
  }

  throw error;
}

export async function runGithubEventAdmissionCli(argv = process.argv.slice(2)) {
  try {
    const options = parseArguments(argv);

    if (options.selfCheck && !options.receipt) {
      return {
        exitCode: exitCodes.OK,
        result: await selfCheckGithubEventAdmission({
          policyPath: options.policy ?? DEFAULT_POLICY_PATH,
        }),
      };
    }

    if (!options.receipt) {
      throw new AdmissionCompilerError("MISSING_INPUT", "A receipt JSON artifact is required.", {
        errors: ["A receipt JSON artifact is required."],
        exitCode: exitCodes.MISSING_INPUT,
      });
    }

    const { policy } = await loadPolicy(options.policy ?? DEFAULT_POLICY_PATH);
    if (options.selfCheck) {
      await selfCheckGithubEventAdmission({
        policyPath: options.policy ?? DEFAULT_POLICY_PATH,
      });
    }

    const receipt = await readJsonArtifact(options.receipt, {
      label: "Receipt",
      malformedCode: "MALFORMED_RECEIPT_JSON",
      missingCode: "MISSING_RECEIPT",
    });

    const priorAdmissions = [];
    for (const priorAdmissionPath of options.priorAdmissions) {
      priorAdmissions.push(await readJsonArtifact(priorAdmissionPath, {
        label: "Prior admission",
        malformedCode: "MALFORMED_PRIOR_ADMISSION_JSON",
        missingCode: "MISSING_PRIOR_ADMISSION",
      }));
    }

    const result = await compileGithubEventAdmission({
      policy,
      priorAdmissions,
      receipt,
    });

    if (options.outputDir) {
      await writeArtifacts(options.outputDir, result);
    }

    return {
      exitCode: exitCodes.OK,
      result,
    };
  } catch (error) {
    return failureResult(error);
  }
}

if (path.resolve(process.argv[1] ?? "") === modulePath) {
  const outcome = await runGithubEventAdmissionCli();
  console.log(stableStringify(outcome.result, { pretty: true }));
  process.exitCode = outcome.exitCode;
}
