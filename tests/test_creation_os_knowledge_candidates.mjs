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
  normalizeSourceBytes,
  projectionDigest,
  writeProjection,
} from "../ops/atlas/creation_os_knowledge_candidates.mjs";

test("normalizes source bytes to the canonical LF Git contract", () => {
  const lf = normalizeSourceBytes(Buffer.from("first\nsecond\n", "utf8"));
  const crlf = normalizeSourceBytes(Buffer.from("first\r\nsecond\r\n", "utf8"));
  assert.deepEqual(crlf, lf);
  assert.throws(
    () => normalizeSourceBytes(Buffer.from("first\rsecond\n", "utf8")),
    /unsupported lone CR line ending/,
  );
});

test("workflow cannot skip direct or transitive Creation OS validation inputs", async () => {
  const workflow = await fs.readFile(
    path.join(ROOT, ".github/workflows/creation-os-knowledge-candidates.yml"),
    "utf8",
  );
  assert.match(workflow, /^  pull_request:\r?$/m);
  assert.doesNotMatch(
    workflow,
    /^    paths(?:-ignore)?:/m,
    "Creation OS validation must run for every PR because it follows transitive evidence links",
  );
});

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

test("binds reproducible provenance to the corrected packet while preserving creation time", async () => {
  const projection = await buildProjection();
  const firstCommit = "2407b0e656775d040099e5618eb194c5c06ee0e7";
  const correctedRevision = "c376810ec75066fb6b21d950f56fcdf986421889";
  const packetPrefix = `git:fawxzzy/ATLAS@${correctedRevision}:${SOURCE_PACKET_REF}#`;

  assert.equal(projection.manifest.source.packet_first_commit, firstCommit);
  assert.equal(projection.manifest.source.packet_first_commit_at, "2026-07-16T06:31:44Z");
  assert.equal(projection.manifest.source.corrected_packet_revision, correctedRevision);
  assert.equal(
    projection.manifest.source.packet_sha256,
    "sha256:e2946fcc95f2b1aa5d871767446e97a0e69da6c66d72c90e53855313c4cf2ca2",
  );
  for (const candidate of projection.candidates) {
    assert.equal(candidate.created_at, "2026-07-16T06:31:44Z");
    assert.equal(candidate.provenance[0].ref, `${packetPrefix}${candidate.candidate_id}`);
    assert.equal(candidate.extensions.atlas_projection.source_packet_first_commit, firstCommit);
    assert.equal(
      candidate.extensions.atlas_projection.source_packet_corrected_revision,
      correctedRevision,
    );
    assert.doesNotMatch(candidate.provenance[0].ref, new RegExp(`@${firstCommit}:`));
  }

  const decision = projection.manifest.records.find(
    (record) => record.record_id === "creation-os-software-repo-voice-first-wedge",
  );
  assert.equal(decision.provenance[0].ref, `${packetPrefix}${decision.record_id}`);
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

  const traversal = `${ARTIFACT_ROOT_REF}/../../../repos/playbook/forbidden.json`;
  const traversalOutputs = new Map(projection.outputs);
  traversalOutputs.set(traversal, Buffer.from("{}\n", "utf8"));
  await assert.rejects(
    () => assertProjectionInvariants({ ...projection, outputs: traversalOutputs }),
    /projection output is not a portable relative path/,
  );
  await assert.rejects(
    () => writeProjection({ outputs: new Map([[traversal, Buffer.from("{}\n", "utf8")]]) }),
    /projection output is not a portable relative path/,
  );
});
