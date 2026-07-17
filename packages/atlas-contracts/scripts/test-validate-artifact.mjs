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
  const emptyArtifact = path.join(temporaryDir, "empty.json");
  await fs.writeFile(emptyArtifact, "{}\n", "utf8");

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
  const projectionDeliveryFixture = fixture("valid", "projection-delivery.v1.json");
  const emptyProjection = expectJson(
    ["--schema", "atlas.projection-delivery.v1", "--artifact", emptyArtifact],
    1,
    "INVALID_ARTIFACT",
  );
  assert(emptyProjection.errors.some((error) => error.includes("is required")));
  const emptyAck = expectJson(
    [
      "--schema", "atlas.projection-ack.v1",
      "--artifact", emptyArtifact,
      "--projection-delivery", projectionDeliveryFixture,
    ],
    1,
    "INVALID_ARTIFACT",
  );
  assert(emptyAck.errors.some((error) => error.includes("is required")));
  const shortCircuitedEmptyAck = expectJson(
    [
      "--schema", "atlas.projection-ack.v1",
      "--artifact", emptyArtifact,
      "--projection-delivery", path.join(temporaryDir, "must-not-be-read.json"),
    ],
    1,
    "INVALID_ARTIFACT",
  );
  assert(shortCircuitedEmptyAck.errors.some((error) => error.includes("is required")));
  assert(shortCircuitedEmptyAck.errors.every((error) => !error.includes("ProjectionDelivery")));
  const missingDeliveryContext = expectJson(
    ["--schema", "atlas.projection-ack.v1", "--artifact", fixture("valid", "projection-ack.v1.json")],
    1,
    "INVALID_ARTIFACT",
  );
  assert(missingDeliveryContext.errors.some((error) => error.includes("requires --projection-delivery")));
  expectJson(
    [
      "--schema=atlas.projection-ack.v1",
      `--artifact=${fixture("valid", "projection-ack.v1.json")}`,
      `--projection-delivery=${projectionDeliveryFixture}`,
    ],
    0,
    "VALID",
  );
  const mismatchedDeliveryContext = expectJson(
    [
      "--schema", "atlas.projection-ack.v1",
      "--artifact", fixture("invalid", "projection-ack.v1.mismatched-delivery.json"),
      "--projection-delivery", projectionDeliveryFixture,
    ],
    1,
    "INVALID_ARTIFACT",
  );
  assert(mismatchedDeliveryContext.errors.some((error) => error.includes("payload_digest")));
  expectJson(
    [
      "--schema", "atlas.card-event.v3",
      "--artifact", fixture("invalid", "card-event.v3.invalid-transition-target.json"),
    ],
    1,
    "INVALID_ARTIFACT",
  );
  const nullTransitionFrom = expectJson(
    [
      "--schema", "atlas.card-event.v3",
      "--artifact", fixture("invalid", "card-event.v3.null-transition-from.json"),
    ],
    1,
    "INVALID_ARTIFACT",
  );
  assert(nullTransitionFrom.errors.some((error) => error.includes("Non-initial transitions require")));
  const ambiguousOperations = expectJson(
    [
      "--schema", "atlas.card-event.v3",
      "--artifact", fixture("invalid", "card-event.v3.ambiguous-operations.json"),
    ],
    1,
    "INVALID_ARTIFACT",
  );
  assert(ambiguousOperations.errors.some((error) => error.includes("duplicate blocker_id")));
  for (const [fixtureName, expectedError] of [
    ["card-event.v3.invalid-initial-materialization.json", "Stable standing anchors"],
    ["card-event.v3.invalid-update-materialization.json", "archive_state archived must move together"],
    ["card-event.v3.archive-entry-missing-state.json", "crossing the archived boundary"],
    ["card-event.v3.archive-entry-missing-standing-anchor.json", "explicit $.changes.set.standing_anchor false"],
    ["card-event.v3.archive-exit-missing-state.json", "crossing the archived boundary"],
    ["card-event.v3.execution-receipt-digest-mismatch.json", "identity and digest"],
  ]) {
    const invalidMaterialization = expectJson(
      [
        "--schema", "atlas.card-event.v3",
        "--artifact", fixture("invalid", fixtureName),
      ],
      1,
      "INVALID_ARTIFACT",
    );
    assert(invalidMaterialization.errors.some((error) => error.includes(expectedError)));
  }
  for (const fixtureName of [
    "card-event.v3.initial-standing-anchor.json",
    "card-event.v3.archive-materialization.json",
    "card-event.v3.archive-exit-materialization.json",
    "card-event.v3.partial-archive-state.json",
  ]) {
    expectJson(
      ["--schema", "atlas.card-event.v3", "--artifact", fixture("valid", fixtureName)],
      0,
      "VALID",
    );
  }
  const unknownProjectionConflict = expectJson(
    [
      "--schema", "atlas.projection-delivery.v1",
      "--artifact", fixture("invalid", "projection-delivery.v1.available-unknown-conflict.json"),
    ],
    1,
    "INVALID_ARTIFACT",
  );
  assert(unknownProjectionConflict.errors.some((error) => error.includes("Available UNKNOWN projection")));
  const appliedDeliveryRetry = expectJson(
    [
      "--schema", "atlas.projection-delivery.v1",
      "--artifact", fixture("invalid", "projection-delivery.v1.applied-retry.json"),
    ],
    1,
    "INVALID_ARTIFACT",
  );
  assert(appliedDeliveryRetry.errors.some((error) => error.includes("must be non-retryable")));
  for (const fixtureName of [
    "projection-delivery.v1.applied-zero-attempt.json",
    "projection-delivery.v1.stale-zero-attempt.json",
    "projection-delivery.v1.failed-zero-attempt.json",
    "projection-delivery.v1.available-unknown-zero-attempt.json",
  ]) {
    const zeroAttempt = expectJson(
      ["--schema", "atlas.projection-delivery.v1", "--artifact", fixture("invalid", fixtureName)],
      1,
      "INVALID_ARTIFACT",
    );
    assert(zeroAttempt.errors.some((error) => error.includes("positive attempt_count")));
  }
  expectJson(
    [
      "--schema", "atlas.projection-delivery.v1",
      "--artifact", fixture("valid", "projection-delivery.v1.unavailable-unknown-zero-attempt.json"),
    ],
    0,
    "VALID",
  );
  const unavailableMissingError = expectJson(
    [
      "--schema", "atlas.projection-delivery.v1",
      "--artifact", fixture("invalid", "projection-delivery.v1.unavailable-unknown-missing-error.json"),
    ],
    1,
    "INVALID_ARTIFACT",
  );
  assert(unavailableMissingError.errors.some((error) => error.includes("availability error evidence")));
  const appliedAckRetry = expectJson(
    [
      "--schema", "atlas.projection-ack.v1",
      "--artifact", fixture("invalid", "projection-ack.v1.applied-retry.json"),
      "--projection-delivery", projectionDeliveryFixture,
    ],
    1,
    "INVALID_ARTIFACT",
  );
  assert(appliedAckRetry.errors.some((error) => error.includes("must be non-retryable")));
  const appliedAckZeroAttempt = expectJson(
    [
      "--schema", "atlas.projection-ack.v1",
      "--artifact", fixture("invalid", "projection-ack.v1.applied-zero-attempt.json"),
      "--projection-delivery", projectionDeliveryFixture,
    ],
    1,
    "INVALID_ARTIFACT",
  );
  assert(appliedAckZeroAttempt.errors.some((error) => error.includes("attempt_count")));
  const unavailableAckMissingError = expectJson(
    [
      "--schema", "atlas.projection-ack.v1",
      "--artifact", fixture("invalid", "projection-ack.v1.unavailable-unknown-missing-error.json"),
      "--projection-delivery", projectionDeliveryFixture,
    ],
    1,
    "INVALID_ARTIFACT",
  );
  assert(unavailableAckMissingError.errors.some((error) => error.includes("availability error evidence")));
  expectJson(
    [
      "--schema", "atlas.projection-ack.v1",
      "--artifact", fixture("valid", "projection-ack.v1.unavailable-unknown.json"),
      "--projection-delivery", projectionDeliveryFixture,
    ],
    0,
    "VALID",
  );
  const malformedTerminalReceipt = expectJson(
    [
      "--schema", "atlas.rollover-manifest.v1",
      "--artifact", fixture("invalid", "rollover-manifest.v1.malformed-terminal-receipt.json"),
    ],
    1,
    "INVALID_ARTIFACT",
  );
  assert(malformedTerminalReceipt.errors.some((error) => error.includes("must satisfy exactly one allowed shape")));
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
  const rootExportPath = path.resolve(
    packageRoot,
    "..",
    "..",
    "docs",
    "registry",
    "project-board-owner-exports",
    "atlas.project-board.owner-export.v1.json",
  );
  const rootExport = JSON.parse(await fs.readFile(rootExportPath, "utf8"));
  const writeTamperedExport = async (name, mutate) => {
    const artifact = structuredClone(rootExport);
    mutate(artifact);
    const artifactPath = path.join(temporaryDir, name);
    await fs.writeFile(artifactPath, `${JSON.stringify(artifact, null, 2)}\n`, "utf8");
    return artifactPath;
  };

  const truncatedMarkerPath = await writeTamperedExport("owner-export.truncated-marker.json", (artifact) => {
    artifact.runtime_readback.marker_lanes[0].units.pop();
  });
  const truncatedMarkerFailure = expectJson(
    ["--schema", "atlas.project-board.owner-export.v1", "--artifact", truncatedMarkerPath],
    1,
    "INVALID_ARTIFACT",
  );
  assert(
    truncatedMarkerFailure.errors.some((error) => error.includes("units length must equal the fixed denominator")),
  );

  const renamedMarkerPath = await writeTamperedExport("owner-export.renamed-markers.json", (artifact) => {
    artifact.runtime_readback.marker_lanes.forEach((marker, markerIndex) => {
      marker.id = `renamed-marker-${markerIndex}`;
      marker.units.forEach((unit, unitIndex) => {
        unit.id = `renamed-unit-${markerIndex}-${unitIndex}`;
      });
    });
  });
  const renamedMarkerFailure = expectJson(
    ["--schema", "atlas.project-board.owner-export.v1", "--artifact", renamedMarkerPath],
    1,
    "INVALID_ARTIFACT",
  );
  assert(
    renamedMarkerFailure.errors.some((error) => error.includes("exact frozen marker and ordered unit identities")),
  );

  const clearedUnknownPath = await writeTamperedExport("owner-export.cleared-unknown.json", (artifact) => {
    artifact.runtime_readback.status_boundaries.unknown = [];
  });
  const clearedUnknownFailure = expectJson(
    ["--schema", "atlas.project-board.owner-export.v1", "--artifact", clearedUnknownPath],
    1,
    "INVALID_ARTIFACT",
  );
  assert(
    clearedUnknownFailure.errors.some((error) => error.includes("unknown must exactly match the runtime source projection")),
  );

  const inventedStalePath = await writeTamperedExport("owner-export.invented-stale.json", (artifact) => {
    artifact.runtime_readback.status_boundaries.stale = ["invented-stale-boundary"];
  });
  const inventedStaleFailure = expectJson(
    ["--schema", "atlas.project-board.owner-export.v1", "--artifact", inventedStalePath],
    1,
    "INVALID_ARTIFACT",
  );
  assert(
    inventedStaleFailure.errors.some((error) => error.includes("canonical empty stale boundary")),
  );

  const runtimeSourcePath = path.resolve(
    packageRoot,
    "..",
    "..",
    "docs",
    "registry",
    "ATLAS-RUNTIME-PLACEMENT-REGISTRY.v1.json",
  );
  const runtimeSourceText = await fs.readFile(runtimeSourcePath, "utf8");
  const runtimeSchemaPath = path.resolve(
    packageRoot,
    "..",
    "..",
    "schemas",
    "atlas.runtime-placement.registry.v1.json",
  );
  const runtimeSchemaText = await fs.readFile(runtimeSchemaPath, "utf8");
  const writeAtlasRootSentinels = async (root) => {
    await fs.mkdir(path.join(root, "schemas"), { recursive: true });
    await fs.writeFile(path.join(root, "stack.yaml"), "version: 1\n", "utf8");
    await fs.writeFile(
      path.join(root, "schemas", "atlas.runtime-placement.registry.v1.json"),
      runtimeSchemaText,
      "utf8",
    );
  };
  const escapeRoot = path.join(temporaryDir, "escape-root");
  const outsideDocs = path.join(temporaryDir, "outside-docs");
  await fs.mkdir(path.join(outsideDocs, "registry"), { recursive: true });
  await fs.writeFile(
    path.join(outsideDocs, "registry", "ATLAS-RUNTIME-PLACEMENT-REGISTRY.v1.json"),
    runtimeSourceText,
    "utf8",
  );
  await writeAtlasRootSentinels(escapeRoot);
  await fs.symlink(outsideDocs, path.join(escapeRoot, "docs"), process.platform === "win32" ? "junction" : "dir");
  const escapedArtifactPath = path.join(escapeRoot, "owner-export.json");
  await fs.writeFile(escapedArtifactPath, `${JSON.stringify(rootExport, null, 2)}\n`, "utf8");
  const escapedSourceFailure = expectJson(
    ["--schema", "atlas.project-board.owner-export.v1", "--artifact", escapedArtifactPath],
    1,
    "INVALID_ARTIFACT",
  );
  assert(
    escapedSourceFailure.errors.some((error) => error.includes("escapes a candidate root after realpath resolution")),
  );

  const ambiguousRoot = path.join(temporaryDir, "ambiguous-root");
  const ambiguousInner = path.join(ambiguousRoot, "inner");
  for (const candidateRoot of [ambiguousRoot, ambiguousInner]) {
    await writeAtlasRootSentinels(candidateRoot);
    const registryDir = path.join(candidateRoot, "docs", "registry");
    await fs.mkdir(registryDir, { recursive: true });
    await fs.writeFile(
      path.join(registryDir, "ATLAS-RUNTIME-PLACEMENT-REGISTRY.v1.json"),
      runtimeSourceText,
      "utf8",
    );
  }
  const ambiguousArtifactPath = path.join(ambiguousInner, "owner-export.json");
  await fs.writeFile(ambiguousArtifactPath, `${JSON.stringify(rootExport, null, 2)}\n`, "utf8");
  const ambiguousSourceFailure = expectJson(
    ["--schema", "atlas.project-board.owner-export.v1", "--artifact", ambiguousArtifactPath],
    1,
    "INVALID_ARTIFACT",
  );
  assert(
    ambiguousSourceFailure.errors.some((error) => error.includes("ambiguous across multiple contained roots")),
  );

  const unidentifiedRoot = path.join(temporaryDir, "unidentified-root");
  const unidentifiedArtifactDir = path.join(unidentifiedRoot, "workspace");
  await fs.mkdir(path.join(unidentifiedRoot, "tmp"), { recursive: true });
  await fs.mkdir(unidentifiedArtifactDir, { recursive: true });
  await fs.writeFile(path.join(unidentifiedRoot, "tmp", "runtime.json"), runtimeSourceText, "utf8");
  const unidentifiedArtifact = structuredClone(rootExport);
  const runtimeSource = unidentifiedArtifact.sources.find(
    (source) => source.source_id === "atlas-runtime-placement-registry",
  );
  runtimeSource.path = "tmp/runtime.json";
  unidentifiedArtifact.runtime_readback.source_ref = "tmp/runtime.json";
  const unidentifiedArtifactPath = path.join(unidentifiedArtifactDir, "owner-export.json");
  await fs.writeFile(unidentifiedArtifactPath, `${JSON.stringify(unidentifiedArtifact, null, 2)}\n`, "utf8");
  const unidentifiedRootFailure = expectJson(
    ["--schema", "atlas.project-board.owner-export.v1", "--artifact", unidentifiedArtifactPath],
    1,
    "INVALID_ARTIFACT",
  );
  assert(
    unidentifiedRootFailure.errors.some((error) => error.includes("could not be resolved from the artifact or working tree")),
  );
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
    ["--schema", "atlas.env.v4", "--artifact", fixture("valid", "env.json")],
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
