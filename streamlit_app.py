import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from io import StringIO

# Done — duplicate-blocking added
# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'habitat_columns' not in st.session_state:
    st.session_state.habitat_columns = []

st.set_page_config(page_title="BIODIVERSITY INDEX CALCULATOR", page_icon="🌿")

st.title("BIODIVERSITY INDEX IN NUTSHELL")
st.subheader("your biodiversity index calculator buddy ^,^")
"\n"
st.write(
    "Masukkan data jenis/species dan jumlah pertemuan satwa pada setiap habitat untuk menghitung indeks "
    "keanekaragaman Shannon-Wiener, Simpson, Pielou dan Evenness per habitat."
)

with st.expander("Contoh format data"):
    st.write(
        "Gunakan tabel dengan kolom `Species/Jenis` dan satu atau lebih kolom habitat dengan nama sesuai lokasi lapangan:\n\n"
        "| Species/Jenis | Sawah | Hutan Primer | Mangrove |\n"
        "|---|---|---|---|\n"
        "| Kupu-kupu | 15 | 10 | 8 |\n"
        "| Burung | 42 | 25 | 18 |\n"
        "| Semut | 23 | 12 | 15 |\n"
        "| Katak | 8 | 5 | 3 |\n"
        "| Kuskus | 5 | 7 | 2 |\n"
        "| ... (tambah sesuai jumlah jenis satwa) | ... | ... | ... |"
    )
    st.write(
        "**Baca dong!\n**\n\n"
        "✓ Nama kolom habitat dapat disesuaikan langsung dengan nama lokasi di lapangan\n\n"
        "✓ Kolom pertama pada upload akan otomatis diperlakukan sebagai `Species/Jenis`, apapun judul kolomnya\n\n"
        "✓ Jumlah kolom habitat dapat ditambah sesuai jumlah lokasi pengamatan\n\n"
        "✓ Aplikasi akan menghitung indeks untuk setiap habitat\n\n"
        "✓ Nama habitat akan otomatis terdeteksi dari file CSV"
    )

def load_data_from_text(data_text):
    df = pd.read_csv(StringIO(data_text), header=None)
    if df.shape[1] < 2:
        raise ValueError("Minimal harus ada kolom species dan satu kolom habitat.")
    df.columns = ["species"] + [f"habitat_{i}" for i in range(1, df.shape[1])]
    return df


def read_csv_flexible(source):
    """Read CSV from a file-like object, bytes, or URL and try to infer delimiter.

    Returns a DataFrame with robust handling for common delimiters and uploaded
    Streamlit files. Raises the underlying pandas error if all attempts fail.
    """
    try:
        # handle file-like objects (Streamlit UploadedFile)
        if hasattr(source, 'read'):
            source.seek(0)
            raw = source.read()
            text = raw.decode('utf-8') if isinstance(raw, (bytes, bytearray)) else raw
            return pd.read_csv(StringIO(text), sep=None, engine='python')

        # otherwise assume source is a path or URL
        return pd.read_csv(source, sep=None, engine='python')
    except Exception:
        # fallback: try common separators
        seps = [',', ';', '\t', '|']
        for sep in seps:
            try:
                if hasattr(source, 'read'):
                    source.seek(0)
                    raw = source.read()
                    text = raw.decode('utf-8') if isinstance(raw, (bytes, bytearray)) else raw
                    df = pd.read_csv(StringIO(text), sep=sep)
                else:
                    df = pd.read_csv(source, sep=sep)
                if df.shape[1] >= 2:
                    return df
            except Exception:
                continue
        # re-raise a helpful error
        raise ValueError("Gagal membaca CSV. Pastikan file CSV memiliki minimal dua kolom dan delimiter standar (comma/semicolon/tab).")


def get_species_column(df):
    for col in df.columns:
        if isinstance(col, str) and col.strip().lower() in {'species', 'species/jenis', 'jenis'}:
            return col
    return None


def find_duplicate_species(df):
    """Return a list of species names that appear more than once (case-insensitive, stripped)."""
    species_col = get_species_column(df)
    if species_col is None:
        return []
    s = df[species_col].astype(str).str.strip()
    norm = s.str.lower()
    dup_mask = norm.duplicated(keep=False)
    if not dup_mask.any():
        return []
    dup_vals = norm[dup_mask].unique().tolist()
    original_names = []
    for v in dup_vals:
        orig = s[norm == v].iloc[0]
        original_names.append(orig)
    return original_names


def normalize_uploaded_dataframe(df):
    if df.shape[1] < 2:
        raise ValueError("Minimal harus ada kolom species dan satu kolom habitat.")
    cols = list(df.columns)
    if cols[0].lower() != "species":
        cols[0] = "species"
        df.columns = cols
    return df


def clean_dataframe(df):
    """Clean dataframe by stripping column names and dropping empty/unnamed columns."""
    # normalize column names
    new_cols = []
    for c in df.columns:
        if isinstance(c, str):
            nc = c.strip()
        else:
            nc = c
        new_cols.append(nc)
    df.columns = new_cols

    # drop columns with names like 'Unnamed: x' or empty string
    drop_cols = [c for c in df.columns if (isinstance(c, str) and (c == '' or c.lower().startswith('unnamed')))]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    # drop columns that are entirely NaN
    df = df.dropna(axis=1, how='all')

    return df


def merge_duplicate_species(df):
    """Merge duplicate species rows by case-insensitive name, summing numeric counts and preserving the first original species name.

    This function detects which column is the species column (using `get_species_column`) so
    it works with different header names before normalization.
    """
    df2 = df.copy()
    species_col = get_species_column(df2)
    if species_col is None:
        return df2
    # create normalized key
    df2['__species_norm'] = df2[species_col].astype(str).str.strip().str.lower()
    other_cols = [c for c in df2.columns if c != species_col and c != '__species_norm']
    if not other_cols:
        df2 = df2.drop(columns='__species_norm')
        # rename species col to standardized name
        df2 = df2.rename(columns={species_col: 'species'})
        return df2
    counts = df2[other_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
    counts['__species_norm'] = df2['__species_norm']
    grouped_counts = counts.groupby('__species_norm').sum()
    orig_names = df2.groupby('__species_norm')[species_col].first()
    result = grouped_counts.copy()
    result['species'] = orig_names
    result = result.reset_index(drop=True)
    # ensure species is first column
    cols = ['species'] + [c for c in result.columns if c != 'species']
    result = result[cols]
    return result


uploaded_file = st.file_uploader("Unggah file CSV", type=["csv"], key="csv_uploader")

with st.expander("📊 Atau gunakan Google Spreadsheet"):
    st.write(
        "**Langkah-langkah menggunakan Google Spreadsheet:**\n\n"
        "1. **Buat atau buka spreadsheet** dengan format yang sesuai (lihat contoh format data di atas)\n"
        "2. **Pastikan kolom pertama berisi nama species**. Judul kolom pertama bisa apa saja dan akan diubah otomatis menjadi `species` oleh aplikasi.\n"
        "3. **Bagikan spreadsheet dengan akses publik**:\n"
        "   - Klik tombol \"Bagikan\" di kanan atas\n"
        "   - Ubah akses ke \"Siapa saja dengan link\"\n"
        "   - Peran: \"Editor\" atau minimal \"Penampil\"\n"
        "   - Salin link yang dibuat\n"
        "4. **Paste link di bawah** dan aplikasi akan otomatis membaca data\n\n"
        "⚠️ **PENTING**: Spreadsheet harus bersifat **publik** agar aplikasi dapat mengakses"
    )
    
    gsheet_url = st.text_input(
        "📎 Paste link Google Spreadsheet Anda di sini:",
        placeholder="https://docs.google.com/spreadsheets/d/SHEET_ID/edit..."
    )
    
    if gsheet_url:
        try:
            # Extract spreadsheet ID from URL
            if '/spreadsheets/d/' in gsheet_url:
                sheet_id = gsheet_url.split('/spreadsheets/d/')[1].split('/')[0]
                # Create CSV export URL
                csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
                df_gsheet = read_csv_flexible(csv_url)
                df_gsheet = normalize_uploaded_dataframe(df_gsheet)
                df_gsheet = clean_dataframe(df_gsheet)

                # check duplicates
                dups = find_duplicate_species(df_gsheet)
                if dups:
                    st.error("⚠️Peringatan penting: ditemukan data spesies yang duplicate.")
                    st.warning("Blok calculation: selesaikan duplikat dulu sebelum perhitungan.")
                    st.write("#### Data duplikat ditemukan pada kolom species")
                    st.write(", ".join(dups))
                    duplicate_rows = df_gsheet[df_gsheet['species'].astype(str).str.strip().str.lower().isin([v.lower() for v in dups])]
                    st.dataframe(duplicate_rows)
                    st.session_state.pending_df = df_gsheet
                    st.session_state.pending_dups = dups
                    st.session_state.pending_source = 'gsheet'
                    st.session_state.pending_habitat_columns = [c for c in df_gsheet.columns if c.lower() != "species"]
                else:
                    st.write("### Data dari Google Spreadsheet")
                    st.dataframe(df_gsheet)

                    habitat_columns = [c for c in df_gsheet.columns if c.lower() != "species"]
                    # Store in session state
                    st.session_state.df = df_gsheet
                    st.session_state.habitat_columns = habitat_columns
                    st.success("✓ Data berhasil dimuat dari Google Spreadsheet!")
            else:
                st.error("Format link tidak valid. Pastikan Anda meng-copy link yang benar dari Google Sheets.")
        except Exception as e:
            st.error(
                f"❌ Gagal membaca Google Spreadsheet. Pastikan:\n"
                f"- Spreadsheet sudah dibagikan dengan akses publik\n"
                f"- Link yang di-paste benar\n"
                f"- Koneksi internet stabil\n\n"
                f"Error: {str(e)}"
            )


if uploaded_file is not None:
    try:
        df = read_csv_flexible(uploaded_file)
        df = normalize_uploaded_dataframe(df)
        df = clean_dataframe(df)

        # check duplicates
        dups = find_duplicate_species(df)
        if dups:
            st.error("⚠️Peringatan penting: ditemukan data spesies yang duplicate.")
            st.warning("⚠️Blok calculation: selesaikan duplikat dulu sebelum perhitungan.")
            st.write("#### Data duplikat ditemukan pada kolom species")
            st.write(", ".join(dups))
            duplicate_rows = df[df['species'].astype(str).str.strip().str.lower().isin([v.lower() for v in dups])]
            st.dataframe(duplicate_rows)
            st.session_state.pending_df = df
            st.session_state.pending_dups = dups
            st.session_state.pending_source = 'upload'
            st.session_state.pending_habitat_columns = [c for c in df.columns if c.lower() != "species"]
        else:
            st.write("### Data yang diunggah")
            st.dataframe(df)
            habitat_columns = [c for c in df.columns if c.lower() != "species"]
            # Store in session state
            st.session_state.df = df
            st.session_state.habitat_columns = habitat_columns
    except Exception as e:
        st.error(f"Gagal membaca file CSV: {e}")
        st.session_state.df = None
        st.session_state.habitat_columns = []
elif st.session_state.df is None:
    st.info("Masukkan data langsung di bawah ini jika tidak ingin mengunggah file CSV atau menggunakan Google Spreadsheet. Jumlah jenis satwa tidak terbatas, sesuaikan dengan hasil pertemuan di lapangan.")
    
    with st.form("species_form"):
        data = st.text_area(
            "Data species (csv format tanpa header). Tambahkan baris baru untuk setiap jenis satwa:",
            value="Kupu-kupu,15,10\nBurung,42,25\nSemut,23,12\nKatak,8,5",
            height=250,
        )
        submitted = st.form_submit_button("📤 Kirim Data Species Manual", use_container_width=True)
    
    if submitted and data:
        try:
            df = load_data_from_text(data)
            df = clean_dataframe(df)

            # check duplicates
            dups = find_duplicate_species(df)
            if dups:
                st.error("⚠️Peringatan penting: ditemukan data spesies yang duplicate.")
                st.warning("⚠️Blok calculation: selesaikan duplikat dulu sebelum perhitungan.")
                st.write("#### Data duplikat ditemukan pada kolom species")
                st.write(", ".join(dups))
                duplicate_rows = df[df['species'].astype(str).str.strip().str.lower().isin([v.lower() for v in dups])]
                st.dataframe(duplicate_rows)
                st.session_state.pending_df = df
                st.session_state.pending_dups = dups
                st.session_state.pending_source = 'manual'
                st.session_state.pending_habitat_columns = [c for c in df.columns if c.lower() != "species"]
            else:
                st.write("### Data yang dimasukkan")
                st.dataframe(df)
                habitat_columns = [c for c in df.columns if c.lower() != "species"]
                # Store in session state
                st.session_state.df = df
                st.session_state.habitat_columns = habitat_columns
                st.rerun()
        except Exception as e:
            st.error(f"Gagal membaca data: {e}")
            st.session_state.df = None
            st.session_state.habitat_columns = []
    elif submitted and not data:
        st.error("Silakan masukkan data terlebih dahulu!")

# If there is pending data with duplicates, require resolution before proceeding
if st.session_state.get('pending_df') is not None:
    st.error("Peringatan: Duplikat species ditemukan: " + ", ".join(st.session_state.get('pending_dups', [])))
    st.info("Selesaikan duplikat agar perhitungan dapat dilakukan. Pilih cara penyelesaian di bawah ini.")
    with st.expander("Tampilkan data yang bermasalah"):
        st.dataframe(st.session_state.pending_df)
    col1, col2, col3 = st.columns(3)
    if col1.button("Gabungkan duplikat (jumlahkan counts)"):
        merged = merge_duplicate_species(st.session_state.pending_df)
        st.session_state.df = merged
        st.session_state.habitat_columns = [c for c in merged.columns if c.lower() != 'species']
        st.session_state.pending_df = None
        st.session_state.pending_dups = []
        st.success("Duplikat digabungkan; perhitungan dapat dilanjutkan.")
        st.rerun()
    # remove duplicates keeping first occurrence
    if col2.button("Hapus entri duplikat (pertahankan entri pertama)"):
        species_col = get_species_column(st.session_state.pending_df) or 'species'
        cleaned = st.session_state.pending_df.drop_duplicates(subset=species_col, keep='first').copy()
        # ensure standardized species column name
        if species_col != 'species':
            cleaned = cleaned.rename(columns={species_col: 'species'})
        st.session_state.df = cleaned
        st.session_state.habitat_columns = [c for c in cleaned.columns if c.lower() != 'species']
        st.session_state.pending_df = None
        st.session_state.pending_dups = []
        st.success("Duplikat dihapus (dipertahankan entri pertama); perhitungan dapat dilanjutkan.")
        st.rerun()
    if col3.button("Batalkan (hapus data yang diunggah)"):
        st.session_state.pending_df = None
        st.session_state.pending_dups = []
        st.info("Data pending dihapus. Silakan unggah atau masukkan data lagi.")

# Input nama habitat (jika dari manual input atau jika ingin mengubah nama)
if st.session_state.df is not None and len(st.session_state.habitat_columns) > 0:
    st.write("### Verifikasi/Ubah nama habitat")
    st.info("Nama habitat sudah terdeteksi dari data. Ubah jika diperlukan:")
    
    with st.form("habitat_names_form"):
        habitat_names = {}
        
        for idx, habitat in enumerate(st.session_state.habitat_columns):
            habitat_names[habitat] = st.text_input(
                f"Nama habitat {idx + 1}:",
                value=habitat,
                key=f"habitat_name_{habitat}"
            )
        
        habitat_submitted = st.form_submit_button("✓ Konfirmasi Nama Habitat", use_container_width=True)
    
    # Rename columns dengan nama habitat yang dipilih
    if habitat_submitted and habitat_names:
        rename_dict = habitat_names
        st.session_state.df = st.session_state.df.rename(columns=rename_dict)
        st.session_state.habitat_columns = list(habitat_names.values())
        st.success("✓ Nama habitat berhasil diperbarui!")
        st.rerun()

if st.session_state.df is not None and len(st.session_state.habitat_columns) > 0:
    df = st.session_state.df.copy()
    habitat_columns = st.session_state.habitat_columns
    
    if df.empty:
        st.warning("Data kosong. Silakan masukkan data species.")
    else:
        if "species" not in df.columns:
            st.error("Format data tidak valid. Pastikan kolom 'species' ada.")
        else:
            if not habitat_columns:
                st.error("Format data tidak valid. Tambahkan setidaknya satu kolom habitat.")
            else:
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
                            x=alt.X('label:N', title='Indeks dan Habitat'),
                            y=alt.Y('Nilai:Q', title='Nilai Indeks'),
                            color=alt.Color('Indeks:N', title='Indeks'),
                            tooltip=['habitat', 'Indeks', 'Nilai'],
                        )
                        .properties(width=900, height=400)
                    )
                    st.altair_chart(chart, use_container_width=True)

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
                    pi_pivot = pi_df.pivot_table(
                        index='species',
                        columns='habitat',
                        values='p_i_ln_p_i',
                        aggfunc='first'
                    ).reset_index()
                    pi_pivot.insert(0, 'No.', range(1, len(pi_pivot) + 1))
                    st.dataframe(pi_pivot)

                    st.success("Yeay! Calculation done.")

