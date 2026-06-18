import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from io import StringIO

st.set_page_config(page_title="Indeks Keanekaragaman Hayati", page_icon="🌿")

st.title("Indeks Keanekaragaman Hayati")
st.write(
    "Masukkan data jenis/species dan jumlah pertemuan satwa pada setiap habitat untuk menghitung indeks "
    "keanekaragaman Shannon-Wiener, Simpson, dan Evenness per habitat."
)

with st.expander("Contoh format data"):
    st.write(
        "Gunakan tabel dengan kolom `species` dan satu atau lebih kolom habitat. Contoh:\n\n"
        "| species | habitat_1 | habitat_2 |\n"
        "|---|---|---|\n"
        "| Kupu-kupu | 15 | 10 |\n"
        "| Burung | 42 | 25 |\n"
        "| Semut | 23 | 12 |\n"
        "| Katak | 8 | 5 |"
    )
    st.write(
        "Kolom habitat dapat ditambah sesuai jumlah lokasi pengamatan. Aplikasi akan menghitung indeks untuk setiap habitat."
    )

uploaded_file = st.file_uploader("Unggah file CSV", type=["csv"])

def load_data_from_text(data_text):
    df = pd.read_csv(StringIO(data_text), header=None)
    if df.shape[1] < 2:
        raise ValueError("Minimal harus ada kolom species dan satu kolom habitat.")
    df.columns = ["species"] + [f"habitat_{i}" for i in range(1, df.shape[1])]
    return df

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.write("### Data yang diunggah")
        st.dataframe(df)
    except Exception as e:
        st.error(f"Gagal membaca file CSV: {e}")
        df = None
else:
    st.info("Masukkan data langsung di bawah ini jika tidak ingin mengunggah file CSV.")
    data = st.text_area(
        "Data species (csv format tanpa header):",
        value="Kupu-kupu,15,10\nBurung,42,25\nSemut,23,12",
        height=170,
    )
    if data:
        try:
            df = load_data_from_text(data)
            st.write("### Data yang dimasukkan")
            st.dataframe(df)
        except Exception as e:
            st.error(f"Gagal membaca data: {e}")
            df = None

if 'df' in locals() and df is not None:
    if df.empty:
        st.warning("Data kosong. Silakan masukkan data species.")
    else:
        if "species" not in df.columns:
            st.error("Format data tidak valid. Pastikan kolom 'species' ada.")
        else:
            habitat_columns = [c for c in df.columns if c != "species"]
            if not habitat_columns:
                st.error("Format data tidak valid. Tambahkan setidaknya satu kolom habitat.")
            else:
                df = df.copy()
                df[habitat_columns] = df[habitat_columns].apply(pd.to_numeric, errors="coerce")
                if df[habitat_columns].isna().any().any():
                    st.error("Semua kolom habitat harus berisi angka. Periksa data Anda.")
                else:
                    df = df.groupby("species", as_index=False)[habitat_columns].sum()

                    st.write("### Ringkasan data species")
                    st.write(f"Jumlah jenis species: {len(df)}")
                    st.write(f"Total individu keseluruhan: {int(df[habitat_columns].sum().sum())}")
                    st.write("### Ringkasan per habitat")

                    def hitung_indeks(col):
                        N = col.sum()
                        if N == 0:
                            return pd.Series({
                                'H_Shannon': 0,
                                'J_Pielou': 0,
                                'Dmg_Margalef': 0,
                                'D_Simpson': 0,
                            })

                        col_nonzero = col[col > 0]
                        S = len(col_nonzero)
                        p_i = col_nonzero / N

                        H = -np.sum(p_i * np.log(p_i))
                        J = H / np.log(S) if S > 1 else 0
                        Dmg = (S - 1) / np.log(N) if N > 1 else 0
                        D = np.sum(p_i ** 2)

                        return pd.Series({
                            'H_Shannon': H,
                            'J_Pielou': J,
                            'Dmg_Margalef': Dmg,
                            'D_Simpson': D,
                        })

                    hasil = df[habitat_columns].apply(hitung_indeks, axis=0)
                    hasil.columns = hasil.columns.astype(str)

                    habitat_species_count = (df[habitat_columns] > 0).sum(axis=0)
                    habitat_individu_total = df[habitat_columns].sum(axis=0)
                    hasil_summary = hasil.T.reset_index().rename(columns={'index': 'habitat'})
                    hasil_summary['species_count'] = hasil_summary['habitat'].map(habitat_species_count)
                    hasil_summary['total_individu'] = hasil_summary['habitat'].map(habitat_individu_total)
                    hasil_summary = hasil_summary[
                        ['habitat', 'species_count', 'total_individu', 'H_Shannon', 'J_Pielou', 'Dmg_Margalef', 'D_Simpson']
                    ]

                    st.write("### Hasil indeks per habitat")
                    st.dataframe(hasil_summary)

                    st.write("#### Analisis indeks")
                    analysis_text = []
                    for index_name in ['H_Shannon', 'J_Pielou', 'Dmg_Margalef', 'D_Simpson']:
                        best_col = hasil.loc[index_name].idxmax()
                        worst_col = hasil.loc[index_name].idxmin()
                        analysis_text.append(
                            f"- **{index_name}**: habitat tertinggi `{best_col}` (nilai {hasil.loc[index_name, best_col]:.4f}), "
                            f"habitat terendah `{worst_col}` (nilai {hasil.loc[index_name, worst_col]:.4f})."
                        )
                    st.markdown("\n".join(analysis_text))

                    chart_df = hasil.T.reset_index().rename(columns={'index': 'habitat'}).melt(
                        id_vars=['habitat'],
                        value_vars=['H_Shannon', 'J_Pielou', 'Dmg_Margalef', 'D_Simpson'],
                        var_name='Indeks',
                        value_name='Nilai',
                    )
                    chart_df['label'] = chart_df['Indeks'] + ' / ' + chart_df['habitat']

                    chart = (
                        alt.Chart(chart_df)
                        .mark_bar()
                        .encode(
                            x=alt.X('Nilai:Q', title='Nilai Indeks'),
                            y=alt.Y('label:N', title='Indeks dan Habitat', sort=alt.EncodingSortField(field='Nilai', order='descending')),
                            color=alt.Color('Indeks:N', title='Indeks'),
                            tooltip=['habitat', 'Indeks', 'Nilai'],
                        )
                        .properties(width=700, height=400)
                    )
                    st.altair_chart(chart, use_container_width=True)

                    st.write("### Detail perhitungan")
                    result_df = df.copy()
                    for habitat in habitat_columns:
                        counts = result_df[habitat].astype(float).values
                        total = counts.sum()
                        p = counts / total if total > 0 else np.zeros_like(counts)
                        result_df[f"{habitat}_proporsi"] = p
                        result_df[f"{habitat}_p * ln(p)"] = (
                            -p * np.log(p)
                        ).replace([np.inf, -np.inf], 0)
                        result_df[f"{habitat}_p^2"] = p ** 2
                    st.dataframe(result_df)

                    pi_df = df.melt(
                        id_vars=['species'],
                        value_vars=habitat_columns,
                        var_name='habitat',
                        value_name='count',
                    )
                    pi_df['total_habitat'] = pi_df.groupby('habitat')['count'].transform('sum')
                    pi_df['p_i'] = np.where(pi_df['total_habitat'] > 0, pi_df['count'] / pi_df['total_habitat'], 0)
                    pi_df['p_i_ln_p_i'] = np.where(
                        pi_df['p_i'] > 0,
                        pi_df['p_i'] * np.log(pi_df['p_i']),
                        0,
                    )
                    pi_df[['p_i', 'p_i_ln_p_i']] = pi_df[['p_i', 'p_i_ln_p_i']].round(4)

                    st.write("### Tabel nilai p_i ln(p_i) per species dan habitat")
                    st.dataframe(pi_df[['species', 'habitat', 'count', 'p_i', 'p_i_ln_p_i']])

                    analysis_pi = []
                    for habitat in habitat_columns:
                        total_pi_lnpi = pi_df.loc[pi_df['habitat'] == habitat, 'p_i_ln_p_i'].sum()
                        analysis_pi.append(
                            f"- **{habitat}**: total p_i ln(p_i) = {total_pi_lnpi:.4f} "
                            f"(Shannon-Wiener = {-total_pi_lnpi:.4f})"
                        )

                    st.write("#### Analisis p_i ln(p_i)")
                    st.write(
                        "Nilai total p_i ln(p_i) per habitat digunakan untuk menghitung indeks Shannon-Wiener. "
                        "Semakin negatif nilainya, semakin tinggi keanekaragaman untuk habitat tersebut."
                    )
                    st.markdown("\n".join(analysis_pi))

                    st.success("Perhitungan selesai.")

