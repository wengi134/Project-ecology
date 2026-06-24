# Project-ecology
Aplikasi Streamlit untuk menghitung indeks keanekaragaman hayati dari data species di beberapa habitat.

## Struktur Proyek

```
project-ekologi/
├── streamlit_app.py
├── requirements.txt
├── README.md
├── pages/
│   ├── 1_Input_Data.py
│   ├── 2_Indeks_Ekologi.py
│   ├── 3_Rank_Abundance.py
│   └── 4_Export_Hasil.py
└── utils/
    ├── diversity.py
    ├── io.py
    └── plotting.py
```

## Fitur Utama

- Unggah data CSV atau gunakan Google Spreadsheet publik
- Masukkan data secara manual jika tidak ingin mengunggah file
- Deteksi dan tangani duplikat species
- Hitung indeks keanekaragaman:
  - Shannon-Wiener
  - Simpson
  - Pielou
  - Margalef
- Tampilkan analisis dan grafik per habitat
- Tampilkan ranking abundance dan ekspor hasil input

## Persiapan

1. Pastikan Python 3.12 atau lebih baru terpasang.
2. Instal dependensi:

```bash
python3 -m pip install -r requirements.txt
```

## Menjalankan Aplikasi

```bash
cd /workspaces/Project-ecology
python3 -m streamlit run streamlit_app.py
```

Buka browser pada alamat `http://localhost:8501`.

## Halaman Aplikasi

- `1_Input_Data`: Unggah CSV, gunakan Google Spreadsheet, atau masukkan data manual.
- `2_Indeks_Ekologi`: Hitung dan tampilkan indeks keanekaragaman per habitat.
- `3_Rank_Abundance`: Tampilkan rank abundance setiap habitat.
- `4_Export_Hasil`: Ekspor data input dalam format CSV.

## Dependensi Utama

- `streamlit`
- `pandas`
- `numpy`
- `altair`

## Catatan

Pastikan file CSV memiliki kolom pertama untuk nama species dan setidaknya satu kolom habitat berisi angka.
