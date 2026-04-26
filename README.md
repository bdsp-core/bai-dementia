# Sleep EEG-Based Brain Age Index and Dementia

Reproducibility package for:

> Ye EM, Sun H, Leone MJ, Paixao L, Thomas RJ, Lam AD, Westover MB.
> **Association of Sleep Electroencephalography-Based Brain Age Index With Dementia.**
> *JAMA Network Open* 2020;3(9):e2017357.
> https://doi.org/10.1001/jamanetworkopen.2020.17357

## What's in the paper

A cross-sectional study of 9,834 polysomnograms in which a sleep-EEG–derived
**Brain Age Index (BAI)** — the difference between brain age estimated from sleep
EEG and chronological age — was computed and compared across diagnostic
groups (Healthy / Non-Dementia / Symptomatic / MCI / Dementia).

- **Dataset:** 9,834 PSGs from the MGH Sleep Laboratory, 2009–2017.
- **Analytic:** 5,144 PSGs with valid BAI examinations.
- **Group breakdown:** 88 dementia, 44 MCI, 1,075 symptomatic, 2,336 nondementia.
- **Headline:** monotonic BAI increase from nondementia → dementia
  (medians 0.20 / 0.58 / 1.65 / 4.18; *P* < .001 for trend).
- **Conclusion:** BAI shows promise as a non-invasive biomarker for progressive
  brain processes that ultimately result in dementia.

## Quick start

```bash
git clone https://github.com/bdsp-core/bai-dementia.git
cd bai-dementia
pip install -r requirements.txt

# Pull the deidentified data (~13 MB; credentialed access required)
aws s3 sync s3://bdsp-opendata-credentialed/bai-dementia-sleep/ ./data/

# Reproduce the figures
python3 code/06_verification/regenerate_figures.py
```

## Repository layout

```
bai-dementia/
├── code/
│   ├── 01_phenotyping/    Elissa Ye's chart-review labeling rules
│                          (regex files, V_pre_2020 EHR notebooks, dementia/
│                          MCI/medications/exclusion criteria)
│   ├── 02_features/       Feature extraction pipeline
│                          (bandpower, multitaper, segment_EEG,
│                          extract_features_parallel, main_BA, main_box_2019)
│   ├── 03_brain_age_model/  Trained GLM model + bias-correction MATLAB code
│                            (MGH_Model.mat, lsq_lut_piecewise.m,
│                            a0_MGH_DataCorrectBias*.m, train/test BA-CA pairs)
│   ├── 04_analysis/       Per-paper analysis notebooks (placeholder; see notes)
│   ├── 05_figures/        Figure regeneration scripts
│   └── 06_verification/   Paper-headline verification + figure reproducers
│       └── figures/       Pre-rendered PNGs from a 2026-04-25 run
├── data/                  README only — actual data lives in S3
├── docs/
├── figures_paper/         The original published Figs 1-4 (.svg, .pdf)
│                          for visual comparison
├── scripts/               De-identification + manifest-build utilities
├── LICENSE                CC BY-NC 4.0
├── README.md, STATUS.md, ToDo.md
└── requirements.txt
```

## Data access

The deidentified data live in the BDSP credentialed-access bucket:

```
s3://bdsp-opendata-credentialed/bai-dementia-sleep/
```

| File | Rows × cols | Description |
|------|-------------|-------------|
| `cohort_v1_deid.csv` | 22,985 × 65 | Per-PSG cohort with the V1 (paper-era) chart-review labels. Keyed by `BDSPPatientID`, `HashID`, `FileNameNew`. Includes Predicted_Stage (Dementia / MCI / Symptomatic / No Dementia / Excluded), all per-disease evidence flags, cognitive scores, demographics. |
| `bai_per_psg_deid.csv` | 2,864 × 9 | Per-PSG raw BAI (BA − CA) from the 2019 model output, joined to BDSP IDs. Columns: `BDSPPatientID, HashID, DOVshifted, ShiftedDays, AgeAtPSG, BrainAgeYr, BAI, NumMissingStage30sEpochs, Note`. **Note: BAI here is the *raw* BA − CA, not the bias-corrected version reported in the paper.** Apply the bias-correction LUT in `code/03_brain_age_model/BA_adjustment_bias.csv` (or the bias-corrected BAI column from the 2023-paper release `s3://bdsp-opendata-credentialed/sleep-dementia-detection/features_MGH_deid.csv`) for paper-comparable values. |
| `bai_psg_manifest.csv` | 13,283 × 10 | One row per analytic-cohort PSG. Columns: `BDSPPatientID, HashID, FileNameNew, DOVshifted, Sex, AgeAtPSG, PSGType, group, session, s3_path`. **`s3_path` points directly to the BIDS .edf** at `s3://bdsp-opendata-repository/PSG/bids/S0001/sub-S0001<BDSPPatientID>/ses-<N>/eeg/...`. 13,002/13,283 (97.9 %) PSGs resolve to a live BIDS path. |

For raw EEG signals, see [data/README.md](data/README.md). The same BIDS layout used by the SLEEP-2023 companion paper applies.

## Reproduction status

This repository was assembled retrospectively. Elissa Ye's original
figure-generation Python/notebook code lived on an internal
Dropbox account that has since been decommissioned, so the figures here
are **regenerated from scratch** in `code/06_verification/regenerate_figures.py`.
See [docs/reproduction_check.md](docs/reproduction_check.md) for the
side-by-side comparison and caveats.

Headline reproductions (full table in `docs/reproduction_check.md`):

- **Cohort sizes:** Dementia n=88 matches paper exactly when V1 labels
  are intersected with `output_BA.csv`. Other group n's diverge from
  paper (paper used additional cohort filtering not preserved in V1).
- **BAI trend:** monotonic increase from Healthy → Non-Dementia →
  Symptomatic → MCI → Dementia is reproduced (Figure 1A).
- **BAI vs cognitive scores:** negative correlation reproduced (R = -0.10
  for MoCA, R = -0.08 for MMSE — paper R = -0.14 / -0.12).
- **Multivariable regression:** Dementia is a significant positive
  predictor of BAI; Sex-Male, Race-Black, Psychotic Disorder all
  positive (matching paper). Some covariate magnitudes / signs differ
  due to cohort + comorbidity-coding differences.

## Companion repository

This is the precursor to the SLEEP 2023 paper. The full feature-engineering
pipeline (spindles, slow oscillations, coherence, bandpowers) +
classification models for that paper live at:

> https://github.com/bdsp-core/dementia-detection-from-sleep

They share the same MGH cohort, BIDS PSG layout, and `mapping.csv`
de-identification crosswalk.

## How to cite

```bibtex
@article{ye2020bai,
  title={Association of Sleep Electroencephalography-Based Brain Age Index With Dementia},
  author={Ye, Elissa M and Sun, Haoqi and Leone, Michael J and Paixao, Luis and
          Thomas, Robert J and Lam, Alice D and Westover, M Brandon},
  journal={JAMA Network Open},
  volume={3}, number={9}, pages={e2017357},
  year={2020},
  doi={10.1001/jamanetworkopen.2020.17357}
}
```

## License

CC BY-NC 4.0. See [LICENSE](LICENSE).
