# Third-Party Playbook Policy

This document defines how ATLAS handles playbooks created outside the stack.

## Core Policy

Third-party playbooks are external content packs.

They are not:

- authoritative stack policy
- approved runtime code
- something to unpack into `repos/cortex`
- something to scatter across active repos during import

## Required Intake Flow

Every third-party pack must move through:

1. import into `data/imports/playbooks/`
2. evaluation against this policy
3. normalization into ATLAS-owned metadata if accepted
4. cataloging in `docs/playbooks/PLAYBOOK-CATALOG.md`
5. selective adoption, or rejection

## Acceptable Inputs

Examples:

- markdown playbooks
- prompt packs
- operator runbooks
- policy docs
- templates
- JSON or YAML metadata bundles

Executable content is not automatically trusted just because it arrived with useful docs.

## Evaluation Criteria

Review each pack for:

1. provenance
2. licensing and reuse constraints
3. safety
4. vendor neutrality
5. portability
6. overlap with existing ATLAS doctrine
7. whether it requires repo mutation to be useful

## Unsafe Or Rejected Characteristics

Reject or quarantine packs that:

- require secrets to evaluate
- require a daemon, background service, or hidden scheduler
- depend on vendor-specific local config files as the primary contract
- rewrite active repos by default
- assume one AI model vendor is the platform truth
- hide state outside ATLAS-owned lanes

## Vendor-Specific Content Rule

Vendor-specific ideas may still be reviewed, but they should only be adopted when they can be translated into an ATLAS-owned, vendor-neutral abstraction.

Examples of acceptable selective adoption:

- a portable event taxonomy
- a generalized validation step
- a checklist concept rewritten in ATLAS terms

Examples of non-acceptable adoption:

- copying a vendor's private config format into stack truth
- standardizing on one vendor's hook file as the stack contract
- unpacking a vendor's helper scripts into active repos without scoped approval

## Adoption Rule

If a pack contains something worth keeping, ATLAS should re-express it in:

- stack docs
- ATLAS-owned schemas
- ATLAS-owned wrapper scripts
- ATLAS-owned validation logic

The adopted artifact should stand on its own without the original vendor pack.

## Rejection Rule

Rejected packs should remain traceable through their import manifest unless legal or safety policy requires removal.

Rejection should record:

- why the pack was rejected
- whether any safe ideas were extracted before rejection
- whether future re-review is worthwhile
