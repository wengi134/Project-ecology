import pandas as pd
from io import StringIO
from typing import Any, List, Optional


def load_data_from_text(data_text: str) -> pd.DataFrame:
    df = pd.read_csv(StringIO(data_text), header=None)
    if df.shape[1] < 3:
        raise ValueError("Minimal harus ada kolom famili, species, dan satu kolom habitat.")
    df.columns = ["famili", "species"] + [f"habitat_{i}" for i in range(1, df.shape[1] - 1)]
    return df


def read_csv_flexible(source: Any) -> pd.DataFrame:
    try:
        if hasattr(source, "read"):
            source.seek(0)
            raw = source.read()
            text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
            return pd.read_csv(StringIO(text), sep=None, engine="python")

        return pd.read_csv(source, sep=None, engine="python")
    except Exception:
        seps = [",", ";", "\t", "|"]
        for sep in seps:
            try:
                if hasattr(source, "read"):
                    source.seek(0)
                    raw = source.read()
                    text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
                    df = pd.read_csv(StringIO(text), sep=sep)
                else:
                    df = pd.read_csv(source, sep=sep)
                if df.shape[1] >= 2:
                    return df
            except Exception:
                continue
        raise ValueError("Gagal membaca CSV. Pastikan file CSV memiliki minimal dua kolom dan delimiter standar (comma/semicolon/tab).")


def get_species_column(df: pd.DataFrame) -> Optional[str]:
    for col in df.columns:
        if isinstance(col, str) and col.strip().lower() in {"species", "species/jenis", "jenis"}:
            return col
    return None


def get_habitat_columns(df: pd.DataFrame) -> List[str]:
    return [c for c in df.columns if isinstance(c, str) and c.strip().lower() not in {"species", "famili"}]


def find_duplicate_species(df: pd.DataFrame) -> List[str]:
    species_col = get_species_column(df)
    if species_col is None:
        return []
    s = df[species_col].astype(str).str.strip()
    norm = s.str.lower()
    dup_mask = norm.duplicated(keep=False)
    if not dup_mask.any():
        return []
    dup_vals = norm[dup_mask].unique().tolist()
    original_names: List[str] = []
    for value in dup_vals:
        original_names.append(s[norm == value].iloc[0])
    return original_names


def normalize_uploaded_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.shape[1] < 2:
        raise ValueError("Minimal harus ada kolom species dan satu kolom habitat.")
    cols = list(df.columns)
    
    # Check if first column is 'famili', second is 'species'
    first_col_name = str(cols[0]).strip().lower() if cols else ""
    second_col_name = str(cols[1]).strip().lower() if len(cols) > 1 else ""
    
    # If first column is not 'famili', insert it (or rename if it looks like species)
    if first_col_name != "famili":
        if first_col_name in {"species", "species/jenis", "jenis"}:
            # First column is species, insert empty famili column before it
            df.insert(0, "famili", "")
            cols = list(df.columns)
        else:
            # Assume first column is famili, rename to lowercase
            cols[0] = "famili"
    else:
        # First column already 'famili', ensure lowercase
        cols[0] = "famili"
    
    # Ensure second column is 'species'
    if len(cols) > 1:
        second_col_name_normalized = str(cols[1]).strip().lower()
        if second_col_name_normalized in {"species", "species/jenis", "jenis"}:
            cols[1] = "species"
        else:
            cols[1] = "species"
    
    df.columns = cols
    return df


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    new_cols = []
    for c in df.columns:
        if isinstance(c, str):
            new_cols.append(c.strip())
        else:
            new_cols.append(c)
    df.columns = new_cols

    drop_cols = [c for c in df.columns if isinstance(c, str) and (c == "" or c.lower().startswith("unnamed"))]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    df = df.dropna(axis=1, how="all")
    return df


def merge_duplicate_species(df: pd.DataFrame) -> pd.DataFrame:
    df2 = df.copy()
    species_col = get_species_column(df2)
    if species_col is None:
        return df2
    df2["__species_norm"] = df2[species_col].astype(str).str.strip().str.lower()
    other_cols = [c for c in df2.columns if c not in {species_col, "__species_norm"}]
    if not other_cols:
        df2 = df2.drop(columns="__species_norm")
        return df2.rename(columns={species_col: "species"})

    counts = df2[other_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
    counts["__species_norm"] = df2["__species_norm"]
    grouped_counts = counts.groupby("__species_norm").sum()
    orig_names = df2.groupby("__species_norm")[species_col].first()
    orig_famili = df2.groupby("__species_norm")["famili"].first() if "famili" in df2.columns else None

    result = grouped_counts.copy()
    result["species"] = orig_names
    if orig_famili is not None:
        result["famili"] = orig_famili
    result = result.reset_index(drop=True)
    
    # Reorder columns: famili, species, then habitat columns
    if "famili" in result.columns:
        cols = ["famili", "species"] + [c for c in result.columns if c not in {"species", "famili"}]
    else:
        cols = ["species"] + [c for c in result.columns if c != "species"]
    return result[cols]


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")
