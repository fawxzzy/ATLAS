# Desktop Robocode Catalog

## Scope

- catalog id: `desktop/robocode`
- parent item: `desktop`
- collection-relative path: `career/notes/ai/aimaterial/lab projects/e - java project/robocode`
- current posture: reference/archive only
- confidence: `0.96`

## Evidence

- likely purpose: bundled Robocode distribution and Java learning archive
- language/toolchain: Java, Robocode distribution, batch and shell launchers
- entrypoints: `project/exec/robocode.bat`, `project/exec/robocode.sh`
- docs/readmes: `project/exec/ReadMe.txt`, `project/exec/ReadMe.html`, `project/exec/versions.md`
- notable assets: bundled sample robots, battle configs, JARs, templates, themes, and desktop launchers
- generated or vendor content present: `yes`

## Decision

- treat this lane as a standalone archive slice, not a repo candidate
- keep future work selective: extract only targeted materials if a Robocode-related recovery need appears
- keep any later decision scoped to this child catalog instead of the full `desktop` bundle

## Keeper Boundary

Provisional keeper candidates if a later narrow extraction is justified:

- `Project/Student Robot/fs_student/YourRobotName.java`
- `Project/config/robocode.properties`
- `Project/config/window.properties`
- `Project/exec/ReadMe.txt`
- `Project/exec/ReadMe.html`
- `Project/exec/versions.md`

Non-keeper or vendor-heavy paths unless a specific Robocode packaging recovery need is established:

- `Project/exec/libs/**`
- `Project/exec/javadoc/**`
- `Project/exec/license/**`
- `Project/exec/robots/**`
- `Project/exec/templates/**`
- `Project/exec/theme/**`
- `Project/Sample Robots/**`
- `Project/exec/*.bat`
- `Project/exec/*.sh`
- `Project/exec/*.command`

Current handling rule:

- keep the full original archive slice in place
- do not extract the vendor/runtime bundle by default
- treat the keeper list above as a narrow candidate set, not an approved ingest decision
