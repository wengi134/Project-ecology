import altair as alt
import pandas as pd


def build_diversity_chart(hasil: pd.DataFrame) -> alt.Chart:
    chart_df = hasil.T.reset_index().rename(columns={"index": "habitat"}).melt(
        id_vars=["habitat"],
        value_vars=["H_Shannon", "J_Pielou", "Dmg_Margalef", "D_Simpson"],
        var_name="Indeks",
        value_name="Nilai",
    )
    chart_df["label"] = chart_df["Indeks"] + " / " + chart_df["habitat"]

    return (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X("label:N", title="Indeks dan Habitat"),
            y=alt.Y("Nilai:Q", title="Nilai Indeks"),
            color=alt.Color("Indeks:N", title="Indeks"),
            tooltip=["habitat", "Indeks", "Nilai"],
        )
        .properties(width=900, height=400)
    )


def build_rank_abundance_chart(rank_df: pd.DataFrame, habitat: str) -> alt.Chart:
    return (
        alt.Chart(rank_df)
        .mark_bar()
        .encode(
            x=alt.X("Rank:O", title="Rank"),
            y=alt.Y(f"{habitat}:Q", title="Count"),
            color=alt.Color(f"{habitat}:Q", scale=alt.Scale(scheme="blues")),
            tooltip=["Rank", "species", habitat],
        )
        .properties(width=700, height=400)
    )


def build_index_chart(index_df: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(index_df)
        .mark_bar()
        .encode(
            x=alt.X("habitat:N", title="Habitat"),
            y=alt.Y("value:Q", title="Nilai"),
            color=alt.Color("index:N", title="Indeks"),
            column=alt.Column("index:N", title="Indeks", header=alt.Header(labelAngle=0, labelOrient="bottom")),
            tooltip=["habitat", "index", "value"],
        )
        .properties(width=200, height=350)
    )


def build_index_chart_by_index(index_df: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(index_df)
        .mark_bar()
        .encode(
            x=alt.X("habitat:N", title="Habitat"),
            y=alt.Y("value:Q", title="Nilai"),
            color=alt.Color("habitat:N", title="Habitat"),
            tooltip=["habitat", "value"],
        )
        .properties(width=700, height=400)
    )
