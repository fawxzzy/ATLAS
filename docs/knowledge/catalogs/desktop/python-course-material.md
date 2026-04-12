# Desktop Python Course Material Catalog

## Scope

- catalog id: `desktop/python-course-material`
- parent item: `desktop`
- collection-relative path: `career/notes/python/material`
- current posture: low-priority reference archive
- confidence: `0.95`

## Evidence

- likely purpose: introductory Python course exercises and notebook archive
- language/toolchain: Python scripts and Jupyter notebooks
- entrypoints: individual scripts and notebooks under `Mod 1 Code Files` and `Module 2 Code Files`
- notable assets: `Intro to Python.ipynb`, `My First Jupyter Notebook.ipynb`
- docs/readmes: none found
- generated or vendor content present: minimal, limited to `.DS_Store`

## Decision

- keep this lane as course-material provenance, not a repo-ingest candidate
- do not promote exercises or notebooks into stack-owned source
- if future reuse is needed, keep extraction narrow and provenance-aware

## Keeper Boundary

Only these path groups are plausible keeper candidates if a specific reuse case later appears:

- `Mod 1 Code Files/*.py`
- `Mod 1 Code Files/*.ipynb`
- `Module 2 Code Files/*.py`
- `Module 3 Code Files/*.py`
- `Module 4 Code Files/*.py`

Non-keeper or courseware-heavy paths by default:

- `Intro-to-Functions.pdf`
- `Intro-to-Python-Programming-_-Course-Layout.pdf`
- `Intro-to-Python-Programming_Mod-1a.docx.pdf`
- `Intro-to-Python-Programming_Mod-1b.docx.pdf`
- `Intro-to-Python-Programming_Mod-2.docx.pdf`
- `Intro-to-Python-Programming_Mod-3.docx.pdf`
- `Intro-to-Variables.pdf`
- `Introduction-to-Python-Programming---Syllabus.pdf`
- `Python_Errors.pdf`
- `String-Functions.pdf`
- `Tips-to-Succeed-on-this-Course.docx.pdf`
- `What-is-a-Python-Script-.pdf`
- `Mod 3 Slide PDF Notetaking Handout Updated/**`
- `Mod 4 Slide PDF Notetaking Handout Updated/**`
- `Module 1 Slide PDF Notetaking Handouts/**`
- `Module 2 PDF Notetaking Handout Updated/**`

Generated or disposable noise:

- `Mod 1 Code Files/.DS_Store`
- `Module 2 Code Files/.DS_Store`
- `Module 3 Code Files/.DS_Store`
- `Module 4 Code Files/.DS_Store`

Current handling rule:

- keep the original archive slice in place
- keep the lane reference-first unless one exact script or notebook earns extraction
- do not treat the course PDFs or slide handouts as stack-owned source
