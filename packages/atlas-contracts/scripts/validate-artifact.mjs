import { createHash } from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import {
  loadJson,
  loadKnownSchema,
  validateJsonSchema,
} from "./lib/validate-json-schema.mjs";
import { validateContractSemantics } from "./lib/validate-semantics.mjs";

export const exitCodes = Object.freeze({
  VALID: 0,
  INVALID_ARTIFACT: 1,
  UNSUPPORTED_SCHEMA: 2,
  MALFORMED_JSON: 3,
  MISSING_INPUT: 4,
});

function parseArguments(argv) {
  const options = { json: false };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--json") {
      options.json = true;
      continue;
    }

    const equalsMatch = argument.match(/^--(schema|artifact)=(.*)$/);
    if (equalsMatch) {
      options[equalsMatch[1]] = equalsMatch[2];
      continue;
    }

    if (argument === "--schema" || argument === "--artifact") {
      const value = argv[index + 1];
      if (!value || value.startsWith("--")) {
        options.argumentError = `${argument} requires a value.`;
        continue;
      }
      options[argument.slice(2)] = value;
      index += 1;
      continue;
    }

    options.argumentError = `Unsupported argument: ${argument}`;
  }
  return options;
}

function makeResult({ ok, code, schema = null, artifact = null, errors = [] }) {
  return { ok, code, schema, artifact, errors };
}

function emit(result, json) {
  if (json) {
    console.log(JSON.stringify(result));
    return;
  }

  console.log(`${result.code}: ${result.ok ? "artifact is valid" : result.errors.join(" ")}`);
}

function schemaResult(entry) {
  return entry ? { id: entry.id, file: `schemas/${entry.file}` } : null;
}

function isPortableSourceRef(value) {
  if (typeof value !== "string" || value.trim() === "") return false;
  const normalized = value.replaceAll("\\", "/");
  if (path.win32.isAbsolute(value) || path.posix.isAbsolute(normalized)) return false;
  return !normalized.split("/").some((segment) => segment === "." || segment === "..");
}

function ancestorDirectories(start) {
  const directories = [];
  let current = path.resolve(start);
  while (true) {
    directories.push(current);
    const parent = path.dirname(current);
    if (parent === current) return directories;
    current = parent;
  }
}

async function loadRuntimeSourceContext(artifactPath, artifact) {
  const sourceRef = artifact?.runtime_readback?.source_ref;
  if (!sourceRef) return {};
  if (!isPortableSourceRef(sourceRef)) {
    return { runtimeSourceError: "runtime source_ref is not an ATLAS-relative portable path" };
  }

  const searchRoots = [path.dirname(path.resolve(artifactPath)), process.cwd()];
  const visited = new Set();
  const containedCandidates = new Map();
  let containmentEscapeSeen = false;
  for (const searchRoot of searchRoots) {
    for (const ancestor of ancestorDirectories(searchRoot)) {
      const candidate = path.resolve(ancestor, ...sourceRef.replaceAll("\\", "/").split("/"));
      if (visited.has(candidate)) continue;
      visited.add(candidate);

      let realRoot;
      let realCandidate;
      try {
        realRoot = await fs.realpath(ancestor);
        realCandidate = await fs.realpath(candidate);
      } catch (error) {
        if (error?.code === "ENOENT" || error?.code === "ENOTDIR") continue;
        return { runtimeSourceError: `runtime source realpath resolution failed: ${error.message}` };
      }

      const relative = path.relative(realRoot, realCandidate);
      if (relative === "" || relative.startsWith(`..${path.sep}`) || relative === ".." || path.isAbsolute(relative)) {
        containmentEscapeSeen = true;
        continue;
      }
      containedCandidates.set(path.normalize(realCandidate), realCandidate);
    }
  }

  if (containmentEscapeSeen) {
    return { runtimeSourceError: "runtime source_ref escapes a candidate root after realpath resolution" };
  }
  if (containedCandidates.size === 0) {
    return { runtimeSourceError: "runtime source_ref could not be resolved from the artifact or working tree" };
  }
  if (containedCandidates.size > 1) {
    return { runtimeSourceError: "runtime source_ref is ambiguous across multiple contained roots" };
  }

  const [selectedCandidate] = containedCandidates.values();
  let bytes;
  try {
    bytes = await fs.readFile(selectedCandidate);
  } catch (error) {
    return { runtimeSourceError: `runtime source could not be read: ${error.message}` };
  }
  const decoded = bytes.toString("utf8").replace(/^\uFEFF/, "");
  const normalized = decoded.replaceAll("\r\n", "\n").replaceAll("\r", "\n");
  try {
    return {
      runtimeSource: JSON.parse(normalized),
      runtimeSourceRevision: `sha256:${createHash("sha256").update(normalized, "utf8").digest("hex")}`,
    };
  } catch {
    return { runtimeSourceError: "runtime source JSON could not be parsed" };
  }
}

export async function runArtifactValidator(argv) {
  const options = parseArguments(argv);
  if (options.argumentError || !options.schema || !options.artifact) {
    return {
      exitCode: exitCodes.MISSING_INPUT,
      result: makeResult({
        ok: false,
        code: "MISSING_INPUT",
        artifact: options.artifact ?? null,
        errors: [options.argumentError ?? "Both --schema and --artifact are required."],
      }),
      json: options.json,
    };
  }

  const loadedSchema = await loadKnownSchema(options.schema);
  if (!loadedSchema.ok) {
    return {
      exitCode: exitCodes.UNSUPPORTED_SCHEMA,
      result: makeResult({
        ok: false,
        code: loadedSchema.code,
        artifact: options.artifact,
        errors: [loadedSchema.error],
      }),
      json: options.json,
    };
  }

  let artifact;
  try {
    artifact = await loadJson(options.artifact);
  } catch (error) {
    if (error instanceof SyntaxError) {
      return {
        exitCode: exitCodes.MALFORMED_JSON,
        result: makeResult({
          ok: false,
          code: "MALFORMED_JSON",
          schema: schemaResult(loadedSchema.entry),
          artifact: options.artifact,
          errors: ["Artifact JSON could not be parsed."],
        }),
        json: options.json,
      };
    }

    if (error?.code === "ENOENT" || error?.code === "ENOTDIR") {
      return {
        exitCode: exitCodes.MISSING_INPUT,
        result: makeResult({
          ok: false,
          code: "MISSING_INPUT",
          schema: schemaResult(loadedSchema.entry),
          artifact: options.artifact,
          errors: ["Artifact JSON path does not exist."],
        }),
        json: options.json,
      };
    }

    throw error;
  }

  const semanticContext = await loadRuntimeSourceContext(options.artifact, artifact);
  const errors = [
    ...validateJsonSchema(artifact, loadedSchema.schema),
    ...validateContractSemantics(loadedSchema.entry.id, artifact, semanticContext),
  ];
  if (errors.length > 0) {
    return {
      exitCode: exitCodes.INVALID_ARTIFACT,
      result: makeResult({
        ok: false,
        code: "INVALID_ARTIFACT",
        schema: schemaResult(loadedSchema.entry),
        artifact: options.artifact,
        errors,
      }),
      json: options.json,
    };
  }

  return {
    exitCode: exitCodes.VALID,
    result: makeResult({
      ok: true,
      code: "VALID",
      schema: schemaResult(loadedSchema.entry),
      artifact: options.artifact,
    }),
    json: options.json,
  };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const outcome = await runArtifactValidator(process.argv.slice(2));
  emit(outcome.result, outcome.json);
  process.exitCode = outcome.exitCode;
}
