# Playbook Notes

# 2026-06-12 - Fitness production deploy must preserve DiscordOS transfer seam

- Rule: `Deploying Adjacent Fitness Work Must Preserve Active DiscordOS Seam`.
- Rule: when Fitness product work is ready while DiscordOS transfer is active, deploy only a branch that contains both the product changes and the DiscordOS transfer seam.
- Pattern: `Owner Work -> Seam Carry-Forward -> Production Proof -> Live Blocker Recheck`.
- Pattern: preserve ready Fitness changes on a branch, carry forward the transfer seam, verify both test families, deploy production, then recheck DiscordOS readiness before any marker claim.
- Failure Mode: `Product Deploy Regresses Transfer Path`.
- Failure Mode: deploying Fitness history/analytics work from a branch without the DiscordOS transfer seam would silently replace the production artifact needed for live traffic transfer.
- Release-summary bullets:
  - Deployed Fitness production `dpl_DHtXDYBLVL9o8XxWCYCNa37Gmz2Q` from `codex/fitness-history-analytics-discordos-transfer`.
  - Preserved the DiscordOS feedback transfer seam while publishing the ready history/analytics work.
  - Kept `Discord OS Feedback Workflow Canonicalization` at `96%` because live readiness still reports `missing_live_workflow_parity_proof` and `missing_live_traffic_transfer_proof`.

# 2026-06-12 - Refresh DCE after supporting-lane threshold changes

- Rule: `Refresh Durable Routing After Supporting-Lane Ratchets`.
- Rule: when a supporting lane closes at a new threshold, DCE must refresh the restart spine before future workers treat the new posture as durable.
- Pattern: `Supporting Lane Ratchet -> DCE Spine Refresh -> Hold`.
- Pattern: supporting lane ratchets -> restart posture becomes one step stale -> refresh DCE spine -> hold until distinct drift or automation appears.
- Failure Mode: `Stale Restart Spine Drift`.
- Failure Mode: current adjacent receipts can be durable while the manifest-backed restart path still routes workers through the previous supporting-lane state.
- Release-summary bullets:
  - Refreshed DCE after `Knowledge Capture & Transfer` moved from `83%` to `84%`.
  - Ratcheted `Durable Context Externalization` from `78%` to `79%`.
  - Kept DCE below `100%` because continuity coverage is still partial, operator-driven, and not broadly automated.

# 2026-06-12 - 100 percent requires exact blocker clearance

- Rule: `100 Percent Requires Exact Blocker Clearance`.
- Rule: a marker may close at `100%` only when the last admitted blocker class is explicitly cleared with durable proof and all preserved exceptions remain visible.
- Pattern: `Scoped Proof -> Exception Preservation -> Marker Closure`.
- Pattern: prove the exact lane scope -> name the retained exception or untrusted surface -> refresh generated projections -> close only that scoped marker.
- Failure Mode: `Clean Wording As Closure Drift`.
- Failure Mode: if finality language hides retained exceptions, untrusted surfaces, owner-repo work, or local/no-remote boundaries, the marker reads as mature while the actual blocker class still exists.
- Release-summary bullets:
  - Captured the June 12 closeout cluster as KCT carry-forward truth.
  - Preserved Verta-core trust scope, Fitness exception scope, owner/runtime lane boundaries, and local/no-remote repo naming truth.
  - Ratcheted `Knowledge Capture & Transfer` from `83%` to `84%`.
  - Kept `Knowledge Capture & Transfer` below `100%` because broader continuity-read automation and general capture/promotion execution are still open.

# 2026-06-05 - Timeout recheck closes the root ladder

- Rule: `Timeout Recheck Closes The Root Ladder`.
- Rule: after one blocked execution receipt and one blocker-recheck receipt for the same timeout class, root stops until runtime state materially changes.
- Pattern: `Blocked Execution -> Timeout Receipt Discipline -> Root Stop`.
- Pattern: run one bounded live proof -> freeze the timeout class and receipt fields -> stop the root ladder for that blocker class.
- Failure Mode: `Timeout Retry Narration Drift`.
- Failure Mode: if root keeps rerunning the same timeout-bound branch after the blocker class is already frozen, the ladder starts narrating activity instead of creating new information.
- Release-summary bullets:
  - Closed the current inline-prompt timeout ladder on `resume_command_timeout`.
  - Froze timeout receipt discipline fields inside the gate.
  - Kept `AI Repetition-to-Automation Pipeline` flat at `31%`.
  - Left no immediate next packet open inside guarded continuation for this blocker class.

# 2026-06-05 - Execution proof must own its timeout

- Rule: `Execution Proof Must Own Its Timeout`.
- Rule: one bounded live proof must classify its own timeout durably inside the gate instead of relying on an outer shell timeout to end the run.
- Pattern: `Admitted Shape -> Bounded Live Proof -> Timeout Receipt`.
- Pattern: admit one exact command shape -> run one live proof with an internal timeout -> kill the local process tree if needed -> write the timeout receipt before leaving the packet.
- Failure Mode: `Outer-Shell Timeout Drift`.
- Failure Mode: if the outer shell kills the proof before the gate writes its receipt, ATLAS loses the real blocker class and cannot honestly route the next packet.
- Release-summary bullets:
  - Added durable `resume_command_timeout` classification for bounded live continuation proofs.
  - Proved the admitted inline-prompt resume shape blocks on a 30-second bounded timeout rather than on stdin.
  - Kept `AI Repetition-to-Automation Pipeline` flat at `31%`.
  - Moved the exact next packet to `AI Repetition-to-Automation Pipeline Guarded Codex Continuation Gate Inline-Prompt Resume Timeout-Boundary And Receipt Discipline Pass 24`.

# 2026-06-05 - Inline prompt first, dash-stdin later

- Rule: `Inline Prompt First, Dash-stdin Later`.
- Rule: when the resume family exposes multiple prompt-bearing surfaces, admit the smallest explicit inline prompt shape first and keep stdin-fed prompt injection deferred until its source boundary is frozen separately.
- Pattern: `Help Contract -> Inline Prompt Admission -> Execution Proof`.
- Pattern: prove prompt support -> admit one exact inline prompt shape -> defer dash-stdin -> run one bounded execution proof only after that.
- Failure Mode: `Prompt-Source Collapsing`.
- Failure Mode: if inline prompt arguments and dash-stdin are treated as the same admission event, the guarded lane loses prompt provenance and widens into a more ambiguous execution surface than the receipt claims.
- Release-summary bullets:
  - Admitted one exact prompt-bearing resume shape: `codex exec resume --last <inline-prompt>`.
  - Kept `codex exec resume --last -` explicitly deferred.
  - Kept `AI Repetition-to-Automation Pipeline` flat at `31%`.
  - Moved the exact next packet to `AI Repetition-to-Automation Pipeline Guarded Codex Continuation Gate Inline-Prompt Resume Execution Proof Pass 23`.

# 2026-06-05 - Help-surface proof must not become implicit prompt injection

- Rule: `Help-Surface Proof Does Not Auto-Admit Prompt Injection`.
- Rule: when the CLI help surface proves prompt-bearing resume variants exist, ATLAS must freeze that contract first and route next into exact prompt-bearing command admission instead of treating help text as permission to run live prompt-fed continuation.
- Pattern: `stderr Boundary -> Help Contract Probe -> Prompt-Bearing Admission Packet`.
- Pattern: freeze the stderr blocker -> prove prompt-argument and dash-stdin support from help -> keep live prompt execution closed -> admit one exact prompt-bearing variant only in the next bounded packet.
- Failure Mode: `Prompt-Surface Overreach Drift`.
- Failure Mode: if help text alone is treated as execution permission, the guarded continuation lane widens from contract proof into live mutation without freezing prompt source, exact shape, or fallback.
- Release-summary bullets:
  - Froze the resume help-surface contract as `resume_prompt_arg_and_stdin_dash_supported`.
  - Preserved `resume_requires_stdin_prompt` as the blocker on the currently admitted promptless command shape only.
  - Kept `AI Repetition-to-Automation Pipeline` flat at `31%`.
  - Moved the exact next packet to `AI Repetition-to-Automation Pipeline Guarded Codex Continuation Gate Prompt-Bearing Resume Command Admission Pass 22`.

# 2026-06-05 - Clear launch blockage before arguing about non-interactive resume semantics

- Rule: `Launch Blocker Cleared Does Not Mean Resume Contract Cleared`.
- Rule: once the exact admitted resume command launches through the active runtime surface, replace the old launch blocker with the narrower command-semantic blocker instead of keeping both alive or claiming success.
- Pattern: `Changed Surface Proof -> Bounded Resume Launch -> Narrower Command-Semantic Blocker`.
- Pattern: prove changed executable order -> run one explicitly enabled bounded resume proof -> freeze the actual stderr-driven blocker class -> route the next packet to the command contract, not another blind launch retry.
- Failure Mode: `Post-Launch Overclaim Drift`.
- Failure Mode: if the lane treats a started process as successful continuation without freezing the stderr-level blocker, automation maturity gets overstated and the next packet loses focus.
- Release-summary bullets:
  - Cleared the old non-packaged launch-path blocker by running the exact admitted resume command through the npm `.cmd` shim.
  - Froze the remaining blocker as `resume_requires_stdin_prompt`.
  - Ratcheted `AI Repetition-to-Automation Pipeline` from `30%` to `31%`.
  - Moved the exact next packet to `AI Repetition-to-Automation Pipeline Guarded Codex Continuation Gate Resume-Stdin Boundary And Non-Interactive Contract Pass 21`.

# 2026-06-04 - Reopen only on changed runtime surface, then prove that surface before live continuation

- Rule: `Changed Runtime Surface Requires Runtime-Surface Proof Before Live Resume`.
- Rule: once a guarded-continuation ladder is closed under the two-strike blocker rule, a materially changed executable/runtime surface may reopen the lane only through one narrower runtime-surface proof packet before any new live resume proof is honest.
- Pattern: `Blocked Packaged Surface -> New Executable Order -> Runtime-Surface Proof -> Later Bounded Resume Proof`.
- Pattern: preserve the historical blocker receipt -> prove the newly resolved executable order and launchability -> keep live continuation blocked by default -> only then consider one bounded real resume proof.
- Failure Mode: `Changed-Surface Skip-Ahead Drift`.
- Failure Mode: if a new Codex executable surface appears and root jumps straight back into live continuation without first freezing the changed-surface proof, the lane overclaims what actually changed and loses the durable contrast with the historical blocker.
- Release-summary bullets:
  - Preserved `windowsapps_packaged_codex_start_access_denied` as the historical packaged-surface blocker.
  - Proved the active Codex runtime surface is now `non_packaged_npm_codex_launchable` with `codex-cli 0.137.0`.
  - Confirmed WindowsApps Codex entries still exist but only as lower-priority command candidates.
  - Kept `AI Repetition-to-Automation Pipeline` flat at `30%`.
  - Moved the exact next packet to `AI Repetition-to-Automation Pipeline Guarded Codex Continuation Gate Non-Packaged Bounded Resume Execution Proof Pass 20`.

# 2026-06-04 - Discord thread title patches must fail closed on punctuation encoding

- Rule: `Discord Thread Titles Must Stay ASCII-Safe By Default`.
- Rule: shell-driven Discord thread title edits should use ASCII-safe punctuation by default; intentional Unicode punctuation requires an explicit UTF-8-safe or escaped source plus exact Discord readback verification.
- Pattern: `Draft Title -> Governed Patch Path -> Exact Readback Verification`.
- Pattern: operator drafts the title -> governed thread-patch path validates title shape -> Discord patch runs -> exact stored title is read back immediately -> only then treat the edit as complete.
- Failure Mode: `Discord Title Punctuation Degradation`.
- Failure Mode: if non-ASCII punctuation is pushed through an ad hoc shell-piped Discord patch path, Discord can store a literal `?` and silently degrade the visible thread title.
- Release-summary bullets:
  - Fixed one live Fitness feedback thread title that had stored `?` instead of the intended separator punctuation.
  - Added a governed `discord:thread:patch` operator path with default ASCII-title guarding and exact readback verification.
  - Recorded the Discord title-encoding failure mode in both stack and Fitness feedback workflow docs.

# 2026-06-04 - Stop the ladder after one exact host-runtime blocker recheck

- Rule: `One Blocked Resume Execution Plus One Runtime Recheck Ends The Root Ladder`.
- Rule: after one blocked real `codex exec resume --last` execution receipt and one narrower host-runtime boundary recheck for the same blocker class, root stops the guarded continuation ladder until runtime state materially changes.
- Pattern: `Exact Resume Command -> Blocked Execution Receipt -> Runtime Boundary Classification -> Hold`.
- Pattern: exact resume command -> blocked execution receipt -> machine-readable runtime classification -> no further root continuation packet by default.
- Failure Mode: `Retry-The-Same-Blocked-Resume Drift`.
- Failure Mode: if root keeps opening new continuation packets against the same Windows runtime-start blocker, the lane drifts into repetitive blocker narration instead of bounded control-plane truth.
- Release-summary bullets:
  - Classified the current host blocker as `windowsapps_packaged_codex_start_access_denied`.
  - Proved the resolved executable path is the packaged WindowsApps Codex binary and preserved that in the decision receipt.
  - Kept `AI Repetition-to-Automation Pipeline` flat at `30%`.
  - Moved the exact next packet to `none immediate inside guarded continuation for the current Windows Codex runtime blocker`.

# 2026-06-04 - Admit only the real resume command

- Rule: `Admit Only The Real Resume Command`.
- Rule: once live execution is enabled for the guarded continuation gate, the admitted command shape is the exact real `codex exec resume --last` family only; arbitrary local proof commands must fail closed.
- Pattern: `Wrapper Capture -> Gate Decision -> Explicit Enable -> Exact Resume Command -> Host-Availability Receipt`.
- Pattern: wrapper-bound capture -> gate decision -> explicit operator allow -> exact real resume command -> either bounded execution receipt or blocked host-availability receipt.
- Failure Mode: `Arbitrary Live-Command Drift`.
- Failure Mode: if explicit enablement still allows arbitrary commands, the continuation gate stops being a guarded Codex continuation seam and becomes a generic command runner.
- Release-summary bullets:
  - Froze live execution to the exact real `codex exec resume --last` command shape.
  - Proved one blocked non-resume path and one blocked current-host runtime path with `[WinError 5] Access is denied`.
  - Kept `AI Repetition-to-Automation Pipeline` flat at `30%`.
  - Moved the exact next packet to `AI Repetition-to-Automation Pipeline Guarded Codex Continuation Gate Windows Codex Runtime Availability Boundary Pass 18`.

# 2026-06-04 - Explicit enablement must stay separate from dry-run disablement

- Rule: `No Live Execution Without Explicit Enable And Wrapper Capture`.
- Rule: `--no-dry-run` alone must never be enough to run a continuation command; live execution requires both explicit operator allow and admitted wrapper-bound receipt capture.
- Pattern: `Capture -> Decision -> Explicit Enable -> One Bounded Command`.
- Pattern: wrapper-bound capture -> gate decision -> explicit operator allow -> one bounded command -> durable execution-status receipt.
- Failure Mode: `No-Dry-Run Drift`.
- Failure Mode: if `--no-dry-run` alone can run commands, the continuation gate silently collapses from guarded classifier into an accidental command runner.
- Release-summary bullets:
  - Froze the explicit enable boundary for the guarded continuation gate.
  - Proved one blocked path for missing allow flag, one blocked path for non-wrapper input, and one admitted bounded local proof command.
  - Kept `AI Repetition-to-Automation Pipeline` flat at `30%`.
  - Moved the exact next packet to `AI Repetition-to-Automation Pipeline Guarded Codex Continuation Gate Real Codex Resume Command Admission Pass 17`.

# 2026-06-04 - Admit live capture before explicit continuation enablement

- Rule: `Admit Capture Before Enablement`.
- Rule: a continuation gate may not discuss explicit live enablement until one wrapper-shaped transcript can be converted into the same durable decision contract as the dry-run result-file path.
- Pattern: `Wrapper Transcript -> Extract Result -> Gate Decision`.
- Pattern: wrapper/session transcript -> extract final ATLAS continuation result -> validate bounded truth -> emit durable decision receipts -> stop unless explicit enablement is separately admitted.
- Failure Mode: `Captureless Auto-Continue Claim`.
- Failure Mode: if live continuation is discussed before wrapper-shaped receipt capture is proven, the automation lane overclaims maturity and loses inspectable proof of what was actually evaluated.
- Release-summary bullets:
  - Admitted one wrapper-bound live-shaped JSONL receipt-capture path for the guarded continuation gate.
  - Kept auto-continuation disabled by default while proving durable JSON and Markdown decision receipts from live-shaped input.
  - Kept `AI Repetition-to-Automation Pipeline` flat at `30%`.
  - Moved the exact next packet to `AI Repetition-to-Automation Pipeline Guarded Codex Continuation Gate Explicit-Enable Boundary And Wrapper-Chain Admission Pass 16`.

# 2026-06-04 - Guarded continuation must freeze stop conditions before it becomes automation

- Rule: `Guard Continue, Do Not Blind Continue`.
- Rule: repeated Codex continuation asks may enter automation candidacy only after the result contract, validator baseline, stop conditions, and durable decision-receipt path are all explicit.
- Pattern: `Bounded Result -> Gate Decision -> Continue Or Stop`.
- Pattern: bounded Codex slice finishes -> emit exact changed-path and next-move result -> run validator-aware gate in dry-run -> continue only when scope, held-lane, and forbidden-class checks still pass.
- Failure Mode: `Blind Continuation Drift`.
- Failure Mode: if `continue` becomes a macro before machine-readable result shape and stop conditions are frozen, the automation lane silently widens into stale-slice replay, doctrine creep, deploy judgment, or destructive cleanup claims.
- Release-summary bullets:
  - Froze one exact guarded continuation contract for repeated manual Codex `continue` asks.
  - Landed one dry-run-only ATLAS gate skeleton, result schema, and prompt template under `ops/codex`.
  - Kept `AI Repetition-to-Automation Pipeline` flat at `30%`.
  - Moved the exact next packet to `AI Repetition-to-Automation Pipeline Guarded Codex Continuation Gate Live Receipt-Capture Admission Pass 15`.

# 2026-06-04 - Reconcile the receipt-package worker cluster once

- Rule: `Reconcile the closed worker cluster once`.
- Rule: after the admitted first slice lands and its proof-and-receipt follow-on closes, root reconciles the cluster once and does not keep replaying packet 1 or packet 2 as fresh next moves.
- Pattern: `admit first slice -> land bounded worker -> harden proof and receipt discipline immediately -> root reconciles once -> no new slice opens by default`.
- Failure Mode: `Third-Family Cluster Replay Drift`.
- Failure Mode: if the already-closed receipt-package worker cluster gets replayed as separate new root steps, the restart spines narrate stale micro-steps instead of the current bounded truth.
- Release-summary bullets:
  - Reconciled the closed first receipt-package worker cluster at the root layer.
  - Ratcheted `_stack Readiness` from `96%` to `97%`.
  - Kept `AI Repetition-to-Automation Pipeline` flat at `30%`.
  - Moved the exact next packet to `none immediate inside _stack Readiness for this first receipt-package slice`.

# 2026-06-04 - Close receipt-package implementation-readiness before worker routing

- Rule: `Receipt-Package Implementation-Ready Means Bounded And Guarded`.
- Rule: implementation-ready for a receipt-package first slice means all design, proof, and handoff seams are frozen and the next move is one bounded worker, not broad automation maturity, doctrine authority, or receipt-finality authority.
- Pattern: `Freeze Receipt-Package Design -> Proof -> Handoff -> Route Worker`.
- Pattern: freeze command -> freeze evidence -> freeze report -> freeze implementation guard -> freeze proof boundary -> freeze first slice -> freeze handoff -> close readiness -> route to one bounded worker.
- Failure Mode: `Receipt-Package Routing Drift After Handoff`.
- Failure Mode: if worker-routing starts before closeout is explicit, the admitted first slice widens into broader execution, doctrine, or authority claims than the frozen receipt-package chain allows.
- Release-summary bullets:
  - Froze one exact implementation-readiness closeout and worker-routing rule for `stack receipt package <lane>`.
  - Ratcheted `_stack Readiness` from `95%` to `96%`.
  - Kept `AI Repetition-to-Automation Pipeline` flat at `30%`.
  - Moved the exact next packet to `_stack stack receipt package first-implementation worker packet 1`.

# 2026-06-04 - Freeze the receipt-package worker handoff before first-slice implementation

- Rule: `Freeze Receipt-Package Worker Handoff Before First-Slice Implementation`.
- Rule: do not authorize first-slice receipt-package implementation work until the worker inherits one exact objective, one exact output contract, one exact proof matrix, one verbatim no-execution guard, and exact stop conditions.
- Pattern: `Guarded Receipt-Package Worker Handoff`.
- Pattern: freeze first slice -> freeze proof matrix -> freeze prompt-pack and handoff contract -> only then decide whether the design chain is materially complete enough to route to implementation.
- Failure Mode: `Receipt-Package Scope Bleed Through Handoff`.
- Failure Mode: if the worker handoff stays implicit, the admitted first slice starts absorbing broader execution, doctrine, or authority claims than the frozen receipt-package chain allows.
- Release-summary bullets:
  - Froze one exact first-implementation prompt-pack and handoff contract for `stack receipt package <lane>`.
  - Ratcheted `_stack Readiness` from `94%` to `95%`.
  - Kept `AI Repetition-to-Automation Pipeline` flat at `30%`.
  - Moved the exact next packet to `_stack Readiness stack receipt package implementation-readiness closeout and worker-routing pass 40`.

# 2026-06-04 - Freeze the receipt-package first slice before worker handoff

- Rule: `Receipt-Package Proof Matrix Before Slice Expansion`.
- Rule: a first receipt-package implementation slice should not be treated as admitted until its proof matrix is explicit enough to bound what counts as success, contradiction, fallback, and non-admission.
- Pattern: `Guarded Receipt-Package First Slice`.
- Pattern: freeze command -> freeze evidence -> freeze report -> freeze implementation guard -> freeze fixture truth limits -> freeze first slice -> freeze worker handoff.
- Failure Mode: `Receipt-Package Slice Inflation Through Support Work`.
- Failure Mode: if a narrowly admitted receipt-package family starts absorbing broader execution or doctrine claims before the proof matrix is explicit, the lane fakes implementation maturity.
- Release-summary bullets:
  - Froze one exact first implementation slice and proof matrix for `stack receipt package <lane>`.
  - Ratcheted `_stack Readiness` from `93%` to `94%`.
  - Kept `AI Repetition-to-Automation Pipeline` flat at `30%`.
  - Moved the exact next packet to `_stack Readiness stack receipt package first-implementation prompt-pack and handoff contract pass 39`.

# 2026-06-04 - Freeze receipt-package fixture proof before first-slice planning

- Rule: `Freeze Receipt-Package Fixture Proof Before Verified Claim`.
- Rule: do not let receipt-package implementation claim to be verified until the exact fixture/static provenance and truth-limit boundary are frozen.
- Pattern: `Receipt-Package Proof Boundary`.
- Pattern: freeze implementation boundary -> freeze lane/marker/restart fixture provenance -> freeze allowed verification scope -> only then admit first code slice planning.
- Failure Mode: `Synthetic Receipt Basis Truth Inflation`.
- Failure Mode: if replayed Book or receipt-shaped fixtures start reading like live lane truth, the support lane begins overstating what local proof has actually established.
- Release-summary bullets:
  - Froze one exact fixture-proof and static-input boundary for `stack receipt package <lane>`.
  - Ratcheted `_stack Readiness` from `92%` to `93%`.
  - Kept `AI Repetition-to-Automation Pipeline` flat at `30%`.
  - Moved the exact next packet to `_stack Readiness stack receipt package first-implementation-slice and proof-matrix admission pass 38`.

# 2026-06-04 - Freeze the no-execution guard before fixture proof

- Rule: `No Receipt-Package Execution Before Admission`.
- Rule: a receipt-package family must not drift from contract, evidence, and report truth into implementation behavior until an explicit implementation-admission boundary is crossed.
- Pattern: `Guarded Receipt-Package Support Lane`.
- Pattern: supporting lane admitted -> command purpose frozen -> evidence gate frozen -> report contract frozen -> implementation boundary frozen -> fixture-only proof boundary next.
- Failure Mode: `Receipt-Package Implementation Drift Through Support Work`.
- Failure Mode: if a support lane smuggles in receipt-package execution behavior before the admitted boundary and verbatim no-execution guard are frozen, the lane starts claiming execution maturity it has not earned.
- Release-summary bullets:
  - Froze one exact implementation-admission boundary and verbatim no-execution guard for `stack receipt package <lane>`.
  - Ratcheted `_stack Readiness` from `91%` to `92%`.
  - Kept `AI Repetition-to-Automation Pipeline` flat at `30%`.
  - Moved the exact next packet to `_stack Readiness stack receipt package fixture-proof and static-input boundary pass 37`.

# 2026-06-04 - Freeze placeholder fallback before implementation admission

- Rule: `Placeholder Fallback Must Stay Explicit`.
- Rule: if restart or cited receipt context disagrees but authoritative lane and marker truth still hold, package the draft skeleton with placeholders and route one bounded reconciliation packet instead of smoothing the contradiction into filled receipt wording.
- Pattern: `Authoritative Draft Skeleton, Fail-Closed Context`.
- Pattern: authoritative lane and marker truth -> optional agreeing restart context -> optional same-story cited receipt -> placeholder fallback on context failure -> no finality or implementation claim.
- Failure Mode: `Pretty Skeleton Overclaim`.
- Failure Mode: if a draft skeleton collapses contradiction into polished prose, the helper starts sounding more certain than the governed lane and restart surfaces actually are.
- Release-summary bullets:
  - Froze one exact report contract and contradiction-routing rule for `stack receipt package <lane>`.
  - Ratcheted `_stack Readiness` from `90%` to `91%`.
  - Kept `AI Repetition-to-Automation Pipeline` flat at `30%`.
  - Moved the exact next packet to `_stack Readiness stack receipt package implementation-admission and no-execution guard pass 36`.

# 2026-06-04 - Freeze receipt-basis discipline before report shaping

- Rule: `Receipt Skeleton Context Must Come From The Live Restart Spine`.
- Rule: receipt-skeleton packaging may fill next-package or same-story support fields only when the current ATLAS restart spine agrees and any cited receipt belongs to that same bounded story.
- Pattern: `Authoritative Lane, Authoritative Marker, Derivative Receipt Context`.
- Pattern: current lane state -> current marker posture -> agreeing restart mirrors -> optional same-story cited receipt -> fail closed or placeholder fallback on contradiction.
- Failure Mode: `Receipt Basis Drift Through Skeleton Packaging`.
- Failure Mode: if a draft skeleton mixes current lane state with stale restart mirrors or superseded receipt context, the packager starts sounding governed while its basis is no longer durable.
- Release-summary bullets:
  - Froze one exact evidence-admission and receipt-basis spine for `stack receipt package <lane>`.
  - Ratcheted `_stack Readiness` from `89%` to `90%`.
  - Kept `AI Repetition-to-Automation Pipeline` flat at `30%`.
  - Moved the exact next packet to `_stack Readiness stack receipt package report-contract and contradiction-routing pass 35`.

# 2026-06-04 - Freeze the receipt-package command spine before receipt-basis routing

- Rule: `Freeze Receipt Package Command Spine Before Evidence Routing`.
- Rule: once a receipt-skeleton subfamily is admitted to `_stack`, support work should freeze the helper's purpose, inputs, outputs, and draft-only guard before opening evidence-admission or implementation questions.
- Pattern: `Receipt Package Command Spine`.
- Pattern: freeze subfamily contract -> admit supporting lane -> freeze command purpose, inputs, outputs, failure exits, and draft-only guard -> only then evaluate evidence admission or implementation readiness.
- Failure Mode: `Receipt Skeleton Scope Inflation`.
- Failure Mode: if a lane jumps from support admission straight into evidence or implementation work, the receipt-packaging helper starts sounding like final receipt authority instead of bounded draft structure.
- Release-summary bullets:
  - Froze one exact `_stack` command spine for `stack receipt package <lane>`.
  - Ratcheted `_stack Readiness` from `88%` to `89%`.
  - Kept `AI Repetition-to-Automation Pipeline` flat at `30%`.
  - Moved the exact next packet to `_stack Readiness stack receipt package evidence-admission and receipt-basis discipline pass 34`.

# 2026-06-04 - Admit subfamily support only after the receipt-skeleton contract exists

- Rule: `Support Admission After Subfamily Contract`.
- Rule: after a combined family is split, supporting-lane admission for the chosen subfamily should be decided only after that exact subfamily contract is frozen.
- Pattern: `Subfamily Support Gate`.
- Pattern: split the family -> choose one exact subfamily -> freeze its contract -> admit support separately -> then freeze the support-lane command seam.
- Failure Mode: `Premature Support Assumption`.
- Failure Mode: if a draft subfamily implies its supporting lane before the support boundary is explicitly admitted from durable owner and candidate truth, the lane fakes readiness and drifts into convenience routing.
- Release-summary bullets:
  - Admitted `_stack Readiness` as the direct supporting lane for `receipt skeleton drafts`.
  - Kept `doctrine-routing drafts` explicitly deferred.
  - Kept both `AI Repetition-to-Automation Pipeline` at `30%` and `_stack Readiness` at `88%`.
  - Moved the exact next packet to `_stack Readiness stack receipt package command-design pass 33`.

# 2026-06-04 - Freeze the chosen receipt-skeleton subfamily before support admission

- Rule: `Subfamily Contract Before Subfamily Expansion`.
- Rule: once a combined family is split, the next honest move is freezing the exact contract of the chosen subfamily before helper expansion or sibling-subfamily work.
- Pattern: `Chosen-Subfamily Narrowing`.
- Pattern: split the family -> choose the safer first subfamily -> freeze that subfamily contract -> only then ask whether support-lane admission is justified.
- Failure Mode: `Split-Family Recombination Drift`.
- Failure Mode: if a split family quietly recombines sibling subfamilies during follow-on work, the lane stops being restart-safe and the owner boundary drifts again.
- Release-summary bullets:
  - Froze the exact contract for `receipt skeleton drafts`.
  - Kept `doctrine-routing drafts` explicitly deferred.
  - Kept supporting-lane posture at `none yet`.
  - Moved the exact next packet to `AI Repetition-to-Automation Pipeline Receipt Skeleton Drafts Supporting-Lane Admission Pass 13`.

# 2026-06-04 - Split the combined third family before reopening support

- Rule: `Split Combined Family Before Expansion`.
- Rule: when a selected automation family spans multiple owner-facing surfaces, split it into exact subfamilies before reopening any support lane or subfamily implementation packet.
- Pattern: `Owner-Boundary Subfamily Split`.
- Pattern: freeze combined contract -> admit split owner boundary -> split exact subfamilies -> choose the safer first subfamily -> freeze that subfamily before reopening support.
- Failure Mode: `False Single-Owner Collapse`.
- Failure Mode: if multiple owner surfaces are compressed into one family story, the next implementation packet reopens the wrong lane and the draft family stops being restart-safe.
- Release-summary bullets:
  - Split the combined third family into `receipt skeleton drafts` and `doctrine-routing drafts`.
  - Chose `receipt skeleton drafts` as the honest first subfamily to advance next.
  - Kept supporting-lane posture at `none new yet`.
  - Moved the exact next packet to `AI Repetition-to-Automation Pipeline Receipt Skeleton Drafts Subfamily Contract Freeze Pass 12`.

# 2026-06-04 - Freeze the split owner surface before draft-family reopen

- Rule: `Split Owner Surface Before Helper Reopen`.
- Rule: when a selected automation family actually spans multiple best-owner surfaces, freeze that split before reopening any support lane or helper implementation packet.
- Pattern: `ATLAS Truth, _stack Receipt Draft, Playbook Doctrine Draft`.
- Pattern: contract-freeze the combined family -> admit the split owner-facing surfaces -> split into exact subfamilies -> only then reopen the relevant owner-side lane.
- Failure Mode: `Merged Draft Owner Drift`.
- Failure Mode: if receipt skeletons and doctrine routing are forced into one convenience owner surface, future implementation reopens the wrong lane or blurs execution ownership with doctrine ownership.
- Release-summary bullets:
  - Froze the split owner-facing admission for `receipt skeleton and doctrine-routing drafts`.
  - Kept both `AI Repetition-to-Automation Pipeline` at `30%` and `_stack Readiness` at `88%`.
  - Kept supporting-lane posture at `none new yet` at the combined-family level.
  - Moved the exact next packet to `AI Repetition-to-Automation Pipeline Receipt Skeleton And Doctrine-Routing Drafts Subfamily Split Pass 11`.

# 2026-06-04 - Freeze the receipt/doctrine draft contract before surface admission

- Rule: `Contract Before Draft Execution`.
- Rule: a draft-oriented automation family must freeze its structure, routing, and stop-condition contract before any helper-home or doctrine-facing admission is considered.
- Pattern: `Receipt Skeleton As Safe Surface`.
- Pattern: select the third safe family -> freeze draft trigger and output contract -> keep supporting lanes held -> ask owner-surface admission separately.
- Failure Mode: `Draft Family Inflation`.
- Failure Mode: if a receipt/doctrine draft family widens into doctrine admission, publication judgment, or proof-pack packaging before its own contract is explicit, the lane creates fake progress instead of safe bounded preparation truth.
- Release-summary bullets:
  - Froze the exact contract for `receipt skeleton and doctrine-routing drafts`.
  - Kept both `AI Repetition-to-Automation Pipeline` at `30%` and `_stack Readiness` at `88%`.
  - Kept supporting-lane posture at `none new yet` for the third family.
  - Moved the exact next packet to `AI Repetition-to-Automation Pipeline Receipt Skeleton And Doctrine-Routing Drafts Owner-Surface Admission Pass 10`.

# 2026-06-04 - Select the third safe automation family after two closed slices

- Rule: `Third Safe Family After First Two Closeouts`.
- Rule: once the first two admitted automation families are honestly closed at their current thresholds, continue the active automation lane by selecting the next safe family instead of forcing more `_stack` motion inside those closed slices.
- Pattern: `Closed-Family Handoff`.
- Pattern: close first family -> close second family -> keep `_stack Readiness` held -> promote the next docs-first candidate family that stays inside hardened truth and receipt surfaces.
- Failure Mode: `Closed-Family Replay Drift`.
- Failure Mode: if the automation lane keeps narrating more work inside already-closed first slices, the lane starts faking momentum instead of admitting that the honest next move is a new bounded family selection.
- Release-summary bullets:
  - Selected `receipt skeleton and doctrine-routing drafts` as the third safe candidate family for `AI Repetition-to-Automation Pipeline`.
  - Kept both `AI Repetition-to-Automation Pipeline` at `30%` and `_stack Readiness` at `88%`.
  - Kept release-proof packaging and QA/LLEL proof-packet preparation deferred below the selected third family.
  - Moved the exact next packet to `AI Repetition-to-Automation Pipeline Receipt Skeleton And Doctrine-Routing Drafts Contract Freeze Pass 9`.

# 2026-06-04 - Reconcile marker worker cluster after first-slice closeout

- Rule: `Reconcile Closed Worker Cluster Once`.
- Rule: once a bounded first-slice worker landing and its immediate proof-hardening follow-on are both already complete, root should reconcile the closed cluster once instead of replaying stale micro next-steps.
- Pattern: `Land Marker Slice -> Harden Proof -> Reconcile Cluster -> Hold`.
- Pattern: land the admitted first marker-checkpoint slice -> tighten receipt and proof discipline immediately -> ratchet once on executed-state change -> close the slice with conditional reopen rules.
- Failure Mode: `Marker Cluster Replay Drift`.
- Failure Mode: if root keeps narrating packet-1 and packet-2 as new moves after the worker cluster already closed, shared restart surfaces drift into duplicate package narration and stale next-packet claims.
- Release-summary bullets:
  - Reconciled the closed `_stack` marker-checkpoint worker cluster in one root receipt.
  - Ratcheted `_stack Readiness` from `87%` to `88%` on the smallest honest executed-state change for the admitted second family.
  - Refreshed current validation posture to `critical=0 error=3 warning=496 info=0`.
  - Moved the exact next packet to `none immediate inside _stack Readiness for this first marker-checkpoint slice`.

# 2026-06-04 - Close marker readiness before worker execution

- Rule: `Marker Implementation-Ready Means Bounded And Guarded`.
- Rule: implementation-ready for a marker-checkpoint first slice means all design, proof, and handoff seams are frozen and the next move is one bounded worker, not broad automation maturity or ratchet authority.
- Pattern: `Freeze Marker Design -> Proof -> Handoff -> Route Worker`.
- Pattern: freeze command -> freeze evidence -> freeze report -> freeze implementation guard -> freeze proof boundary -> freeze first slice -> freeze handoff -> close readiness -> route to one bounded worker.
- Failure Mode: `Marker Routing Drift After Handoff`.
- Failure Mode: if worker-routing begins before implementation-readiness closeout is explicit, prompt wording or adjacent urgency widens the admitted first slice into broader execution, broader mutation, or broader authority claims than the frozen marker-checkpoint chain actually allows.
- Release-summary bullets:
  - Closed the remaining docs-only implementation-readiness ambiguity for `_stack` marker-checkpoint first-slice work.
  - Ratcheted `_stack Readiness` from `86%` to `87%` on the smallest honest readiness-closeout seam for the second admitted family.
  - Moved the exact next packet to `_stack stack marker checkpoint first-implementation worker packet 1`.

# 2026-06-04 - Freeze marker worker handoff before first-slice implementation

- Rule: `Freeze Marker Worker Handoff Before First-Slice Implementation`.
- Rule: do not authorize first-slice marker-checkpoint implementation work until the worker inherits one exact objective, one exact output contract, one exact proof matrix, one verbatim no-execution guard, and exact stop conditions.
- Pattern: `Guarded Marker Worker Handoff`.
- Pattern: freeze first slice -> freeze proof matrix -> freeze prompt-pack and handoff contract -> only then decide whether the design chain is materially complete enough to route to implementation.
- Failure Mode: `Marker Scope Bleed Through Handoff`.
- Failure Mode: if the worker handoff contract is left implicit, the admitted first slice expands through prompt wording into broader execution, broader mutation, or broader authority claims than the frozen marker-checkpoint chain actually allows.
- Release-summary bullets:
  - Froze the exact worker objective and inherited contract spine for `_stack` marker-checkpoint first-slice implementation.
  - Ratcheted `_stack Readiness` from `85%` to `86%` on the smallest honest worker-handoff seam for the second admitted family.
  - Moved the exact next packet to `_stack Readiness stack marker checkpoint implementation-readiness closeout and worker-routing pass 32`.

# 2026-06-04 - Freeze marker proof matrix before first slice expansion

- Rule: `Marker Proof Matrix Before Slice Expansion`.
- Rule: a first marker-checkpoint implementation slice should not be treated as admitted until its proof matrix is explicit enough to bound what counts as success, contradiction, and non-admission.
- Pattern: `Guarded Marker First Slice`.
- Pattern: freeze command -> freeze evidence -> freeze report -> freeze implementation guard -> freeze fixture truth limits -> freeze first slice -> freeze worker handoff.
- Failure Mode: `Marker Slice Inflation Through Support Work`.
- Failure Mode: a support lane becomes fake progress when a narrowly admitted marker-checkpoint family expands into broader execution or adjacent automation claims without proof-matrix discipline.
- Release-summary bullets:
  - Froze the narrowest first implementation slice for `stack marker checkpoint` after the local-proof boundary closed.
  - Ratcheted `_stack Readiness` from `84%` to `85%` on the smallest honest first-slice admission seam for the second admitted family.
  - Moved the exact next packet to `_stack Readiness stack marker checkpoint first-implementation prompt-pack and handoff contract pass 31`.

# 2026-06-04 - Freeze marker fixture proof before verified claim

- Rule: `Freeze Marker Fixture Proof Before Verified Claim`.
- Rule: do not let marker-checkpoint implementation claim to be verified until the exact fixture/static provenance and truth-limit boundary are frozen.
- Pattern: `Checkpoint Fixture Proof Boundary`.
- Pattern: freeze implementation boundary -> freeze marker/restart fixture provenance -> freeze allowed verification scope -> only then admit first code slice planning.
- Failure Mode: `Synthetic Checkpoint Truth Inflation`.
- Failure Mode: rich local fixtures or replayed book snapshots can start to look like live marker truth, so a future command appears proven even though it has only passed synthetic or replayed checkpoint-shape checks.
- Release-summary bullets:
  - Froze the exact fixture/static-input boundary for `stack marker checkpoint` after implementation admission closed.
  - Ratcheted `_stack Readiness` from `83%` to `84%` on the smallest honest verification-boundary seam for the second admitted family.
  - Moved the exact next packet to `_stack Readiness stack marker checkpoint first-implementation-slice and proof-matrix admission pass 30`.

# 2026-06-04 - Freeze marker implementation admission before fixture proof

- Rule: `No Marker-Checkpoint Execution Before Admission`.
- Rule: a marker-checkpoint family must not drift from contract, evidence, and report truth into implementation behavior until an explicit implementation-admission boundary is crossed.
- Pattern: `Guarded Marker Support Lane`.
- Pattern: helper home admitted -> command purpose frozen -> evidence gate frozen -> report contract frozen -> implementation boundary frozen -> fixture-only proof boundary next.
- Failure Mode: `Marker Implementation Drift Through Support Work`.
- Failure Mode: a support lane becomes fake progress when it smuggles in checkpoint execution behavior before the admission boundary and no-execution guard are explicitly frozen.
- Release-summary bullets:
  - Froze the exact implementation-admission boundary for `stack marker checkpoint` after command, evidence, and report shape were already explicit.
  - Ratcheted `_stack Readiness` from `82%` to `83%` on the smallest honest implementation-boundary seam for the second admitted family.
  - Moved the exact next packet to `_stack Readiness stack marker checkpoint fixture-proof and static-input boundary pass 29`.

# 2026-06-04 - Make checkpoint-only fallback explicit before implementation

- Rule: `Checkpoint-Only Fallback Must Stay Explicit`.
- Rule: if restart context disagrees but authoritative marker truth still holds, package the checkpoint only and route one bounded reconciliation packet instead of smoothing the contradiction into next-package prose.
- Pattern: `Authoritative Checkpoint, Fail-Closed Context`.
- Pattern: authoritative marker checkpoint -> optional agreeing restart context -> optional same-story cited receipt -> checkpoint-only fallback on context failure -> no ratchet or implementation claim.
- Failure Mode: `Pretty Checkpoint Overclaim`.
- Failure Mode: if the report contract lets restart-context failure collapse into polished prose instead of an explicit checkpoint-only fallback, the helper sounds more certain than the governed marker and restart surfaces actually are.
- Release-summary bullets:
  - Froze the receipt-ready report contract for `stack marker checkpoint` across checkpoint-only, checkpoint-plus-context, and explicit context-unavailable paths.
  - Ratcheted `_stack Readiness` from `81%` to `82%` on the smallest honest report-contract seam for the second admitted family.
  - Moved the exact next packet to `_stack Readiness stack marker checkpoint implementation-admission and no-execution guard pass 28`.

# 2026-06-04 - Checkpoint context must come from the live restart spine

- Rule: `Checkpoint Context Must Come From The Live Restart Spine`.
- Rule: marker checkpoint rendering may cite next-package or hold-reason context only when the current restart spine agrees and the cited receipt belongs to that same bounded story.
- Pattern: `Authoritative Marker, Derivative Restart Context`.
- Pattern: current marker table -> agreeing restart mirrors -> optional same-story cited receipt -> fail closed on contradiction or stale context.
- Failure Mode: `Restart Context Drift Through Checkpoint Rendering`.
- Failure Mode: if marker-checkpoint wording is allowed to mix the current marker table with stale restart mirrors, uncited receipt memory, or superseded package ladders, the helper sounds precise while the routing truth is no longer governed.
- Release-summary bullets:
  - Froze the exact evidence hierarchy for `stack marker checkpoint`: authoritative marker truth from `02-lanes-and-markers.md`, derivative restart mirrors, and optional same-story cited receipt context.
  - Ratcheted `_stack Readiness` from `80%` to `81%` on the smallest honest evidence-admission seam for the second admitted family.
  - Moved the exact next packet to `_stack Readiness stack marker checkpoint report-contract and contradiction-routing pass 27`.

# 2026-06-04 - Freeze marker command spine before evidence routing

- Rule: `Freeze Marker Command Spine Before Evidence Routing`.
- Rule: once a marker-checkpoint family is admitted to `_stack`, support work should freeze the helper's purpose, inputs, outputs, and no-ratchet guard before opening evidence-admission or implementation questions.
- Pattern: `Marker Checkpoint Command Spine`.
- Pattern: freeze family contract -> admit helper home -> freeze command purpose, inputs, outputs, failure exits, and no-ratchet guard -> only then evaluate evidence admission or implementation readiness.
- Failure Mode: `Checkpoint Helper Scope Inflation`.
- Failure Mode: if a lane skips the command spine and jumps straight from helper-home admission into evidence or implementation work, the marker-checkpoint helper starts sounding like ratchet authority or generalized coordination logic before its bounded operator surface is explicit.
- Release-summary bullets:
  - Froze one exact `_stack` command-design spine for `stack marker checkpoint` after helper-home admission landed.
  - Ratcheted `_stack Readiness` from `79%` to `80%` on the smallest honest new operator-facing command seam.
  - Moved the exact next packet to `_stack Readiness stack marker checkpoint evidence-admission and restart-surface discipline pass 26`.

# 2026-06-04 - Marker truth owner and helper home can differ

- Rule: `Marker Truth Owner And Helper Home Can Differ`.
- Rule: a repeated marker-checkpoint family may keep truth ownership in ATLAS while assigning helper-home ownership to `_stack` when the work is shared operator execution rather than doctrine, product runtime, or consumer projection.
- Pattern: `ATLAS Truth, _stack Marker Helper`.
- Pattern: freeze marker-checkpoint contract in ATLAS -> admit `_stack` as helper home for shared execution -> keep marker truth, receipt consequence, and ratchet judgment in ATLAS.
- Failure Mode: `Root Marker Helper Drift`.
- Failure Mode: if ATLAS root keeps helper-home ownership for a marker-checkpoint family that already belongs on `_stack`, the system confuses marker truth recording with governed execution and future implementation work reopens the wrong lane.
- Release-summary bullets:
  - Admitted `_stack` as the helper home for `marker checkpoint rendering` while keeping ATLAS as the truth owner.
  - Opened `_stack Readiness` as the direct supporting dependency for the second family.
  - Moved the exact next packet to `_stack Readiness stack marker checkpoint command-design pass 25`.

# 2026-06-03 - Freeze checkpoint render contract before helper admission

- Rule: `Freeze Checkpoint Contract Before Helper Admission`.
- Rule: do not bind marker checkpoint rendering to a helper home or ratchet-facing surface until the projection contract itself is explicit and restart-safe.
- Pattern: `Marker Projection Before Surface Admission`.
- Pattern: select second-safe seam -> freeze trigger, stable inputs, expected checkpoint artifact, failure boundary, safe fallback, owner boundary, and non-claim boundary -> only then decide whether `_stack` or another surface should host the helper.
- Failure Mode: `Checkpoint Render Overclaim`.
- Failure Mode: if a marker-checkpoint helper is admitted before its projection contract is explicit, the render path starts sounding like ratchet authority, supporting lanes reopen too early, and restart surfaces drift from decisive receipts.
- Release-summary bullets:
  - Froze `marker checkpoint rendering` as the second-family contract without reopening `_stack` or Playbook.
  - Kept supporting-lane posture at `none new yet` for the second family while `_stack Readiness` stays held for the closed first family only.
  - Moved the exact next packet to `AI Repetition-to-Automation Pipeline Marker Checkpoint Rendering Owner-Surface Admission Pass 7`.

# 2026-06-03 - Promote the next safe family after the first one closes

- Rule: `Second Safe Family After First Family Closeout`.
- Rule: once a first admitted automation family reaches an honest stop point, continue the active lane by selecting the next safe family rather than forcing more motion inside the closed family.
- Pattern: `Adjacent Safe Family Promotion`.
- Pattern: close first family cleanly -> compare deferred families again -> pick the nearest family that reuses hardened truth surfaces without reopening execution, deploy, or authority lanes.
- Failure Mode: `Family Replay Drift`.
- Failure Mode: the automation lane loses honesty when it keeps replaying a closed first family instead of admitting that the next move is a different safe family.
- Release-summary bullets:
  - Kept the first validation-summary family closed at its current threshold instead of reopening `_stack` from momentum alone.
  - Selected `marker checkpoint rendering` as the second safe family because it stays adjacent to hardened validation and marker truth without widening authority.
  - Kept both `_stack Readiness` and `AI Repetition-to-Automation Pipeline` flat while moving the exact next packet to a second-family contract freeze.

# 2026-06-03 - Tighten receipt discipline after first execution

- Rule: `Receipt Discipline After First Execution`.
- Rule: once a first admitted slice executes successfully, the next honest step is tightening proof and receipt discipline before opening any broader slice.
- Pattern: `Executed Slice Reconciliation`.
- Pattern: executed slice lands -> required and optional report fields get locked -> bounded path discipline gets proven -> root reconciles once -> no new slice opens by default.
- Failure Mode: `Proof Drift After First Success`.
- Failure Mode: if a first successful packet is not immediately followed by proof and receipt tightening, the lane starts sounding more mature than the frozen contract actually proves.
- Release-summary bullets:
  - Hardened the first `_stack` validation-summary slice with explicit required-field, optional-field, unavailable-delta, and bounded-path proof.
  - Kept `_stack Readiness` flat because this was proof hardening inside the admitted slice, not a broader execution threshold.
  - Closed the immediate `_stack` first-slice cluster with no new supporting packet open by default.

# 2026-06-03 - Operate only inside admitted slice

- Rule: `Operate Only Inside Admitted Slice`.
- Rule: once a family becomes worker-routable, execution must remain inside the already-admitted slice until new evidence explicitly expands it.
- Pattern: `Proof-Matrix-Bounded Worker Packet`.
- Pattern: frozen contract spine -> frozen proof matrix -> bounded worker landing -> drift classification -> proof-and-receipt follow-on.
- Failure Mode: `Worker Packet Scope Leak`.
- Failure Mode: if a routable first slice expands into adjacent automation claims, broader repo mutation, or report semantics outside the frozen proof matrix, the packet creates fake progress instead of bounded execution truth.
- Release-summary bullets:
  - Landed the first bounded `_stack` validation-summary implementation slice inside the frozen report, proof, and no-execution guard.
  - Classified the live `stack.lock.yaml` error triplet as expected in-flight `_stack` dirty-state drift rather than canonical corruption.
  - Kept `AI Repetition-to-Automation Pipeline` flat and moved the exact next `_stack` packet to first-implementation worker proof-and-receipt packet 2.

# 2026-06-03 - Close readiness before expansion

- Rule: `Close Readiness Before Expansion`.
- Rule: once a first implementation slice and handoff contract exist, the next honest move is implementation-readiness closeout and routing discipline before broader execution or adjacent family expansion.
- Pattern: `Bounded Worker Routing`.
- Pattern: freeze first slice -> freeze proof matrix -> freeze prompt-pack and handoff -> close implementation-readiness -> route to one bounded worker.
- Failure Mode: `Routing Drift After Handoff`.
- Failure Mode: if worker-routing starts before implementation-readiness closeout is explicit, the admitted slice widens through handoff ambiguity into broader execution or broader authority than the frozen chain actually allows.
- Release-summary bullets:
  - Closed the remaining docs-only implementation-readiness ambiguity for `_stack` validation-summary first-slice work.
  - Froze the exact rule for leaving root docs-only and routing to one bounded implementation worker.
  - Moved the next `_stack` packet to first-implementation worker packet 1.

# 2026-06-03 - Freeze worker handoff before first-slice implementation

- Rule: `Freeze Worker Handoff Before First-Slice Implementation`.
- Rule: do not authorize first-slice implementation work until the worker inherits one exact objective, one exact output contract, one exact proof matrix, one verbatim no-execution guard, and exact stop conditions.
- Pattern: `Guarded Worker Handoff`.
- Pattern: freeze first slice -> freeze proof matrix -> freeze prompt-pack and handoff contract -> only then decide whether the design chain is materially complete enough to route to implementation.
- Failure Mode: `Scope Bleed Through Handoff`.
- Failure Mode: if the worker handoff contract is implicit, the admitted first slice expands through prompt wording into broader execution, broader mutation, or broader authority claims than the frozen design chain actually allows.
- Release-summary bullets:
  - Froze the exact worker objective and inherited contract spine for `_stack` validation-summary first-slice implementation.
  - Froze the exact preserved payload surface, proof obligations, allowed-touch surfaces, forbidden surfaces, and stop conditions.
  - Moved the next `_stack` packet to implementation-readiness closeout and worker-routing work.

# 2026-06-03 - Freeze proof matrix before first slice expansion

- Rule: `Proof Matrix Before Slice Expansion`.
- Rule: a first implementation slice should not be treated as admitted until its proof matrix is explicit enough to bound what counts as success, contradiction, and non-admission.
- Pattern: `Guarded First Slice`.
- Pattern: freeze command -> freeze evidence -> freeze report -> freeze implementation guard -> freeze fixture truth limits -> freeze first slice -> freeze worker handoff.
- Failure Mode: `Slice Inflation Through Support Work`.
- Failure Mode: a support lane becomes fake progress when a narrowly admitted validation-summary family expands into broader execution or adjacent automation claims without proof-matrix discipline.
- Release-summary bullets:
  - Froze the narrowest first implementation slice for `_stack` validation-summary work after the local-proof boundary closed.
  - Froze the exact proof matrix over snapshot-only, snapshot-plus-delta, baseline-unavailable, contradiction, invalid-input, and validator-failed branches.
  - Moved the next `_stack` packet to first-implementation prompt-pack and handoff-contract work.

# 2026-06-03 - Freeze fixture proof before verified claim

- Rule: `Freeze Fixture Proof Before Verified Claim`.
- Rule: do not let a validation-summary implementation claim to be verified until the exact fixture/static provenance and truth-limit boundary are frozen.
- Pattern: `Artifact-Pair Proof Boundary`.
- Pattern: freeze implementation boundary -> freeze artifact-pair and baseline-fixture provenance -> freeze allowed verification scope -> only then admit first code slice planning.
- Failure Mode: `Synthetic Snapshot Truth Inflation`.
- Failure Mode: rich local fixtures or replayed artifact snapshots can start to look like live stack truth, so a future command appears proven even though it has only passed synthetic or replayed evidence-shape checks.
- Release-summary bullets:
  - Froze the exact fixture/static-input boundary for `_stack` validation-summary work after implementation admission closed.
  - Admitted only synthetic artifact-pair fixtures, synthetic baseline fixtures, and receipt-derived/static snapshots under explicit provenance and truth-limit labeling.
  - Moved the next `_stack` packet to first-implementation-slice and proof-matrix admission work.

# 2026-06-03 - No execution before admission

- Rule: `No Execution Before Admission`.
- Rule: a validation-summary family must not drift from contract/report truth into implementation behavior until an explicit implementation-admission boundary is crossed.
- Pattern: `Guarded Support Lane`.
- Pattern: supporting lane selected -> command purpose frozen -> evidence gate frozen -> report contract frozen -> implementation boundary frozen -> fixture-only proof boundary next.
- Failure Mode: `Implementation Drift Through Support Work`.
- Failure Mode: a support lane becomes fake progress when it smuggles in execution behavior before the admission boundary and no-execution guard are explicitly frozen.
- Release-summary bullets:
  - Froze the exact implementation-admission boundary for `_stack` validation-summary work after command, evidence, and report shape were already explicit.
  - Admitted validator invocation and receipt-ready summary rendering only under the existing governed artifact path.
  - Moved the next `_stack` packet to fixture-proof and static-input boundary work after the no-execution guard closed.

# 2026-06-03 - Resume allowed does not mean replay allowed

- Rule: `Do Not Replay Consumed Planning Class`.
- Rule: if a generic next-package class has already been fully packetized and later boundary receipts paused further widening, a reopen decision may resume the lane without reopening the old class.
- Pattern: `Reopen Without Replay`.
- Pattern: bridge blocker narrows -> adjacent lane may resume -> previously consumed planning class is checked -> stale generic next package is removed instead of replayed.
- Failure Mode: `Generic Next-Package Recursion`.
- Failure Mode: if a reopen packet keeps pointing at an already-consumed planning class, the system mistakes historical packet names for fresh work and loops root coordination back into duplicate receipts.
- Release-summary bullets:
  - Reconciled the DiscordOS bridge-independent reopen against no-duplicate-package discipline.
  - Confirmed the named-port planning class was already consumed across the May 26 consumer-planning, implementation-planning, tooling/readiness, and lookup execution-readiness chain.
  - Removed the stale implication that root should reopen another generic DiscordOS planning packet by default.

# 2026-06-03 - Resume independent lane work once the blocker leaves repo/runtime truth

- Rule: `Resume Independent Lane, Park External Proof Seam`.
- Rule: when a blocker has crossed out of repo/runtime truth and into an external/session seam, resume independent owner work now and keep only the proof seam parked.
- Pattern: `Bridge-Independent Reopen`.
- Pattern: repo/runtime prerequisites green -> blocker reclassified to external/session seam -> resume independent lane packages -> keep proof-seam reopen condition explicit.
- Failure Mode: `Bridge Blocker Scope Inflation`.
- Failure Mode: if one external/session proof blocker is allowed to freeze every adjacent lane, the system reopens the wrong repo, delays independent work, and mistakes a narrow bridge hold for a global separation blocker.
- Release-summary bullets:
  - Packaged the DiscordOS consequence of the Fitness bridge reclassification: bridge-independent DiscordOS work may resume now.
  - Kept the Fitness Discord pass-9 seam explicitly parked behind live bridge recovery rather than declaring the whole Discord/Fitness boundary closed.
  - Preserved the no-runtime/no-schema/no-cutover boundary while later reconciling the stale generic next-package ladder separately.

# 2026-06-03 - Report shape must freeze before implementation admission

- Rule: `Freeze Report Shape Before Command Admission`.
- Rule: do not admit implementation work for a summary command until the success and failure payloads are specific enough that contradiction handling cannot drift into prose.
- Pattern: `Snapshot Contract Before Implementation`.
- Pattern: freeze command purpose -> freeze evidence gate -> freeze report contract -> freeze contradiction routing -> only then discuss implementation admission.
- Failure Mode: `Pretty Output Contradiction Drift`.
- Failure Mode: if a command reaches implementation before the report payload and routing notes are explicit, current snapshots, unavailable deltas, and contradictions get smoothed into prose that sounds safer than the governed evidence really is.
- Release-summary bullets:
  - Froze the receipt-ready report contract for `_stack` validation-summary work across both success and failure paths.
  - Admitted one narrow partial-snapshot exception only for `delta-baseline-unavailable` when current paired artifacts still agree.
  - Moved the next `_stack` packet to implementation-admission and no-execution guard work after report shape and contradiction routing closed.

# 2026-06-03 - Delta summaries need one exact baseline, not narrative memory

- Rule: `Delta Needs One Exact Baseline`.
- Rule: count-delta reporting is allowed only when one cited durable baseline carries one exact attributable validator tuple from the same bounded story.
- Pattern: `Receipt-Cited Count Delta`.
- Pattern: current paired artifacts -> one cited durable baseline receipt -> exact four-count comparison -> fail closed on contradiction or ambiguity.
- Failure Mode: `Narrative Delta Drift`.
- Failure Mode: if validation-summary delta wording leans on recap prose, debt-class narration, or multiple ambiguous historical counts, the command sounds precise while the baseline truth is not actually governed.
- Release-summary bullets:
  - Froze the exact current validation-summary authority at the paired latest md/json artifacts, not at restart mirrors or receipt prose.
  - Narrowed admitted `--delta-from` baselines to one cited durable receipt with one exact attributable four-count tuple from the same bounded story.
  - Moved the next `_stack` packet to report-contract and contradiction-routing work after evidence admission and delta discipline closed.

# 2026-06-03 - Normalize major ATLAS system surfaces into the Book without duplicating repo truth

- Rule: `Normalize System Role, Not Repo Detail`.
- Rule: when a major ATLAS system surface becomes important to restart, cross-system coordination, or lane selection, reconcile owner-repo truth into the ATLAS Book as restart-friendly system documentation without copying repo-local implementation detail into root doctrine.
- Pattern: `ATLAS Systems-Doc Normalization`.
- Pattern: identify one major ATLAS system surface -> read owner-repo README, architecture, and operator truth -> extract role, ownership boundaries, shipped-vs-planned surfaces, seams, and retrieval order -> publish one Book chapter plus bounded spine links -> keep repo-local command and implementation truth in the owner repo.
- Failure Mode: `Book Mirrors The Repo`.
- Failure Mode: if the Book starts duplicating command tables, implementation specifics, or repo-local contracts, root retrieval becomes noisy and drifts from the owner surface it is supposed to index.
- Release-summary bullets:
  - Made ATLAS systems-doc normalization explicit as a repeatable pattern rather than a one-off Lifeline note.
  - Bound the pattern primarily to `Truth Map & ATLAS Book`, with secondary ties to `Inventory & Truth Map`, `Knowledge Capture & Transfer`, and `Durable Context Externalization`.
  - Kept the active execution order unchanged: `AI Repetition-to-Automation Pipeline` remains active and `_stack Readiness stack validate validation-summary evidence-admission and delta-discipline pass 18` remains the next exact move.

# 2026-06-03 - Support the frozen family before expanding the family set

- Rule: `Support Frozen Family Before Expanding Family Set`.
- Rule: once a first safe automation family is selected and admitted, support work should harden its execution surface before opening adjacent candidate families.
- Pattern: `Validation Summary Command Spine`.
- Pattern: freeze the family contract in ATLAS -> admit the `_stack` command home -> freeze command purpose, inputs, outputs, and fail-closed delta discipline -> only then evaluate evidence admission or implementation readiness.
- Failure Mode: `Admission Replay Drift`.
- Failure Mode: if a lane replays already-landed admission work instead of freezing the newly required command surface, the system spends motion on explanation while `_stack` readiness does not become more executable.
- Release-summary bullets:
  - Froze one exact `_stack` command-design spine for validation summary and delta reporting after pass 4 had already admitted the execution home.
  - Kept `AI Repetition-to-Automation Pipeline` active at `30%` because no governed operator surface with repeatable proof exists yet.
  - Moved the exact next question to admitted baseline and delta-discipline handling under `_stack Readiness`, rather than widening into adjacent automation families.

# 2026-06-03 - Truth owner and command home can differ

- Rule: `Truth Owner And Command Home Can Differ`.
- Rule: a repeated family may keep truth ownership in ATLAS while assigning execution-home ownership to `_stack` when the work is shared operator execution rather than doctrine or product-runtime truth.
- Pattern: `ATLAS Truth, _stack Execution`.
- Pattern: freeze the family contract in ATLAS first, then admit `_stack` as the command home only when the family trigger, proof artifact, fallback, and non-claim boundary are already explicit.
- Failure Mode: `Root Convenience Command Drift`.
- Failure Mode: if ATLAS root keeps execution-home ownership for a family that already belongs on `_stack`, future implementation work reopens the wrong lane and confuses truth recording with governed execution.
- Release-summary bullets:
  - Admitted `_stack` as the execution home for validation summary and delta reporting while keeping ATLAS as the truth owner.
  - Opened `_stack Readiness` as the first real supporting dependency because the owner-surface admission now routes future work through a shared command surface.
  - Kept marker posture flat because owner-surface admission still stops short of implementation or repeatable proof.

# 2026-06-03 - Freeze family contract before naming command home

- Rule: `Freeze Family Contract Before Naming Command Home`.
- Rule: do not bind a repeated family to `_stack`, Playbook, Cortex, or an owner repo until the family contract itself is explicit and restart-safe.
- Pattern: `Contract Before Surface Admission`.
- Pattern: select one repeated seam -> freeze trigger, stable inputs, proof artifact, failure boundary, safe fallback, owner boundary, and non-claim boundary -> only then evaluate owner-surface admission.
- Failure Mode: `Owner-Surface Premature Binding`.
- Failure Mode: if a repeated seam gets attached to an implementation home before its contract is explicit, adjacency pressure gets mislabeled as readiness and held lanes reopen too early.
- Release-summary bullets:
  - Froze validation summary and delta reporting as one exact ATLAS-side family contract rather than leaving it as a loosely selected seam.
  - Kept supporting lane at `none yet` because contract freeze does not itself admit `_stack`, Playbook, or owner-repo dependency.
  - Routed the next question to owner-surface admission only after the family contract became restart-safe.

# 2026-06-03 - Promote repeated seams, not adjacent friction

- Rule: `Automate Repeated Seams, Not Adjacent Friction`.
- Rule: only promote a repeated seam when the repetition itself is the active, evidence-backed bottleneck rather than nearby workflow discomfort from held or blocked families.
- Pattern: `Spine-Fed Automation Candidate`.
- Pattern: derive automation-candidate truth from the hardened workflow spine and canonical restart/book substrate first, then select one bounded repeated seam before naming any implementation owner or support lane.
- Failure Mode: `Automation Drift From Boundary Amnesia`.
- Failure Mode: if a pipeline packet forgets which seams are still blocked by external/session conditions, human approval, or held-family boundaries, it starts narrating nearby friction as automation progress and reopens families that were supposed to stay held.
- Release-summary bullets:
  - Selected validation summary and delta reporting as the highest-leverage first-safe automation-candidate family from the active ATLAS-side lane.
  - Kept marker checkpoints and receipt/doctrine drafts first-safe but deferred, rather than widening into multiple families at once.
  - Preserved no supporting lane yet because the selected seam can still be frozen ATLAS-side before any implementation owner or adjacent lane needs to reopen.

## 2026-06-02 - A future-stageable subset is not the same thing as a stage-ready subset

- Rule: `Future-Stageable Is Not Stage-Ready`.
- Rule: once a dirty-root subset is bounded coherently, it may be described as a preserved future-stageable candidate only; do not call it stage-ready or commit-ready until selective staging or equivalent operational proof exists.
- Pattern: `Subset Honesty Checkpoint`.
- Pattern: boundary freeze -> direct-dependency audit -> staging-honesty check -> hold until real stage intent or worktree change exists.
- Failure Mode: `Staging Theater`.
- Failure Mode: if workers translate subset coherence into implied staging readiness, restart truth begins promising operational safety that the current checkout has not proven.
- Release-summary bullets:
  - Froze the minimum blocker-preservation subset at a future-stageable-candidate ceiling only.
  - Kept stage-ready and commit-ready claims explicitly out of bounds.
  - Closed the current root-only docs ladder inside `stabilize-root-worktree` unless real stage intent or material checkout change appears.

## 2026-06-02 - Cortex contract export must freeze before any new agent surface widens

- Rule: `Contract Before Agent`.
- Rule: no Cortex agent surface should exist without a governed contract exported from ATLAS/Playbook truth.
- Pattern: `Truth-Owned Interface Export`.
- Pattern: ATLAS defines agent contracts; Cortex consumes them without owning readiness truth.
- Failure Mode: `Interface Drift Through Dual Ownership`.
- Failure Mode: if both ATLAS and Cortex define agent truth independently, the system splits its contract model and loses determinism.
- Release-summary bullets:
  - Froze one reusable export surface for current Cortex-facing candidate families with exact fields: `contract_id`, `family_name`, `trigger`, `stable_inputs`, `expected_proof_artifact`, `fallback_path`, `owner_boundary`, `non_claim_boundary`, and `admissibility_state`.
  - Froze the current exportable-now family set as `validation-summary-shadow`, `marker-checkpoint-shadow`, and `receipt-doctrine-draft-shadow`.
  - Froze no additional family into `shadow-only` in this packet; the safe set is now either exported already or still blocked until a later family-specific contract packet lands.
  - Preserved the blocked family set as fresh live proof capture through the frozen bridge path, final deploy or publication judgment, doctrine admission, destructive cleanup or secret approval, and ambiguous visual or acceptance review.
  - Held marker posture flat because this packet froze reusable interface truth only; it did not widen live consumption proof, owner authority, or automation-ready scope.

## 2026-06-02 - Residual active-tranche files should carry only on direct subset dependency

- Rule: `Direct Dependency Before Carry`.
- Rule: a file joins the first future stageable subset only when the already-frozen subset depends on it directly for coherence, not because it is nearby, historically related, or likely useful later.
- Pattern: `Residual Boundary Audit`.
- Pattern: once the main tranche is frozen, recheck leftover files as a small residual set instead of reopening the whole tranche question.
- Failure Mode: `Residual Gravity`.
- Failure Mode: if older adjacent files keep re-entering the active tranche through familiarity, completeness pressure, or "might as well" logic, the minimum subset inflates back into a broad dirty-root story.
- Release-summary bullets:
  - Froze the earlier Cortex/read-model book and test surfaces as a later adjacent hold rather than letting them re-enter the minimum blocker-preservation subset.
  - Preserved direct-dependency admission as the only honest carry rule after the main tranche and mirror questions were already resolved.
  - Routed the next slice toward subset honesty, not more adjacency expansion.

## 2026-06-01 - Truth mirrors should travel only when the blocked subset directly depends on them

- Rule: `Mirror Follows Direct Dependency`.
- Rule: do not pull root truth mirrors into the first future stageable subset unless the blocked receipt or restart chain directly depends on those mirror updates to preserve honest state.
- Pattern: `Adjacent Mirror Hold`.
- Pattern: freeze the blocker-preservation subset first, then keep broader manifest, lock, registry, inventory, and policy mirrors as a later adjacent hold unless direct dependency is proven.
- Failure Mode: `Mirror Adjacency Creep`.
- Failure Mode: if nearby mirror files travel just because they are authoritative, the first bounded subset expands into broad topology reconciliation and loses its blocker-preservation purpose.
- Release-summary bullets:
  - Froze the seven coupled mirror surfaces as a later adjacent hold rather than carrying them with the first future stageable root-worktree subset.
  - Preserved the distinction between blocker-preservation truth and broader stack-topology mirror refresh.
  - Left later mirror travel as an explicit follow-up question instead of letting it happen by adjacency.

## 2026-06-01 - Stage the minimum coherent shared-root subset before carrying adjacent mirrors

- Rule: `Minimum Coherent Subset First`.
- Rule: when a shared-root lane is still blocked, the first future stageable subset should be the smallest coherent receipt and restart-truth chain that preserves the blocker story without dragging adjacent mirrors or support backlog by implication.
- Pattern: `Mirror Carry Later`.
- Pattern: freeze the minimum receipt-and-restart subset first, then decide in a later packet whether adjacent truth mirrors must travel with it.
- Failure Mode: `Boundary Inflation`.
- Failure Mode: if workers widen the first stageable subset just because nearby files are related, the root lane starts narrating adjacency instead of evidence and turns one bounded hold into another broad dirty-root story.
- Release-summary bullets:
  - Froze the first future stageable candidate for `stabilize-root-worktree` as the root-worktree receipt chain plus the three shared restart/index surfaces and `PLAYBOOK_NOTES.md`.
  - Kept coupled truth mirrors, older Cortex/read-model files, and mixed tracked support backlog explicitly outside that minimum subset by default.
  - Preserved later truth-mirror carry as a separate question instead of widening the first boundary by implication.

## 2026-06-01 - Shared-root stabilization should preserve held tranches before inventing commit-ready subsets

- Rule: `Held Tranche Before Commit Story`.
- Rule: after a dirty shared root checkout is fully classified, preserve the active tranche and its coupled truth mirrors as one intentional held tranche until a later packet proves a narrower stageable subset.
- Pattern: `Support Backlog Later Hold`.
- Pattern: separate mixed governance, memory, and QA support surfaces into an explicit later hold instead of smearing them across the active tranche by implication.
- Failure Mode: `Synthetic Commitability`.
- Failure Mode: if workers invent a commit-ready subset before tranche travel boundaries are explicit, restart truth overstates root stability and staging theater replaces real stabilization evidence.
- Release-summary bullets:
  - Froze the current root route: active restart surfaces plus coupled truth mirrors stay together as one intentional held stabilization tranche.
  - Separated the mixed tracked governance/memory/QA support set into a later independent hold instead of letting it widen the active tranche or collapse into cleanup residue.
  - Refused to imply commit/staging readiness from classification alone, so future sessions inherit one explicit route instead of another dirty-root reinventory pass.

## 2026-06-01 - Green validation does not outrank a broad dirty shared root

- Rule: `Shared Root Cleanliness Gate`.
- Rule: when the ATLAS root is a shared active writer surface and `git status` shows broad modified or untracked root-owned state, freeze new lane claims and publication decisions until that dirty state is explicitly classified or intentionally preserved.
- Pattern: `Classify Before Cleanup`.
- Pattern: read-model blocker -> dirty-root inventory -> ownership and retention split -> explicit preserve/cleanup decision -> only then resume lane advancement.
- Failure Mode: `Route Past Dirty Root`.
- Failure Mode: if workers treat green validation as permission to keep opening new root lanes while the shared checkout is broadly dirty, restart truth drifts and unrelated residue gets reinterpreted as fresh lane work.
- Release-summary bullets:
  - Froze `stabilize-root-worktree` as the honest immediate lane once the Cortex read models exposed broad dirty-root state across shared ATLAS surfaces.
  - Separated this blocker from the already-cleared `lock-registry-hygiene` family so future sessions do not reopen stale stack-lock narration.
  - Preserved the deferred Cortex lane `promote-cortex-receipt-interpretation-consumption-feedback-wave11` without claiming it is honest to advance from the current checkout.
  - Held marker posture flat because this packet classifies and freezes the blocker; it does not clear it.

## 2026-06-01 - Cortex should consume governed repetition contracts, not invent its own readiness model

- Rule: `Cortex Follows Governed Repetition`.
- Rule: Cortex agents may only be introduced from already-governed repetition families with explicit trigger, input, proof, fallback, and owner-boundary truth.
- Pattern: `Contract-First Agent Shadowing`.
- Pattern: define the contract against the repetition ledger first, then let Cortex shadow the workflow without claiming production authority.
- Failure Mode: `Agent Premature Entanglement`.
- Failure Mode: if Cortex agents are introduced before contract and boundary truth are frozen, they become a new drift surface rather than a reduction in operator load.
- Release-summary bullets:
  - Froze one exact contract model for deriving Cortex agent families from the repetition ledger without letting Cortex become a second truth owner.
  - Separated first-safe shadow families such as validation summaries, marker checkpoints, and receipt or doctrine draft helpers from blocked human-judgment or bridge-dependent families.
  - Preserved the existing system boundary: ATLAS and Playbook govern truth, while Cortex only consumes exported contracts.
  - The first live contract-consumption proof now exists for `validation-summary-shadow`: it loads the governed contract and emits a local artifact with authority flags explicitly false.
  - That earns only the smallest honest move on the interface lane because one bounded preparation helper now crosses from doctrine into consumer proof without creating a second truth surface.
  - The second live shadow-consumption proof now exists for `marker-checkpoint-shadow`: it projects the ATLAS marker and restart surfaces into a local Cortex artifact while keeping ratchet authority explicitly false.
  - That earns only the smallest honest move on `Cortex Readiness` because runtime breadth widened by one more bounded consumer path without any authority growth.
  - The third live shadow-consumption proof now exists for `receipt-doctrine-draft-shadow`: it drafts bounded receipt or doctrine structure from governed sources while keeping doctrine-admission and receipt-finalization authority explicitly false.
  - That earns only the smallest honest move on `Cortex Readiness` because the current safe shadow family set is now fully consumed on the live runtime surface without changing ownership.

## 2026-06-01 - Automation claims must follow stable repetition, not repeated frustration

- Rule: `Automation Follows Stable Repetition`.
- Rule: do not promote a repeated workflow into automation candidacy until its trigger, inputs, proof artifact, and fallback path are all explicit and stable.
- Pattern: `Operator Repetition Ledger`.
- Pattern: repeated operator actions should be captured as named families with trigger, boundary, proof expectation, and safe fallback so future helper work aims at real repetition instead of vague friction.
- Pattern: `Bounded Automation Candidate Ladder`.
- Pattern: manual repetition -> structured repetition -> automation candidate -> automation-ready.
- Failure Mode: `Automation Claim Inflation`.
- Failure Mode: if a workflow still depends on hidden toggles, ad hoc prompting, or unstable proof capture, calling it automation-ready creates false confidence and downstream churn.
- Release-summary bullets:
  - Froze one exact threshold for when repeated operator work is allowed to enter automation candidacy at all.
  - Separated first-safe preparation families such as validation summaries, marker checkpoints, receipt packaging, doctrine routing, and proof-packet preparation from human-judgment or externally blocked families.
  - Kept the frozen Codex <-> Chrome bridge lane explicitly outside automation honesty instead of letting repeated blockage masquerade as automation debt.
  - Held marker posture flat because no candidate family graduated into a real governed operator surface.

## 2026-06-01 - Feedback-loop readiness depends on deterministic proof loops, not just available proof parts

- Rule: `Proof-Loop Before Pixel-Loop`.
- Rule: do not claim UI iteration readiness until the proof-capture path is deterministic enough to verify Codex-applied changes without ad hoc operator stitching.
- Pattern: `Local-First Verification Spine`.
- Pattern: request/spec intake -> bounded mutation -> governed local runtime -> fresh proof capture -> receipt/truth update.
- Failure Mode: `Manual Toggle Drift`.
- Failure Mode: if the QA/LLEL loop depends on hidden toggles, one-off prompting, or inconsistent runtime setup, the system will overstate readiness and under-deliver repeatability.
- Release-summary bullets:
  - Froze one exact deterministic threshold for `Feedback Loop Readiness` instead of letting the lane drift between generic QA doctrine and bridge-specific blockage.
  - Recorded that request/spec intake, mutation governance, local runtime truth, and receipt packaging are already real, while deterministic proof capture is the missing replayable link.
  - Kept the bridge lane frozen as inherited background truth rather than misclassifying it as a fresh owner-side or ATLAS-side blocker.
  - Held marker posture flat because no replayable end-to-end proof loop was actually re-run.

## 2026-06-01 - Frozen bridge lanes should preserve external blocker doctrine instead of reopening green repo work

- Rule: `Session-Scoped External Blocker Freeze`.
- Rule: when repo/runtime truth is green and the only missing proof depends on a live external/session bridge, freeze all repo/root mutation until one live bridge success occurs.
- Rule: `Upstream Product Fault Hold`.
- Rule: when owner-scope setup has already been ruled out and the remaining blocker is a product/runtime defect outside repo truth, freeze the lane and preserve only restart-relevant truth.
- Pattern: green repo/runtime -> live bridge timeout -> freeze shared restart truth -> wait for one successful live runtime call -> immediately rerun the exact blocked proof packet.
- Failure Mode: `Fake Motion After Green`.
- Failure Mode: do not generate reconciliation churn, cleanup passes, or repo-framed retries once the lane is blocked outside repo/runtime work.
- Release-summary bullets:
  - Froze the Codex <-> Chrome bridge lane as an external/session-scoped blocker rather than letting it drift back into ATLAS/root or Fitness-local repair work.
  - Preserved the exact restart rule that pass 9 is not honest until one successful live Codex-to-Chrome runtime call exists from a responsive session.
  - Linked the canonical bug packet instead of recreating duplicate blocked-state narration: `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-POST-INSTALL-CODEX-CHROME-BRIDGE-TIMEOUT-BOUNDARY-RECEIPT-2026-06-01.md` plus `docs/ops/ROOT-BOUNDED-DISPATCHER-RECONCILIATION-AFTER-FITNESS-DISCORD-POST-INSTALL-CODEX-CHROME-BRIDGE-TIMEOUT-BOUNDARY-RECEIPT-CLOSEOUT-2026-06-01.md`.
  - Made the remaining fault domain explicit: not a default-browser issue, not an ATLAS/root issue, not a Fitness repo/runtime issue, but the Codex desktop <-> Chrome extension handshake/runtime in the current session.

## 2026-05-31 - Acceptance-criteria governance now spans `_stack` and the highest-signal owner prompt surfaces

- Rule: mutating Codex tasks are not governed unless they declare `Acceptance Criteria`, `Expected Changed Paths`, `Expected Unchanged Paths`, and `Blocked / Skipped Reporting Rules`.
- Rule: summary text is not proof.
- Rule: maintained owner-repo mutating prompt generators and templates should emit the contract directly instead of relying on operator memory or adjacent docs.
- Pattern: `Spec-to-Diff Verification Gate`.
- Pattern: gate implementation -> `_stack` prompt migration -> owner-repo prompt-surface migration.
- Failure Mode: `Summary-Truth Drift`.
- Failure Mode: silent legacy fallback persists when a maintained mutating prompt surface ships without the acceptance-criteria contract even though the gate exists elsewhere.
- Release-summary bullets:
  - Closed the `_stack` gate lane, the `_stack` prompt-authoring migration lane, and the highest-signal owner-repo mutating prompt migration lane as one governance family.
  - Widened the contract from `_stack` into Playbook prompt compilers/templates, Fitness reviewed-task prompt generation, and Mazer visual-evidence prompt authoring.
  - Left historical, archived, runtime-generated, and otherwise intentionally out-of-scope prompt artifacts deferred on purpose rather than pretending universal governed coverage.
  - Preserved the unrelated Mazer verify blocker as a separate repo-local dependency issue instead of misclassifying it as prompt-contract drift.

## 2026-05-31 - Mutating Codex work needs criterion-level proof before completion claims

- Rule: mutating Codex tasks are not considered governed unless they declare acceptance criteria.
- Rule: a worker may not claim completion for mutating work unless every declared acceptance criterion is explicitly accounted for and each `satisfied` criterion is provable from the final repo diff.
- Rule: legacy mutating prompts may stay on a compatibility path temporarily, but new mutating prompt surfaces must not ship without the acceptance-criteria contract.
- Pattern: `Spec-to-Diff Verification Gate`.
- Pattern: request intent -> explicit acceptance criteria -> structured completion artifact -> final diff proof -> success or blocked or failed.
- Failure Mode: `Summary-Truth Drift`.
- Failure Mode: a summary or final note sounds complete even though the repository diff does not prove that every requested edit actually landed.
- Release-summary bullets:
  - Closed the `_stack` spec-to-diff gate lane at mechanism level after proving one real success path and one real blocked failure path through the runner.
  - Moved success authority from worker summary text to criterion-level diff proof for prompts that declare acceptance criteria.
  - Separated mechanism closure from adoption closure so future work can focus on legacy prompt migration instead of re-litigating the runner design.

## 2026-05-28 - Fast safe cadence should be explicit when receipts are strong but operator drag is rising

- Rule: cluster proof and inventory passes before running a ratchet.
- Rule: do not ratchet just because a new receipt landed; ratchet only when operator reality materially changed.
- Rule: every pass prompt must answer whether the package is already durable, who owns the surface, which shared canonical files it touches, and what remains blocked after it lands.
- Rule: shared ATLAS root spine files should be treated as serialized write surfaces.
- Pattern: proof cluster -> one ratchet -> one shared-surface refresh only when needed.
- Pattern: one root writer -> one owner-repo writer -> one read-only scout.
- Failure Mode: repeated micro-ratchets and overlapping root writers create more process drag than the underlying work justifies.
- Failure Mode: a speed-up pass widens scope by turning proof growth into implied execution approval.
- Release-summary bullets:
  - Froze the default cluster-first cadence for marker-heavy governance work.
  - Added a mandatory preflight checklist for durability, ownership, shared-file scope, and blocked-after-this-pass posture.
  - Serialized shared ATLAS root spine writes to reduce merge collisions and restart-surface churn.

## 2026-05-27 - Operator-grade governance doctrine still needs explicit invariants and trust semantics before ratification

- Rule: ATLAS may project, index, verify, and coordinate; it may not silently absorb implementation ownership or mutable child state.
- Rule: adoption is not verification.
- Rule: transcript residue is not memory.
- Rule: Cortex memory must be provenance-backed.
- Rule: Lifeline is threshold-triggered, not identity-driven.
- Pattern: coordination-only root -> owner-truth child repos -> provenance-backed memory -> explicit verification authority -> ratified governance only after trust-class and exception normalization.
- Failure Mode: governance language sounds precise enough to feel final while still drifting because owners, trust classes, exception records, and metric contracts remain implicit.
- Release-summary bullets:
  - Packaged the ratification review durably instead of leaving it in chat.
  - Elevated the reusable invariants that should constrain future doctrine work.
  - Preserved the distinction between a strong v1 draft and final governed doctrine.

## 2026-05-27 - Durable context must externalize out of volatile worker continuity

- Rule: External Context First.
- Rule: when a lane has a maintained continuity manifest, retrieve it before trusting chat recap or remembered session state.
- Pattern: Ephemeral Worker, Durable Substrate.
- Pattern: continuity manifest -> receipt chain -> owner truth surfaces -> verification/adoption surfaces -> chat nuance last.
- Failure Mode: Recursive Context Rot Loop.
- Failure Mode: a continuity manifest that starts copying owner truth instead of pointing to it becomes a second truth store and recreates drift under a more official name.
- Durable Context Externalization: tracks whether critical continuity is reconstructable from ATLAS and owner-repo artifacts rather than trapped in GPT/Codex chats, prompt carryover, or operator memory.
- Release-summary bullets:
  - Added Durable Context Externalization as a first-class marker instead of leaving continuity durability implicit inside knowledge-capture or book-quality lanes.
  - Froze the doctrine that workers should retrieve durable context before trusting chat continuity.
  - Named the recursive context-rot failure mode so future lanes can distinguish durable continuity from conversational carryover.

## 2026-05-27 - Prompt packs should resume from durable context, not transcript continuity

- Rule: canonical continuation prompts should treat prior chat continuity as non-authoritative.
- Rule: active restart surfaces should prefer continuity manifests, receipt chains, truth maps, promoted notes, and owner verification/adoption surfaces before transcript recap.
- Pattern: continuity manifest -> current book chapter -> receipt chain -> owner truth surface -> verification/adoption surface -> transcript nuance last.
- Failure Mode: a restart prompt that still trusts remembered session state before durable retrieval recreates stale package ordering and wrong-lane continuation drift.
- Release-summary bullets:
  - Normalized the active ATLAS continuation pack so retrieval-first doctrine is expressed consistently instead of only implied.
  - Removed stale restart guidance that still pointed at older Local Data Gateway package ordering.
  - Reinforced that transcript carryover is optional nuance, not a canonical restart substrate.

## 2026-05-27 - Manifest-backed continuity requires active restart routing, not just manifest doctrine

- Rule: a lane may claim `manifest-backed` continuity only when an active ATLAS-root manifest points to the current decisive receipt, owner truth surfaces, and relevant verification/adoption surfaces.
- Rule: a lane may claim `manifest-backed` continuity only while that manifest is still fresh enough to match the lane's current checkpoint, marker posture, blocked-work posture, and next-package ladder.
- Rule: continuity manifests are adoption-ready first for cross-repo or cross-surface lanes with dense receipt chains and non-trivial owner routing.
- Pattern: restart guide -> active continuity manifest -> governing receipt chain -> owner truth surface -> verification/adoption surface -> transcript nuance last.
- Pattern: manifest exists -> lane advances -> freshness check -> refresh or downgrade to manifest-present only until refreshed.
- Failure Mode: calling a lane `manifest-backed` before restart can actually follow the manifest chain turns continuity doctrine into label theater.
- Failure Mode: a manifest remains visible and plausible after the lane has moved past it, so workers trust a stale retrieval map instead of the current decisive receipt chain.
- Release-summary bullets:
  - Froze the difference between a manifest contract existing and a lane actually being manifest-backed.
  - Named the first-adoption lane set for continuity-manifest seeding without pretending those manifests already exist.
  - Preserved root as continuity routing only while keeping owner repos as truth owners.

## 2026-05-27 - Local data gateway proof packaging matures evidence, not handoff authority

- Rule: local proof packaging is evidence packaging, not handoff authorization.
- Rule: marker movement after proof packaging requires real-workflow proof that the packaged bundle preserves explicit no-send, no-execution, no remote-target, and no automatic-handoff state.
- Pattern: contract -> validator -> dry-run emitter -> local review -> local proof package -> proof receipt -> marker ratchet.
- Failure Mode: treating a packaged proof bundle as implied permission to send, sync, post, or execute downstream work collapses evidence packaging into hidden transport authority.
- Release-summary bullets:
  - Added the rule that proof packaging strengthens local evidence maturity without opening handoff authority.
  - Preserved the send boundary by requiring explicit proof that packaged bundles still record no-send and no-authorization state on real workflows.

## 2026-05-27 - Local data gateway review proof ratchet requires explicit no-send approval evidence

- Rule: local packet review is a governance checkpoint, not transport authority.
- Rule: marker movement after review requires proof that approval remains local-only and records explicit no-send and no-execution attestation on real workflows.
- Pattern: contract -> validator -> dry-run emitter -> local review -> proof receipt -> marker ratchet.
- Failure Mode: treating a local `approved` disposition as implied authorization for downstream send or execution collapses the review boundary into hidden transport logic.
- Release-summary bullets:
  - Added the rule that review-proof maturity depends on explicit no-send and no-execution attestation, not just the existence of a review helper.
  - Preserved the local-first boundary by separating review maturity from any future handoff or send lane.

## 2026-05-27 - Local data gateway is now admitted doctrine, not only a marker idea

- Rule: raw data lands locally first, and downstream systems receive purpose-built packets rather than messy raw input by default.
- Rule: a governed packet must carry purpose, schema/version, sensitivity, provenance, transformation record, validation result, redaction status, dedupe status, exclusion summary, receipt/proof reference, and minimum useful payload.
- Rule: packet quality depends on proving what stayed local, not only what was exported.
- Rule: the first `_stack` helper boundary must stay local-only with `preview`, `emit`, and `validate` modes, and must not include `send`, `sync`, `post`, `submit`, or `mutate`.
- Rule: marker movement beyond the first doctrine ratchet requires live helper proof on real workflows, not just packet doctrine or helper existence.
- Pattern: local source -> packet contract -> real-workflow exemplar proof -> helper contract -> implementation planning -> local-only helper.
- Pattern: validator proof -> dry-run emitter proof -> marker ratchet only after no-send local artifact behavior is proven on real workflows.
- Failure Mode: moving the marker or helper ambition forward before a reusable packet contract, exemplar proof, and helper boundary are all durable confuses doctrine maturity with implementation maturity.
- Failure Mode: moving the marker because the emitter exists, without proving its no-send local artifact behavior on real workflows, mistakes implementation presence for reusable governed behavior.
- Release-summary bullets:
  - Admitted Local Data Gateway as durable doctrine rather than a marker-only idea.
  - Froze the required packet field set and the no-send helper boundary.
  - Limited the first honest marker move to a small doctrine-plus-proof ratchet rather than claiming implementation readiness.

## 2026-05-26 - Local data gateway should be a first-class stack marker

- Rule: raw data lands locally first; remote systems receive purpose-built packets.
- Rule: local preprocessing must happen before data leaves the machine or repo boundary for a model, API, SaaS tool, remote database, automation, teammate, or shared system.
- Rule: exported payloads should carry purpose, schema or version, sensitivity label, source or provenance, transformation record, and minimum useful payload shape.
- Pattern: raw input -> local normalize, validate, redact, classify, dedupe, extract -> minimum useful payload -> remote refinement, sync, collaboration, or specialized processing.
- Failure Mode: sending messy raw data directly to an AI, API, SaaS tool, or remote database creates privacy risk, token waste, duplicate state, and weak provenance.
- Failure Mode: repeated local preprocessing that never graduates into command surfaces recreates the same manual cleanup debt in every lane.
- Local Data Gateway: tracks whether raw data is processed locally before export and whether repeated local preprocessing becomes governed reusable command surface.
- Release-summary bullets:
  - Added Local Data Gateway as a first-class convergence marker instead of leaving it as a hidden sub-note inside secret hygiene or data hygiene lanes.
  - Defined the local-by-default boundary and the minimum payload contract for exports to remote systems.
  - Connected the marker to secret hygiene, Supabase hygiene, automation graduation, core pattern spread, and truth-map doctrine.

## 2026-05-24 - Playbook origin and research trail should stay explicit

- Rule: Playbook is not another AI coding assistant; it is the deterministic repo runtime and trust layer between humans or AI agents and real repositories.
- Rule: verify before plan; plan before apply; apply before trust renewal.
- Rule: mutation follows trust, not curiosity.
- Rule: declared mutation scope must be enforced before apply succeeds.
- Rule: knowledge must be promoted before it influences execution.
- Rule: research doctrine and implemented runtime truth are separate layers.
- Rule: CI is a release gate, not a place.
- Rule: measure outcomes, not activity.
- Rule: unsafe speed is not value.
- Pattern: verify -> plan -> apply -> verify.
- Pattern: state -> transformation -> enforcement.
- Pattern: evidence -> compaction -> promoted doctrine -> bounded execution.
- Pattern: declare scope -> enforce scope -> mutate -> receipt.
- Pattern: local receipt -> optional publish sync -> optional deployment handoff.
- Pattern: start read-only, expand by evidence.
- Pattern: state -> narrative compression.
- Failure Mode: AI mutation without evidence boundaries.
- Failure Mode: command-surface drift between roadmap, generated docs, CLI help, and actual runtime behavior.
- Failure Mode: correct-but-dense truth reduces adoption even when the underlying system is technically right.
- Failure Mode: research-as-status lets speculative theory masquerade as implemented runtime capability.
- Failure Mode: advisory scope bundles mistaken for real safety.
- Release-summary bullets:
  - Consolidated the Playbook origin story and research trail into one root-owned continuity artifact.
  - Reaffirmed the canonical remediation loop as `verify -> plan -> apply -> verify`.
  - Preserved the distinction between research doctrine, architecture framing, and live runtime truth.
  - Captured the strongest reusable rules, patterns, and failure modes as stack-readable doctrine.
- Continuity reference: `docs/ops/PLAYBOOK-ORIGIN-RESEARCH-TRAIL-2026-05-24.md`

## 2026-05-24 - Core pattern convergence should be its own lane

- Rule: strong reusable ideas should not stay trapped inside one repo, one workflow, or one operator habit when they clearly belong across the stack.
- Rule: capturing patterns is not the same as spreading them; documentation alone does not prove convergence.
- Rule: Playbook should hold reusable doctrine, while ATLAS should show where that doctrine applies and who owns each implementation boundary.
- Pattern: extract reusable rule or pattern -> map owner and applicability -> route into doctrine and stack docs -> verify later adoption in implementation lanes.
- Failure Mode: a stack can look well-documented while still behaving like isolated local habits because the best ideas never actually spread.
- Failure Mode: treating Playbook Everywhere + Cortex Interface as sufficient hides whether the strongest ideas from Fitness, Lifeline, `_stack`, QA, release, or Discord have converged into shared practice.
- Release-summary bullets:
  - Added Core Pattern Convergence as a separate lane from knowledge capture and interface adoption.
  - Defined the lane as stack-wide spread of reusable rules, patterns, and failure modes.
  - Preserved the split between doctrine capture, doctrine visibility, and actual cross-stack application.

## 2026-05-24 - Repeated AI work should graduate into explicit automation lanes

- Rule: repeated Codex, AI, or operator asks should be noticed, classified, and routed toward safe automation instead of being re-executed manually forever.
- Rule: automation graduation is separate from long-run AI batching; one lane turns repetition into commands, while the other governs bounded multi-step job execution.
- Rule: only safe, reviewable, owner-clear workflows should graduate into `_stack`, Playbook, or bot command surfaces.
- Pattern: repeated request -> repetition receipt or marker -> owner and risk classification -> narrow command contract -> verification and rollback path -> documented operator surface.
- Failure Mode: leaving repeated mechanical work in chat burns context and tokens while hiding the real opportunity for durable command surfaces.
- Failure Mode: turning an unstable or ambiguous workflow into a command too early just automates confusion.
- Release-summary bullets:
  - Added the doctrine that repeated AI and operator work should feed an explicit automation-conversion lane.
  - Distinguished repetition-to-automation from long-run batch orchestration.
  - Added the rule that new command surfaces require owner clarity, verification, and rollback paths.

## 2026-05-17 - Discord moderation should stay reversible and explicit

- Rule: community moderation should escalate through logged notice and warning lanes before punitive action whenever possible.
- Rule: default Discord moderation should isolate through reversible role and channel changes, not through bans, kicks, or message deletion.
- Rule: every moderation action must create or update a case record and keep a release or resolution path.
- Pattern: notice or warning -> logged case -> Purgatory isolation if needed -> release or warning-clear -> safe role restoration.
- Pattern: during Purgatory, remove access roles such as `Verified`, preserve unrelated non-access roles, and show only the Purgatory category and channel.
- Pattern: branded moderation messages may DM the target fail-soft, but delivery failure must never block the case write or role transition.
- Failure Mode: production behavior must not live only on an unmerged branch; merge the live-tested moderation polish back into `main` before treating it as stack truth.
- Failure Mode: silent bans, destructive moderation, or missing restore paths create drama and make recovery harder than the original incident.
- Release-summary bullets:
  - Added the reversible Discord moderation doctrine with notice, warning, Purgatory, and release lanes.
  - Added the rule that moderation changes must remain logged, restorable, and no-ban-by-default.
  - Added the explicit merge-back requirement when a live moderation polish ships from a branch first.

## 2026-05-17 - Discord shipped-card promotion should use one public format only

- Rule: a shipped Discord feedback card gets one public updates-channel post, not multiple overlapping update formats.
- Rule: thread audit comments stay compact and operational inside the feedback thread.
- Rule: when a specific feedback card ships, the public updates-channel post should use the short `Update:` card-promotion format and end with `Report ID: <short id>`.
- Rule: do not also publish the broad `@everyone` release-summary template for that same shipped card unless the owner explicitly wants a separate aggregate release note.
- Pattern: shipped card -> compact thread audit comment -> one public card-promotion update post.
- Failure Mode: mixing thread-audit copy, broad release-summary copy, and card-promotion copy for the same shipped card creates duplicate logic and confusing public history.
- Status: Proposed

## 2026-05-17 - Discord community ops should keep one board and low-noise channels

- Rule: the Discord feedback board is the visible community board, not a second task system.
- Rule: feedback card mutations stay in the forum thread as audit comments and board export artifacts; they do not auto-post to updates, ATLAS, or GitHub.
- Rule: only `Updates` and `Main` are loud channels; other Discord workflows should avoid broad pings by default.
- Rule: the bot must not claim it can force user-level channel or category mute settings, because those are personal Discord client preferences.
- Pattern: feedback forum card -> audit comments -> board export -> reviewed Verta Core / Playbook planning input -> curated Update Bot promotion if user-facing.
- Pattern: server inventory -> noise audit -> conservative dry-run recommendations -> reviewed permission or mention changes.
- Pattern: moderation escalates through notice or warning -> logged case -> reversible Purgatory isolation if needed -> release or warning-clear.
- Failure Mode: duplicating raw Discord cards into ATLAS or GitHub creates conflicting task truth and noisy sprint churn.
- Failure Mode: claiming the bot can mute channels for users hides the real permission and allowed-mentions model.
- Release-summary bullets:
  - Added the one-board, reviewed-promotion Discord workflow doctrine.
  - Added the low-noise rule that only `Updates` and `Main` are loud channels.
  - Added the rule that inventory and audit tooling should enforce mention and permission truth without fake personal-mute claims.

## 2026-05-11 - QA LLEL adoption semantics

- Rule: repo blockers exposed by QA LLEL should be fixed in the owning repo, not hidden in root QA logic.
- Rule: package and docs repos should not report browser-emulation semantics unless browser evidence actually exists.
- Rule: a failed preflight must block promotion for every evidence profile, including docs governance.
- Rule: repo lint failures are repo-owned blockers; root QA should surface them, not bypass them.
- Pattern: root-owned capture machinery should also own its runtime dependencies; child repos should declare only app or command intent.
- Pattern: adoption means child-owned QA intent plus root-readable receipts, not root-side prototype manifests.
- Pattern: warning counts should become a governed budget before they become promotion blockers.
- Pattern: visual diff failures must be classified before either UI remediation or baseline blessing.
- Failure Mode: blessing a baseline before classifying the diff turns QA into approval theater.
- Failure Mode: letting non-visual repos report as browser-emulation passes creates semantic drift unless the evidence profile is shown separately from the promotion outcome.
- Failure Mode: treating hundreds of warnings as harmless creates silent governance debt.
- Failure Mode: fixing repo failures in root QA logic hides ownership and weakens the evidence model.

## 2026-04-28 - Fitness live UI and real mobile screenshot lane

- Rule: for live mobile UI refinement on fitness, prefer the real signed-in local app on `http://127.0.0.1:3000` and use isolated browser sessions only.
- Rule: keep the user's personal browser windows untouched; launch and close Codex-owned browser sessions only.
- Rule: store durable runtime auth in `runtime/fitness/live-user-auth-current-project.json` and refresh it before capture work instead of creating throwaway users.
- Rule: keep screenshot artifacts in repo-local `.codex/qa/captures/` for active proof and promote only the references worth handoff into `tmp/screens/`.
- Pattern: use the repo screenshot runner `scripts/qa/cdp-edge.mjs` for deterministic route loads and short click sequences.
- Pattern: if capture state becomes ambiguous, use a direct Playwright script with `ensureFreshSessionArtifactFile()` plus `buildCookiesFromArtifactSession()` to force the exact signed-in screen state and take the shot.
- Pattern: when using Playwright cookie bootstrap, do not pass both `url` and `path` to `addCookies`; strip `path` when `url` is present.
- Pattern: prefer proof from the real signed-in route first; use preview routes only when the real route is blocked or when a narrow capture harness is explicitly needed.
- Pattern: for live UI work, inspect shared component branches first and reuse the shared shell or token path before making one-off class tweaks.
- Failure Mode: the recurring fitness stale-chunk state is `Cannot find module './1682.js'` from `.next/server/webpack-runtime.js`; fix the single `:3000` runtime before doing anything else.
- Recovery Path:
  1. stop only the process listening on `127.0.0.1:3000`
  2. delete `repos/fawxzzy-fitness/.next`
  3. relaunch one server with `node scripts/dev.mjs --hostname 127.0.0.1 --port 3000`
- Failure Mode: dev and preview routes that use `useBottomActions` must be wrapped in `BottomActionsProvider`, or production deploys can fail on unrelated preview pages.
- Failure Mode: a failed production deploy on this lane is often blocked by unrelated shared or dev-route build issues; inspect the actual Vercel build error before blaming the current UI patch.
- Release-summary bullets:
  - Added the preferred real-signed-in live UI refinement lane for fitness.
  - Added the auth-artifact refresh and cookie-bootstrap pattern for reliable isolated screenshots.
  - Added the cdp-edge first, direct Playwright fallback second capture strategy.
  - Added the stale `.next` chunk recovery path as a standard repo-level repair.
  - Added the rule that preview routes using bottom actions must ship with their provider wrapper or they will poison production deploys.

## 2026-04-28 - Fitness logged-session and add-exercise UI patterns

- Rule: when the user is refining the logged-session screen, treat `view` and `edit` as the same product lane with shared shells, not separate one-off layouts.
- Rule: for history/logged-session counts, derive the visible exercise and set totals from the actually logged exercises on the screen, not from the original routine template summary.
- Pattern: the logged-session lower-half focus area should behave like one viewport shell.
  1. top focused card stays pinned
  2. middle content is the only vertical scroller
  3. bottom notes or configure surface sits just above the bottom dock with minimal dead space
- Pattern: when a set is focused in logged-session edit mode, replace the bottom note surface with the horizontal measurement rail and let the top pinned card become the set card.
- Pattern: delete actions attached to cards should reuse the same bottom-action danger intent and color treatment as the shared bottom dock delete buttons; do not restyle them separately.
- Pattern: set cards on the logged-session screen should reuse the same rounded shell language as the Today/current-session exercise cards instead of inventing a second border treatment.
- Pattern: compact exercise-card metadata that behaves like a tag count can live on the trailing rail with the chevron when the visual goal is a single right-edge cluster instead of a title-row badge.
- Pattern: metric value strings that contain list separators should render shared green-dot separators through the metric renderer, not via ad hoc text.
- Pattern: reusable editor fields with a floating top-right label should use one shared shell component so the border, label cutout, and focus treatment stay in sync across screens.
- Implementation note: the current reusable primitive is `repos/fawxzzy-fitness/src/components/ui/LabeledEditorField.tsx`.
- Pattern: the `LabeledEditorField` mask should use the app background color, not a darker chip color, so the title looks like a clean border break instead of a floating badge.
- Failure Mode: if the input focus highlight looks offset, check whether the inner input still carries its own border or ring; the wrapper shell must own the only visible border.
- Failure Mode: if the title text in a compact history header clips descenders like the `g` in `Legs`, loosen the title line-height before changing font size.
- Pattern: add-exercise for current session and edit day should continue sharing the same flow shell and goal/configure stack so future refinements land in both places together.
- Pattern: the add-exercise configure area can host horizontally scrolling measurement inputs, but the dock itself should stay width-contained; only the measurement lane should visually overflow or clip.
- Failure Mode: when the local Playwright Chromium bundle is missing, use the installed Edge channel for isolated screenshots rather than touching the user's personal browser.
- Release-summary bullets:
  - Added the logged-session viewport-shell model for pinned top card, scrolling middle content, and dock-adjacent bottom content.
  - Added the rule that history totals must reflect logged exercises, not template exercises.
  - Added the shared labeled editor field primitive and the focus/label-cutout implementation notes.
  - Added the shared delete-action and set-card styling doctrine for logged-session surfaces.
  - Added the add-exercise dock containment and horizontal measurement-lane pattern.

## 2026-04-28 - Fitness add-exercise live pass follow-ups

- Rule: when a user is approving mobile UI from screenshots, only use fresh signed-in local captures from the real route; stale fixture boards or cached filenames are not acceptable proof.
- Rule: after each live pass on fitness add-exercise, post the exact local screenshot inline and prefer a new timestamped filename when there is any risk of cache confusion.
- Pattern: the current-session add-exercise screen and the routine edit-day add-exercise screen must keep sharing the same `ExercisePicker` and goal dock path; land visual cleanup in the shared component layer first.
- Pattern: the search bar should stay pinned to the top of the real mobile scroll container, not only to a nested list wrapper; validate sticky behavior by scrolling the actual screen state after edits.
- Pattern: the configure-goal panel should sit above the blurred bottom action bar as its own fixed dock. Keep the button bar blur attached to the buttons, not spread through the whole goal panel surface.
- Pattern: the preview section should use a simple green divider plus a compact `Preview` line, and missing-goal feedback should render as `missing <metric>` until all required metrics exist.
- Pattern: add-exercise measurement titles can share the floating-label primitive positioning, but compact measurement fields may need their own label rendering treatment instead of blindly copying text-input background chips.
- Failure Mode: if the right side of the exercise cards looks wider than the left on mobile, inspect the picker viewport width and any right-only list padding before touching the card component.
- Failure Mode: if the goal field titles look clipped, confirm whether the border is visually intersecting the glyphs or whether the label span itself is clipping; they are different fixes.
- Failure Mode: screenshot harness configs that wait for removed text like `Configure goal` become silently stale after UI changes and must be updated before the next capture.
- Release-summary bullets:
  - Added the real signed-in timestamped screenshot requirement for add-exercise live passes.
  - Added the shared sticky-search, split dock, and preview-divider doctrine for the add-exercise flow.
  - Added the right-gutter diagnostic path for picker viewport width issues.
- Added the warning that compact goal-label clipping may be border intersection, stale capture state, or span clipping, and each has to be debugged separately.

## 2026-04-28 - Fitness account/settings live pass

- Rule: the account/settings screen should now behave like a focused accordion lane, not a tall stacked settings form.
- Pattern: keep one shared outer settings shell, then render only one expanded section at a time.
  1. `Data & Account`
  2. `Preferences`
  3. `Import Legacy Data`
- Pattern: when one settings section opens, hide the sibling sections from the visible stack so the expanded section owns the vertical space, similar to the focused-card behavior used on logged-session detail.
- Pattern: collapsed settings sections should render as centered disclosure cards with:
  - centered title
  - chevron anchored bottom-right
  - no extra subtitle/body text in the collapsed state
- Pattern: expanded settings sections should drop the inner secondary border shell; keep the outer section card border only and let the inner controls sit on the shared screen surface.
- Pattern: settings save actions should only look active when there is an unsaved change since the last successful save, not merely a change from the original server props.
- Pattern: account header identity should be centered and render:
  - `username | email` when a username exists
  - `email` only otherwise
- Pattern: for this screen, username fallback should use the same lane as the account form:
  - auth metadata username/display_name first
  - remembered login display name next
  - derived email local-part fallback last
- Pattern: the preferences section keeps the segmented side-by-side control language, but the labels should be centered directly above their control groups.
- Pattern: legacy import is a single-action flow in the UI now.
  - user provides legacy email and password
  - one button runs export, import, and parity in sequence
  - raw snapshot JSON is no longer exposed in the normal mobile UI
- Pattern: destructive or status tags on the settings screen should use the plain signature-meta tag style, not pill chips, unless they are part of a true action control.
- Implementation note: the client accordion owner is:
  - `repos/fawxzzy-fitness/src/components/settings/SettingsAccordionClient.tsx`
- Implementation note: the client header identity fallback is:
  - `repos/fawxzzy-fitness/src/components/settings/SettingsHeaderIdentity.tsx`
- Failure Mode: if a capture script assumes sibling sections remain in the DOM after one section expands, it will fail after the focused-accordion refactor. Reopen the page fresh for each expanded-state screenshot.
- Failure Mode: a server-rendered header cannot see remembered local login state. If the mobile header needs the remembered name, move that identity row into a small client component instead of trying to patch server-only metadata reads.
- Release-summary bullets:
  - Added the focused-account accordion model for settings.
  - Added the single-action legacy import rule and removed raw snapshot exposure from the normal mobile flow.
  - Added the centered username/email header fallback chain.
  - Added the rule that save buttons must gray back out after a successful save baseline resets.

## 2026-04-25 - Launcher routes, target app installs

- Rule: a launcher routes users to the target app's canonical install route; the target app owns installability, iOS gates, and standalone access truth.
- Rule: a native PWA install button may only exist for the current origin after `beforeinstallprompt` has fired.
- Pattern: use a split platform flow.
  1. iOS in-app browser: hard gate with `Open in Safari` and copy link.
  2. iOS Safari browser tab: hard gate with `Share, then Add to Home Screen`.
  3. iOS standalone/Home Screen: allow normal access.
  4. Android and other non-iOS browsers: allow access and show native install UI only when the browser exposes it.
- Failure Mode: do not treat `localStorage` or `sessionStorage` as installed truth.
- Failure Mode: do not label cross-origin navigation as `Install`.
- Failure Mode: do not wrap the entire app shell when browser auth and recovery routes must remain usable in-browser.
- Failure Mode: browser automation can prove app logic and mocked install states, but real iOS Add to Home Screen and real Android native install prompts still need manual device QA.
- Release-summary bullets:
  - Added launcher-to-target-app installer routing doctrine for cross-origin PWAs.
  - Added the iOS in-app browser, Safari, and standalone access-gate pattern.
  - Added the rule that native install CTAs are current-origin only and capability-gated.
  - Added runtime standalone detection as the installed-state source of truth.
  - Added manual-device QA as a required final step for real install flows.

## 2026-04-23 - Fitness auth must not own install acquisition

- Rule: app auth flow must not own install acquisition UX when install is handled externally.
- Pattern: auth/recovery routes should keep one shared shell with inline status and error messages instead of branching into screen-per-state variants.
- Failure Mode: install-first route branching and standalone recovery error screens create extra state surfaces, stale capture-map truth, and mobile UI drift for flows that should stay message-level.

## 2026-04-23 - Fitness release lanes require manual _stack deploys and reusable QA auth

- Type: Guardrail
- Summary: Fitness deploy and QA work must use `_stack` deploy entrypoints, keep Vercel Git auto-deploy creation disabled, and verify auth-aware local flows with one permanent Supabase QA user instead of random signup users.
- Suggested Playbook File: docs/GUARDRAILS/fitness-auth-deploy-qa-lane.md
- Rationale: Prevents repeated auth/deploy chaos where throwaway users accumulate, local browser and server Supabase env drift apart, Git-triggered Vercel deploys silently reappear, or deploys run from the wrong repo boundary.
- Evidence: repos/_stack/ops/Test-FitnessDeployLink.ps1, repos/_stack/ops/Test-FitnessDoctor.ps1, repos/fawxzzy-fitness/scripts/qa/fitness-qa-user.mjs, repos/fawxzzy-fitness/scripts/qa/fitness-local-feedback.mjs
- Status: Proposed

## Deploy identity guards

- Production deploy guards should validate the configured live hosting identity for the current lane, not a guessed future owner or namespace.
- For Vercel-backed repos, keep the expected scope and project in checked-in operator config and allow explicit environment overrides for one-off validation.
- Treat visible team-label cleanup and namespace changes as separate lanes. Namespace changes can alter future generated hosting URLs and should not be bundled into an unrelated production deploy.
- Hosting identity checks must validate immutable team/project IDs, not only mutable slugs or display names.
- Use connector-confirmed project identity as source of truth, then mirror that identity into operator deploy guards and repo-local `.vercel/project.json` metadata.
- Failure Mode: A team rename makes slug-only checks lie, which looks like a wrong-owner failure even when the linked Vercel project is correct.
- If Vercel sees the correct team and project but a fresh pushed SHA creates no deployment object, classify it as a Git integration ingestion failure before diagnosing app code or retrying production deploys from the CLI.
- After connector repair, prefer one fresh Git-triggered branch deployment as the proof path; only resume production shipping after Vercel creates and runs that branch deployment from Git.
- Failure Mode: Repeated CLI production retries can mask the real issue when Git-connected preview creation is disabled or dead, which makes an ingestion outage look like an app or build failure.
- Failure Mode: A mounted app folder under the ATLAS stack root inherits the parent repo boundary and poisons Git recovery until the app is recloned as a real standalone repo.
- Failure Mode: Windows prebuilt deploy fallback can fail on symlink packaging; do not diagnose app code from that signal alone.

## 2026-05-11 - QA release governance

- Rule: Repo lint failures are repo-owned blockers; root QA should surface them, not bypass them.

## 2026-05-22 - Branch discipline for root-launched Codex lanes

- Rule: no Codex lane starts until the owner repo and the target branch or worktree are explicit.
- Rule: use clean worktrees for repo-specific lanes.
- Rule: use ATLAS root branches only for stack-root docs, projection, standards, audits, and cross-repo coordination slices.
- Pattern: root lane decides owner repo -> owner repo or root worktree is named -> target branch is named -> work starts only inside that declared surface.
- Pattern: if a lane is repo-specific, prefer an isolated worktree over reusing whatever branch was already active in another chat.
- Failure Mode: starting multiple Codex chats from the ATLAS root without an explicit owner repo and target branch lets unrelated work inherit the active branch and creates mixed replay branches that are hard to classify later.

## 2026-05-22 - AI long-run batch orchestration must stay bounded and supervisor-led

- Rule: long-run AI batching is a job-oriented orchestration problem, not an invitation to keep one giant interactive Codex session alive indefinitely.
- Rule: unattended or multi-hour batching should use bounded jobs, isolated worktrees, durable checkpoints, and explicit verification gates.
- Rule: root doctrine may define the lane and contracts first, but `_stack` should own execution-oriented orchestration contracts and Playbook should own reusable verification and workflow doctrine.
- Pattern: research -> root doctrine -> lane or job contract -> supervised single-lane pilot -> only then wider unattended batching.
- Pattern: each batch job should declare owner repo, target worktree, allowed write scope, checkpoint surface, and exit verification before execution begins.
- Failure Mode: treating one large interactive ATLAS-root session as the default batching model recreates branch contamination, weakens verification boundaries, and hides partial failures until the lane is too large to review safely.
- Rule: Manual attestation may satisfy physical/manual review, but it must never be labeled as automated provider proof.
- Rule: Promotion wording must match the evidence profile that actually passed.
- Rule: Fitness must remain non-release-ready until real manual or provider-backed physical evidence exists.
- Rule: No-credential provider readiness must never produce a false physical pass.
- Rule: Release readiness must match the target SHA or stack lock pin, not just a recent receipt.
- Rule: Release readiness may also require a trusted receipt origin when the release profile enables it.
- Pattern: Release readiness is repo-tier specific; physical-device proof belongs to release-critical web flows, not every repo.
- Pattern: Release policy turns QA receipts into operational gates.
- Pattern: Local receipts prove logic; CI or protected receipts prove release trust.
- Pattern: Receipt selection should prefer strongest valid evidence, not just newest evidence.
- Pattern: Adoption drift scanning prevents root prototypes from masquerading as real child-repo adoption.
- Pattern: Prototype QA configs must be explicitly labeled, adopted, or retired.
- Pattern: Rehearse release gates with both passing and intentionally blocked repos.
- Pattern: Warning-budget reporting gives governance debt shape before turning it into hard enforcement.
- Failure Mode: Once release readiness exists, stale receipts can create false confidence unless adoption freshness is checked.
- Failure Mode: Fresh receipts for the wrong commit can create false release confidence.
- Failure Mode: Correct-SHA receipts can still be weak if they were produced outside the trusted release path.
- Failure Mode: A newer `local_dev` receipt can overshadow a stronger trusted release receipt unless evidence ranking is explicit.
- Failure Mode: Windows `.pyc` cache write failures can create false verification noise unless cache hygiene is part of the verification path.
- Failure Mode: Treating `warning_count=559` as harmless forever turns governance debt into background noise.
- Failure Mode: Using one generic promoted label hides whether a repo passed package, docs, web visual, manual physical, or provider physical evidence.

## 2026-05-22 - Stack lock regeneration must wait for root normalization

- Rule: do not repair or regenerate `stack.lock.yaml` while the ATLAS root is behind `origin/main` and preserved recovery residue is still intentionally present.
- Rule: lock refresh belongs after preservation classification and root reconciliation, not during transitional branch-normalization posture.
- Pattern: preserve replay evidence -> classify archive or recovery or package ownership -> reconcile root with `origin/main` -> regenerate `stack.lock.yaml` -> rerun validation.
- Failure Mode: refreshing the lock during a dirty or transitional root phase bakes temporary branch, residue, or preservation state into the pinned stack contract.

## 2026-05-22 - Strategic convergence lanes must be explicit near the front of the program

- Rule: strategic lanes are part of the convergence program, not separate random work.
- Rule: Vision Consolidation belongs near the front so later cleanup and convergence work optimize toward the real endgame instead of local hygiene only.
- Rule: long-run doctrine lanes should be recorded in marker docs before implementation or cleanup widens.
- Pattern: Vision Consolidation -> Inventory & Truth Map -> Branch & Worktree Normalization -> Workflow Convergence -> Dependency Untangling -> later adoption and publication lanes.
- Pattern: every strategic lane should answer the same five questions:
  - why does this exist
  - what is the endgame
  - what does done look like
  - how does it align with ATLAS
  - what should we stop doing
- Vision Consolidation: defines the endgame, purpose, done-state, and ATLAS alignment for every lane.
- Cortex Integration into Playbook: tracks how Cortex planning or admission work becomes Playbook-readable doctrine, contracts, patterns, or validation logic without moving runtime ownership too early.
- Knowledge Capture: tracks whether key reasoning, rules, patterns, failures, and decisions are recorded in durable docs instead of trapped in chat.
- Feedback Loop Readiness: tracks whether each lane can receive, process, and route user or system feedback into ATLAS, Playbook, Discord, or repo workflows.
- Truth Map Book: consolidates documentation, roadmaps, notes, systems, concepts, and lane maps into one definitive cross-referenced guide.
- Dependency Untangling: tracks hidden coupling between lanes and reduces it so future Fitness, Discord, and ATLAS work can run in parallel safely.
- Knowledge Transfer Readiness: tracks whether a future teammate, Codex worker, or Cortex agent could continue the work from docs and receipts.
- Future Self Alignment: periodic review that today’s work still serves the long-term vision.
- Sandbox Simulation Readiness: ensures each lane has safe places to test bold ideas without risking core systems.

## 2026-05-15 - Discord verification, member numbers, and future bot doctrine

- Type: Pattern
- Summary: Discord should display source-app truth through signed Fitness-hosted interactions, durable member links, and governed side effects rather than running a local bot as system authority.
- Current truth:
  - Active: Fitness-hosted Discord HTTP interactions endpoint
  - Prototype/fallback only: `fawxzzy-fitness-discord-bot` Gateway bot
  - Identity authority: Fitness plus Supabase profiles
  - Discord responsibilities: signed interaction transport, modal UI, role display, nickname display
  - Playbook and ATLAS responsibilities: patterns, receipts, triage, reviewed promotion, not noisy automatic writes
- Rule: Fitness owns identity; Discord consumes proof.
- Rule: Email knowledge is not identity proof.
- Rule: Unsigned Discord interaction payloads must never reach role-grant logic.
- Rule: Public member numbers compact from `#1` while Zac remains `#0`.
- Rule: Automation accounts must not consume public member numbers.
- Rule: Discord bug reports should be queued and triaged before becoming repo truth.
- Rule: Release posts must be curated for users, not copied from internal logs.
- Pattern: Authenticated Fitness session -> one-time token -> signed Discord modal submit -> token consume -> role grant.
- Pattern: Fitness profile number -> Discord member link -> nickname sync.
- Pattern: Discord support modal -> structured DB queue -> Playbook triage -> reviewed issue or task.
- Pattern: Release ledger or PRs -> curated release copy -> Discord announcement.
- Failure Mode: Local Gateway bots, email-only checks, or auth middleware redirects make Discord verification unavailable or unsafe.
- Failure Mode: Discord owner or higher-role users verify correctly but cannot be renamed by the bot.
- Failure Mode: Changing DB member numbers without Discord resync leaves stale nicknames.
- Failure Mode: Direct Discord-to-repo writes create noisy or abusive history.
- Failure Mode: Raw technical release posts are hostile to normal users.
- Future backlog:
  - Bug Report Bot should use a signed Discord modal, store structured reports in Supabase, and enter a review queue before any Playbook, ATLAS, or GitHub promotion.
  - Curated Release Bot should publish only admin-approved user-facing updates and must not dump raw deploy logs, migrations, or internal changelog noise.
- Evidence: Fawxzzy Fitness Discord verification build, PR #20, PR #21, PR #22
- Status: Proposed

## 2026-05-16 - Discord community systems should close operations and doctrine before more bots ship

- Rule: finish the operating system before adding another bot.
- Rule: Discord is the community surface, not the ATLAS control plane.
- Rule: deployment metadata is input, not release copy.
- Rule: feedback attachments are Discord-hosted evidence, not app DB blobs.
- Rule: optional Discord decoration must fail soft.
- Rule: database triggers do not call Discord.
- Pattern: production proof -> doctor command -> migration reconciliation -> docs truth -> doctrine update -> next feature.
- Failure Mode: stacking more Discord features on undocumented production lessons creates brittle automation and stale docs.

## 2026-05-16 - Supabase migration ledger repair should require schema evidence

- Rule: migration ledger repair requires schema evidence first.
- Pattern: verify production effects -> repair exact versions -> validate -> document.
- Failure Mode: blind migration repair makes the ledger claim schema history that production does not actually have.

## 2026-05-22 - Marker consolidation should reduce noise without losing concepts

- Rule: every future report ends with the full marker table, including future lanes at `0%`.
- Rule: marker names should stay consolidated when multiple names describe the same endgame.
- Pattern: keep historical completion markers separate, but collapse overlapping future-program markers into one stronger dashboard line.
- Unified Workflow Convergence: combines overall integration, workflow convergence, Discord workflow unification, QA/LLEL workflow convergence, Fitness workflow integration, and `_stack` integration.
- Truth Map & ATLAS Book: combines documentation connection web, Truth Map Book, and ATLAS Book.
- Playbook Everywhere + Cortex Interface: combines Playbook Everywhere Adoption with Cortex Integration into Playbook.
- Knowledge Capture & Transfer: combines knowledge capture and knowledge transfer readiness.
- Vision & Future Alignment: combines Vision Consolidation and Future Self Alignment.
- Full Stack Re-sync, Clean & Closeout: combines broad re-sync/clean work with final cleanup closeout.
- Discord Workflow & Documentation Publishing: combines Discord workflow consolidation with documentation channel publishing.
- Post-Convergence Lane Split Readiness: combines split preparation with future Fitness, Discord, and ATLAS lane readiness.
- Failure Mode: marker sprawl makes the dashboard noisy enough that operators stop trusting it even when the underlying ideas are correct.

## 2026-05-23 - Canonical source and tmp dependency risks need first-class convergence markers

- Rule: canonical repo truth must not drift into `tmp/`, deploy clones, or operator recovery worktrees.
- Rule: duplicate source surfaces, branding sources, Discord publication reliability, secret hygiene, and manual deploy exceptions are convergence blockers, not side tasks.
- Pattern: restore canonical repo roots first -> eliminate hidden `tmp/` dependency second -> decommission duplicate surfaces third -> only then widen cleanup and workflow convergence.
- Canonical Repo Restoration: tracks whether canonical repo roots exist again under `repos/`, especially Fitness, and whether production workflows truly point there.
- Duplicate Surface Decommission: tracks duplicate or orphaned source surfaces until each is removed, archived, retained as evidence, or routed into a canonical repo.
- Tmp Dependency Elimination: tracks removal of production-critical dependence on `tmp/` worktrees, deploy clones, and preservation checkouts.
- Brand Asset Canonicalization: tracks whether ATLAS owns the single canonical branding source and downstream apps consume reproducible generated outputs.
- Preview Cache & Surface Consistency: tracks whether deployed icon, preview, PWA, and share surfaces match the canonical branding source and can be verified cleanly.
- Operator Secret Path Hygiene: tracks whether secret-backed operator flows avoid spilling env or secret residue into repo roots.
- Manual Deploy Exception Burn-Down: tracks the remaining risk from direct deploy behavior outside `_stack`.
- Discord Workflow, Publication & Docs Reliability: combines Discord workflow reliability, `#updates` posting stability, fallback path clarity, and documentation-channel publication into one durable marker.
- Failure Mode: if canonical repos, deploy truth, and `tmp/` dependency are not fixed before broader convergence, the stack keeps recreating the same wrong-repo, wrong-branch, wrong-deploy confusion.

## 2026-05-24 - Marker model should absorb Discord OS separation and data hygiene explicitly

- Rule: when a cross-stack cleanup concern is really infrastructure ownership or data-governance work, it should get a durable marker instead of hiding inside a vague future lane.
- Rule: stale Vercel project and deployment surfaces belong under existing deploy-authority and duplicate-surface lanes, not under a new one-off marker.
- Pattern: reuse an existing marker when the work is fundamentally duplicate-surface or deploy-authority cleanup; add a new marker only when the concern has distinct ownership, sequencing, and done-state.
- Discord OS Infrastructure Separation: supersedes the older Discord OS extraction-review framing and tracks separation of Discord OS code, Vercel, Supabase, env ownership, and shared-data contracts away from Fitness-hosted default coupling.
- Fitness Supabase Profile/Data Hygiene: tracks inventory, cleanup planning, and governance of Fitness auth/profile/data surfaces, especially unknown, duplicate, and automation-linked identities.
- Duplicate Surface Decommission and Manual Deploy Exception Burn-Down should both explicitly absorb stale Vercel surface cleanup targets when those surfaces can confuse source truth or deploy authority.
- Failure Mode: if Discord OS separation and Fitness data hygiene stay implicit, later cleanup mixes repo, deploy, bot, and identity concerns into one vague migration lane and raises breakage risk.

## 2026-06-02 - Quarantine posture must stay distinct from normal secret retention

- Rule: quarantine is not normal retention; sensitive files moved under `secrets/**` quarantine must not be treated as ordinary archive evidence or routine operator source material.
- Pattern: move sensitive residue out of ordinary archive carry -> keep it under ignored `secrets/**` quarantine -> verify adjacent retained metadata is non-secret -> freeze operator posture before any broader mutation.
- Failure Mode: secret posture drift happens when retention posture, quarantine posture, ignore rules, and operator expectations stop matching, so a local secret path becomes implicitly trusted or casually mutated.

## 2026-06-02 - Current execution order must be durable before future workers depend on it

- Rule: durable before convenient; do not treat session-local lane order or held-lane posture as durable until it is externalized into restart-safe surfaces that future workers actually retrieve.
- Pattern: recent lane closeouts accumulate -> active execution order and held posture become chat-dependent -> externalize that spine into continuity manifest plus restart surfaces -> hand off to the next selected lane.
- Failure Mode: context leakage through chat reliance happens when the current execution order, held-lane posture, or reopen rules still depend on conversation memory instead of durable restart surfaces.

## 2026-06-02 - Current closeout lessons must be captured before they decay into recap

- Rule: capture current closeout lessons before they decay into chat recap.
- Pattern: recent bounded closeouts land -> restart truth becomes durable -> admit the cluster as transfer-ready KCT evidence -> hold flat until a distinct new capture or promotion question appears.
- Failure Mode: current reusable lessons remain scattered across adjacent receipts and chat memory, so future workers can restart but still cannot inherit the distilled transfer value without reconstructing it themselves.

## 2026-06-02 - Durable execution routing must refresh after adjacent-lane closure

- Rule: refresh durable execution-state routing after an adjacent lane closes at a new threshold.
- Pattern: externalize active spine -> adjacent supporting lane closes at a new threshold -> refresh the DCE spine so immediate lane, held lanes, and conditional supporting reopen rules stay durable.
- Failure Mode: stale next-package drift happens when a manifest-backed restart spine still routes to a supporting packet that already closed or no longer opens automatically.

## 2026-06-02 - External bridge blockers must not masquerade as repo repair

- Rule: when all repo/runtime prerequisites are green and the remaining blocker is a live session bridge, stop repo repair and classify the blocker at the external/session boundary.
- Pattern: clear repo-local prerequisites -> verify bridge-specific readiness -> reclassify the remaining blocker as external/session-scoped -> hold adjacent cleanup lanes flat unless a direct path or naming dependency reappears.
- Failure Mode: repo repair churn continues after the active dependency has already crossed out of local code and into browser/session bridge state.

## 2026-06-03 - Workflow convergence should consume hardened boundaries instead of reopening them

- Rule: converge active workflow before adjacent cleanup; use canonical substrate and hardened boundary lanes as input to the current operating spine instead of reopening them by adjacency.
- Pattern: substrate becomes durable -> one active lane is selected -> hardened adjacent lanes stay held -> supporting work opens only on direct dependency -> root packages the clarified workflow seam into restart-safe truth.
- Failure Mode: workflow-convergence drift into cleanup happens when operators reopen naming, substrate, archive, or authority lanes just to make the current workflow feel connected.
