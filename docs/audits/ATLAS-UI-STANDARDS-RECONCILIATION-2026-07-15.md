# ATLAS UI Standards Research Reconciliation

Date: `2026-07-15`

## Provenance

- Source: `data/imports/ui-standards/deep-research-2026-07-15/deep-research-report.md`
- Source SHA-256: `77f882e6af10eb4094e79033769ab8d8010ba2e6d473c620ef55750340941723`
- Source length: `497` lines, `37219` bytes
- Source status: preserved external research input
- Review status: reconciled, not canonical

The complete report was reviewed. Its recommendations were compared with current root governance, the Atlas Book, QA LLEL, UI observation and proof, Atlas Contracts, Playbook doctrine adoption, card lifecycle, marker policy, and owner boundaries.

## Existing Inventory

### Root UI And Visual Doctrine

- `AGENTS.md`
  UI mutation checklist, canonical-surface-first normalization, route-aware proof, live-data safety, and no proof-free completion claims.
- `docs/standards/ATLAS-QA-LLEL.md`
  Canonical evidence, lens, promotion, release-profile, waiver, adapter, artifact, and adoption-drift standard.
- `docs/architecture/VISUAL-CHANGE-WORKFLOW.md`
  Route and state capture loop, isolated browser rule, requested-change checklist, data lane, and recovery procedure.
- `docs/architecture/ATLAS-VISUAL-OPERATOR.md`
  Codex-owned browser and route-aware visual operator boundary.
- `docs/standards/FAWXZZY-THEME-STANDARD.md` and `docs/standards/fawxzzy-sage-theme/**`
  Shared brand and theme inputs. These are not a universal owner-token override.
- `docs/standards/BRANDING-ASSET-PIPELINE.md`
  Canonical source to generated outputs to declared consumer drift pattern.

### UI Observation And Proof

- `schemas/atlas.ui.observation.v1.json`
- `schemas/atlas.ui.capture-map.v1.json`
- `schemas/atlas.ui.drift.report.v1.json`
- `schemas/atlas.ui.visual-proof.v1.json`
- `schemas/atlas.ui.proof-summary.v1.json`
- `ops/atlas/ui_observe/**`
- `ops/atlas/ui_visual_proof/**`
- `ops/atlas/ui_proof/**`

These lanes already provide stable capture IDs, owner-truth refs, semantic observation, deterministic drift, image assertions, and a derived combined proof summary. Current concrete observation and image proof are Fitness-specific and remain validator-only.

### QA And Audit Tooling

The root already owns thirteen `atlas.qa.*` schema families and the `ops/atlas/qa/**` pipeline for:

- adapters and scenarios
- emulated and physical lenses
- browser and provider capture
- artifact collection and validation
- repo-native test evidence
- visual diff and governed baselines
- manual attestation and waiver
- evaluation, promotion, evidence index, and release readiness
- adoption drift and CI gate orchestration

The default web lens set is `desktop.chromium`, `android.chrome`, and `iphone.webkit`. Release policy already maps Fitness to `release_critical_web`, Trove to `web_visual`, Playbook to `docs_governance`, and Lifeline and Foundation to `package_contract`.

### Cards, Markers, Receipts, And Knowledge

- `atlas.card-record.v2`
  Shared wire lifecycle and card identity.
- `atlas.project-board.owner-export.v1`
  Stable candidate and owner-export semantics with objective, acceptance, blockers, evidence, and relationship fields.
- `atlas.evidence-bundle.v2`
  Correlated command, test, diff, screenshot, source, and readback evidence.
- `atlas.execution-receipt.v2`
  Terminal execution result and changed-path proof.
- `atlas.marker-evidence.v2`
  Numerator, denominator, freshness, evidence, transition, and rollup policy.
- `atlas.knowledge-candidate.v2`
  Candidate Rule, Pattern, Failure Mode, automation opportunity, or governance gap with provenance and review state.
- `atlas.board-event.v2`
  Idempotent board intent, expected version, result, and readback.

### Atlas Book And Playbook

- The Atlas Book is a docs-only truth-map and receipt projection. It does not replace owner truth, release ledgers, Discord state, Playbook, or `_stack`.
- Playbook owns promoted doctrine. Atlas records source-linked adoption and conformance evidence and must not copy doctrine bodies into a second registry.
- `docs/architecture/PLAYBOOK-INGEST-PIPELINE.md` already defines import, evaluation, normalization, catalog, and selective adoption boundaries.

## Reconciliation Ledger

| Input or current surface | Disposition | Resulting rule | Owner | Enforcement path |
|---|---|---|---|---|
| Complete research report | Retain | Preserve exact bytes and hash as external evidence; never treat citations or recommendations as canonical by default. | ATLAS root | Import manifest and validator hash check |
| QA LLEL evidence and promotion model | Retain | It remains the canonical stack evidence and promotion layer. | ATLAS root QA | Local, CI, release |
| Root UI mutation checklist and canonical-surface rules | Retain | Promote into stable standard IDs and remediation checklist contract. | ATLAS root plus owner repos | Local and review gates |
| Existing UI observer, drift, visual proof, and combined summary | Retain | Reuse as specialized evidence lanes; generalize through adapters only after owner proof. | ATLAS root validator plus owner repos | Local and QA LLEL |
| Existing CardRecord lifecycle | Merge | Map `unplanned` to `intake`, `planned` to `planning`, and preserve existing ready, in-progress, review, completed, and blocked wire values. | Atlas Contracts | Schema and semantic validator |
| One never-closed UI audit feature card per project | Supersede | Keep durable audit findings and audit lineage; close remediation cards normally; create new sustainment audits instead of one immortal feature card. | ATLAS root contracts and DiscordOS writer | Finding/remediation schemas plus board readback later |
| Weighted completion score and exception penalties | Supersede | Use frozen integer denominators, verified units, absolute debt counts, and derived display percentages only. | ATLAS root marker policy | `atlas.marker-evidence.v2` after denominator acceptance |
| WCAG 2.2 AA target | Merge | Accept as the default web UI target, verified against current W3C Recommendation material. | ATLAS root plus owner repos | Accessibility evidence in local, CI, release profiles |
| APG patterns | Merge | Use as advisory widget and keyboard guidance, not a normative standard or design system. | Owner repos | Review and accessibility evidence |
| Report device matrix | Merge | Preserve the existing default desktop, Android, and iPhone WebKit triad; add tablet, narrow desktop, or physical lenses by profile and route risk. | ATLAS QA plus owner repos | QA lens and scenario contracts |
| Report tool stack | Defer universal mandate | Require capabilities, not vendors. Wrap healthy repo-native tools before adding Playwright, axe, Storybook, Lighthouse, BrowserStack, or alternatives. | Owner repos | Adoption profile acceptance |
| Host-native CI recommendation | Merge | Use existing QA LLEL entrypoint and thin orchestration; do not duplicate repo behavior in workflow YAML. | ATLAS root plus owner repos | CI tier |
| Real-device strategy | Retain and narrow | Emulate broadly; require physical or valid manual evidence only for profile-defined release-critical flows. | ATLAS QA plus owner repos | Release tier |
| Semantic tokens, canonical components, aliases, and wrappers | Merge | Accept the architecture pattern while keeping owner repo token and component truth canonical. | Owner repos | Shared-foundation migration wave |
| Fawxzzy theme and sage theme pack | Retain with boundary | Shared brand input and opt-in consumer mapping; not a universal implementation override. | ATLAS brand governance plus owner repos | Consumer drift and repo-local verify |
| Atlas as authoritative, Discord as reflection | Retain with current owner split | Registry and evidence remain Atlas-root truth; board application and publication remain DiscordOS single-writer work. | ATLAS root and DiscordOS | Board event plus readback after separate authority |
| Research failure modes directly becoming Playbook entries | Supersede | First create verified findings, then reviewed KnowledgeCandidate records, then owner-side Playbook promotion. | ATLAS root and Playbook | Knowledge review and source-linked adoption |
| Atlas Book as standards source | Supersede | The Book projects program version and receipts only; registry and standards doc remain normative. | ATLAS root | Book receipt projection after execution |
| Research timelines and percentage phase gates | Reference only | Treat dates as illustrative and replace percentage gates with evidence-backed entry and exit criteria. | ATLAS root and owner repos | Migration wave receipts |
| Accessibility evidence contract | Gap closed at foundation | Add accessibility status and refs to `atlas.ui.audit-finding.v1`; owner adapters remain future work. | ATLAS root schema; owner repos later | Schema and owner adoption packets |
| Finding to remediation correlation | Gap closed at foundation | Add stable finding and remediation IDs plus CardRecord lifecycle mapping. | ATLAS root contracts | Validator and focused tests |
| Stable policy standard IDs | Gap closed at foundation | Add versioned registry IDs separate from existing evidence-contract IDs. | ATLAS root | Registry schema and validator |
| Machine-readable requested-change checklist | Gap closed at foundation | Add checklist items and terminal status rules to the remediation contract. | ATLAS root schema; owner repos later | Local and review gates |
| Owner adoption | Gap remains | Root artifacts do not prove owner adoption. Candidate cards remain unplanned with percentage null. | Each owner repo | Later bounded owner packets |

## Accepted Foundation Decisions

1. The program is permanent governance, not a one-time visual cleanup.
2. The stable standard registry is root-owned and versioned.
3. Existing QA LLEL and Atlas Contracts remain authoritative for evidence, cards, markers, receipts, and knowledge.
4. Owner repos retain implementation and product truth.
5. WCAG 2.2 AA is the default web UI target.
6. Audit findings are durable; remediation cards close through the existing lifecycle.
7. Metrics use evidence units and frozen denominators.
8. Owner adoption is profile-based and proof-backed.
9. Atlas Book and DiscordOS are downstream projections for their respective fact classes.
10. Playbook promotion requires reviewed, repeated, verified evidence.

## Explicitly Not Accepted

- one permanently open feature card as the only audit record
- weighted subjective completion and exception penalties
- a universal mandated vendor toolchain
- automatic Playbook promotion from a research recommendation
- automatic owner profile assignment when applicability is unknown
- a stack-wide completion percentage before owner baselines exist
- root observation or theme files replacing owner implementation truth
- marker movement from this docs and contract foundation alone

## Owner-Lane Candidate Inventory

The candidate registry creates no live cards. It provides unplanned CardRecord-backed packets for:

- Fitness: proposed release-critical web adoption
- Trove: proposed standard web adoption
- Mazer: profile selection and baseline
- Socials OS: applicability and profile selection
- Stream: applicability and prototype reconciliation
- Nat1 Games: owner availability and profile selection
- DiscordOS: UI applicability separated from board-writer authority
- Playbook: later verified failure-pattern review

Foundation and Lifeline retain their current nonvisual package-contract QA classification unless an owner later identifies a UI-bearing scope. Playbook retains docs-governance release policy; its candidate packet concerns doctrine promotion, not UI profile adoption.

## Encoding Review

The imported report is valid UTF-8 and includes typographic punctuation plus private-use citation delimiters. Some Windows output paths can render those bytes as mojibake. The exact source is therefore preserved only as digest-bound evidence.

All new normative program files use ASCII text. `ops/atlas/ui_standards/validate.py` rejects:

- non-ASCII characters in declared normative files
- common mojibake fragments
- missing or changed evidence exceptions
- an imported report whose digest no longer matches provenance

## Remaining Dependencies

- Owner approval of applicability and adoption profile
- Owner-side accessibility evidence integration
- Owner-side route, state, and component baseline
- QA LLEL adapter and scenario extension where missing
- DiscordOS admission and readback for any later live card projection
- Playbook review after repeated verified findings exist

None of these dependencies blocks the root foundation. They block claims of owner adoption, enforcement, or completion.
