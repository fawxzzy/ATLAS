import { validateProjectBoardOwnerExport } from "./validate-project-board-owner-export.mjs";

const semanticValidators = Object.freeze({
  "atlas.project-board.owner-export.v1": validateProjectBoardOwnerExport,
});

export function validateContractSemantics(contractId, value, context = {}) {
  return semanticValidators[contractId]?.(value, context) ?? [];
}
