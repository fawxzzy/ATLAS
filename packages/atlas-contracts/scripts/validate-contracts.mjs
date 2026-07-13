import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const packageRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
);

const schemaDir = path.join(packageRoot, "schemas");
const fixturesDir = path.join(packageRoot, "fixtures");

const schemaPlan = [
  {
    file: "atlas.env.v1.schema.json",
    valid: "valid/env.json",
    invalid: "invalid/env.missing-required.json",
  },
  {
    file: "atlas.app-registration.v1.schema.json",
    valid: "valid/app-registration.json",
    invalid: "invalid/app-registration.bad-repo-class.json",
  },
  {
    file: "atlas.health.v1.schema.json",
    valid: "valid/health.json",
    invalid: "invalid/health.bad-status.json",
  },
  {
    file: "atlas.event.v1.schema.json",
    valid: "valid/event.json",
    invalid: "invalid/event.bad-type.json",
  },
  {
    file: "atlas.receipt.v1.schema.json",
    valid: "valid/receipt.json",
    invalid: "invalid/receipt.bad-status.json",
  },
  {
    file: "atlas.component-manifest.v2.schema.json",
    valid: "valid/component-manifest.v2.json",
    invalid: "invalid/component-manifest.v2.bad-authority.json",
  },
  {
    file: "atlas.job-envelope.v2.schema.json",
    valid: "valid/job-envelope.v2.json",
    invalid: "invalid/job-envelope.v2.bad-authority.json",
  },
  {
    file: "atlas.execution-receipt.v2.schema.json",
    valid: "valid/execution-receipt.v2.json",
    invalid: "invalid/execution-receipt.v2.bad-status.json",
  },
  { file: "atlas.context-packet.v2.schema.json", valid: "valid/context-packet.v2.json", invalid: "invalid/context-packet.v2.no-sources.json" },
  { file: "atlas.evidence-bundle.v2.schema.json", valid: "valid/evidence-bundle.v2.json", invalid: "invalid/evidence-bundle.v2.bad-classification.json" },
  { file: "atlas.approval-record.v2.schema.json", valid: "valid/approval-record.v2.json", invalid: "invalid/approval-record.v2.bad-decision.json" },
  { file: "atlas.worker-lease.v2.schema.json", valid: "valid/worker-lease.v2.json", invalid: "invalid/worker-lease.v2.bad-status.json" },
  { file: "atlas.card-record.v2.schema.json", valid: "valid/card-record.v2.json", invalid: "invalid/card-record.v2.bad-lifecycle.json" },
  { file: "atlas.board-event.v2.schema.json", valid: "valid/board-event.v2.json", invalid: "invalid/board-event.v2.bad-result.json" },
  { file: "atlas.marker-evidence.v2.schema.json", valid: "valid/marker-evidence.v2.json", invalid: "invalid/marker-evidence.v2.bad-rollup.json" },
  { file: "atlas.knowledge-candidate.v2.schema.json", valid: "valid/knowledge-candidate.v2.json", invalid: "invalid/knowledge-candidate.v2.bad-kind.json" },
];

const isoDateTimePattern =
  /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$/;

function isPlainObject(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function joinPath(base, segment) {
  if (!base) {
    return segment;
  }

  if (segment.startsWith("[")) {
    return `${base}${segment}`;
  }

  return `${base}.${segment}`;
}

function resolveRef(rootSchema, ref) {
  if (!ref.startsWith("#/")) {
    throw new Error(`Unsupported $ref: ${ref}`);
  }

  const segments = ref
    .slice(2)
    .split("/")
    .map((segment) => segment.replace(/~1/g, "/").replace(/~0/g, "~"));

  let current = rootSchema;
  for (const segment of segments) {
    current = current?.[segment];
  }

  if (!current) {
    throw new Error(`Unresolvable $ref: ${ref}`);
  }

  return current;
}

function validateSchema(value, schema, rootSchema, atPath = "$") {
  if (schema.$ref) {
    return validateSchema(value, resolveRef(rootSchema, schema.$ref), rootSchema, atPath);
  }

  if (schema.anyOf) {
    const branchErrors = schema.anyOf.map((branch) =>
      validateSchema(value, branch, rootSchema, atPath),
    );
    if (branchErrors.some((errors) => errors.length === 0)) {
      return [];
    }
    return [
      `${atPath} must satisfy at least one allowed shape`,
      ...branchErrors.flat(),
    ];
  }

  const errors = [];

  if (schema.const !== undefined && value !== schema.const) {
    errors.push(`${atPath} must equal ${JSON.stringify(schema.const)}`);
  }

  if (schema.enum && !schema.enum.includes(value)) {
    errors.push(
      `${atPath} must be one of ${schema.enum.map((entry) => JSON.stringify(entry)).join(", ")}`,
    );
  }

  if (schema.type !== undefined) {
    const allowedTypes = Array.isArray(schema.type) ? schema.type : [schema.type];
    const matchesType = allowedTypes.some((type) => {
      if (type === "null") {
        return value === null;
      }
      if (type === "array") {
        return Array.isArray(value);
      }
      if (type === "object") {
        return isPlainObject(value);
      }
      if (type === "integer") {
        return Number.isInteger(value);
      }
      return typeof value === type;
    });

    if (!matchesType) {
      errors.push(`${atPath} must be of type ${allowedTypes.join(" | ")}`);
      return errors;
    }
  }

  if (typeof value === "string") {
    if (schema.minLength !== undefined && value.length < schema.minLength) {
      errors.push(`${atPath} must have length >= ${schema.minLength}`);
    }

    if (schema.pattern) {
      const regex = new RegExp(schema.pattern);
      if (!regex.test(value)) {
        errors.push(`${atPath} must match pattern ${schema.pattern}`);
      }
    }

    if (schema.format === "date-time") {
      if (!isoDateTimePattern.test(value) || Number.isNaN(Date.parse(value))) {
        errors.push(`${atPath} must be an ISO 8601 UTC timestamp`);
      }
    }
  }

  if (typeof value === "number") {
    if (schema.minimum !== undefined && value < schema.minimum) {
      errors.push(`${atPath} must be >= ${schema.minimum}`);
    }
    if (schema.maximum !== undefined && value > schema.maximum) {
      errors.push(`${atPath} must be <= ${schema.maximum}`);
    }
  }

  if (Array.isArray(value)) {
    if (schema.minItems !== undefined && value.length < schema.minItems) {
      errors.push(`${atPath} must contain at least ${schema.minItems} item(s)`);
    }

    if (schema.items) {
      value.forEach((item, index) => {
        errors.push(
          ...validateSchema(item, schema.items, rootSchema, joinPath(atPath, `[${index}]`)),
        );
      });
    }
  }

  if (isPlainObject(value)) {
    const propertyKeys = Object.keys(value);
    const definedProperties = schema.properties ?? {};
    const requiredProperties = schema.required ?? [];

    for (const key of requiredProperties) {
      if (!(key in value)) {
        errors.push(`${joinPath(atPath, key)} is required`);
      }
    }

    if (schema.additionalProperties === false) {
      for (const key of propertyKeys) {
        if (!(key in definedProperties)) {
          errors.push(`${joinPath(atPath, key)} is not allowed`);
        }
      }
    }

    for (const [key, propertySchema] of Object.entries(definedProperties)) {
      if (key in value) {
        errors.push(
          ...validateSchema(value[key], propertySchema, rootSchema, joinPath(atPath, key)),
        );
      }
    }
  }

  return errors;
}

async function loadJson(relativePath) {
  const fullPath = path.join(
    relativePath.startsWith("valid") || relativePath.startsWith("invalid")
      ? fixturesDir
      : schemaDir,
    relativePath,
  );
  const raw = await fs.readFile(fullPath, "utf8");
  return JSON.parse(raw);
}

async function main() {
  const failures = [];

  for (const plan of schemaPlan) {
    const schema = await loadJson(plan.file);
    const validFixture = await loadJson(plan.valid);
    const invalidFixture = await loadJson(plan.invalid);

    const validErrors = validateSchema(validFixture, schema, schema);
    if (validErrors.length > 0) {
      failures.push(
        `${plan.valid} should be valid for ${plan.file}\n${validErrors
          .map((error) => `  - ${error}`)
          .join("\n")}`,
      );
    }

    const invalidErrors = validateSchema(invalidFixture, schema, schema);
    if (invalidErrors.length === 0) {
      failures.push(
        `${plan.invalid} should fail validation for ${plan.file}`,
      );
    }
  }

  if (failures.length > 0) {
    console.error("ATLAS contract validation failed:\n");
    for (const failure of failures) {
      console.error(failure);
      console.error("");
    }
    process.exitCode = 1;
    return;
  }

  console.log("ATLAS contract validation passed.");
}

await main();
