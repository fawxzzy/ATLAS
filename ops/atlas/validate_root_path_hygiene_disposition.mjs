#!/usr/bin/env node
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const SCHEMA_VERSION = "atlas.root_path_hygiene_disposition.v1";
const CATEGORY = "atlas-root-path";
const PRESERVED_PACKET = "docs/ops/ATLAS-CURRENT-STATE-INTELLIGENCE-PACKET-2026-07-10.md";
const OWNER_PREFIX = "repos/_stack/";
const EXCLUDED_REASON = "newer_finding_outside_historical_denominator";
const OWNER_COMMIT = /^[0-9a-f]{7,64}$/;

function hash(value) {
  return createHash("sha256").update(JSON.stringify(value)).digest("hex");
}

function fingerprintFromEvidence(evidence) {
  return hash({
    category: evidence.category,
    path: evidence.path,
    line_number: evidence.line_number,
    message: evidence.message,
    line_preview_sha256: evidence.line_preview_sha256,
  });
}

function error(errors, message) {
  errors.push(message);
}

function parseArgs(argv) {
  const options = { json: false };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--json") {
      options.json = true;
      continue;
    }
    if (!["--registry", "--receipt", "--phase"].includes(token) || !argv[index + 1]) {
      throw new Error(`invalid argument: ${token}`);
    }
    const key = token.slice(2);
    if (options[key]) throw new Error(`duplicate argument: ${token}`);
    options[key] = argv[index + 1];
    index += 1;
  }
  if (!options.registry || !options.receipt || !["initial", "final"].includes(options.phase)) {
    throw new Error("usage: node ops/atlas/validate_root_path_hygiene_disposition.mjs --registry <file> --receipt <file> --phase initial|final [--json]");
  }
  return options;
}

function loadJson(path, label) {
  try {
    return JSON.parse(readFileSync(path, "utf8"));
  } catch (cause) {
    throw new Error(`${label} is unreadable JSON: ${cause.message}`);
  }
}

function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function validateRow(row, errors, label, target) {
  if (!isObject(row)) return error(errors, `${label} must be an object`);
  for (const field of ["fingerprint", "category", "path", "line_number", "message", "line_preview_sha256"]) {
    if (!(field in row)) error(errors, `${label} is missing ${field}`);
  }
  if (typeof row.fingerprint !== "string" || !/^[0-9a-f]{64}$/.test(row.fingerprint)) error(errors, `${label} has invalid fingerprint`);
  if (row.category !== CATEGORY) error(errors, `${label} has wrong category`);
  if (typeof row.path !== "string" || row.path.startsWith("/") || /^[A-Za-z]:[\\/]/.test(row.path)) error(errors, `${label} has invalid root-relative path`);
  if (!Number.isInteger(row.line_number) || row.line_number < 1) error(errors, `${label} has invalid line_number`);
  if (typeof row.message !== "string" || row.message.length === 0) error(errors, `${label} has invalid message`);
  if (typeof row.line_preview_sha256 !== "string" || !/^[0-9a-f]{64}$/.test(row.line_preview_sha256)) error(errors, `${label} has invalid line_preview_sha256`);
  if (typeof row.fingerprint === "string" && typeof row.category === "string" && typeof row.path === "string" && Number.isInteger(row.line_number) && typeof row.message === "string" && typeof row.line_preview_sha256 === "string" && row.fingerprint !== fingerprintFromEvidence(row)) {
    error(errors, `${label} fingerprint does not match its evidence`);
  }
  if (target) {
    if (!["preserved_historical", "owner_remediation"].includes(row.row_class)) error(errors, `${label} has invalid row_class`);
    if (typeof row.accepted !== "boolean") error(errors, `${label} has invalid accepted flag`);
    if (typeof row.disposition !== "string") error(errors, `${label} has invalid disposition`);
  } else if (row.reason !== EXCLUDED_REASON) {
    error(errors, `${label} must use ${EXCLUDED_REASON}`);
  }
}

function receiptRows(receipt, errors) {
  if (!isObject(receipt) || !Array.isArray(receipt.findings)) {
    error(errors, "receipt.findings must be an array");
    return [];
  }
  const rows = [];
  receipt.findings.forEach((finding, index) => {
    if (!isObject(finding) || finding.category !== CATEGORY) return;
    const details = finding.details;
    if (!isObject(details) || !Number.isInteger(details.line_number) || typeof details.line_preview !== "string" || typeof finding.path !== "string" || typeof finding.message !== "string") {
      error(errors, `receipt finding ${index} has malformed warning evidence`);
      return;
    }
    const evidence = {
      category: finding.category,
      path: finding.path,
      line_number: details.line_number,
      message: finding.message,
      line_preview_sha256: hash(details.line_preview),
    };
    rows.push({ ...evidence, fingerprint: fingerprintFromEvidence(evidence) });
  });
  return rows;
}

function duplicateFingerprints(rows, errors, label) {
  const seen = new Set();
  for (const row of rows) {
    if (seen.has(row.fingerprint)) error(errors, `${label} contains duplicate fingerprint ${row.fingerprint}`);
    seen.add(row.fingerprint);
  }
}

function compareSets(actual, expected, errors, label) {
  for (const fingerprint of expected) if (!actual.has(fingerprint)) error(errors, `${label} missing ${fingerprint}`);
  for (const fingerprint of actual) if (!expected.has(fingerprint)) error(errors, `${label} has unexpected ${fingerprint}`);
}

export function validateRegistryAndReceipt(registry, receipt, phase) {
  const errors = [];
  if (!isObject(registry)) error(errors, "registry must be an object");
  if (registry?.schema_version !== SCHEMA_VERSION) error(errors, `schema_version must be ${SCHEMA_VERSION}`);
  if (!isObject(registry?.lane) || registry.lane.id !== "root-path-hygiene" || registry.lane.plan_id !== "plan-07dfe809d062b89cafde" || registry.lane.cortex_packet_id !== "root-path-hygiene-cortex-bridge-v1") error(errors, "registry lane identity is invalid");
  if (registry?.lane?.historical_denominator !== 25) error(errors, "historical denominator must be 25");
  if (!isObject(registry?.evidence_contract) || registry.evidence_contract.category !== CATEGORY || registry.evidence_contract.fingerprint_algorithm !== "sha256-json-v1" || registry.evidence_contract.preserved_packet !== PRESERVED_PACKET) error(errors, "evidence contract is invalid");
  const targets = Array.isArray(registry?.target_rows) ? registry.target_rows : (error(errors, "target_rows must be an array"), []);
  const excluded = Array.isArray(registry?.excluded_newer_rows) ? registry.excluded_newer_rows : (error(errors, "excluded_newer_rows must be an array"), []);
  targets.forEach((row, index) => validateRow(row, errors, `target_rows[${index}]`, true));
  excluded.forEach((row, index) => validateRow(row, errors, `excluded_newer_rows[${index}]`, false));
  duplicateFingerprints(targets, errors, "target_rows");
  duplicateFingerprints(excluded, errors, "excluded_newer_rows");
  const targetSet = new Set(targets.map((row) => row.fingerprint));
  for (const row of excluded) if (targetSet.has(row.fingerprint)) error(errors, `excluded row duplicates target ${row.fingerprint}`);
  if (targets.length !== 25) error(errors, "target_rows must contain exactly 25 rows");
  if (excluded.length !== 3) error(errors, "excluded_newer_rows must contain exactly 3 rows");
  const preserved = targets.filter((row) => row.row_class === "preserved_historical");
  const owners = targets.filter((row) => row.row_class === "owner_remediation");
  if (preserved.length !== 16 || owners.length !== 9) error(errors, "target row split must be 16 preserved and 9 owner rows");
  for (const row of preserved) {
    if (row.path !== PRESERVED_PACKET || row.disposition !== "accepted_preserve_historical" || row.accepted !== true) error(errors, `preserved row ${row.fingerprint} has wrong evidence or disposition`);
  }
  for (const row of owners) {
    if (!row.path.startsWith(OWNER_PREFIX) || row.owner !== "_stack") error(errors, `owner row ${row.fingerprint} has wrong owner evidence`);
    if (phase === "initial" && (row.disposition !== "pending_owner_remediation" || row.accepted !== false || "remediation" in row)) error(errors, `initial owner row ${row.fingerprint} must be pending and unaccepted`);
    if (phase === "final" && (row.disposition !== "accepted_owner_remediation" || row.accepted !== true || !isObject(row.remediation) || row.remediation.owner_repository !== "_stack" || !OWNER_COMMIT.test(row.remediation.owner_commit ?? ""))) error(errors, `final owner row ${row.fingerprint} must be accepted with owner commit evidence`);
  }
  const actualRows = receiptRows(receipt, errors);
  duplicateFingerprints(actualRows, errors, "receipt warnings");
  const actualSet = new Set(actualRows.map((row) => row.fingerprint));
  const preservedSet = new Set(preserved.map((row) => row.fingerprint));
  const ownerSet = new Set(owners.map((row) => row.fingerprint));
  const excludedSet = new Set(excluded.map((row) => row.fingerprint));
  const expectedPresent = new Set([...preservedSet, ...excludedSet, ...(phase === "initial" ? ownerSet : [])]);
  compareSets(actualSet, expectedPresent, errors, `${phase} receipt warnings`);
  const accepted = targets.filter((row) => row.accepted === true).length;
  const pending = targets.filter((row) => row.accepted === false).length;
  const expectedCounts = phase === "initial"
    ? { current_warnings: 28, target: 25, accepted: 16, pending: 9, excluded_newer: 3, complete: false }
    : { current_warnings: 19, target: 25, accepted: 25, pending: 0, excluded_newer: 3, complete: true };
  const counts = registry?.counts;
  if (!isObject(counts)) error(errors, "counts must be an object");
  for (const [key, value] of Object.entries(expectedCounts)) if (counts?.[key] !== value) error(errors, `counts.${key} must be ${value} for ${phase}`);
  if (counts?.current_warnings !== actualRows.length || counts?.accepted !== accepted || counts?.pending !== pending) error(errors, "counts do not match registry rows or receipt");
  return { ok: errors.length === 0, phase, errors, summary: { current_warnings: actualRows.length, target_rows: targets.length, accepted, pending, excluded_newer: excluded.length, complete: counts?.complete === true } };
}

function main() {
  let options;
  try {
    options = parseArgs(process.argv.slice(2));
    const result = validateRegistryAndReceipt(loadJson(options.registry, "registry"), loadJson(options.receipt, "receipt"), options.phase);
    if (options.json) console.log(JSON.stringify(result));
    else console.log(result.ok ? `root-path-hygiene ${options.phase} validation passed` : `root-path-hygiene ${options.phase} validation failed:\n- ${result.errors.join("\n- ")}`);
    process.exitCode = result.ok ? 0 : 1;
  } catch (cause) {
    const result = { ok: false, phase: options?.phase ?? null, errors: [cause.message] };
    if (options?.json || process.argv.includes("--json")) console.log(JSON.stringify(result));
    else console.error(`root-path-hygiene validation failed: ${cause.message}`);
    process.exitCode = 1;
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) main();
