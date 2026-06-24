import streamlit as st

from pages import load_page_module

PAGE_MODULES = [
    ("1_Input_Data", "Input Data"),
    ("2_Indeks_Ekologi", "Indeks Ekologi"),
    ("3_Rank_Abundance", "Rank Abundance"),
    ("4_Export_Hasil", "Export Hasil"),
]

st.set_page_config(page_title="BIODIVERSITY INDEX CALCULATOR", page_icon="🌿")

st.title("PROJECT EKOLOGI")
st.subheader("Aplikasi menghitung indeks keanekaragaman hayati")

page = st.sidebar.radio("Pilih halaman", [label for _, label in PAGE_MODULES])
page_name = next(name for name, label in PAGE_MODULES if label == page)
module = load_page_module(f"{page_name}.py")
module.render()
