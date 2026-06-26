import streamlit as st
import pandas as pd
from utils.diversity import calculate_diversity_metrics, get_analysis_text, melt_species_habitat, pivot_pi_values


def render_indeks_ekologi_page():
    st.title("2. Indeks Ekologi")

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

    # Check if famili column exists, warn if not but continue
    has_famili = "famili" in df.columns
    if not has_famili:
        st.warning("⚠️ Kolom 'famili' tidak ditemukan. Perhitungan indeks ekologi akan dilanjutkan, namun tanpa kategori famili.")

    if not habitat_columns:
        st.error("Format data tidak valid. Tambahkan setidaknya satu kolom habitat.")
        return

    df[habitat_columns] = df[habitat_columns].apply(pd.to_numeric, errors="coerce")
    if df[habitat_columns].isna().any().any():
        st.error("Semua kolom habitat harus berisi angka. Periksa data Anda.")
        return

    df = df.groupby("species", as_index=False).agg(
        {**{col: "sum" for col in habitat_columns}, 
         **({"famili": "first"} if has_famili else {})}
    )

    st.write("### Ringkasan data species")
    st.write(f"Jumlah jenis species: {len(df)}")
    st.write(f"Total individu keseluruhan: {int(df[habitat_columns].sum().sum())}")
    st.write("### Ringkasan per habitat")

    hasil_summary = calculate_diversity_metrics(df, habitat_columns)
    st.write("### Hasil indeks per habitat")
    st.dataframe(hasil_summary)

    st.write("#### Analisis indeks")
    analysis_text = get_analysis_text(hasil_summary.set_index('habitat').T)
    st.markdown("\n".join(analysis_text))

    from utils.plotting import build_index_chart, build_index_chart_by_index

    st.write("### Visualisasi indeks per habitat")
    st.write("Grafik di bawah ini mengelompokkan setiap indeks berdasarkan habitat, sehingga Anda dapat membandingkan nilai H_Shannon, J_Pielou, Dmg_Margalef, dan D_Simpson untuk setiap habitat.")
    index_df = hasil_summary.melt(
        id_vars=["habitat"],
        value_vars=["H_Shannon", "J_Pielou", "Dmg_Margalef", "D_Simpson"],
        var_name="index",
        value_name="value",
    )
    habitat_order = hasil_summary.sort_values(by="H_Shannon", ascending=False)["habitat"].tolist()
    st.altair_chart(build_index_chart(index_df, habitat_order=habitat_order), width='stretch')

    st.write("### Visualisasi per indeks habitat")
    for index_name in ["H_Shannon", "J_Pielou", "Dmg_Margalef", "D_Simpson"]:
        st.write(f"#### {index_name}")
        index_table = hasil_summary[["habitat", index_name]].sort_values(by=index_name, ascending=False).reset_index(drop=True)
        st.dataframe(index_table)

        habitat_order_for_index = index_table["habitat"].tolist()
        index_chart_df = index_table.rename(columns={index_name: "value"})
        st.altair_chart(
            build_index_chart_by_index(index_chart_df, habitat_order=habitat_order_for_index),
            width='stretch',
        )

    pi_df = melt_species_habitat(df, habitat_columns)
    st.write("### Tabel nilai p_i ln(p_i) per species dan habitat")
    st.dataframe(pivot_pi_values(pi_df))


def render():
    render_indeks_ekologi_page()
