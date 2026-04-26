"""Regenerate the 4 figures from Ye et al., JAMA Network Open 2020.

Outputs land under `code/06_verification/figures/`.

Inputs (PHI; staged locally under _box_inspect/):
  output_BA.csv                              raw per-PSG BA, CA
  study_criteria_table_label.xlsx (V1)       paper-era cohort labels
  mapping.csv                                PatientID/FolderName ↔ HashID/BDSPPatientID
  features_MGH_deid.csv                      bias-corrected BAI per PSG (HashID)
  MMSE_list_sans_text.csv, MoCA_list_sans_text.csv   cognitive scores
  comorbidities_deid.csv                     comorbidity flags (from 2023 paper work)
  RPDR_Dem_All.csv                           race/ethnicity for the regression model

Run from repo root:
  python3 code/06_verification/regenerate_figures.py
"""
from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats as ss
import statsmodels.api as sm

warnings.filterwarnings("ignore")

ROOT = Path("/Users/mwestover/GithubRepos/Elissa-bai")
BA_OUT = ROOT / "_box_inspect/csvs/output_BA.csv"
COHORT = ROOT / "_box_inspect/dementia_detection_other/medical_data/study_criteria_table_label.xlsx"
MAPPING = ROOT / "_box_inspect/bdsp_collab_essentials/mapping.csv"
FEATURES = ROOT / "_s3_stage/sleep-dementia-detection/features_MGH_deid.csv"
COMORB = ROOT / "_s3_stage/sleep-dementia-detection/comorbidities_deid.csv"
MMSE = ROOT / "_box_inspect/csvs/MMSE_list_sans_text.csv"
MOCA = ROOT / "_box_inspect/csvs/MoCA_list_sans_text.csv"
DEMOG_RPDR = ROOT / "_box_inspect/dementia_detection_other/medical_data/RPDR_Dem_All.csv"

OUT = ROOT / "bai-dementia/code/06_verification/figures"
OUT.mkdir(parents=True, exist_ok=True)

GROUP_ORDER = ["Healthy", "No Dementia", "Symptomatic", "MCI", "Dementia"]
GROUP_COLOR = {"Healthy": "#3a4f8a",
               "No Dementia": "#7eaad6",
               "Symptomatic": "#d4d4d4",
               "MCI": "#e8a888",
               "Dementia": "#c64c3a"}


def build_master_df():
    """Join BAI + cohort labels + cognitive scores + demographics."""
    print("Loading…")
    ba = pd.read_csv(BA_OUT, sep="\t")
    ba.columns = [c.strip() for c in ba.columns]
    ba["BAI_raw"] = ba["BA (yr)"] - ba["CA (yr)"]

    c = pd.read_excel(COHORT)
    mapping = pd.read_csv(MAPPING, dtype=str)

    # Per-PSG bias-corrected BAI from features_MGH_deid (HashID).
    # Drop Age to avoid collision with cohort.Age — we use cohort.Age throughout.
    f = pd.read_csv(FEATURES, usecols=["HashID", "BAI"], low_memory=False)

    # Master join: cohort × output_BA (raw) × mapping (HashID) × features (corrected BAI)
    df = c[["FolderName", "PatientID", "Predicted_Stage", "Age", "Sex"]].copy()
    df = df.merge(ba[["SubjectID", "BAI_raw", "BA (yr)", "CA (yr)", "NumMissingStage"]],
                  left_on="FolderName", right_on="SubjectID", how="left")
    df = df.merge(mapping[["FileNameOriginal", "HashID", "BDSPPatientID"]],
                  left_on="FolderName", right_on="FileNameOriginal", how="left")
    df = df.merge(f.rename(columns={"BAI": "BAI_corrected"}), on="HashID", how="left")

    # Add MMSE / MoCA — keep latest non-NaN score per patient
    mmse = pd.read_csv(MMSE).dropna(subset=["MMSEScore"])
    mmse_max = mmse.groupby("PatientID", as_index=False)["MMSEScore"].max()
    moca = pd.read_csv(MOCA).dropna(subset=["MoCAScore"])
    moca_max = moca.groupby("PatientID", as_index=False)["MoCAScore"].max()
    df = df.merge(mmse_max, on="PatientID", how="left").merge(moca_max, on="PatientID", how="left")

    print(f"master df: {df.shape}")
    return df


# ---------------------------------------------------------------------------
# Figure 1
# ---------------------------------------------------------------------------

def fig1(df):
    """A: BAI by group (median + IQR upper whisker).
       B: BA vs CA scatter, Healthy vs Dementia, with identity line."""
    print("\n[Figure 1] BAI by group + BA vs CA")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

    # Panel A — bar plot per group with median + IQR-upper whisker.
    # "Healthy" = the BAI training cohort (uses train CSV BA-CA pairs).
    train = pd.read_csv(ROOT / "_dropbox_inspect/brainAge_model/MGH_Sleep_CA_BAs_tr.csv")
    train["BAI"] = train["dA"]  # dA = BA - CA
    healthy_bai = train["BAI"]

    rows = []
    for g in ["Healthy", "No Dementia", "Symptomatic", "MCI", "Dementia"]:
        if g == "Healthy":
            bai = healthy_bai
        else:
            sub = df[df["Predicted_Stage"] == g]
            bai = sub["BAI_corrected"].dropna()
        rows.append({
            "group": g, "n": len(bai),
            "median": bai.median(),
            "q25": bai.quantile(.25),
            "q75": bai.quantile(.75),
        })
    s = pd.DataFrame(rows)
    print(s.to_string(index=False))

    ax = axes[0]
    bars = ax.bar(range(len(s)), s["median"], color=[GROUP_COLOR[g] for g in s["group"]],
                  edgecolor="black", linewidth=0.6)
    # Upper IQR whisker only
    yerr_upper = (s["q75"] - s["median"]).clip(lower=0)
    ax.errorbar(range(len(s)), s["median"], yerr=[np.zeros(len(s)), yerr_upper],
                fmt="none", ecolor="black", elinewidth=0.8, capsize=5)
    # Significance brackets — Mann-Whitney vs Healthy is too aggressive; use vs No Dementia
    for i, g in enumerate(s["group"]):
        if g in ("Symptomatic", "MCI", "Dementia"):
            sub = df.loc[df["Predicted_Stage"] == g, "BAI_corrected"].dropna()
            ref = df.loc[df["Predicted_Stage"] == "No Dementia", "BAI_corrected"].dropna()
            if len(sub) and len(ref):
                _, p = ss.mannwhitneyu(sub, ref, alternative="two-sided")
                top = float(s.loc[s["group"] == g, "q75"].iloc[0]) + 0.5
                ax.text(i, top, "p<0.001" if p < 0.001 else f"p={p:.3f}",
                        ha="center", va="bottom", fontsize=8)
    ax.set_xticks(range(len(s)))
    ax.set_xticklabels(s["group"], rotation=20, ha="right")
    ax.set_ylabel("Brain Age Index (BAI)")
    ax.set_ylim(-1, max(7, s["q75"].max() + 1))
    ax.axhline(0, color="gray", lw=0.5)
    ax.set_title("A. BAI by group", loc="left", fontweight="bold")
    ax.grid(True, axis="y", alpha=0.2)

    # Panel B — BA vs CA scatter
    ax = axes[1]
    healthy = df[(df["Predicted_Stage"] == "No Dementia") & df["BA (yr)"].notna()]
    dem = df[(df["Predicted_Stage"] == "Dementia") & df["BA (yr)"].notna()]
    ax.scatter(healthy["CA (yr)"], healthy["BA (yr)"], s=14, alpha=0.25,
               color=GROUP_COLOR["No Dementia"], label=f"Non-Dementia (n={len(healthy):,})")
    ax.scatter(dem["CA (yr)"], dem["BA (yr)"], s=22, alpha=0.85,
               color=GROUP_COLOR["Dementia"], edgecolor="white", lw=0.4,
               label=f"Dementia (n={len(dem):,})")
    lo, hi = 30, 100
    ax.plot([lo, hi], [lo, hi], "k--", lw=1)
    ax.set_xlim(45, 90); ax.set_ylim(20, 120)
    ax.set_xlabel("Chronological Age (yrs)"); ax.set_ylabel("Brain Age (yrs)")
    ax.set_title("B. Brain Age vs Chronological Age", loc="left", fontweight="bold")
    ax.legend(loc="upper left", frameon=False)
    ax.grid(True, alpha=0.2)

    fig.tight_layout()
    fig.savefig(OUT / "figure1_bai_by_group.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    s.to_csv(OUT / "figure1_summary.csv", index=False)
    print(f"  wrote {OUT / 'figure1_bai_by_group.png'}")


# ---------------------------------------------------------------------------
# Figure 2 — BAI vs MoCA / MMSE
# ---------------------------------------------------------------------------

def fig2(df):
    print("\n[Figure 2] BAI vs MoCA / MMSE")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, score, title in [(axes[0], "MoCAScore", "A. BAI vs MoCA"),
                              (axes[1], "MMSEScore", "B. BAI vs MMSE")]:
        sub = df[(df[score].notna()) & (df["BAI_corrected"].notna())]
        if len(sub) < 5:
            ax.text(.5, .5, "no overlap", ha="center", transform=ax.transAxes); continue
        x = sub[score].astype(float).to_numpy()
        y = sub["BAI_corrected"].astype(float).to_numpy()
        ax.scatter(x, y, s=12, alpha=0.4, color="#444")
        # Regression
        slope, intercept, r, p, _ = ss.linregress(x, y)
        xs = np.linspace(0, 30, 100)
        ax.plot(xs, slope * xs + intercept, "k-", lw=1.5)
        ax.text(0.05, 0.05, f"R = {r:.4f}, p={'<0.01' if p < 0.01 else f'={p:.3f}'}",
                transform=ax.transAxes, fontsize=10, va="bottom")
        ax.set_xlabel(score.replace("Score", ""))
        ax.set_ylabel("BAI")
        ax.set_xlim(0, 30); ax.set_ylim(-30, 40)
        ax.set_title(title, loc="left", fontweight="bold")
        ax.grid(True, alpha=0.2)
    fig.tight_layout()
    fig.savefig(OUT / "figure2_bai_vs_cognitive.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {OUT / 'figure2_bai_vs_cognitive.png'}")


# ---------------------------------------------------------------------------
# Figure 3 — multivariable regression coefficients (forest plot)
# ---------------------------------------------------------------------------

def fig3(df):
    print("\n[Figure 3] Multivariable BAI ~ Dementia + covariates")
    # Add comorbidities (BDSPPatientID-keyed). Both sides must be str for the join.
    com = pd.read_csv(COMORB, dtype=str)
    df = df.copy()
    df["BDSPPatientID"] = df["BDSPPatientID"].astype(str).str.replace(r"\.0$", "", regex=True)
    com["BDSPPatientID"] = com["BDSPPatientID"].astype(str).str.replace(r"\.0$", "", regex=True)
    df = df.merge(com, on="BDSPPatientID", how="left", suffixes=("", "_g"))

    # Add race/ethnicity from RPDR_Dem
    try:
        rpdr_dem = pd.read_csv(DEMOG_RPDR, dtype=str, usecols=["EMPI", "Race"])
        # Need to chain EMPI ↔ PatientID via cohort table
        c = pd.read_excel(COHORT, dtype=str)
        c["PatientID"] = c["PatientID"].astype(str)
        c["EMPI"] = c["EMPI"].astype(str).str.replace(r"\.0$", "", regex=True)
        rpdr_dem["EMPI"] = rpdr_dem["EMPI"].astype(str)
        c = c[["PatientID", "EMPI"]].drop_duplicates().merge(rpdr_dem, on="EMPI", how="left")
        df = df.merge(c[["PatientID", "Race"]].drop_duplicates("PatientID"),
                      on="PatientID", how="left")
        df["RaceWhite"] = df["Race"].astype(str).str.contains("White-WHITE", na=False).astype(int)
        df["RaceBlack"] = df["Race"].astype(str).str.contains("Black", na=False).astype(int)
        df["RaceAsian"] = df["Race"].astype(str).str.contains("Asian", na=False).astype(int)
    except Exception as e:
        print(f"  WARN: race not loaded: {e}")
        df["RaceWhite"] = 0; df["RaceBlack"] = 0; df["RaceAsian"] = 0

    # Build covariate matrix
    df = df[df["BAI_corrected"].notna() & df["Predicted_Stage"].isin(GROUP_ORDER[1:])].copy()
    df["DementiaBin"] = (df["Predicted_Stage"] == "Dementia").astype(int)
    df["SexMale"] = (df["Sex"].astype(str).str.lower().str[0] == "m").astype(int)

    bool_cols = ["Cardiovascular_disease", "Obstructive_sleep_apnea",
                 "Mood_disorder", "Obesity", "Insomnia", "Diabetes",
                 "Anxiety_disorder", "Psychotic_disorder", "Alcoholism"]
    for c in bool_cols:
        if c in df.columns:
            df[c] = df[c].astype(str).map({"True": 1, "False": 0, "1": 1, "0": 0}).fillna(0).astype(int)
        else:
            df[c] = 0

    # standardize Age
    df["Age_z"] = (df["Age"].astype(float) - df["Age"].astype(float).mean()) / df["Age"].astype(float).std()

    cov_order = ["DementiaBin", "SexMale", "RaceBlack", "Psychotic_disorder",
                 "Cardiovascular_disease", "Diabetes",
                 "Anxiety_disorder", "RaceWhite",
                 "Obesity", "Mood_disorder", "Insomnia", "Alcoholism",
                 "Age_z", "RaceAsian"]
    cov_labels = ["Dementia", "Sex-Male", "Race-Black", "Psychotic Disorder",
                  "Cardiovascular Disease", "Diabetes", "Anxiety Disorder", "Race-White",
                  "Obesity", "Mood Disorder", "Insomnia", "Alcoholism", "Age", "Race-Asian"]
    X = sm.add_constant(df[cov_order].astype(float).fillna(0))
    y = df["BAI_corrected"].astype(float)
    res = sm.OLS(y, X).fit()
    print(res.summary().tables[1])

    # Extract coefficients (drop const)
    coefs = res.params.drop("const")
    ci_lo = res.conf_int().iloc[1:, 0]
    ci_hi = res.conf_int().iloc[1:, 1]
    pvals = res.pvalues.drop("const")

    coef_df = pd.DataFrame({
        "covariate": cov_labels, "coef": coefs.values,
        "ci_lo": ci_lo.values, "ci_hi": ci_hi.values, "p": pvals.values,
    })
    # Order by coef descending
    coef_df = coef_df.sort_values("coef", ascending=False).reset_index(drop=True)
    coef_df.to_csv(OUT / "figure3_coefficients.csv", index=False)

    fig, ax = plt.subplots(figsize=(11, 6))
    y_pos = np.arange(len(coef_df))
    sig = coef_df["p"] < 0.05
    for i, r in coef_df.iterrows():
        ax.plot([r["ci_lo"], r["ci_hi"]], [i, i], color="black", lw=1.2)
        marker = "o" if r["p"] < 0.05 else "o"
        ax.plot(r["coef"], i, marker=marker,
                markerfacecolor="black" if r["p"] < 0.05 else "white",
                markeredgecolor="black", markersize=8)
        ax.text(r["coef"], i + 0.3, f"{r['coef']:.3f}", fontsize=7, ha="center")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(coef_df["covariate"])
    ax.invert_yaxis()
    ax.axvline(0, color="red", lw=0.7, ls="--")
    ax.set_xlabel("Coefficient (β)")
    ax.set_xlim(-10, 10)
    # Legend
    ax.plot([], [], "ko", label="Significant p ≤ 0.05")
    ax.plot([], [], "wo", markeredgecolor="black", label="Not Significant p > 0.05")
    ax.legend(loc="upper right", frameon=False)
    ax.set_title("Multivariable regression: BAI ~ Dementia + covariates")
    ax.grid(True, axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(OUT / "figure3_regression_forest.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {OUT / 'figure3_regression_forest.png'}")


# ---------------------------------------------------------------------------
# Figure 4 — EEG features by stage (DEM vs No Dementia)
# Only "panel A" (OR plot) is reproduced from sklearn LR; B and C require
# loading the full feature matrix and ranking by mean difference.
# ---------------------------------------------------------------------------

def fig4(df):
    print("\n[Figure 4] EEG feature ORs by stage (DEM vs No Dementia)")
    # Use the deidentified full feature matrix from the 2023 paper's S3 release
    full = pd.read_csv(ROOT / "_s3_stage/sleep-dementia-detection/features_full_deid.csv",
                       low_memory=False)
    print(f"  features_full: {full.shape}")
    df = df[df["HashID"].notna()].copy()
    full["HashID"] = full["HashID"].astype(str)
    df["HashID"] = df["HashID"].astype(str)
    # Drop overlapping cols from features_full that we already have in df
    overlap = [c for c in ("BDSPPatientID", "DOVshifted", "ShiftedDays", "FileNameNew",
                            "Sex", "Age") if c in full.columns]
    full_thin = full.drop(columns=overlap, errors="ignore")
    m = df.merge(full_thin, on="HashID", how="inner")
    m = m[m["Predicted_Stage"].isin(["Dementia", "No Dementia"])].copy()
    print(f"  joined for fig4: {len(m)}")
    m["DEM"] = (m["Predicted_Stage"] == "Dementia").astype(int)

    # Identify per-stage features by column name
    feature_cols = [c for c in full_thin.columns if c not in ("HashID",)]
    stage_pat = {"Wake": ["_W_", "_W$", "Wake"],
                 "N1": ["N1_", "_N1_"],
                 "N2": ["N2_", "_N2_"],
                 "N3": ["N3_", "_N3_"],
                 "REM": ["_R_", "_R$", "REM"]}

    # For panel A, compute univariate OR (per-feature LR coefficient with binary DEM outcome)
    from sklearn.linear_model import LogisticRegression
    rows = []
    for fc in feature_cols:
        v = pd.to_numeric(m[fc], errors="coerce")
        ok = v.notna()
        if ok.sum() < 100:
            continue
        v_z = (v - v.mean()) / max(v.std(), 1e-9)
        try:
            lr = LogisticRegression(max_iter=200).fit(v_z[ok].to_numpy().reshape(-1, 1),
                                                      m.loc[ok, "DEM"].to_numpy())
            rows.append({"feature": fc, "OR": float(np.exp(lr.coef_[0][0]))})
        except Exception:
            continue
    or_df = pd.DataFrame(rows)
    or_df.to_csv(OUT / "figure4_feature_ORs.csv", index=False)

    # Plot panel A — stage × band stacked bars (simplified)
    def stage_of(name):
        n = name.lower()
        if "_w_" in n or "_w$" in n.lower() or n.endswith("_w"): return "Wake"
        for s in ("n1", "n2", "n3"):
            if f"_{s}_" in n or n.endswith(f"_{s}"): return s.upper()
        if "_r_" in n or n.endswith("_r") or "rem" in n: return "REM"
        return "?"

    def band_of(name):
        n = name.lower()
        if "alpha" in n: return "Alpha (8-12 Hz)"
        if "theta" in n: return "Theta (4-8 Hz)"
        if "delta" in n: return "Delta (0.5-4 Hz)"
        if "sigma" in n or "spindle" in n: return "Sigma (11-15 Hz)"
        return "Waveform"

    or_df["stage"] = or_df["feature"].apply(stage_of)
    or_df["band"] = or_df["feature"].apply(band_of)
    or_df = or_df[or_df["stage"] != "?"]
    band_color = {"Sigma (11-15 Hz)": "#3eb55a", "Alpha (8-12 Hz)": "#d92a2a",
                  "Theta (4-8 Hz)": "#e6c33b", "Delta (0.5-4 Hz)": "#3a7eb8",
                  "Waveform": "#888"}

    stages = ["Wake", "N1", "N2", "N3", "REM"]
    fig, axes = plt.subplots(len(stages), 1, figsize=(8, 9), sharex=True)
    for ax, st in zip(axes, stages):
        sub = or_df[or_df["stage"] == st].copy()
        if len(sub) == 0:
            ax.set_ylabel(st, fontweight="bold"); continue
        sub = sub.sort_values("OR")
        # Stack horizontal bars colored by band
        for band, col in band_color.items():
            ss_ = sub[sub["band"] == band]
            ax.barh(np.arange(len(sub)), np.where(sub["band"] == band, sub["OR"] - 1, 0),
                    left=1, color=col, label=band if st == "Wake" else None,
                    edgecolor="none")
        ax.axvline(1, color="black", lw=0.7)
        ax.axvline(0.8, color="black", lw=0.5, ls="--")
        ax.axvline(1.2, color="black", lw=0.5, ls="--")
        ax.set_yticks([]); ax.set_xlim(0.0, 2.0)
        ax.set_ylabel(f"{st}\nFeatures", fontsize=10, fontweight="bold", rotation=0,
                      ha="right", va="center")
        if st == "Wake":
            ax.legend(loc="upper right", fontsize=7, frameon=False)
    axes[-1].set_xlabel("Odds Ratio (per-feature LR; <1 = lower in DEM, >1 = higher in DEM)")
    fig.suptitle("Figure 4 — EEG feature univariate ORs (Dementia vs No Dementia)", y=1.0)
    fig.tight_layout()
    fig.savefig(OUT / "figure4_eeg_feature_ORs.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {OUT / 'figure4_eeg_feature_ORs.png'}")


# ---------------------------------------------------------------------------

def main():
    df = build_master_df()
    fig1(df)
    fig2(df)
    fig3(df)
    fig4(df)
    print("\nAll outputs in", OUT)
    for p in sorted(OUT.iterdir()):
        print(f"  {p.name}  ({p.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
