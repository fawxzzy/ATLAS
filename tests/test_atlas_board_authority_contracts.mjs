import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  loadKnownSchema,
  validateJsonSchema,
} from "../packages/atlas-contracts/scripts/lib/validate-json-schema.mjs";
import { validateContractSemantics } from "../packages/atlas-contracts/scripts/lib/validate-semantics.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const BASE = "4617c67b367b04dbc287ab2b20b23469e3ec37b7";
const EXPECTED_PATH_SET_DIGEST = "b7e427c102012241b71a296dba55c95ef64aa10f42cd9fdb75d75091bc9c77fe";
const EXPECTED_TREE_DIGEST = "736271a2e95b5151b57bc6a34db732c49deee8e24ee3dedb4494575044528609";
const EXPECTED_PACKETS = Object.freeze([
  "ATLAS-BOARD-000",
  "ATLAS-BOARD-001",
  "STACK-BOARD-001",
  "DOS-PROJ-001",
  "LIFE-SUP-001",
  "ATLAS-CONTROL-001",
  "CORTEX-BOARD-001",
  "STACK-SUP-001",
  "STACK-ROLL-001",
  "DOS-PROJ-002",
  "ATLAS-HIST-001",
  "ATLAS-CUTOVER-001",
  "DOS-DEBT-001",
  "ATLAS-BOARD-002",
]);

function git(...args) {
  return execFileSync("git", args, { cwd: ROOT, encoding: "utf8" }).trimEnd();
}

function sha256(value) {
  return createHash("sha256").update(value, "utf8").digest("hex");
}

async function loadJson(ref) {
  return JSON.parse(await fs.readFile(path.join(ROOT, ref), "utf8"));
}

function isProtectedPath(ref) {
  return ref.toLowerCase().includes("v2")
    || ref === "ops/atlas/native_board_correlation.mjs"
    || ref === "tests/test_atlas_native_board_correlation.mjs"
    || ref === "docs/audits/ATLAS-FULL-SYSTEM-OPENING-AUDIT-2026-07-12.md"
    || ref === "docs/memory/initiatives/continuity-manifest-atlas-full-system-re-evaluation.json"
    || ref === "docs/ops/ATLAS-MARKER-INTEGRITY-51-FAMILY-100-PERCENT-CLOSEOUT-2026-07-15.md";
}

const baseHead = git("rev-parse", BASE);
assert.equal(baseHead, BASE, "exact ATLAS-BOARD-000 base must be available");

function protectedEntries(treeish) {
  return git("ls-tree", "-r", treeish)
    .split("\n")
    .map((line) => {
      const match = line.match(/^\d+\s+blob\s+([0-9a-f]{40})\t(.+)$/);
      return match ? { blob: match[1], ref: match[2] } : null;
    })
    .filter((entry) => entry && isProtectedPath(entry.ref))
    .sort((left, right) => Buffer.compare(Buffer.from(left.ref), Buffer.from(right.ref)));
}

const entries = protectedEntries(BASE);
const headEntries = protectedEntries("HEAD");

assert.equal(entries.length, 63, "protected v2/historical/native path count must remain frozen");
assert.deepEqual(headEntries, entries, "HEAD protected v2/historical/native path set and blobs must equal the exact baseline");
const pathInput = `${entries.map((entry) => entry.ref).join("\n")}\n`;
const treeInput = `${entries.map((entry) => `${entry.blob} ${entry.ref}`).join("\n")}\n`;
assert.equal(sha256(pathInput), EXPECTED_PATH_SET_DIGEST);
assert.equal(sha256(treeInput), EXPECTED_TREE_DIGEST);

const protectedDiff = git("diff", "--name-only", BASE, "--", ...entries.map((entry) => entry.ref));
assert.equal(protectedDiff, "", "v2, native correlation, and historical snapshots must be tree-invariant");

const migration = await loadJson("docs/registry/ATLAS-BOARD-AUTHORITY-MIGRATION.v1.json");
const migrationSchema = await loadKnownSchema("atlas.board-authority-migration.v1");
assert.equal(migrationSchema.ok, true);
assert.deepEqual(validateJsonSchema(migration, migrationSchema.schema), []);
assert.deepEqual(validateContractSemantics("atlas.board-authority-migration.v1", migration), []);
assert.equal(migration.v2_contract_baseline.file_count, entries.length);
assert.equal(migration.v2_contract_baseline.path_set_digest, `sha256:${EXPECTED_PATH_SET_DIGEST}`);
assert.equal(migration.v2_contract_baseline.tree_digest, `sha256:${EXPECTED_TREE_DIGEST}`);
assert.equal(migration.v2_authority_snapshot.status, "UNKNOWN");
assert.equal(migration.one_time_import.status, "not-started");
assert.equal(migration.first_v3_acceptance.status, "not-accepted");
assert.equal(migration.rollback.current_mode, "v2-authority-allowed");

const laneRegistry = await loadJson("docs/registry/ATLAS-FULL-SYSTEM-REEVALUATION-LANES.json");
const boardLane = laneRegistry.backlog_candidates.find((entry) => entry.id === "lane-atlas-board-authority-v3");
assert(boardLane, "board authority lane must be registered in the canonical lane registry");
assert.equal(boardLane.marker_id, boardLane.id);
assert.equal(boardLane.packet_id, "ATLAS-BOARD-000");
assert.equal(boardLane.program_id, "program-atlas-board-authority-v3");
assert.equal(boardLane.percentage, null);
assert.equal(boardLane.completed_units, null);
assert.equal(boardLane.measurement_status, "UNMEASURED");
assert.equal(boardLane.denominator.value, null);
assert.equal(boardLane.full_system_audit_points, 0);
assert.equal(boardLane.runtime_activation_steps_added, 0);
assert.deepEqual(boardLane.fixed_units.map((unit) => unit.id), EXPECTED_PACKETS);
assert.equal(boardLane.fixed_units[0].status, "review");
assert(boardLane.fixed_units.slice(1).every((unit) => unit.status.includes("blocked")));
assert.equal(boardLane.next_packet.id, "ATLAS-BOARD-001");

const programSource = await loadJson("docs/programs/ATLAS-MASTER-PROGRAM-REGISTER.v1.source.json");
const generatedRegister = await loadJson("docs/registry/ATLAS-MASTER-PROGRAM-REGISTER.v1.json");
for (const register of [programSource, generatedRegister]) {
  const program = register.programs.find((entry) => entry.id === "program-atlas-board-authority-v3");
  assert(program, "board authority program must be registered");
  assert.equal(program.measurement_status, "UNMEASURED");
  assert(program.next_packet.startsWith("ATLAS-BOARD-001"));
}
assert(generatedRegister.authority_indexes.clean_and_resync_lane_registry.backlog_ids.includes(boardLane.id));

const runtimeRegistry = await loadJson("docs/registry/ATLAS-RUNTIME-PLACEMENT-REGISTRY.v1.json");
assert.equal(runtimeRegistry.activation_sequence.length, 8, "runtime activation sequence remains exactly eight steps");
assert.equal(runtimeRegistry.next_owner_side_activation_packet, null, "runtime selector remains exhausted");

console.log("ATLAS board authority repository consistency tests passed.");
