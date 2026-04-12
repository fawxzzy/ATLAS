# Desktop LRPython / Linear Regression Catalog

## Scope

- catalog id: `desktop/lrpython-linear-regression`
- parent item: `desktop`
- collection-relative path: `career/notes/ai/aimaterial/lab projects/linearregression - base/LRPython`
- current posture: copy-first selective ingest executed; originals retained
- confidence: `0.94`

## Evidence

- likely purpose: Python linear regression lab and Visual Studio Python project archive
- language/toolchain: Python, Visual Studio Python project, batch launchers
- entrypoints: `LinearRegression.py`, `LinearBasic.bat`, `LinearPolynomial.bat`, `LinearPolyReg.bat`
- data assets: `LinearTrainData1.csv`, `LinearTrainData2.csv`, `LinearTestData1.csv`, `LinearTestData2.csv`, `LRTrainDataReg.csv`, `LRTestDataReg.csv`
- project markers: `LRPython.pyproj`
- generated or vendor content present: `yes`, including compiled artifacts such as `Regression.dll`, `.iobj`, and `.ipdb`

## Decision

- executed copy-first selective ingest into `data/imports/knowledge/personal/desktop-lrpython-linear-regression`
- the imported child archive contains only the approved source, test, CSV dataset, and project-file keeper scope
- archive id: `personal--desktop-lrpython-linear-regression`
- do not promote this child lane as a repo and do not treat the current archive slice as an application repo
- keep the original archive slice in place until a later explicit reclaim step is approved

## Keeper Boundary

Approved keeper scope copied into the child archive:

- `LinearRegression.py`
- `LinearRegressionBasic.py`
- `LinearRegressionPolynomial.py`
- `LinearRegressionPolyReg.py`
- `Regression.py`
- `BokehRegressionPlotting.py`
- `LRBasicTest.py`
- `LRPolyTest.py`
- `LRPolyRegTest.py`
- `LinearTrainData1.csv`
- `LinearTrainData2.csv`
- `LinearTestData1.csv`
- `LinearTestData2.csv`
- `LRTrainDataReg.csv`
- `LRTestDataReg.csv`
- `LRPython.pyproj`

Secondary keeper candidates only if toolchain provenance matters:

- `LinearBasic.bat`
- `LinearPolynomial.bat`
- `LinearPolyReg.bat`

Non-keeper generated artifacts:

- `Regression.dll`
- `Regression.iobj`
- `Regression.ipdb`

Current handling rule:

- use the imported child archive as the working lane for any future LRPython review or reuse
- keep batch launchers optional and provenance-only unless a concrete tooling reason appears
- leave compiled outputs behind unless a provenance-only note later requires them
