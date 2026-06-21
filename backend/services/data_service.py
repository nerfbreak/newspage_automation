"""Data processing service - refactored from data_processor.py.
All Streamlit dependencies removed.
"""
import logging
import pandas as pd
import zipfile

logger = logging.getLogger(__name__)


def load_data_from_bytes(file_bytes: bytes, filename: str) -> pd.DataFrame | None:
    """Load a DataFrame from raw bytes (CSV, Excel, or ZIP).
    Replaces the Streamlit file_uploader-based load_data().
    """
    fname = filename.lower()
    try:
        if fname.endswith('.csv'):
            import io
            buf = io.BytesIO(file_bytes)
            df = pd.read_csv(buf, sep='\t', dtype=str)
            if df.shape[1] <= 1:
                buf.seek(0)
                return pd.read_csv(buf, sep=',', dtype=str)
            return df

        if fname.endswith(('.xls', '.xlsx')):
            import io
            return pd.read_excel(io.BytesIO(file_bytes), dtype=str)

        if fname.endswith('.zip'):
            import io
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                target = next((n for n in z.namelist() if "INVT_MASTER" in n and n.lower().endswith(".csv")), None)
                if not target:
                    target = next((n for n in z.namelist() if n.lower().endswith(".csv")), None)
                if not target:
                    return None
                with z.open(target) as f:
                    return pd.read_csv(f, sep='\t', dtype=str)
    except Exception as e:
        logger.error("Error reading file %s: %s", filename, e)
        return None
    return None


def load_data_from_file(file_path: str) -> pd.DataFrame | None:
    """Load a DataFrame from a file path."""
    fname = file_path.lower()
    try:
        if fname.endswith('.csv'):
            df = pd.read_csv(file_path, sep='\t', dtype=str)
            if df.shape[1] <= 1:
                return pd.read_csv(file_path, sep=',', dtype=str)
            return df
        if fname.endswith(('.xls', '.xlsx')):
            return pd.read_excel(file_path, dtype=str)
    except Exception as e:
        logger.error("Error reading file %s: %s", file_path, e)
        return None
    return None


def process_compare(df1, df2, sku_col1, desc_col1, qty_col1, sku_col2, qty_col2,
                    target_skus, multipliers, np_user_id=""):
    """Compare Newspage and Distributor dataframes.
    Returns (merged_df, mismatches_df) - identical logic to original data_processor.
    """
    d1 = df1[[sku_col1, desc_col1, qty_col1]].copy()
    d1 = d1.dropna(subset=[sku_col1])
    d1[sku_col1] = d1[sku_col1].astype(str).str.split('.').str[0].str.strip()
    d1 = d1[~d1[sku_col1].str.lower().isin(['nan', 'none', '', 'total', 'grand total'])]

    EXCLUDE_PREFIX = ['8021803', '8021804']
    d1[sku_col1] = d1[sku_col1].apply(
        lambda x: '0' + str(x) if (str(x) in target_skus and str(x) not in EXCLUDE_PREFIX) else x
    )
    d1[qty_col1] = pd.to_numeric(
        d1[qty_col1].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False),
        errors='coerce'
    ).fillna(0)
    d1_agg = (
        d1.groupby(sku_col1)
        .agg({desc_col1: 'first', qty_col1: 'sum'})
        .reset_index()
        .rename(columns={sku_col1: 'SKU', desc_col1: 'Description', qty_col1: 'Newspage'})
    )

    if 'Aktif' in df2.columns:
        df2 = df2[pd.to_numeric(df2['Aktif'], errors='coerce') == 1]
    if 'Nama Gudang' in df2.columns:
        df2 = df2[df2['Nama Gudang'].astype(str).str.strip().str.upper() == 'GUDANG UTAMA']

    d2 = df2[[sku_col2, qty_col2]].copy()
    d2 = d2.dropna(subset=[sku_col2])
    d2[sku_col2] = d2[sku_col2].astype(str).str.split('.').str[0].str.strip()
    d2 = d2[~d2[sku_col2].str.lower().isin(['nan', 'none', '', 'total', 'grand total'])]

    d2[sku_col2] = d2[sku_col2].apply(
        lambda x: '0' + str(x) if (str(x) in target_skus and str(x) not in EXCLUDE_PREFIX) else x
    )
    d2[qty_col2] = pd.to_numeric(
        d2[qty_col2].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False),
        errors='coerce'
    ).fillna(0)

    for rule in multipliers:
        target = str(rule['sku_target']).strip()
        d2.loc[d2[sku_col2] == target, qty_col2] *= rule['multiplier_value']

    d2_agg = (
        d2.groupby(sku_col2)[qty_col2]
        .sum()
        .reset_index()
        .rename(columns={sku_col2: 'SKU', qty_col2: 'Distributor'})
    )

    merged = pd.merge(d1_agg, d2_agg, on='SKU', how='outer')
    merged[['Newspage', 'Distributor']] = merged[['Newspage', 'Distributor']].fillna(0)
    merged['Description'] = merged['Description'].fillna('ITEM NOT IN MASTER')
    merged['Selisih'] = merged['Distributor'] - merged['Newspage']
    merged['Status'] = merged['Selisih'].apply(lambda x: 'Match' if x == 0 else 'Mismatch')

    mismatches = merged[merged['Status'] == 'Mismatch'].sort_values('Selisih')
    return merged, mismatches
