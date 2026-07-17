import process from "node:process";
import path from "node:path";
import {
  fixturesDir,
  knownSchemaPlan,
  loadJson,
  loadKnownSchema,
  validateJsonSchema,
} from "./lib/validate-json-schema.mjs";
import { validateContractSemantics } from "./lib/validate-semantics.mjs";

async function main() {
  const failures = [];

  for (const plan of knownSchemaPlan) {
    const loadedSchema = await loadKnownSchema(plan.id);
    const validFixture = await loadJson(path.join(fixturesDir, plan.valid));
    const invalidFixture = await loadJson(path.join(fixturesDir, plan.invalid));
    const semanticContext = plan.id === "atlas.projection-ack.v1"
      ? { projectionDelivery: await loadJson(path.join(fixturesDir, "valid/projection-delivery.v1.json")) }
      : {};

    const validErrors = [
      ...validateJsonSchema(validFixture, loadedSchema.schema),
      ...validateContractSemantics(plan.id, validFixture, semanticContext),
    ];
    if (validErrors.length > 0) {
      failures.push(
        `${plan.valid} should be valid for ${plan.file}\n${validErrors
          .map((error) => `  - ${error}`)
          .join("\n")}`,
      );
    }

    const invalidErrors = [
      ...validateJsonSchema(invalidFixture, loadedSchema.schema),
      ...validateContractSemantics(plan.id, invalidFixture, semanticContext),
    ];
    if (invalidErrors.length === 0) {
      failures.push(`${plan.invalid} should fail validation for ${plan.file}`);
    }
  }

  const ownerExportSchema = await loadKnownSchema("atlas.project-board.owner-export.v1");
  const cardRecordSchema = await loadKnownSchema("atlas.card-record.v2");
  const {
    $schema: _cardSchemaDialect,
    $id: _cardSchemaId,
    title: _cardSchemaTitle,
    ...cardRecordShape
  } = cardRecordSchema.schema;
  if (
    JSON.stringify(ownerExportSchema.schema.$defs.card_record)
    !== JSON.stringify(cardRecordShape)
  ) {
    failures.push(
      "atlas.project-board.owner-export.v1 must embed the exact atlas.card-record.v2 shape",
    );
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
