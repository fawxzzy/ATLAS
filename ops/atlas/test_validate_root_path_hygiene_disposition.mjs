#!/usr/bin/env node
import { createHash } from "node:crypto";
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { spawnSync } from "node:child_process";

const root = resolve(new URL("../..", import.meta.url).pathname.slice(process.platform === "win32" ? 1 : 0));
const validator = join(root, "ops/atlas/validate_root_path_hygiene_disposition.mjs");
const registryPath = join(root, "docs/registry/ROOT-PATH-HYGIENE-DISPOSITION.v1.json");
const receiptPath = join(root, "runtime/receipts/validation/stack-validation.latest.json");
const clone = (value) => JSON.parse(JSON.stringify(value));
const readJson = (path) => JSON.parse(readFileSync(path, "utf8"));
const hash = (value) => createHash("sha256").update(JSON.stringify(value)).digest("hex");
const fingerprint = (row) => hash({ category: row.category, path: row.path, line_number: row.line_number, message: row.message, line_preview_sha256: row.line_preview_sha256 });

function writeFixture(directory, name, registry, receipt) {
  const fixtureRegistry = join(directory, `${name}.registry.json`);
  const fixtureReceipt = join(directory, `${name}.receipt.json`);
  writeFileSync(fixtureRegistry, `${JSON.stringify(registry, null, 2)}\n`, "utf8");
  writeFileSync(fixtureReceipt, `${JSON.stringify(receipt, null, 2)}\n`, "utf8");
  return { fixtureRegistry, fixtureReceipt };
}

function run(name, registry, receipt, phase, expectedOk, directory) {
  const { fixtureRegistry, fixtureReceipt } = writeFixture(directory, name, registry, receipt);
  const result = spawnSync(process.execPath, [validator, "--registry", fixtureRegistry, "--receipt", fixtureReceipt, "--phase", phase, "--json"], { encoding: "utf8" });
  const payload = JSON.parse(result.stdout);
  if ((result.status === 0) !== expectedOk || payload.ok !== expectedOk) {
    throw new Error(`${name}: expected ok=${expectedOk}, got status=${result.status}, output=${result.stdout}${result.stderr}`);
  }
  return payload;
}

function finalFixture(registry, receipt) {
  const nextRegistry = clone(registry);
  const nextReceipt = clone(receipt);
  nextReceipt.findings = nextReceipt.findings.filter((finding) => !finding.path.startsWith("repos/_stack/"));
  for (const row of nextRegistry.target_rows.filter((row) => row.row_class === "owner_remediation")) {
    row.disposition = "accepted_owner_remediation";
    row.accepted = true;
    row.remediation = { owner_repository: "_stack", owner_commit: "bb1eabe3980f248cccc4b50fb242d9f3fba1954f" };
  }
  nextRegistry.counts = { current_warnings: 19, target: 25, accepted: 25, pending: 0, excluded_newer: 3, complete: true };
  return { registry: nextRegistry, receipt: nextReceipt };
}

const directory = mkdtempSync(join(tmpdir(), "atlas-root-path-hygiene-"));
try {
  if (!existsSync(validator) || !existsSync(registryPath) || !existsSync(receiptPath)) throw new Error("real validator, registry, or receipt is missing");
  const registry = readJson(registryPath);
  const receipt = readJson(receiptPath);
  const livePhase = registry.counts?.complete === true ? "final" : "initial";
  run(`real-${livePhase}`, registry, receipt, livePhase, true, directory);
  const final = livePhase === "final"
    ? { registry: clone(registry), receipt: clone(receipt) }
    : finalFixture(registry, receipt);
  run("valid-final", final.registry, final.receipt, "final", true, directory);

  const duplicate = clone(registry);
  duplicate.target_rows.push(clone(duplicate.target_rows[0]));
  run("duplicate", duplicate, receipt, livePhase, false, directory);

  const missing = clone(registry);
  missing.target_rows.pop();
  run("missing", missing, receipt, livePhase, false, directory);

  const extra = clone(registry);
  const extraRow = { category: "atlas-root-path", path: "docs/ops/EXTRA.md", line_number: 1, message: "Absolute path leak detected in committed text.", line_preview_sha256: hash("synthetic extra") };
  extraRow.fingerprint = fingerprint(extraRow);
  extraRow.row_class = "preserved_historical";
  extraRow.disposition = "accepted_preserve_historical";
  extraRow.accepted = true;
  extra.target_rows.push(extraRow);
  run("extra", extra, receipt, livePhase, false, directory);

  const denominator = clone(registry);
  denominator.lane.historical_denominator = 24;
  run("denominator", denominator, receipt, livePhase, false, directory);

  const disposition = clone(registry);
  const dispositionOwner = disposition.target_rows.find((row) => row.row_class === "owner_remediation");
  if (livePhase === "initial") {
    dispositionOwner.disposition = "accepted_owner_remediation";
    dispositionOwner.accepted = true;
    dispositionOwner.remediation = { owner_repository: "_stack", owner_commit: "bb1eabe3980f248cccc4b50fb242d9f3fba1954f" };
  } else {
    dispositionOwner.disposition = "pending_owner_remediation";
    dispositionOwner.accepted = false;
    delete dispositionOwner.remediation;
  }
  run("disposition", disposition, receipt, livePhase, false, directory);

  const unexpected = clone(receipt);
  unexpected.findings.push({ severity: "warning", category: "atlas-root-path", path: "docs/ops/UNEXPECTED.md", message: "Absolute path leak detected in committed text.", details: { line_number: 1, line_preview: "synthetic unexpected warning" } });
  run("unexpected-warning", registry, unexpected, livePhase, false, directory);
  console.log(`root path hygiene validator fixtures passed: real ${livePhase}, valid final, duplicate, missing, extra, denominator, disposition, unexpected-warning`);
} finally {
  rmSync(directory, { recursive: true, force: true });
}
