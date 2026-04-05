# Notebook CI summary

- Passed: 1
- Failed: 12
- Skipped: 6

## Failed notebooks

- `notebooks/P10_Data_Reduction_Geodmeographics.ipynb` — 2. readChar(con, 5L, useBytes = TRUE)
- `notebooks/P11_Data_Reduction_Indices.ipynb` — 3. file(file, "rt")
- `notebooks/P12_Spatial_Relationships.ipynb` — 6. stop(msg, call. = FALSE, domain = NA)
- `notebooks/P13_Regression.ipynb` — Traceback:
- `notebooks/P15_Network_Analysis.ipynb` — 6. stop(msg, call. = FALSE, domain = NA)
- `notebooks/P1_Introduction_to_R.ipynb` — 1. setwd("c:/temp")
- `notebooks/P2_Data_Manipulation_in_R.ipynb` —  .     "./data/tfl-daily-cycle-hires.xlsx")
- `notebooks/P4_Descriptive_Statistics.ipynb` — 6. stop(msg, call. = FALSE, domain = NA)
- `notebooks/P6_Mapping_Areas.ipynb` — 6. stop(msg, call. = FALSE, domain = NA)
- `notebooks/P7_Mapping_Points.ipynb` — Traceback:
- `notebooks/P7_Visualizing_Points.ipynb` — 6. stop(msg, call. = FALSE, domain = NA)
- `notebooks/P8_Mapping_Flows.ipynb` — 6. stop(msg, call. = FALSE, domain = NA)

## Skipped notebooks

- `python_example_for_Jupyter.ipynb` — Python-based notebooks are excluded from this CI workflow.
- `notebooks/P14_ABM.ipynb` — Requires NetLogo and rJava tooling that is not available in CI.
- `notebooks/P1_Introduction_to_Python.ipynb` — Python-based notebooks are excluded from this CI workflow.
- `notebooks/P2_Data_Manipulation_in_Python.ipynb` — Python-based notebooks are excluded from this CI workflow.
- `notebooks/P3_Basic_SQL.ipynb` — Uses external Carto services and write-capable SQL examples that are not CI-safe.
- `notebooks/P9_Linking_R_to_the_Web.ipynb` — Requires live third-party APIs and Twitter credentials.

## Passed notebooks

- `notebooks/P5_Charts_and_Graphs.ipynb`
