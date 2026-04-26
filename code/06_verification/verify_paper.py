"""Verify reproduction of the 2020 BAI paper headline numbers.

Paper: Ye EM, Sun H, Leone MJ, Paixao L, Thomas RJ, Lam AD, Westover MB.
       Association of Sleep EEG-Based Brain Age Index With Dementia.
       JAMA Network Open 2020;3(9):e2017357.

Headline numbers from the paper:
  Dataset:    9,834 PSGs total
  Analytic:   5,144 PSGs with BAI examinations
  Categories: 88 dementia, 44 MCI, 1,075 symptomatic, 2,336 nondementia
  BAI:        nondementia 0.20 [0.42], symptomatic 0.58 [0.41],
              MCI 1.65 [1.20], dementia 4.18 [1.02]   (median [IQR])

This verification uses two BAI sources:
  (a) RAW BAI (BA - CA) from output_BA.csv (the 2019 model output) — produces
      the right cohort sizes when filtered to V1 labels but the BAI values
      have not been bias-corrected, so don't match paper magnitudes.
  (b) BIAS-CORRECTED BAI from features_MGH_deid.csv (the 2023-paper deid
      release; same model + bias correction pipeline used in the 2020 paper)
      — gives a closer match to paper magnitudes but joins to a slightly
      different cohort (the SBOP cohort excludes prevalent dementia at PSG).

The exact paper-cohort BAI numbers are not directly reproducible from
shipped artifacts because the paper's cohort filter (5,144 PSGs) was not
carried forward to V6/SBOP-era data.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path("/Users/mwestover/GithubRepos/Elissa-bai")
BA_OUT = ROOT / "_box_inspect/csvs/output_BA.csv"
COHORT_V1 = ROOT / "_box_inspect/dementia_detection_other/medical_data/study_criteria_table_label.xlsx"
MAPPING = ROOT / "_box_inspect/bdsp_collab_essentials/mapping.csv"
FEATURES_MGH = ROOT / "_s3_stage/sleep-dementia-detection/features_MGH_deid.csv"

PAPER_N = {"No Dementia": 2336, "Symptomatic": 1075, "MCI": 44, "Dementia": 88}
PAPER_BAI = {"No Dementia": 0.20, "Symptomatic": 0.58, "MCI": 1.65, "Dementia": 4.18}
PAPER_IQR = {"No Dementia": 0.42, "Symptomatic": 0.41, "MCI": 1.20, "Dementia": 1.02}


def report(label, m, bai_col):
    print(f"\n--- {label} ---")
    print(f"  {'group':12s} {'n':>5s} {'paper_n':>7s}  {'BAI med':>8s} {'BAI IQR':>8s}  "
          f"{'paper_BAI':>9s} {'paper_IQR':>9s}")
    for stage in ["No Dementia", "Symptomatic", "MCI", "Dementia"]:
        sub = m[m["Predicted_Stage"] == stage]
        if len(sub) == 0:
            continue
        bai = sub[bai_col].dropna()
        iqr = bai.quantile(.75) - bai.quantile(.25)
        print(f"  {stage:12s} {len(sub):>5d} {PAPER_N[stage]:>7d}  "
              f"{bai.median():>8.2f} {iqr:>8.2f}  "
              f"{PAPER_BAI[stage]:>9.2f} {PAPER_IQR[stage]:>9.2f}")


def main():
    print("Loading…")
    ba = pd.read_csv(BA_OUT, sep="\t")
    ba.columns = [c.strip() for c in ba.columns]
    ba["BAI_raw"] = ba["BA (yr)"] - ba["CA (yr)"]

    c = pd.read_excel(COHORT_V1)
    print(f"V1 cohort: {c.shape}, "
          f"Predicted_Stage: {c['Predicted_Stage'].value_counts(dropna=False).to_dict()}")

    # (a) raw BAI from output_BA.csv joined to V1 by FolderName
    m1 = ba.merge(c[["FolderName", "Predicted_Stage"]],
                  left_on="SubjectID", right_on="FolderName", how="inner")
    m1 = m1[(m1["NumMissingStage"] == 0) & m1["BAI_raw"].notna()]
    report("(a) raw BAI = BA - CA (output_BA.csv × V1)", m1, "BAI_raw")

    # (b) bias-corrected BAI from features_MGH_deid.csv via mapping.csv
    fmgh = pd.read_csv(FEATURES_MGH, usecols=["HashID", "BAI"])
    mapping = pd.read_csv(MAPPING, dtype=str)[["FileNameOriginal", "HashID"]]
    m2 = c[["FolderName", "Predicted_Stage"]].merge(
        mapping, left_on="FolderName", right_on="FileNameOriginal", how="left"
    ).merge(fmgh, on="HashID", how="inner")
    report("(b) bias-corrected BAI (features_MGH_deid.csv × V1)", m2, "BAI")

    print(f"\nPaper headline:  total={5144} with BAI;  "
          f"DEM={88} MCI={44} Symp={1075} None={2336}")


if __name__ == "__main__":
    main()
