"""De-identify the 2020 BAI-paper analytic cohort and BAI-per-PSG table.

Outputs:
  bai_per_psg_deid.csv   — per-PSG deidentified BAI values
  cohort_v1_deid.csv     — V1-era cohort labels (matches the 2020 paper:
                           88 dementia, 119 MCI, 392 symptomatic, 1262 no-dementia)
  bai_psg_manifest.csv   — analytic-cohort PSG manifest with BIDS S3 paths

PHI inputs (gitignored under _box_inspect/):
  brain_age_Dementia/data/output_BA.csv               raw per-PSG BAI
  dementia_detection/medical_data/study_criteria_table_label.xlsx  V1 labels
  bdsp_collab_essentials/mapping.csv                  PatientID/FolderName ↔ HashID/BDSPPatientID
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path("/Users/mwestover/GithubRepos/Elissa-bai")
BA_OUT = ROOT / "_box_inspect/csvs/output_BA.csv"
COHORT = ROOT / "_box_inspect/dementia_detection_other/medical_data/study_criteria_table_label.xlsx"
MAPPING = ROOT / "_box_inspect/bdsp_collab_essentials/mapping.csv"
S3_STAGE = ROOT / "_s3_stage/bai-dementia-sleep"
S3_STAGE.mkdir(parents=True, exist_ok=True)


def main():
    # ------- BAI per PSG -------
    ba = pd.read_csv(BA_OUT, sep="\t")
    ba.columns = [c.strip() for c in ba.columns]
    ba["BAI_raw"] = ba["BA (yr)"] - ba["CA (yr)"]
    print(f"output_BA: {ba.shape}, valid raw-BAI rows: {ba['BAI_raw'].notna().sum():,}")

    mapping = pd.read_csv(MAPPING, dtype=str)
    # SubjectID = FolderName in this older format
    j = ba.merge(mapping[["FileNameOriginal", "HashID", "BDSPPatientID",
                           "DOVshifted", "ShiftedDays"]],
                 left_on="SubjectID", right_on="FileNameOriginal", how="left")
    deid_ba = j[j["HashID"].notna()].copy()
    deid_ba = deid_ba.rename(columns={"CA (yr)": "AgeAtPSG", "BA (yr)": "BrainAgeYr",
                                      "NumMissingStage": "NumMissingStage30sEpochs"})
    deid_ba["BAI"] = deid_ba["BAI_raw"]  # Note: raw, not bias-corrected. See README.
    deid_ba = deid_ba[["BDSPPatientID", "HashID", "DOVshifted", "ShiftedDays",
                       "AgeAtPSG", "BrainAgeYr", "BAI", "NumMissingStage30sEpochs", "Note"]]
    out_ba = S3_STAGE / "bai_per_psg_deid.csv"
    deid_ba.to_csv(out_ba, index=False)
    print(f"wrote {out_ba}: {deid_ba.shape}")

    # ------- Cohort V1 (matches 2020 paper) -------
    c = pd.read_excel(COHORT)
    c["MRN_key"] = c["MRN_key"].astype(str).str.replace(r"\.0$", "", regex=True)
    mapping["MRN"] = mapping["MRN"].astype(str).str.replace(r"\.0$", "", regex=True)
    c["DateOfVisit"] = pd.to_datetime(c["DateOfVisit"])
    mapping["DOV"] = pd.to_datetime(mapping["DOV"])
    j = c.merge(mapping[["PatientID", "MRN", "DOV", "BDSPPatientID", "HashID",
                          "FileNameNew", "DOVshifted", "ShiftedDays", "DOBshifted"]],
                left_on=["PatientID", "MRN_key", "DateOfVisit"],
                right_on=["PatientID", "MRN", "DOV"], how="inner")
    drop_phi = ["FolderName", "PatientID", "EMPI", "MRN_x", "MRN_y", "MRN", "MRN_key",
                "LastName", "FirstName", "DateOfBirth", "DateOfVisit", "Path", "DOV",
                "Note", "CDR_Note", "Low_CDR_Note", "MMSE_Note", "High_MMSE_Note",
                "MoCA_Note", "High_MoCA_Note", "Neuropsych_Note"]
    c_deid = j.drop(columns=[k for k in drop_phi if k in j.columns])
    front = ["BDSPPatientID", "HashID", "FileNameNew", "DOVshifted",
             "ShiftedDays", "DOBshifted", "Sex", "Age", "TypeOfTest", "Predicted_Stage"]
    front = [k for k in front if k in c_deid.columns]
    c_deid = c_deid[front + [k for k in c_deid.columns if k not in front]]
    out_c = S3_STAGE / "cohort_v1_deid.csv"
    c_deid.to_csv(out_c, index=False)
    print(f"wrote {out_c}: {c_deid.shape}")

    # ------- Analytic-cohort PSG manifest (DEM/MCI/Symptomatic/None) -------
    ana = c_deid[c_deid["Predicted_Stage"].isin(
        ["Dementia", "MCI", "Symptomatic", "No Dementia"])].copy()
    ana["group"] = ana["Predicted_Stage"].map(
        {"Dementia": "DEM", "MCI": "MCI",
         "Symptomatic": "Symptomatic", "No Dementia": "None"})
    keep = ["BDSPPatientID", "HashID", "FileNameNew", "DOVshifted",
            "Sex", "Age", "TypeOfTest", "group"]
    manifest = ana[keep].rename(columns={"Age": "AgeAtPSG", "TypeOfTest": "PSGType"})
    out_m = S3_STAGE / "bai_psg_manifest.csv"
    manifest.to_csv(out_m, index=False)
    print(f"wrote {out_m}: {manifest.shape}")
    print()
    print("group counts:", manifest["group"].value_counts(dropna=False).to_dict())


if __name__ == "__main__":
    main()
