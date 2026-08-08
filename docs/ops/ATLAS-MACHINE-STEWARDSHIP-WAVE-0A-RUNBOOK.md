# ATLAS Machine Stewardship Wave 0A Runbook

## Purpose

This runbook validates the source-only Wave 0A evidence plane and, when
separately authorized, records one redacted non-admin sample. It does not
authorize machine management or Lifeline execution.

## Preconditions

Before running a sample:

1. use an isolated ATLAS worktree at an exact admitted commit;
2. confirm the writer reservation and exact path ceiling;
3. confirm the output root is an admitted local `tmp/` path;
4. run the focused tests before observing the host;
5. remain non-elevated and do not supply credentials or environment values.

## Source verification

From the isolated ATLAS worktree:

```powershell
python -m unittest tests.test_atlas_machine_stewardship -v
python ops/validation/validate_stack.py --json
python -m compileall -q ops/atlas/machine_stewardship tests/test_atlas_machine_stewardship.py
```

Validate both fixtures through the CLI:

```powershell
python -m ops.atlas.machine_stewardship.cli validate tests/fixtures/atlas-machine-stewardship/observed-state.v1.json
python -m ops.atlas.machine_stewardship.cli validate tests/fixtures/atlas-machine-stewardship/policy.v1.json
```

The test suite validates all five schemas and proves byte-identical
nonvolatile normalization across two observations.

## Authorized sample

Only when a task explicitly admits a local sample, pass its exact output root:

```powershell
python -m ops.atlas.machine_stewardship.cli sample --output-dir <admitted-local-tmp-root>
```

The command creates one content-addressed observation directory and refuses to
overwrite it. Its only outputs are:

- `observed-state.v1.json`;
- `validation-report.v1.json`;
- `sample-manifest.v1.json`.

Inspect those files for:

- secret-like assignments;
- unredacted user-home segments;
- cookies, tokens, keys, authorization values, or environment values;
- file contents or content-derived fields;
- UNC paths;
- any claim of deletion safety or machine mutation.

The expected count for each category is zero.

## Collector limitations

The identity collector retains an irreversible host-label fingerprint plus
general OS metadata. The Windows storage collector reads fixed logical-volume
capacity metadata only. It does not enumerate directories, files, reparse
points, cloud placeholders, or shares. On a non-Windows platform, storage
collection returns a structured `UNSUPPORTED_PLATFORM` error rather than
guessing.

An inaccessible or malformed volume record is isolated. The observation may be
partial while identity evidence remains valid.

## Prohibited actions

This runbook never authorizes:

- elevation or UAC;
- registry writes;
- startup, service, or scheduled-task mutation;
- installation, upgrade, uninstall, repair, quarantine, movement, or deletion;
- security changes;
- file-content collection;
- network-share traversal or upload;
- cloud-placeholder hydration;
- ATLAS or Lifeline runtime activation;
- treating missing evidence as deletion safety.

## Extending the collectors

Do not add a deferred collector to the existing Wave 0A admission. Create a
new bounded contract lane, document its privacy and protected-zone boundary,
add deterministic fixtures and negative tests, and obtain an exact source
admission. Machine mutation still belongs to a separately admitted Lifeline
primitive.

Deferred families are:

1. top-level directory aggregation and configurable large-file metadata scan;
2. WinGet, AppX/MSIX, and read-only uninstall-registry application inventory;
3. startup, services, scheduled tasks, and optional already-installed Autoruns;
4. developer-tool discovery;
5. bounded performance sampling;
6. recovery and security status collectors;
7. complete whole-machine baseline acceptance across all collector families.

## Terminal evidence

A source-only receipt must state:

- exact base, tree, worktree, branch, and 15-path diff;
- commands, exit codes, test counts, and deterministic hashes;
- sample paths, byte counts, and hashes;
- secret and boundary scan results;
- explicit zero machine-state mutation;
- explicit no stage, commit, push, PR, review, ready, merge, or activation.
