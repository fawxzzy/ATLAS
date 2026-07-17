import { validateProjectBoardOwnerExport } from "./validate-project-board-owner-export.mjs";
import { boardAuthoritySemanticValidators } from "./validate-board-authority.mjs";

const semanticValidators = Object.freeze({
  "atlas.project-board.owner-export.v1": validateProjectBoardOwnerExport,
  ...boardAuthoritySemanticValidators,
});

export function validateContractSemantics(contractId, value, context = {}) {
  return semanticValidators[contractId]?.(value, context) ?? [];
}
