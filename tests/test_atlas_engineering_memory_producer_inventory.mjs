import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const STACK_ROOT = process.env.ATLAS_STACK_ROOT
  ? path.resolve(process.env.ATLAS_STACK_ROOT)
  : path.join(ROOT, "repos", "_stack");

async function loadJson(relative) {
  return JSON.parse(await fs.readFile(path.join(ROOT, ...relative.split("/")), "utf8"));
}

async function readInventorySource(relative) {
  const stackPrefix = "repos/_stack/";
  const target = relative.startsWith(stackPrefix)
    ? path.join(STACK_ROOT, ...relative.slice(stackPrefix.length).split("/"))
    : path.join(ROOT, ...relative.split("/"));
  try {
    return await fs.readFile(target, "utf8");
  } catch (error) {
    if (error.code === "ENOENT" && relative.startsWith(stackPrefix)) return null;
    throw error;
  }
}

test("every admitted mutating executor installs pre-mutation and terminal Engineering Memory gates", async () => {
  const inventory = await loadJson("docs/registry/ATLAS-ENGINEERING-MEMORY-PRODUCER-INVENTORY.v1.json");
  assert.equal(inventory.execution_truth, "installed");
  assert.deepEqual(inventory.uninstalled_admitted_mutating_executors, []);
  assert.deepEqual(
    inventory.admitted_mutating_executors.map((item) => item.producer_id).sort(),
    ["stack.canonical-workspace", "stack.repo-task"],
  );
  for (const producer of inventory.admitted_mutating_executors) {
    assert.equal(producer.status, "installed");
    assert.equal(producer.pre_mutation_gate, "mutation");
    assert.deepEqual(producer.terminal_gates, ["verify", "archive"]);
    const source = await readInventorySource(producer.path);
    if (source !== null) {
      assert.match(source, /New-AtlasContractsV2Producer/);
      assert.match(source, /Complete-AtlasEngineeringMemoryCloseout/);
    }
  }
});

test("higher-level engineering entrypoints delegate to an installed executor", async () => {
  const inventory = await loadJson("docs/registry/ATLAS-ENGINEERING-MEMORY-PRODUCER-INVENTORY.v1.json");
  const installed = new Set(inventory.admitted_mutating_executors.map((item) => item.producer_id));
  for (const entrypoint of inventory.delegating_entrypoints) {
    assert.equal(installed.has(entrypoint.delegates_to), true, `${entrypoint.entrypoint_id} has no installed target`);
    const source = await readInventorySource(entrypoint.path);
    if (source !== null) {
      assert.equal(source.includes(entrypoint.evidence), true, `${entrypoint.entrypoint_id} delegation evidence drifted`);
    }
  }
});

test("policy installation and producer inventory retain the same exact executor identities", async () => {
  const [inventory, policy] = await Promise.all([
    loadJson("docs/registry/ATLAS-ENGINEERING-MEMORY-PRODUCER-INVENTORY.v1.json"),
    loadJson("docs/registry/ATLAS-ENGINEERING-MEMORY-POLICY.v1.json"),
  ]);
  assert.deepEqual(
    [...policy.installation.installed_producers].sort(),
    inventory.admitted_mutating_executors.map((item) => item.producer_id).sort(),
  );
});
