# KODE BOT PLAYWRIGHT (SUDAH DIVALIDASI DI PRODUCTION)

Ini adalah implementasi bot yang sudah berjalan di production. **Jangan ubah timeout, selector, atau urutan langkah** tanpa alasan kuat — semuanya sudah disesuaikan dengan perilaku server Newspage yang lambat.

### Konstanta Timeout (WAJIB dipakai)
```python
# Server Newspage sangat lambat. Gunakan nilai ini:
POPUP_TIMEOUT    = max(TIMEOUT_MS, 180_000)  # Popup loading: 3 menit
SEPARATOR_TIMEOUT = max(TIMEOUT_MS, 60_000)  # Radio button setelah select_option: 1 menit
SERVER_TIMEOUT   = max(TIMEOUT_MS, 300_000)  # Server confirmation dialog: 5 menit
DOWNLOAD_TIMEOUT = 240_000                    # Download link: 4 menit
```

### Login ke Newspage
```python
def _login(page, user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, ui_log):
    ui_log("AUTH", f"Connecting to {URL_LOGIN}...")
    page.goto(URL_LOGIN, wait_until="domcontentloaded")
    ui_log("AUTH", "DOM ready. Injecting credentials...")
    page.locator("id=txtUserid").fill(user_id_np)
    page.locator("id=txtPasswd").fill(pass_np)
    page.locator("id=btnLogin").click(force=True)

    # Handle active session interceptor (jika ada sesi aktif di Newspage)
    try:
        btn = page.locator("id=SYS_ASCX_btnContinue")
        btn.wait_for(state="visible", timeout=5_000)
        ui_log("AUTH", "Active session detected. Bypassing...")
        btn.click(force=True)
    except Exception:
        ui_log("SYS", "No interceptor. Clean session acquired.")

    page.wait_for_url("**/Default.aspx", timeout=TIMEOUT_MS, wait_until="domcontentloaded")
    ui_log("AUTH", "Login successful.")
```

### Navigasi ke Import/Export Job
```python
def _navigate_to_import_export(page, TIMEOUT_MS, ui_log):
    ui_log("NAV", "Navigating to System module...")
    page.wait_for_timeout(1000)

    # Klik tab System jika visible
    try:
        sys_tab = page.locator("id=pag_Sys_Root_tab_Detail_tab_Header")
        if sys_tab.is_visible():
            sys_tab.click(force=True)
            page.wait_for_timeout(800)
    except:
        pass

    target_id = "pag_Sys_Root_tab_Detail_itm_Job"

    try:
        page.wait_for_selector(f"id={target_id}", state="attached", timeout=TIMEOUT_MS)
        # JS click bypass: menu item mungkin tidak visible tapi sudah ada di DOM
        page.evaluate(f"document.getElementById('{target_id}').click()")
        page.wait_for_timeout(1500)
    except Exception as e:
        # Fallback: brute-force via text
        try:
            parent = page.locator("[id*='itm_SysAdminSetup']").first
            if parent.is_visible():
                parent.click(force=True)
                page.wait_for_timeout(1000)
            page.get_by_text("Import/Export Job").first.click(force=True)
        except:
            raise e

    page.wait_for_timeout(1000)

    # Klik Add untuk buat job baru
    btn_add = page.locator("id=pag_FW_SYS_INTF_JOB_btn_Add_Value")
    btn_add.wait_for(state="visible", timeout=TIMEOUT_MS)
    btn_add.click(force=True)
    page.wait_for_timeout(500)
```

### Job: Ekstraksi Inventory Master
```python
def _dispatch_extraction_job(page, TIMEOUT_MS, WAREHOUSE, ui_log):
    # Setup job header
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_TYPE_Value").select_option("E")
    page.wait_for_timeout(1000)
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_DESC_Value").fill("Text Inventory Master")
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_TIMEOUT_Value").fill("9999999")
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_EXE_TYPE_Value").select_option("M")
    page.wait_for_timeout(1000)

    # Next → bypass disclaimer
    page.locator("id=pag_FW_SYS_INTF_JOB_RootNew_btn_Next_Value").click(force=True)
    page.wait_for_timeout(1000)
    ok_btn = page.locator("id=pag_FW_DisclaimerMessage_btn_okay_Value")
    ok_btn.wait_for(state="visible", timeout=TIMEOUT_MS)
    ok_btn.click(force=True)
    page.wait_for_timeout(500)

    # Buka popup interface selection
    page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_INTF_ID_SelectButton").click(force=True)
    page.wait_for_timeout(1000)

    # Search interface ID (POPUP SANGAT LAMBAT - gunakan timeout 3 menit)
    search_field = page.locator("id=pop_Dynamic_gft_List_2_FilterField_Value")
    search_field.wait_for(state="visible", timeout=max(TIMEOUT_MS, 180_000))
    search_field.fill("E_20150315090000028")
    page.locator("id=pop_Dynamic_grd_Main_SearchForm_ButtonSearch_Value").click(force=True)
    page.wait_for_timeout(800)

    target = page.get_by_text("E_20150315090000028", exact=True)
    target.wait_for(state="visible", timeout=max(TIMEOUT_MS, 180_000))
    target.click(force=True)
    page.wait_for_timeout(800)

    # Set file type → WAJIB tunggu radio button visible setelah select_option
    page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_FILE_TYPE_Value").select_option("D")
    page.wait_for_timeout(1500)
    sep = page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_FLD_SEPARATOR_STD_Value_0")
    sep.wait_for(state="visible", timeout=max(TIMEOUT_MS, 60_000))
    sep.check()
    page.wait_for_timeout(2000)

    # Warehouse filter
    page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_grd_DynamicFilter_ctl02_dyn_Field_txt_Value").fill(WAREHOUSE)
    page.wait_for_timeout(1500)

    # Commit dan save
    page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_btn_Add_Value").click(force=True)
    page.wait_for_timeout(2000)
    page.locator("id=pag_FW_SYS_INTF_JOB_RootNew_btn_Save_Value").click(force=True)

    # Tunggu konfirmasi server (BISA 5 MENIT)
    page.locator("id=TF_Prompt_btn_Ok_Value").wait_for(
        state="visible", timeout=max(TIMEOUT_MS, 300_000)
    )
    page.locator("id=TF_Prompt_btn_Ok_Value").click(force=True)

    # Download (BISA 4 MENIT)
    with page.expect_download(timeout=240_000) as dl:
        btn = page.locator("id=pag_FW_SYS_INTF_STATUS_JOB_btn_Download_Value")
        btn.wait_for(state="visible", timeout=240_000)
        btn.click(force=True)

    download = dl.value
    filename = download.suggested_filename
    path = f"temp_ext_{filename}"
    download.save_as(path)
    return filename, path
```

### Job: Ekstraksi Sales (Invoice Detail)
```python
def _dispatch_sales_job(page, TIMEOUT_MS, start_date, end_date, ui_log):
    # start_date, end_date format: "DD/MM/YYYY"

    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_TYPE_Value").select_option("E")
    page.wait_for_timeout(1000)
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_DESC_Value").fill("Invoice Detail")
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_TIMEOUT_Value").fill("9999999")
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_EXE_TYPE_Value").select_option("M")
    page.wait_for_timeout(1000)
    page.locator("id=pag_FW_SYS_INTF_JOB_RootNew_btn_Next_Value").click(force=True)
    page.wait_for_timeout(2000)
    page.locator("id=pag_FW_DisclaimerMessage_btn_okay_Value").wait_for(state="visible", timeout=TIMEOUT_MS)
    page.locator("id=pag_FW_DisclaimerMessage_btn_okay_Value").click(force=True)
    page.wait_for_timeout(2000)

    # Interface ID untuk sales
    page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_INTF_ID_SelectButton").click(force=True)
    page.wait_for_timeout(2000)
    page.locator("id=pop_Dynamic_gft_List_2_FilterField_Value").wait_for(
        state="visible", timeout=max(TIMEOUT_MS, 180_000)
    )
    page.locator("id=pop_Dynamic_gft_List_2_FilterField_Value").fill("E_28880804000000001")
    page.locator("id=pop_Dynamic_grd_Main_SearchForm_ButtonSearch_Value").click(force=True)
    page.wait_for_timeout(2000)
    page.locator("id=pop_Dynamic_grd_Main_ctl02_DynCol_INTF_ID_Value").click(force=True)
    page.wait_for_timeout(2000)

    page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_FILE_TYPE_Value").select_option("D")
    page.wait_for_timeout(1500)
    sep = page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_FLD_SEPARATOR_STD_Value_0")
    sep.wait_for(state="visible", timeout=max(TIMEOUT_MS, 60_000))
    sep.check()
    page.wait_for_timeout(1500)

    # Filter status Invoiced
    page.locator(
        "id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_grd_DynamicFilter_ctl13_dyn_Field_drp_Value"
    ).select_option("Invoiced")
    page.wait_for_timeout(3500)  # PostBack server

    # WAJIB inject tanggal via JavaScript — jangan gunakan click UI kalender
    sd_d, sd_m, sd_y = start_date.split('/')
    ed_d, ed_m, ed_y = end_date.split('/')
    page.evaluate(f"""() => {{
        function setCalDate(inputId, extenderId, day, month, year, dateStr) {{
            var el = document.getElementById(inputId);
            if (el) {{ el.value = dateStr; el.dispatchEvent(new Event('change', {{bubbles: true}})); }}
            try {{
                var ce = $find(extenderId);
                if (ce) {{ ce._selectedDate = new Date(year, month - 1, day); ce._textbox.set_Value(dateStr); }}
            }} catch(e) {{}}
        }}
        setCalDate(
            'pag_FW_SYS_INTF_JOB_DTL_PopupNew_grd_DynamicFilter_ctl15_dyn_Field_dat_Value',
            'pag_FW_SYS_INTF_JOB_DTL_PopupNew_grd_DynamicFilter_ctl15_dyn_Field_dat_ajax_CalendarExtender',
            {int(sd_d)}, {int(sd_m)}, {int(sd_y)}, '{start_date}'
        );
        setCalDate(
            'pag_FW_SYS_INTF_JOB_DTL_PopupNew_grd_DynamicFilter_ctl16_dyn_Field_dat_Value',
            'pag_FW_SYS_INTF_JOB_DTL_PopupNew_grd_DynamicFilter_ctl16_dyn_Field_dat_ajax_CalendarExtender',
            {int(ed_d)}, {int(ed_m)}, {int(ed_y)}, '{end_date}'
        );
    }}""")
    page.wait_for_timeout(1500)

    page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_btn_Add_Value").click(force=True)
    page.wait_for_timeout(2000)
    page.locator("id=pag_FW_SYS_INTF_JOB_RootNew_btn_Save_Value").click(force=True)
    page.wait_for_timeout(2000)
    page.locator("id=TF_Prompt_btn_Ok_Value").wait_for(
        state="visible", timeout=max(TIMEOUT_MS, 300_000)
    )
    page.locator("id=TF_Prompt_btn_Ok_Value").click(force=True)

    with page.expect_download(timeout=240_000) as dl:
        btn = page.locator("id=pag_FW_SYS_INTF_STATUS_JOB_btn_Download_Value")
        btn.wait_for(state="visible", timeout=240_000)
        btn.click(force=True)

    download = dl.value
    filename = download.suggested_filename
    path = f"temp_sales_{filename}"
    download.save_as(path)
    return filename, path
```

### Stock Adjustment (Inject ke Newspage)
```python
def _navigate_to_stock_adjustment(page, TIMEOUT_MS, WAREHOUSE, REASON_CODE, ui_log):
    # Navigasi ke modul Stock Adjustment di Newspage
    # (Setiap implementasi Newspage mungkin berbeda, sesuaikan dengan menu client)
    pass  # Implementasi spesifik sesuai struktur menu Newspage

def _inject_adjustment_row(page, sku, qty, TIMEOUT_MS, ui_log):
    """Inject satu baris SKU + qty ke form Stock Adjustment Newspage."""
    sku_input = page.locator("id=pag_I_StkAdj_NewGeneral_sel_PRD_CD_Value")
    sku_input.fill(sku)
    sku_input.press("Tab")          # Trigger server-side SKU lookup
    page.wait_for_timeout(1500)     # Tunggu lookup selesai

    qty_ea = page.locator("id=pag_I_StkAdj_NewGeneral_txt_QTY1_Value")
    qty_ea.wait_for(state="visible", timeout=TIMEOUT_MS)
    qty_ea.fill(str(qty))

    page.locator("id=pag_I_StkAdj_NewGeneral_btn_Add_Value").click(force=True)

    # Tunggu form reset (konfirmasi row berhasil ditambah)
    page.wait_for_function(
        "document.getElementById('pag_I_StkAdj_NewGeneral_sel_PRD_CD_Value').value === ''",
        timeout=TIMEOUT_MS
    )

def execute_adjustment(df_mismatch, bot_user, bot_pass, URL_LOGIN,
                       TIMEOUT_MS, WAREHOUSE, REASON_CODE):
    """
    Inject semua baris mismatch ke Newspage.
    ATURAN KRITIS: Jika ADA 1 row gagal → ABORT, JANGAN click Save.
    Ini mencegah dokumen adjustment yang tidak lengkap masuk ke sistem.
    """
    success_count = 0
    failed_count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        _login(page, bot_user, bot_pass, "", URL_LOGIN, TIMEOUT_MS, print)
        _navigate_to_stock_adjustment(page, TIMEOUT_MS, WAREHOUSE, REASON_CODE, print)

        for idx, row in df_mismatch.iterrows():
            sku = str(row['SKU']).strip()
            qty = str(int(float(row['Selisih'])))

            if row.get('Status') == 'Invalid':
                continue

            try:
                _inject_adjustment_row(page, sku, qty, TIMEOUT_MS, print)
                df_mismatch.at[idx, 'ExecStatus'] = 'Success'
                success_count += 1
            except Exception as e:
                df_mismatch.at[idx, 'ExecStatus'] = 'Failed'
                failed_count += 1

        # ABORT jika ada failure
        if failed_count > 0:
            browser.close()
            raise Exception(f"ABORTED: {failed_count} failures. Document NOT saved.")

        # Save dokumen ke Newspage
        page.locator("id=pag_I_StkAdj_NewGeneral_btn_Save_Value").click()
        try:
            yes_btn = page.locator("id=pag_PopUp_YesNo_btn_Yes_Value")
            yes_btn.wait_for(state="visible", timeout=5000)
            yes_btn.click()
        except:
            pass  # Auto-confirmed
        page.wait_for_timeout(5000)

        # Logout
        try:
            page.once("dialog", lambda d: d.accept())
            page.locator("id=btnLogout").click(timeout=10000)
            page.wait_for_timeout(2000)
        except:
            pass

        browser.close()

    return success_count, failed_count
```

---

## DATA PROCESSING RULES

### SKU Normalization
```python
EXCLUDE_PREFIX = ['8021803', '8021804']

def normalize_sku(sku: str, TARGET_SKUS: list) -> str:
    sku = str(sku).split('.')[0].strip()
    if sku.lower() in ['nan', 'none', '', 'total', 'grand total']:
        return None
    if sku in TARGET_SKUS and sku not in EXCLUDE_PREFIX:
        sku = '0' + sku
    return sku
```

### Distributor File Filtering
```python
def filter_distributor_df(df: pd.DataFrame) -> pd.DataFrame:
    # Filter hanya stok aktif
    if 'Aktif' in df.columns:
        df = df[pd.to_numeric(df['Aktif'], errors='coerce') == 1]
    # Filter hanya gudang utama
    if 'Nama Gudang' in df.columns:
        df = df[df['Nama Gudang'].str.strip().str.upper() == 'GUDANG UTAMA']
    return df
```

### Rekonsiliasi
```python
def reconcile(df_newspage, df_distributor, sku_col_np, desc_col_np, qty_col_np,
               sku_col_dist, qty_col_dist, TARGET_SKUS, multiplier_rules):
    # Normalize dan aggregate Newspage
    d1 = df_newspage.copy()
    d1[sku_col_np] = d1[sku_col_np].apply(lambda x: normalize_sku(x, TARGET_SKUS))
    d1 = d1.dropna(subset=[sku_col_np])
    d1[qty_col_np] = pd.to_numeric(d1[qty_col_np], errors='coerce').fillna(0)
    d1_agg = d1.groupby(sku_col_np).agg(
        {desc_col_np: 'first', qty_col_np: 'sum'}
    ).reset_index().rename(columns={
        sku_col_np: 'SKU', desc_col_np: 'Description', qty_col_np: 'Newspage'
    })

    # Normalize, filter, aggregate Distributor
    d2 = filter_distributor_df(df_distributor.copy())
    d2[sku_col_dist] = d2[sku_col_dist].apply(lambda x: normalize_sku(x, TARGET_SKUS))
    d2 = d2.dropna(subset=[sku_col_dist])
    d2[qty_col_dist] = pd.to_numeric(d2[qty_col_dist], errors='coerce').fillna(0)

    # Apply multiplier rules
    for rule in multiplier_rules:
        mask = d2[sku_col_dist] == str(rule['sku_target']).strip()
        d2.loc[mask, qty_col_dist] *= rule['multiplier_value']

    d2_agg = d2.groupby(sku_col_dist)[qty_col_dist].sum().reset_index().rename(
        columns={sku_col_dist: 'SKU', qty_col_dist: 'Distributor'}
    )

    # Merge dan hitung selisih
    merged = pd.merge(d1_agg, d2_agg, on='SKU', how='outer')
    merged[['Newspage', 'Distributor']] = merged[['Newspage', 'Distributor']].fillna(0)
    merged['Description'] = merged['Description'].fillna('ITEM NOT IN MASTER')
    merged['Selisih'] = merged['Distributor'] - merged['Newspage']
    merged['Status'] = merged['Selisih'].apply(lambda x: 'Match' if x == 0 else 'Mismatch')

    mismatches = merged[merged['Status'] == 'Mismatch'].sort_values('Selisih')
    return merged, mismatches
```

### Security: Enkripsi Password
```python
from cryptography.fernet import Fernet

def encrypt_password(plain: str, master_key: str) -> str:
    f = Fernet(master_key.encode())
    return f.encrypt(plain.encode()).decode()

def decrypt_password(encrypted: str, master_key: str) -> str:
    if not encrypted:
        return ""
    try:
        f = Fernet(master_key.encode())
        return f.decrypt(encrypted.encode()).decode()
    except Exception:
        return ""  # Jangan raise — return kosong agar tidak crash

# Cek apakah sudah terenkripsi
def is_encrypted(value: str) -> bool:
    return value.startswith("gAAAAA")
```

---

## INTERFACE IDs NEWSPAGE

| Interface ID | Fungsi |
|---|---|
| `E_20150315090000028` | Inventory Master (INVT_MASTER) |
| `E_28880804000000001` | Sales / Invoice Detail |
| `E_20150417000000043` | Promo sync #1 |
| `E_20150417000000044` | Promo sync #2 |
| `E_20150417000000050` | Promo sync #3 |
| `E_20150417000000048` | Promo sync #4 |
| `E_20150417000000093` | Promo sync #5 |
