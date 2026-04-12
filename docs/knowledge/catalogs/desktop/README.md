# Desktop Subproject Catalog

This catalog records the current child-level split for the mixed `desktop` ingest item.

The parent `desktop` bundle stays a collection-level manifest. Durable ATLAS truth for the split lives here instead of under `tmp/`.

## Parent Posture

- parent item: `desktop`
- current posture: mixed archive, not a repo
- decision boundary: keep the parent unpromoted and make ingest-or-reference decisions per child catalog
- provenance note: the original machine-local source path remains local review evidence and is intentionally omitted from this tracked doc

## Child Catalogs

| Catalog ID | Collection-relative path | Current posture | Next decision |
| --- | --- | --- | --- |
| `desktop/robocode` | `career/notes/ai/aimaterial/lab projects/e - java project/robocode` | Reference/archive only | Keep cataloged; allow only targeted extraction if a Robocode recovery need appears. |
| `desktop/lrpython-linear-regression` | `career/notes/ai/aimaterial/lab projects/linearregression - base/LRPython` | Copy-first selective ingest executed; originals retained | Use `data/imports/knowledge/personal/desktop-lrpython-linear-regression` as the working lane and leave the parent slice in place unless a later reclaim step is explicitly approved. |
| `desktop/python-course-material` | `career/notes/python/material` | Low-priority reference archive | Keep as course-material provenance and do not treat it as repo-ingest material. |

## Current Rule

- Do not promote `desktop` wholesale.
- Do not collapse the child lanes back into one recovered project.
- Do not make repo-ingest claims from this catalog alone.
- Keep the imported originals in place unless a later child-level extraction or reclaim step is explicitly executed.
- Use the child docs below when a later ingest-or-reference decision is needed.

## Child Docs

- [Robocode](robocode.md)
- [LRPython / Linear Regression](lrpython-linear-regression.md)
- [Python Course Material](python-course-material.md)
