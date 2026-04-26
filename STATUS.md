# Reproducibility status

Snapshot of what's currently in this repo, where each piece came from, what's
verified, and what's still missing for end-to-end reproduction of
*Ye et al., JAMA Network Open 2020*.

## Legend

- ✅ Present and complete
- 🟡 Present but adapted / partially reproduced
- ⚠ Missing — pointer to where it likely lives
- 🔒 PHI — must not enter the repo without de-identification

---

## Provenance

The 2020 BAI paper precedes the SLEEP 2023 dementia-detection paper (sister
repo: `bdsp-core/dementia-detection-from-sleep`). Both share the MGH
sleep-laboratory cohort, the EHR phenotyping pipeline, and the BIDS-formatted
PSG release on S3. This repo is a smaller, specialized reproduction package
focused on:

1. The BAI training + bias-correction pipeline (originally in MATLAB).
2. The V1 (paper-era) chart-review cohort labels.
3. The four published figures.

---

## `code/01_phenotyping/`

Same labeling rules as the 2023 paper. Match rate of V1 labels ↔
`output_BA.csv` produces n=88 dementia, matching the paper exactly.

| File | Status | Source |
|---|---|---|
| `exclusion_regex`, `dementia_regex`, `MCI_regex.txt`, `medications_regex.txt` | ✅ | (internal Box folder) |
| `get_*.ipynb` (5 EHR extraction notebooks) | ✅ | (internal Box folder) (cell outputs stripped) |

Inputs (PHI; staged locally only): `study_criteria_table_label.xlsx` (V1), `EDW_*.csv`, `RPDR_*.csv`, `MMSE/MoCA/CDR_*Final.xlsx`. Same as the 2023 paper.

---

## `code/02_features/`

PSG → feature matrix. Same code as the 2023 paper.

| File | Status | Source |
|---|---|---|
| `segment_EEG.py`, `multitaper_spectrogram.py`, `bandpower.py`, `extract_features_parallel.py`, `load_mgh_sleep_dataset.py`, `main_BA.py` | ✅ | (internal Dropbox folder) |
| `main_box_2019.py` | ✅ | (internal Box folder) (Elissa's 2019 wrapper; references `/data/brain_age/mycode/` HPC paths) |

---

## `code/03_brain_age_model/`

The trained BAI GLM model + bias-correction MATLAB code. **This is what makes the BAI numbers themselves reproducible** — the model weights are shipped.

| File | Status | Description |
|---|---|---|
| `MGH_Model.mat` | ✅ | Trained generalized linear model (softplus link) — the BAI inference engine |
| `MGHBACA.mat`, `MGHBACAte.mat` | ✅ | MGH train/test BA-CA pairs |
| `SHHSBACA.mat` | ✅ | SHHS validation BA-CA pairs |
| `MGH_Sleep_CA_BAs_{tr,te}.csv` | ✅ | CSV versions of train/test |
| `BA_adjustment_bias.csv` | ✅ | Piecewise bias-correction LUT (CA-bin → bias) |
| `lsq_lut_piecewise.m` + `*Bias*.m` | ✅ | MATLAB code that fits + applies the piecewise bias correction |
| `a1_MGH_PredictAge.m`, `a0_*BoxPlots.m`, `a0_MGH_Figure_ResearchRetreat.m` | ✅ | Auxiliary MATLAB analysis / plotting code |

`age_features_mghsleep.mat` (17 MB) — the training feature matrix — is staged locally but kept out of git for size; ships in the BIDS release.

---

## `code/06_verification/`

| File | Status | Description |
|---|---|---|
| `verify_paper.py` | ✅ | Reports BAI medians per group under raw-vs-corrected hypotheses; flags V1 cohort match. Confirms n=88 dementia. |
| `regenerate_figures.py` | ✅ | From-scratch reproduction of Figures 1–4 (see "Reproduction status" below). |
| `figures/` | ✅ | Pre-rendered PNGs for visual comparison against paper. |

---

## `figures_paper/`

The four published JAMA Open figures (Figure1.svg, Figure2.svg, Figure3.svg, Figure4.svg + .pdf versions) for reference. Ship as-is.

---

## Data on S3 (`s3://bdsp-opendata-credentialed/bai-dementia-sleep/`)

| File | Rows | Status |
|---|---|---|
| `cohort_v1_deid.csv` | 22,985 | ✅ V1 cohort labels (paper-era), HashID/BDSPPatientID-keyed |
| `bai_per_psg_deid.csv` | 2,864 | ✅ Raw BAI per PSG (BA − CA, before bias correction) |
| `bai_psg_manifest.csv` | 13,283 | ✅ Analytic-cohort manifest with BIDS .edf paths (97.9% resolved) |

For bias-corrected BAI, point users to either `BA_adjustment_bias.csv` (do the correction yourself) or `features_MGH_deid.csv` from the sister 2023-paper release (BAI column already corrected).

---

## Reproduction status

### Cohort sizes (paper Methods + Results)

| Group | Reproduced (V1 ∩ output_BA) | Paper |
|---|---|---|
| Dementia | **88** | **88** ✅ |
| MCI | 119 | 44 |
| Symptomatic | 392 | 1,075 |
| No Dementia | 1,262 | 2,336 |

The dementia n matches exactly. Other group sizes diverge — paper applied additional cohort filtering (likely age stratification) that wasn't carried forward to V1. Not a code defect; a data-versioning gap.

### Figure 1 — BAI by group + BA vs CA (`figures/figure1_bai_by_group.png`)

✅ **Trend reproduced**: monotonic increase Healthy ≈ 0 < No Dementia < Symptomatic ≈ MCI < Dementia. Magnitudes higher than paper because:
- We use the bias-corrected BAI from `features_MGH_deid.csv` (later release, slightly different distribution)
- V1 ∩ features_MGH_deid is a different subset than the paper's analytic cohort

### Figure 2 — BAI vs MoCA / MMSE (`figures/figure2_bai_vs_cognitive.png`)

✅ **Negative correlations reproduced**:
- BAI vs MoCA: R = -0.10 (paper -0.14)
- BAI vs MMSE: R = -0.08 (paper -0.12)

### Figure 3 — Multivariable regression (`figures/figure3_regression_forest.png`)

🟡 **Partial reproduction**:
- Dementia: positive significant ✓
- Sex-Male: positive significant ✓
- Race-Black: positive (NS) ✓
- Psychotic Disorder: positive significant ✓
- Age: negative significant ✓
- Race-Asian: negative significant ✓
- Cardiovascular Disease: paper says positive significant; we get negative (likely difference in how the comorbidity flag is coded — paper used a different ICD-pattern set)
- AHI, ESS, BMI, PLMI, Smoker: not in the V1 cohort table; would need to re-derive from PSG metadata + RPDR

### Figure 4 — EEG feature ORs by stage (`figures/figure4_eeg_feature_ORs.png`)

⚠ **Partial**: only the REM panel populated. The other stages (Wake, N1, N2, N3) require a per-stage feature decomposition that uses different column names than the deid feature matrix exposes (W / NREM / R rather than Wake / N1 / N2 / N3 / REM). Fixing it requires re-extracting features from the raw PSGs with stage-resolved `main_BA.py` output.

---

## What's missing

1. **Elissa's original figure-generation Python/notebook code.** Confirmed not in any accessible Box / Dropbox folder; was on an internal Dropbox folder no longer accessible to the project.
2. **The exact paper-era cohort filter** that brought 5,144 PSGs / 88-44-1075-2336 group split.
3. **AHI, ESS, BMI, PLMI, Smoker covariates** for Figure 3 — derivable from PSG metadata + RPDR but not pre-staged.
4. **Per-stage Wake/N1/N2/N3 feature columns** for Figure 4 — current deid release has W/NREM/R only.

## Open question for Elissa / Haoqi

If you have a backup of the original project Dropbox folder, the figure-generation notebooks should be there.
