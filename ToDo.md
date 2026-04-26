# ToDo — JAMA Open 2020 BAI paper

Concrete next steps for completing reproduction. Most of the heavy lifting
overlaps with the SLEEP-2023 sister repo (`bdsp-core/dementia-detection-from-sleep`)
which already shipped a comprehensive deid release.

## P0 — Recover original figure code (if possible)

### 1. Email Elissa Ye / Haoqi Sun for the figure-generation notebooks
- The figures-Python is not in any Box / Dropbox folder I've searched.
- It was on the internal Dropbox folder no longer accessible referenced
  in `step2b_*ElissaCriteria*.py` as `${DEMENTIA_DATA_ROOT}/`.
- Elissa likely has a copy on a personal machine or Google Drive backup.

## P1 — Tighten figure reproduction

### 2. Recover the paper-era cohort filter
- Paper analytic cohort: 5,144 PSGs / 88 DEM / 44 MCI / 1075 Symp / 2336 None.
- V1 ∩ `output_BA.csv` gives DEM=88 (exact) but other categories differ.
- Suspect filter: age ≥ 50, MoCA/MMSE coverage threshold, or PSG quality filter.
- Document in code/04_analysis/ once recovered.

### 3. Add AHI / ESS / BMI / PLMI / Smoker to Figure 3 covariates
- These were in paper Fig 3 but not shipped in V1 cohort.
- Derive from `RPDR_Dia_All.csv` (Smoker, comorbidities) +
  `mastersheet_outcome_deid.xlsx` (AHI, BMI, ESS) from the SLEEP-2023 release.

### 4. Fix Figure 4 stage decomposition
- Current deid features use W/NREM/R aggregation.
- Re-extract with explicit Wake/N1/N2/N3/REM separation by re-running
  `main_BA.py` with per-stage output mode. Out of scope for direct reproduction
  on existing data; requires raw PSGs.

### 5. Implement bias-correction in Python
- Currently we use the bias-corrected BAI from `features_MGH_deid.csv`
  (downstream release). For users who want to re-run end-to-end:
  - Implement `BA_adjustment_bias.csv` LUT lookup in Python (mirror MATLAB's
    `lsq_lut_piecewise.m`).
  - Validate against `features_MGH_deid.csv` BAI column.

## P2 — Repo polish

### 6. Document how to re-run the BAI MATLAB pipeline
- `MGH_Model.mat` + `a1_MGH_PredictAge.m` is the inference path.
- Add `code/03_brain_age_model/README.md` with a worked example
  (load .mat → score a held-out PSG → write BAI).

### 7. Adapt `notebooks/` with an end-to-end example
- Walk through: load a deidentified feature row → score with the GLM model
  → apply bias correction → output BAI. Both Python and MATLAB versions.

### 8. Document the Healthy reference
- Healthy = the 2,330-subject training set in `MGH_Sleep_CA_BAs_tr.csv`.
- This is what the BAI is calibrated against (BAI ≈ 0 on Healthy by construction).

## P3 — Nice-to-have

### 9. SHHS validation reproduction
- We have `SHHSBACA.mat` and `SHHS_BA_CA.csv` from the brainAge folder.
- Paper supplement reports a SHHS validation; could regenerate that figure too.

### 10. Companion bdsp.io publication page
- Link to GitHub + S3, mirror citation, link to the SLEEP-2023 sister page.
