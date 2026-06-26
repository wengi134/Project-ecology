import streamlit as st
from utils.io import (
    clean_dataframe,
    get_habitat_columns,
    get_species_column,
    load_data_from_text,
    normalize_uploaded_dataframe,
    read_csv_flexible,
    find_duplicate_species,
)


def render_input_data_page():
    st.title("1. Input Data")
    st.write("Unggah file CSV, masukkan data manual, atau gunakan Google Spreadsheet.")
    st.markdown(
        "#### Contoh format data input\n"
        "Gunakan kolom pertama `Famili`, kolom kedua `Spesies`, dan kolom berikutnya untuk jumlah individu per habitat. Jika mengunggah CSV, pastikan file disimpan dengan format CSV dengan pemisah koma.\n\n"
        "| Famili | Spesies | Hutan | Sawah | Kebun | Pemukiman | Sungai | Pantai |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| Pongidae | Kuskus | 15 | 10 | 18 | 8 | 40 | 6 |\n"
        "| Pongidae | Orangutan | 4 | 0 | 2 | 3 | 2 | 1 |\n"
        "| Cervidae | Rusa totol | 0 | 12 | 35 | 28 | 15 | 0 |\n"
        "| Sciuridae | Bajing kelapa | 8 | 5 | 6 | 2 | 18 | 0 |\n"
    )
    st.info(
        "Tips:\n"
        "- `Famili` adalah kategori taksonomi (contoh: Pongidae, Cervidae, Sciuridae).\n"
        "- `Spesies` harus diisi dengan nama jenis satwa atau takson.\n"
        "- Kolom habitat berisi jumlah individu untuk masing-masing lokasi.\n"
        "- Jika menggunakan Google Spreadsheet, pastikan dokumen berstatus publik dan format kolom sama.\n"
    )

    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'habitat_columns' not in st.session_state:
        st.session_state.habitat_columns = []

    st.subheader("Unggah file CSV")
    uploaded_file = st.file_uploader("Pilih file CSV di Peragkatmu", type=["csv"], key="csv_uploader")

    st.subheader("Gunakan Google Spreadsheet")
    with st.expander("📊 Hubungkan dengan Google Spreadsheet"):
        st.write(
            "**Langkah-langkah menggunakan Google Spreadsheet:**\n\n"
            "1. **Buat atau buka spreadsheet** dengan format yang sesuai.\n"
            "2. **Pastikan kolom pertama berisi Famili, kolom kedua berisi nama Species**.\n"
            "3. **Bagikan spreadsheet dengan akses publik**.\n"
            "4. **Paste link di bawah** dan aplikasi akan otomatis membaca data.\n\n"
            "⚠️ **PENTING**: Spreadsheet harus bersifat **publik** agar aplikasi dapat mengakses"
        )

        gsheet_url = st.text_input(
            "📎 Paste link Google Spreadsheet Anda di sini:",
            placeholder="https://docs.google.com/spreadsheets/d/SHEET_ID/edit..."
        )

        if gsheet_url:
            try:
                if '/spreadsheets/d/' in gsheet_url:
                    sheet_id = gsheet_url.split('/spreadsheets/d/')[1].split('/')[0]
                    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
                    df_gsheet = read_csv_flexible(csv_url)
                    df_gsheet = normalize_uploaded_dataframe(df_gsheet)
                    df_gsheet = clean_dataframe(df_gsheet)

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
                        st.session_state.pending_habitat_columns = get_habitat_columns(df_gsheet)
                    else:
                        st.write("### Data dari Google Spreadsheet")
                        st.dataframe(df_gsheet)
                        st.session_state.df = df_gsheet
                        st.session_state.habitat_columns = get_habitat_columns(df_gsheet)
                        st.success("✓ Data berhasil dimuat dari Google Spreadsheet!")
                        st.info(
                            "📊 **Data siap untuk dianalisis!**\n\n"
                            "Silakan lihat hasil analisis pada halaman berikut:\n\n"
                            "- **2. Indeks Ekologi** - Lihat indeks keanekaragaman (Shannon, Pielou, Margalef, Simpson)\n"
                            "- **3. Rank Abundance** - Lihat peringkat kelimpahan spesies per habitat\n"
                            "- **4. Export Hasil** - Unduh data input dalam format CSV"
                        )
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
                st.session_state.pending_habitat_columns = get_habitat_columns(df)
            else:
                st.write("### Data yang diunggah")
                st.dataframe(df)
                st.session_state.df = df
                st.session_state.habitat_columns = get_habitat_columns(df)
                st.success("✓ Data berhasil diunggah!")
                st.info(
                    "📊 **Data siap untuk dianalisis!**\n\n"
                    "Silakan lihat hasil analisis pada halaman berikut:\n\n"
                    "- **2. Indeks Ekologi** - Lihat indeks keanekaragaman (Shannon, Pielou, Margalef, Simpson)\n"
                    "- **3. Rank Abundance** - Lihat peringkat kelimpahan spesies per habitat\n"
                    "- **4. Export Hasil** - Unduh data input dalam format CSV"
                )
        except Exception as e:
            st.error(f"Gagal membaca file CSV: {e}")
            st.session_state.df = None
            st.session_state.habitat_columns = []
    elif st.session_state.df is None:
        st.subheader("Masukkan Data Manual")
        st.info(
            "- Kolom pertama: Famili (kategori taksonomi).\n"
            "- Kolom kedua: Spesies (nama jenis satwa).\n"
            "- Kolom ketiga dan seterusnya: Jumlah individu per habitat.\n"
            "- Masukkan data langsung di bawah ini jika *tidak ingin* mengunggah file CSV atau menggunakan Google Spreadsheet.\n"
            "- Jumlah jenis satwa tidak terbatas, sesuaikan dengan hasil pertemuan di lapangan.\n"
            "- Tambahkan baris baru untuk setiap jenis satwa.\n"
            "- Edit nama habitat setelah data manual dikirim.\n"
        )
        with st.form("species_form"):
            data = st.text_area(
                "Masukkan data manual di bawah ini (*csv format tanpa header: famili,spesies,habitat1,habitat2,...*).\n",
                value="Lepidoptera,Kupu-kupu,15,10\nAves,Burung,42,25\nInsecta,Semut,23,12\nAmphibia,Katak,8,5",
                height=250,
            )
            submitted = st.form_submit_button("📤 Kirim Data Species Manual", width='stretch')

        if submitted and data:
            try:
                df = load_data_from_text(data)
                df = clean_dataframe(df)
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
                    st.session_state.pending_habitat_columns = get_habitat_columns(df)
                else:
                    st.write("### Data yang dimasukkan")
                    st.dataframe(df)
                    st.session_state.df = df
                    st.session_state.habitat_columns = get_habitat_columns(df)
                    st.success("✓ Data berhasil dimasukkan!")
                    st.info(
                        "📊 **Data siap untuk dianalisis!**\n\n"
                        "Silakan lihat hasil analisis pada halaman berikut:\n\n"
                        "- **2. Indeks Ekologi** - Lihat indeks keanekaragaman (Shannon, Pielou, Margalef, Simpson)\n"
                        "- **3. Rank Abundance** - Lihat peringkat kelimpahan spesies per habitat\n"
                        "- **4. Export Hasil** - Unduh data input dalam format CSV"
                    )
                    st.rerun()
            except Exception as e:
                st.error(f"Gagal membaca data: {e}")
                st.session_state.df = None
                st.session_state.habitat_columns = []
        elif submitted and not data:
            st.error("Silakan masukkan data terlebih dahulu!")

    if st.session_state.get('pending_df') is not None:
        st.error("Peringatan: Duplikat species ditemukan: " + ", ".join(st.session_state.get('pending_dups', [])))
        st.info("Selesaikan duplikat agar perhitungan dapat dilakukan. Pilih cara penyelesaian di bawah ini.")
        with st.expander("Tampilkan data yang bermasalah"):
            st.dataframe(st.session_state.pending_df)
        col1, col2, col3 = st.columns(3)
        if col1.button("Gabungkan duplikat (jumlahkan counts)"):
            from utils.io import merge_duplicate_species
            merged = merge_duplicate_species(st.session_state.pending_df)
            st.session_state.df = merged
            st.session_state.habitat_columns = get_habitat_columns(merged)
            st.session_state.pending_df = None
            st.session_state.pending_dups = []
            st.success("Duplikat digabungkan; perhitungan dapat dilanjutkan.")
            st.rerun()
        if col2.button("Hapus entri duplikat (pertahankan entri pertama)"):
            species_col = get_species_column(st.session_state.pending_df) or 'species'
            cleaned = st.session_state.pending_df.drop_duplicates(subset=species_col, keep='first').copy()
            if species_col != 'species':
                cleaned = cleaned.rename(columns={species_col: 'species'})
            st.session_state.df = cleaned
            st.session_state.habitat_columns = get_habitat_columns(cleaned)
            st.session_state.pending_df = None
            st.session_state.pending_dups = []
            st.success("Duplikat dihapus (dipertahankan entri pertama); perhitungan dapat dilanjutkan.")
            st.rerun()
        if col3.button("Batalkan (hapus data yang diunggah)"):
            st.session_state.pending_df = None
            st.session_state.pending_dups = []
            st.info("Data pending dihapus. Silakan unggah atau masukkan data lagi.")

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
            habitat_submitted = st.form_submit_button("✓ Konfirmasi Nama Habitat", width='stretch')
        if habitat_submitted and habitat_names:
            st.session_state.df = st.session_state.df.rename(columns=habitat_names)
            st.session_state.habitat_columns = list(habitat_names.values())
            st.success("✓ Nama habitat berhasil diperbarui!")
            st.rerun()


def render():
    render_input_data_page()
