import pandas as pd
import zipfile
import streamlit as st
from utils import safe_parse_numeric
from database import EXCLUDE_PREFIX

def load_data(file):
    if file is None: 
        return None
        
    filename = file.name.lower()
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(file, sep='\t', dtype=str)
            if df.shape[1] <= 1:
                file.seek(0)
                return pd.read_csv(file, sep=',', dtype=str)
            return df
            
        if filename.endswith(('.xls', '.xlsx')):
            return pd.read_excel(file, dtype=str)
            
        if filename.endswith('.zip'):
            with zipfile.ZipFile(file) as z:
                target = next((n for n in z.namelist() if "INVT_MASTER" in n and n.lower().endswith(".csv")), None)
                if not target: 
                    target = next((n for n in z.namelist() if n.lower().endswith(".csv")), None)
                if not target:
                    return None
                with z.open(target) as f:
                    return pd.read_csv(f, sep='\t', dtype=str)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None
    return None

def clean_sku_column(df, col, TARGET_SKUS=None):
    df = df.dropna(subset=[col])
    df[col] = df[col].astype(str).str.split('.').str[0].str.strip()
    df = df[~df[col].str.lower().isin(['nan', 'none', '', 'total', 'grand total'])]
    if TARGET_SKUS:
        df[col] = df[col].apply(lambda x: '0' + str(x) if (str(x) in TARGET_SKUS and str(x) not in EXCLUDE_PREFIX) else x)
    return df

def process_compare(df1, df2, sku_col1, desc_col1, qty_col1, sku_col2, qty_col2, TARGET_SKUS, multipliers, np_user_id=""):
    d1 = df1[[sku_col1, desc_col1, qty_col1]].copy()
    d1 = clean_sku_column(d1, sku_col1, TARGET_SKUS)
    d1[qty_col1] = d1[qty_col1].apply(safe_parse_numeric)
    d1_agg = (d1.groupby(sku_col1).agg({desc_col1: 'first', qty_col1: 'sum'}).reset_index().rename(columns={sku_col1: 'SKU', desc_col1: 'Description', qty_col1: 'Newspage'}))
    
    if 'Aktif' in df2.columns: 
        df2 = df2[pd.to_numeric(df2['Aktif'], errors='coerce') == 1]
    if 'Nama Gudang' in df2.columns: 
        df2 = df2[df2['Nama Gudang'].astype(str).str.strip().str.upper() == 'GUDANG UTAMA']
        
    d2 = df2[[sku_col2, qty_col2]].copy()
    d2 = clean_sku_column(d2, sku_col2, TARGET_SKUS)
    
    # Auto-align SKUs missing leading zeros (Excel drops zeros)
    d1_skus = set(d1_agg['SKU'].unique())
    d2[sku_col2] = d2[sku_col2].apply(lambda x: '0' + str(x) if str(x) not in d1_skus and ('0' + str(x)) in d1_skus else str(x))
    
    d2[qty_col2] = d2[qty_col2].apply(safe_parse_numeric)
    
    for rule in multipliers:
        # Match multiplier rule from database
        target = str(rule['sku_target']).strip()
        d2.loc[d2[sku_col2] == target, qty_col2] *= rule['multiplier_value']

    d2_agg = (d2.groupby(sku_col2)[qty_col2].sum().reset_index().rename(columns={sku_col2: 'SKU', qty_col2: 'Distributor'}))
    
    merged = pd.merge(d1_agg, d2_agg, on='SKU', how='outer')
    merged[['Newspage', 'Distributor']] = merged[['Newspage', 'Distributor']].fillna(0)
    merged['Description'] = merged['Description'].fillna('ITEM NOT IN MASTER')
    merged['Selisih'] = merged['Distributor'] - merged['Newspage']
    merged['Status'] = merged['Selisih'].apply(lambda x: 'Match' if x == 0 else 'Mismatch')
    
    mismatches = merged[merged['Status'] == 'Mismatch'].sort_values('Selisih')
    return merged, mismatches
