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

    if not habitat_columns:
        st.error("Format data tidak valid. Tambahkan setidaknya satu kolom habitat.")
        return

    df[habitat_columns] = df[habitat_columns].apply(pd.to_numeric, errors="coerce")
    if df[habitat_columns].isna().any().any():
        st.error("Semua kolom habitat harus berisi angka. Periksa data Anda.")
        return

    df = df.groupby("species", as_index=False)[habitat_columns].sum()

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

    from utils.plotting import build_diversity_chart
    chart = build_diversity_chart(hasil_summary.set_index('habitat').T)
    st.altair_chart(chart, use_container_width=True)

    pi_df = melt_species_habitat(df, habitat_columns)
    st.write("### Tabel nilai p_i ln(p_i) per species dan habitat")
    st.dataframe(pivot_pi_values(pi_df))


def render():
    render_indeks_ekologi_page()
