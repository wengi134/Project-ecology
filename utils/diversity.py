import numpy as np
import pandas as pd


def hitung_indeks(col: pd.Series) -> pd.Series:
    N = col.sum()
    if N == 0:
        return pd.Series({
            "H_Shannon": 0,
            "J_Pielou": 0,
            "Dmg_Margalef": 0,
            "D_Simpson": 0,
        })

    col_nonzero = col[col > 0]
    S = len(col_nonzero)
    p_i = col_nonzero / N

    H = -np.sum(p_i * np.log(p_i))
    J = H / np.log(S) if S > 1 else 0
    Dmg = (S - 1) / np.log(N) if N > 1 else 0
    D = np.sum(p_i ** 2)

    return pd.Series({
        "H_Shannon": H,
        "J_Pielou": J,
        "Dmg_Margalef": Dmg,
        "D_Simpson": D,
    })


def calculate_diversity_metrics(df: pd.DataFrame, habitat_columns: list[str]) -> pd.DataFrame:
    hasil = df[habitat_columns].apply(hitung_indeks, axis=0)
    hasil.columns = hasil.columns.astype(str)

    habitat_species_count = (df[habitat_columns] > 0).sum(axis=0)
    habitat_individu_total = df[habitat_columns].sum(axis=0)

    hasil_summary = hasil.T.reset_index().rename(columns={"index": "habitat"})
    hasil_summary["species_count"] = hasil_summary["habitat"].map(habitat_species_count)
    hasil_summary["total_individu"] = hasil_summary["habitat"].map(habitat_individu_total)
    return hasil_summary[["habitat", "species_count", "total_individu", "H_Shannon", "J_Pielou", "Dmg_Margalef", "D_Simpson"]]


def get_analysis_text(hasil: pd.DataFrame) -> list[str]:
    analysis_text = []
    for index_name in ["H_Shannon", "J_Pielou", "Dmg_Margalef", "D_Simpson"]:
        best_col = hasil.loc[index_name].idxmax()
        worst_col = hasil.loc[index_name].idxmin()
        analysis_text.append(
            f"- **{index_name}**: habitat tertinggi `{best_col}` (nilai {hasil.loc[index_name, best_col]:.4f}), "
            f"habitat terendah `{worst_col}` (nilai {hasil.loc[index_name, worst_col]:.4f})."
        )
    return analysis_text


def melt_species_habitat(df: pd.DataFrame, habitat_columns: list[str]) -> pd.DataFrame:
    pi_df = df.melt(
        id_vars=["species"],
        value_vars=habitat_columns,
        var_name="habitat",
        value_name="count",
    )
    pi_df["total_habitat"] = pi_df.groupby("habitat")["count"].transform("sum")
    pi_df["p_i"] = np.where(pi_df["total_habitat"] > 0, pi_df["count"] / pi_df["total_habitat"], 0)
    pi_df["p_i_ln_p_i"] = np.where(
        pi_df["p_i"] > 0,
        pi_df["p_i"] * np.log(pi_df["p_i"]),
        0,
    )
    pi_df[["p_i", "p_i_ln_p_i"]] = pi_df[["p_i", "p_i_ln_p_i"]].round(4)
    return pi_df


def pivot_pi_values(pi_df: pd.DataFrame) -> pd.DataFrame:
    pi_pivot = pi_df.pivot_table(
        index="species",
        columns="habitat",
        values="p_i_ln_p_i",
        aggfunc="first"
    ).reset_index()
    pi_pivot.insert(0, "No.", range(1, len(pi_pivot) + 1))
    return pi_pivot
