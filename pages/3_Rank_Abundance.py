import streamlit as st
import pandas as pd
import altair as alt
from utils.diversity import calculate_diversity_metrics
from utils.plotting import build_rank_abundance_chart, build_index_chart_by_index


def render_rank_abundance_page():
    st.title("3. Rank Abundance")

    if st.session_state.get('df') is None or not st.session_state.get('habitat_columns'):
        st.info("Silakan masukkan atau unggah data terlebih dahulu di halaman Input Data.")
        return

    df = st.session_state.df.copy()
    habitat_columns = st.session_state.habitat_columns

    if df.empty:
        st.warning("Data kosong. Silakan masukkan data species.")
        return

    if "species" not in df.columns:
        st.error("Format data tidak valid. Pastikan kolom 'species' ada.")
        return

    df[habitat_columns] = df[habitat_columns].apply(pd.to_numeric, errors="coerce")
    if df[habitat_columns].isna().any().any():
        st.error("Semua kolom habitat harus berisi angka. Periksa data Anda.")
        return

    df = df.groupby("species", as_index=False)[habitat_columns].sum()

    # membuat chart untuk setiap habitat berdasarkan rank abundance
    st.write("### Habitat berdasarkan kekayaan species dan total populasi")
    habitat_summary = pd.DataFrame({
        "habitat": habitat_columns,
        "species_richness": (df[habitat_columns] > 0).sum(axis=0).values,
        "total_population": df[habitat_columns].sum(axis=0).values,
    })

    # hitung indeks Shannon per habitat dan gabungkan
    hasil_summary = calculate_diversity_metrics(df, habitat_columns)
    shannon_map = dict(zip(hasil_summary["habitat"], hasil_summary["H_Shannon"]))
    habitat_summary["H_Shannon"] = habitat_summary["habitat"].map(shannon_map)

    # urutkan descending berdasarkan species_richness lalu total_population
    habitat_summary = habitat_summary.sort_values(
        ["species_richness", "total_population"], ascending=[False, False]
    ).reset_index(drop=True)
    habitat_summary.insert(0, "rank", habitat_summary.index + 1)
    st.dataframe(habitat_summary)

    st.write("### Diagram batang habitat berdasarkan kekayaan species dan total populasi (urut descending species_richness)")
    # siapkan data untuk chart: tampilkan species_richness dan total_population berdampingan per habitat
    chart_df = habitat_summary.melt(
        id_vars=["habitat", "rank"],
        value_vars=["species_richness", "total_population"],
        var_name="metric",
        value_name="value",
    )
    # ordering descending by species_richness
    order = habitat_summary["habitat"].tolist()

    # color mapping: blue for species_richness, soft blue for total_population
    color_scale = alt.Scale(domain=["species_richness", "total_population"], range=["#1f77b4", "#9ecae1"])

    chart = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X("habitat:N", title="Habitat", sort=order),
            y=alt.Y("value:Q", title="Nilai"),
            color=alt.Color("metric:N", scale=color_scale, title="Metrik"),
            xOffset="metric:N",
            tooltip=["habitat", "metric", "value"],
        )
        .properties(width=900, height=420)
    )
    st.altair_chart(chart, use_container_width=True)

    st.write("### Rank Abundance per habitat")
    for habitat in habitat_columns:
        st.write(f"#### {habitat}")
        rank_df = (
            df[["species", habitat]]
            .sort_values(by=habitat, ascending=False)
            .reset_index(drop=True)
        )
        rank_df.index += 1
        rank_df.insert(0, "Rank", rank_df.index)
        st.dataframe(rank_df)
        st.altair_chart(build_rank_abundance_chart(rank_df, habitat), use_container_width=True)

    st.write("### Nilai indeks per habitat")
    hasil_summary = calculate_diversity_metrics(df, habitat_columns)
    index_long = hasil_summary.melt(
        id_vars=["habitat"],
        value_vars=["H_Shannon", "J_Pielou", "Dmg_Margalef", "D_Simpson"],
        var_name="index",
        value_name="value",
    ).sort_values(["habitat", "index"])

    st.dataframe(index_long)

    st.write("### Diagram batang nilai indeks per habitat")
    for index_name in ["H_Shannon", "J_Pielou", "Dmg_Margalef", "D_Simpson"]:
        st.write(f"#### {index_name}")
        subset = index_long[index_long["index"] == index_name]
        st.altair_chart(build_index_chart_by_index(subset), use_container_width=True)


def render():
    render_rank_abundance_page()
