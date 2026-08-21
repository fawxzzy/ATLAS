# ATLAS Engineering Memory Task Harness

Use this harness for implementation work that begins as a rough operator note.
Do not ask the operator to fill a structured prompt when the task can be
normalized from repository evidence.

## Required opening

Begin natural-language output with a two-line maximum `Quick summary:`, then:

```text
Done: known or completed
Now: active task
Next: intended move
```

Include a repository health check and preserve dirty user state.

## Required order

1. Preserve the operator's exact source note.
2. Bind one canonical `atlas.card-record.v2` identity and one correlated
   `atlas.job-envelope.v2` identity.
3. Normalize project, repository, route/state, component, task type, acceptance
   criteria, verification requirements, and parent scope lock into
   `job.extensions.engineering_memory`.
4. Search the current repository and ATLAS docs for precedents. Search sibling
   repos, Playbook, archives, tests, design-system docs, and visual fixtures when
   relevant.
5. Attach the results and choose `reuse`, `adapt`, `reject`, or
   `first-durable-pattern`. If no precedent exists, state: `No matching
   precedent found. Creating first durable pattern.`
6. When the source says `same as`, `match`, `carry over`, `make it like`,
   `reuse`, or equivalent language, classify it as `ui_parity`; name the source
   surface, target surfaces, shared properties, and shared implementation or
   documented variant.
7. Freeze the parent's acceptance criteria. Create stable linked child tasks for
   newly discovered independent work; never absorb them silently.
8. Run the mutation gate before editing source:

   ```powershell
   node ops/atlas/engineering_memory_gate.mjs `
     --job-envelope <job.json> `
     --card-record <card.json> `
     --gate mutation
   ```

9. Implement the smallest coherent change from the canonical component or
   precedent.
10. Run repo-local deterministic checks. For visual work, navigate to the actual
    route/state, capture or inspect source and target surfaces, and reconcile
    every requested item.
11. Attach evidence and run `--gate verify`. Never mark a task done just because
    code changed. Mark it done only after expected behavior is verified through
    tests, screenshots, DOM evidence, a local run, or an explicit limitation
    that keeps the task partial/blocked rather than verified.
12. Create a repo-visible completion archive using existing conventions. Include
    task identity, date, branch/revision if available, changed files, knowledge
    entries, verification, unverified items, risks, follow-ups, and final status
    `complete`, `partial`, or `blocked`.
13. Run `--gate archive`, emit the normal execution receipt, reconcile the card,
    and persist the ATLAS thread-context checkpoint.

## Fast-lane rule

Use `fast` only for one clear issue, one or two components, a known verification
route, simple acceptance criteria, and no schema, migration, Auth, security,
production, secret, billing, or destructive boundary. If it expands, promote it
to `normal` and preserve the original parent task.

Fast-lane human output:

```text
Captured
Precedent checked
Changed
Verified
Archived
```

## Completion output

```text
Done:
- ...

Verified:
- ...

Changed files:
- ...

Created/updated rules:
- ...

Created/updated patterns:
- ...

Created/updated failure modes:
- ...

Created/updated decisions:
- ...

Archive:
- ...

Not verified:
- ...

Follow-up tasks:
- ...

Final status:
- complete | partial | blocked
```

Canonical policy:
`docs/registry/ATLAS-ENGINEERING-MEMORY-POLICY.v1.json`.
