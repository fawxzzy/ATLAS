# Desktop LRPython / Linear Regression Catalog

## Scope

- catalog id: `desktop/lrpython-linear-regression`
- parent item: `desktop`
- collection-relative path: `career/notes/ai/aimaterial/lab projects/linearregression - base/LRPython`
- current posture: archive/reference with selective extraction potential
- confidence: `0.94`

## Evidence

- likely purpose: Python linear regression lab and Visual Studio Python project archive
- language/toolchain: Python, Visual Studio Python project, batch launchers
- entrypoints: `LinearRegression.py`, `LinearBasic.bat`, `LinearPolynomial.bat`, `LinearPolyReg.bat`
- data assets: `LinearTrainData1.csv`, `LinearTrainData2.csv`, `LinearTestData1.csv`, `LinearTestData2.csv`, `LRTrainDataReg.csv`, `LRTestDataReg.csv`
- project markers: `LRPython.pyproj`
- generated or vendor content present: `yes`, including compiled artifacts such as `Regression.dll`, `.iobj`, and `.ipdb`

## Decision

- keep this lane separate from the other desktop material when future ingest decisions are made
- allow only a later narrow decision about metadata, datasets, or source extraction
- do not treat the current archive slice as an application repo just because it has project files

## Keeper Boundary

Strong keeper candidates if this child lane later earns selective ingest:

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

- keep the original archive slice in place until a child-level ingest decision is made
- bias any future extraction toward source, tests, datasets, and the project file
- leave compiled outputs behind unless a provenance-only note later requires them
