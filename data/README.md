# Data — pointers to the BDSP S3 release

This repository ships **code only**. The deidentified data live in the BDSP
credentialed-access bucket.

## S3 location

```
s3://bdsp-opendata-credentialed/bai-dementia-sleep/
```

| File | Rows × cols | Description |
|------|-------------|-------------|
| `cohort_v1_deid.csv` | 22,985 × 65 | Per-PSG cohort with V1 (paper-era) chart-review labels — Predicted_Stage in {Dementia, MCI, Symptomatic, No Dementia, Excluded}. Keyed by `BDSPPatientID, HashID, FileNameNew, DOVshifted, ShiftedDays, DOBshifted`. The DEM count (n=88) when intersected with the BAI table matches the paper exactly. |
| `bai_per_psg_deid.csv` | 2,864 × 9 | Per-PSG raw BAI from the 2019 model output, deidentified. Columns: `BDSPPatientID, HashID, DOVshifted, ShiftedDays, AgeAtPSG, BrainAgeYr, BAI, NumMissingStage30sEpochs, Note`. **BAI is raw BA − CA**, not the bias-corrected value reported in the paper. Two ways to recover the bias-corrected BAI: (a) apply `code/03_brain_age_model/BA_adjustment_bias.csv` LUT to `BA - CA` per chronological-age bin; (b) use the `BAI` column from the SLEEP-2023 sister release `s3://bdsp-opendata-credentialed/sleep-dementia-detection/features_MGH_deid.csv` (same model, bias-corrected), keyed by `HashID`. |
| `bai_psg_manifest.csv` | 13,283 × 10 | One row per analytic-cohort PSG (DEM/MCI/Symptomatic/None). Columns: `BDSPPatientID, HashID, FileNameNew, DOVshifted, Sex, AgeAtPSG, PSGType, group, session, s3_path`. **`s3_path` points directly to the BIDS .edf** at `s3://bdsp-opendata-repository/PSG/bids/S0001/sub-S0001<BDSPPatientID>/ses-<N>/eeg/sub-S0001<BDSPPatientID>_ses-<N>_task-psg_eeg.edf`. 13,002/13,283 (97.9 %) PSGs resolve to a live BIDS path. |

All tables use the deidentified key conventions:

- `BDSPPatientID` — stable per-patient ID in the BDSP namespace
- `HashID` — SHA-256 hash of the source PSG; unique per recording
- `FileNameNew` — `<HashID>_<YYYYMMDD>_<HHMMSS>` (legacy filename; use `s3_path` for the BIDS-formatted location)
- `DOVshifted`, `DOBshifted`, `ShiftedDays` — per-patient random date offset (±365 d) applied consistently to every date for that patient

## How to download

Credentialing: https://bdsp.io/credentialing/

```bash
# Full set (~13 MB — small because the BAI tables are summary statistics)
aws s3 sync s3://bdsp-opendata-credentialed/bai-dementia-sleep/ ./data/

# Or with rclone
rclone sync s3:bdsp-opendata-credentialed/bai-dementia-sleep/ ./data/
```

## How the deidentified data were derived

`scripts/deidentify_bai_cohort.py` joins the PHI source tables with `mapping.csv` from the BDSP collaboration folder, which provides the canonical
`(PatientID, MRN, DOV) → (BDSPPatientID, HashID, FileNameNew, DOVshifted)` crosswalk for every PSG in the BDSP-deID release. PSG-to-BIDS-session resolution uses the per-subject `scans.tsv` files from the BIDS S3 release.

## Raw PSG recordings

Raw deidentified EEG signals are at:

```
s3://bdsp-opendata-repository/PSG/bids/S0001/sub-S0001<BDSPPatientID>/ses-<N>/eeg/...edf
```

The same BIDS prefix is used by the SLEEP-2023 companion paper (`bdsp-core/dementia-detection-from-sleep`) — recordings can be re-used across both reproducibility packages.
