import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const scriptsDir = path.dirname(fileURLToPath(import.meta.url));
const packageRoot = path.resolve(scriptsDir, "..");
const cliPath = path.join(scriptsDir, "validate-artifact.mjs");
const fixture = (...parts) => path.join(packageRoot, "fixtures", ...parts);

function invoke(args) {
  const child = spawnSync(process.execPath, [cliPath, ...args], {
    cwd: packageRoot,
    encoding: "utf8",
  });
  return {
    status: child.status,
    output: child.stdout.trim(),
    error: child.stderr.trim(),
  };
}

function expectJson(args, expectedStatus, expectedCode) {
  const outcome = invoke([...args, "--json"]);
  assert.equal(outcome.status, expectedStatus, outcome.error);
  const result = JSON.parse(outcome.output);
  assert.equal(result.code, expectedCode);
  assert.equal(result.ok, expectedStatus === 0);
  assert.ok(Array.isArray(result.errors));
  return result;
}

const temporaryDir = await fs.mkdtemp(path.join(os.tmpdir(), "atlas-contracts-validator-"));
try {
  const malformedArtifact = path.join(temporaryDir, "malformed.json");
  await fs.writeFile(malformedArtifact, '{"contract_version":', "utf8");

  const validV1 = expectJson(
    ["--schema", "atlas.env.v1", "--artifact", fixture("valid", "env.json")],
    0,
    "VALID",
  );
  assert.deepEqual(validV1.schema, {
    id: "atlas.env.v1",
    file: "schemas/atlas.env.v1.schema.json",
  });

  expectJson(
    ["--schema", "schemas/atlas.component-manifest.v2.schema.json", "--artifact", fixture("valid", "component-manifest.v2.json")],
    0,
    "VALID",
  );
  expectJson(
    ["--schema", "atlas.env.v1", "--artifact", fixture("invalid", "env.missing-required.json")],
    1,
    "INVALID_ARTIFACT",
  );
  expectJson(
    ["--schema", "atlas.component-manifest.v2", "--artifact", fixture("invalid", "component-manifest.v2.bad-authority.json")],
    1,
    "INVALID_ARTIFACT",
  );
  expectJson(
    ["--schema", "atlas.github.event-receipt.v1", "--artifact", fixture("valid", "github.event-receipt.v1.json")],
    0,
    "VALID",
  );
  expectJson(
    ["--schema", "schemas/atlas.github.event-admission.v1.schema.json", "--artifact", fixture("valid", "github.event-admission.v1.json")],
    0,
    "VALID",
  );
  expectJson(
    ["--schema", "atlas.github.projection-intent.v1", "--artifact", fixture("valid", "github.projection-intent.v1.json")],
    0,
    "VALID",
  );
  expectJson(
    ["--schema", "atlas.project-board.owner-export.v1", "--artifact", fixture("valid", "project-board.owner-export.v1.json")],
    0,
    "VALID",
  );
  const semanticFailure = expectJson(
    ["--schema", "atlas.project-board.owner-export.v1", "--artifact", fixture("invalid", "project-board.owner-export.v1.semantic-conflict.json")],
    1,
    "INVALID_ARTIFACT",
  );
  assert(semanticFailure.errors.some((error) => error.includes("ATLAS-relative portable path")));
  assert(semanticFailure.errors.some((error) => error.includes("acceptance_criteria")));
  expectJson(
    ["--schema", "atlas.github.event-receipt.v1", "--artifact", fixture("invalid", "github.event-receipt.v1.bad-authority.json")],
    1,
    "INVALID_ARTIFACT",
  );
  expectJson(
    ["--schema", "atlas.github.event-admission.v1", "--artifact", fixture("invalid", "github.event-admission.v1.bad-decision.json")],
    1,
    "INVALID_ARTIFACT",
  );
  expectJson(
    ["--schema", "atlas.github.projection-intent.v1", "--artifact", fixture("invalid", "github.projection-intent.v1.bad-external-mutation.json")],
    1,
    "INVALID_ARTIFACT",
  );
  expectJson(
    ["--schema", "atlas.env.v3", "--artifact", fixture("valid", "env.json")],
    2,
    "UNSUPPORTED_CONTRACT_VERSION",
  );
  expectJson(
    ["--schema", "atlas.unknown.v1", "--artifact", fixture("valid", "env.json")],
    2,
    "UNKNOWN_SCHEMA",
  );
  expectJson(
    ["--schema", "atlas.env.v1", "--artifact", malformedArtifact],
    3,
    "MALFORMED_JSON",
  );
  expectJson([], 4, "MISSING_INPUT");
  expectJson(
    ["--schema", "schemas/../schemas/atlas.env.v1.schema.json", "--artifact", fixture("valid", "env.json")],
    2,
    "INVALID_SCHEMA_REFERENCE",
  );

  console.log("ATLAS artifact validator tests passed.");
} finally {
  await fs.rm(temporaryDir, { recursive: true, force: true });
}
