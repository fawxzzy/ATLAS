#!/usr/bin/env node

import { copyFile, mkdir, readFile, stat } from "node:fs/promises";
import crypto from "node:crypto";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const SCRIPT_DIRECTORY = path.dirname(fileURLToPath(import.meta.url));
const BRANDING_ROOT = path.resolve(SCRIPT_DIRECTORY, "..");
const ATLAS_ROOT = path.resolve(BRANDING_ROOT, "..");
const DEFAULT_MANIFEST_PATH = path.join(BRANDING_ROOT, "manifest.json");

function parseArguments(argv) {
  const options = {
    manifestPath: DEFAULT_MANIFEST_PATH,
    check: false,
    dryRun: false
  };

  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--manifest") {
      index += 1;
      const value = argv[index];
      if (!value) {
        throw new Error("Missing value for --manifest.");
      }
      options.manifestPath = path.resolve(process.cwd(), value);
      continue;
    }
    if (argument === "--check") {
      options.check = true;
      continue;
    }
    if (argument === "--dry-run") {
      options.dryRun = true;
      continue;
    }
    throw new Error(`Unknown argument: ${argument}`);
  }

  return options;
}

async function readJson(filePath) {
  return JSON.parse(await readFile(filePath, "utf8"));
}

async function sha256(filePath) {
  const content = await readFile(filePath);
  return crypto.createHash("sha256").update(content).digest("hex");
}

function resolveAtlasPath(relativePath) {
  return path.resolve(ATLAS_ROOT, relativePath);
}

function ensureString(value, label) {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new Error(`${label} must be a non-empty string.`);
  }
  return value.trim();
}

async function validateConsumers(manifest) {
  const consumers = Array.isArray(manifest.consumers) ? manifest.consumers : [];
  if (consumers.length === 0) {
    throw new Error("Manifest must define at least one consumer.");
  }

  return Promise.all(
    consumers.map(async (consumer, index) => {
      const id = ensureString(consumer.id, `consumers[${index}].id`);
      const source = resolveAtlasPath(ensureString(consumer.source, `consumers[${index}].source`));
      const target = resolveAtlasPath(ensureString(consumer.target, `consumers[${index}].target`));
      await stat(source);
      return {
        id,
        description: typeof consumer.description === "string" ? consumer.description.trim() : "",
        source,
        target
      };
    })
  );
}

async function main() {
  const options = parseArguments(process.argv.slice(2));
  const manifest = await readJson(options.manifestPath);
  const consumers = await validateConsumers(manifest);

  const staleConsumers = [];

  for (const consumer of consumers) {
    let status = "unchanged";
    let targetExists = true;
    try {
      await stat(consumer.target);
    } catch {
      targetExists = false;
    }

    if (!targetExists) {
      status = "missing";
    } else {
      const [sourceHash, targetHash] = await Promise.all([sha256(consumer.source), sha256(consumer.target)]);
      if (sourceHash !== targetHash) {
        status = "stale";
      }
    }

    if (status === "unchanged") {
      console.log(`ok    ${path.relative(ATLAS_ROOT, consumer.target)}`);
      continue;
    }

    staleConsumers.push({
      ...consumer,
      status
    });

    if (options.check || options.dryRun) {
      console.log(`${status.padEnd(5)} ${path.relative(ATLAS_ROOT, consumer.target)}`);
      continue;
    }

    await mkdir(path.dirname(consumer.target), { recursive: true });
    await copyFile(consumer.source, consumer.target);
    console.log(`sync  ${path.relative(ATLAS_ROOT, consumer.target)}`);
  }

  if (options.check && staleConsumers.length > 0) {
    console.error(`Brand consumer drift detected in ${staleConsumers.length} target(s).`);
    process.exitCode = 1;
    return;
  }

  if (!options.check && !options.dryRun && staleConsumers.length === 0) {
    console.log("All brand consumers are already current.");
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
