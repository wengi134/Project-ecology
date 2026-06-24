import streamlit as st
import pandas as pd
from utils.io import dataframe_to_csv_bytes


def render_export_hasil_page():
    st.title("4. Export Hasil")

    if st.session_state.get('df') is None or not st.session_state.get('habitat_columns'):
        st.info("Silakan masukkan atau ungggah data terlebih dahulu di halaman Input Data.")
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

    if st.button("Unduh data CSV hasil input"):
        csv_bytes = dataframe_to_csv_bytes(df)
        st.download_button(
            label="Unduh CSV",
            data=csv_bytes,
            file_name="ecology_input_data.csv",
            mime="text/csv",
        )

    st.write("### Pratinjau data input")
    st.dataframe(df)


def render():
    render_export_hasil_page()
