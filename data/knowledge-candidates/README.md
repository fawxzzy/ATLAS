# Atlas Knowledge Candidate Data

This directory is the durable Atlas-root home for real knowledge-candidate
projection packets.

## Layout

Each bounded packet uses `data/knowledge-candidates/<packet>/` and contains:

- one `*.knowledge-candidate.v2.json` artifact for each schema-eligible Atlas
  `KnowledgeCandidate`;
- one deterministic manifest covering every source record, including records
  that are intentionally outside the contract;
- byte and source-field hashes that bind owner handoffs to exact inputs.

Packet-specific generators and check commands live under `ops/atlas/`. Owner
handoffs live under `docs/ops/`; owner repositories are never output targets.

## Contract boundary

The canonical schema owns the allowed `KnowledgeCandidate` kinds. A source
record that is not one of those kinds remains visible in the packet manifest
with an explicit exclusion reason and no candidate artifact. It must not be
relabelled to force contract eligibility.

Candidate admission is review-only. Atlas projection creates no Playbook
doctrine, Cortex authority, owner-repository mutation, or automatic promotion.
