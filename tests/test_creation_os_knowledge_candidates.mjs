import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import test from "node:test";

import {
  ARTIFACT_ROOT_REF,
  ROOT,
  SOURCE_PACKET_REF,
  assertProjectionInvariants,
  assertSourcePacket,
  buildProjection,
  checkProjection,
  projectionDigest,
} from "../ops/atlas/creation_os_knowledge_candidates.mjs";

test("generates six schema-valid candidates and one manifest-only Decision byte-stably", async () => {
  const first = await buildProjection();
  const second = await buildProjection();
  assert.equal(first.candidates.length, 6);
  assert.equal(first.manifest.records.length, 7);
  assert.equal(projectionDigest(first), projectionDigest(second));
  const result = await checkProjection(first);
  assert.equal(result.byte_stable, true);
  assert.equal(result.owner_repository_outputs, 0);
  assert.equal(result.candidate_count, 6);

  const decision = first.manifest.records.find(
    (record) => record.record_id === "creation-os-software-repo-voice-first-wedge",
  );
  assert.equal(decision.kind, "decision");
  assert.equal(decision.contract_eligible, false);
  assert.equal(decision.artifact_path, null);
  assert.equal(decision.artifact_sha256, null);
});

test("fails closed when a source statement changes", async () => {
  const source = await fs.readFile(path.join(ROOT, SOURCE_PACKET_REF), "utf8");
  const changed = source.replace(
    "Atlas remains human-directed; autonomy does not imply external or",
    "Atlas remains human-directed; autonomy now implies external or",
  );
  assert.notEqual(changed, source);
  assert.throws(
    () => assertSourcePacket(changed),
    /statement drifted from its locked source text/,
  );
});

test("fails closed when source evidence changes", async () => {
  const source = await fs.readFile(path.join(ROOT, SOURCE_PACKET_REF), "utf8");
  const changed = source.replace(
    "../architecture/ATLAS-CONTRACTS-V2-SCOPE.md#authority-boundaries",
    "../architecture/ATLAS-CONTRACTS-V2-SCOPE.md#drifted-boundary",
  );
  assert.notEqual(changed, source);
  assert.throws(
    () => assertSourcePacket(changed),
    /evidence references drifted from the source packet/,
  );
});

test("fails closed on unsupported kind and destination mapping", async () => {
  const projection = await buildProjection();
  const candidates = structuredClone(projection.candidates);
  candidates[0].suggested_destination = "Playbook/patterns";
  await assert.rejects(
    () => assertProjectionInvariants({ ...projection, candidates }),
    /unsupported kind\/destination mapping/,
  );
});

test("fails closed on filename, manifest hash, and Decision artifact drift", async () => {
  const projection = await buildProjection();
  const outputs = new Map(projection.outputs);
  outputs.delete(
    `${ARTIFACT_ROOT_REF}/creation-os-human-directed-authority.knowledge-candidate.v2.json`,
  );
  const manifest = structuredClone(projection.manifest);
  manifest.records[0].artifact_sha256 = "sha256:tampered";
  const decision = manifest.records.find(
    (record) => record.record_id === "creation-os-software-repo-voice-first-wedge",
  );
  decision.artifact_path = `${ARTIFACT_ROOT_REF}/${decision.record_id}.knowledge-candidate.v2.json`;
  decision.artifact_sha256 = "sha256:tampered";
  outputs.set(decision.artifact_path, Buffer.from("{}\n", "utf8"));

  await assert.rejects(
    () => assertProjectionInvariants({ ...projection, manifest, outputs }),
    (error) => error.errors.some((message) => message.includes("filename/path contract drifted"))
      && error.errors.some((message) => message.includes("artifact hash drifted"))
      && error.errors.some((message) => message.includes("manifest-only")),
  );
});

test("rejects any owner-repository output target", async () => {
  const projection = await buildProjection();
  const outputs = new Map(projection.outputs);
  outputs.set("repos/playbook/forbidden.json", Buffer.from("{}\n", "utf8"));
  await assert.rejects(
    () => assertProjectionInvariants({ ...projection, outputs }),
    /projection output escapes the root-owned boundary/,
  );
});
