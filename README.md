# Project-ecology
Ecology indexes in nutshell (trial)

## Streamlit Deployment

Aplikasi ini menghitung indeks keanekaragaman hayati dari data species dan jumlah individu di setiap habitat pengamatan.
Hasil dari aplikasi ini adalah perbandingan nilai indeks-indeks keanekaragaman hayati pada setiap habitat pengamatan.

### Jalankan lokal

1. Instal dependensi:

```bash
pip install -r requirements.txt
```

2. Jalankan Streamlit:

```bash
streamlit run streamlit_app.py
```

### Input Data

- Unggah file CSV dengan kolom `species` dan `habitat`
- Atau masukkan data langsung dalam format CSV tanpa header di area teks

### Indeks yang dihitung

- Shannon-Wiener
- Simpson
- Evenness
- Pielou
