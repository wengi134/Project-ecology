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


def build_index_chart(index_df: pd.DataFrame, habitat_order: list[str] | None = None) -> alt.Chart:
    x_encoding = alt.X(
        "habitat:N",
        title="Habitat",
        axis=alt.Axis(labelAngle=90),
        sort=alt.SortArray(habitat_order) if habitat_order else None,
    )

    return (
        alt.Chart(index_df)
        .mark_bar()
        .encode(
            x=x_encoding,
            y=alt.Y("value:Q", title="Index value", stack=None),
            color=alt.Color("index:N", title="Indeks"),
            xOffset=alt.XOffset("index:N"),
            tooltip=["habitat", "index", "value"],
        )
        .properties(width=700, height=400)
    )


def build_index_chart_by_index(index_df: pd.DataFrame, habitat_order: list[str] | None = None) -> alt.Chart:
    x_encoding = alt.X(
        "habitat:N",
        title="Habitat",
        axis=alt.Axis(labelAngle=90),
        sort=alt.SortArray(habitat_order) if habitat_order else None,
    )

    return (
        alt.Chart(index_df)
        .mark_bar(fill="#A8D5BA", stroke="#2F8F4B", strokeWidth=1)
        .encode(
            x=x_encoding,
            y=alt.Y("value:Q", title="Index value"),
            tooltip=["habitat", "value"],
        )
        .properties(width=700, height=400)
    )
