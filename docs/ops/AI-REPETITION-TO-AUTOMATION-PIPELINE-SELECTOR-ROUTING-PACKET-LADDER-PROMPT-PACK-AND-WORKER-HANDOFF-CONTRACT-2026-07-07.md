# AI Repetition-to-Automation Pipeline Selector-Routing Packet Ladder Prompt-Pack And Worker Handoff Contract

Date: 2026-07-07

## Worker Objective

Use the already-landed generic packet-ladder helper to produce deterministic packet-ladder proof for the accepted `selector-routing` review card.

This worker does not implement selector-routing automation, selector mutation, routing-rule mutation, validation verdicts, release readiness, or platform checks. The objective is bounded to proving that the existing root-only packet ladder can safely package the selector/routing candidate family without widening authority.

## Required Command

```powershell
python ops\atlas\automation_candidate_packet_ladder.py --json --candidate-id selector-routing --decision-ref docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-SELECTOR-ROUTING-CANDIDATE-REVIEW-CONTRACT-FREEZE-2026-07-07.md
```

## Required Checks

- focused packet-ladder helper tests still pass
- live helper output returns `status=ok`
- live helper output returns `candidate_id=selector-routing`
- live helper output returns `candidate_review_status=review_ready`
- live helper output returns `packet_ladder` stage count `5`
- live helper output returns `safe_to_use=true`
- stack validation has no critical or error findings
- continuity restart index remains clean
- ATLAS marker surfaces exclude Fitness and Mazer owner-lane work from this root marker movement

## Stop Conditions

Stop without committing if:

- the helper no longer reports the candidate as `review_ready`
- output reports blockers
- validation returns a critical or error
- any owner repo would need mutation
- any secret, deploy, BrowserStack, Vercel, Supabase, Fitness, or Mazer state would need to be touched
- the worker would need to infer selector-routing implementation truth, validation verdicts, release readiness, or governance truth beyond the helper output

## Next Package

`AI Repetition-to-Automation Pipeline selector-routing packet ladder implementation-readiness closeout and worker routing`
