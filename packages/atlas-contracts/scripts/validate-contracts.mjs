import process from "node:process";
import path from "node:path";
import {
  fixturesDir,
  knownSchemaPlan,
  loadJson,
  loadKnownSchema,
  validateJsonSchema,
} from "./lib/validate-json-schema.mjs";

async function main() {
  const failures = [];

  for (const plan of knownSchemaPlan) {
    const loadedSchema = await loadKnownSchema(plan.id);
    const validFixture = await loadJson(path.join(fixturesDir, plan.valid));
    const invalidFixture = await loadJson(path.join(fixturesDir, plan.invalid));

    const validErrors = validateJsonSchema(validFixture, loadedSchema.schema);
    if (validErrors.length > 0) {
      failures.push(
        `${plan.valid} should be valid for ${plan.file}\n${validErrors
          .map((error) => `  - ${error}`)
          .join("\n")}`,
      );
    }

    const invalidErrors = validateJsonSchema(invalidFixture, loadedSchema.schema);
    if (invalidErrors.length === 0) {
      failures.push(`${plan.invalid} should fail validation for ${plan.file}`);
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
