import sys
import os
import re
import time
import asyncio
import zipfile
import subprocess
from contextlib import contextmanager
import pandas as pd
import streamlit as st
import database
import utils
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def _setup_event_loop():
    try: asyncio.get_event_loop()
    except RuntimeError: asyncio.set_event_loop(asyncio.new_event_loop())


@contextmanager
def managed_browser_session(user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, ui_log):
    ensure_playwright()
    _setup_event_loop()
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        ui_log("SYS", "Spawning browser context with isolated session...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(no_viewport=True)
        page = context.new_page()
        try:
            _login(page, user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, ui_log)
            yield page, browser
        except Exception as e:
            try:
                os.makedirs("screenshots", exist_ok=True)
                sp = f"screenshots/error_{int(time.time())}.png"
                page.screenshot(path=sp, timeout=2000)
                e.screenshot_path = sp
            except Exception:
                pass
            raise
        finally:
            browser.close()
            ui_log("SYS", "Browser closed. Releasing session memory...")

def ensure_playwright():
    try:
        with sync_playwright() as p:
            # Try to get executable path. If it raises an error, we need to install.
            try:
                executable = p.chromium.executable_path
                if not os.path.exists(executable):
                    raise Exception("Executable missing")
            except Exception:
                subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception as e:
        try:
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        except Exception as e2:
            st.error(f"Failed to install browser engine: {e2}")

def _login(page, user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, ui_log):
    ui_log("AUTH", f"Connecting to {URL_LOGIN}...")
    
    # Check if this is superuser based on secrets
    try:
        is_super = user_id_np == st.secrets.get("NP_USER_SUPER")
    except Exception:
        is_super = False
    account_desc = "SUPERUSER" if is_super else f"[{selected_distributor}]"
    
    page.goto(URL_LOGIN, wait_until="networkidle")
    ui_log("AUTH", f"DOM ready. Injecting {account_desc} credentials...")
    page.locator("id=txtUserid").fill(user_id_np)
    page.locator("id=txtPasswd").fill(pass_np)
    page.locator("id=btnLogin").click(force=True)
    
    # Menunggu secara dinamis (hingga TIMEOUT_MS) agar Newspage memproses login.
    # Bisa langsung masuk ke Default.aspx ATAU memunculkan popup interceptor.
    start_time = time.time()
    while time.time() - start_time < (TIMEOUT_MS / 1000.0):
        if "Default.aspx" in page.url:
            ui_log("SYS", "No interceptor detected. Clean session acquired.")
            break
            
        try:
            btn = page.locator("id=SYS_ASCX_btnContinue")
            if btn.is_visible():
                ui_log("AUTH", "Active session interceptor detected. Bypassing...")
                btn.click(force=True)
                break
        except Exception:
            pass
            
        page.wait_for_timeout(500)
    else:
        # Jika loop habis tapi URL belum berubah dan popup tidak ada
        if "Default.aspx" not in page.url:
            raise Exception("Timeout: Server tidak merespon saat verifikasi login. Kredensial mungkin salah atau server down.")
    
    # Harus menggunakan networkidle agar semua JS click handler (actionpath) terpasang sebelum _navigate_to_stock_adjustment dijalankan.
    page.wait_for_url("**/Default.aspx", timeout=TIMEOUT_MS, wait_until="networkidle")
    ui_log("AUTH", "Login successful. Session established.")
    ui_log("SUCCESS", "Handshake verified.")

def _wait_for_page_ready(page, timeout_ms, ui_log=None, context=""):
    """Menunggu halaman/in-page AJAX request selesai sebelum lanjut ke step berikutnya.
    Menggunakan networkidle (500ms tanpa aktivitas network) sebagai sinyal utama.
    Aman dipanggil kapan saja — fallback graceful jika sudah dalam kondisi idle.
    """
    wait_timeout = min(timeout_ms, 30_000)
    label = f" [{context}]" if context else ""
    if ui_log:
        ui_log("WAIT", f"Waiting for page to settle{label}...")
    try:
        page.wait_for_load_state("networkidle", timeout=wait_timeout)
    except Exception:
        # Jika networkidle timeout (mis. server punya background polling ringan),
        # lanjutkan saja — error nyata akan ditangkap oleh wait_for(state=...) berikutnya.
        if ui_log:
            ui_log("WAIT", f"Networkidle timeout{label} — proceeding cautiously.")

def _navigate_to_import_export(page, TIMEOUT_MS, ui_log):
    ui_log("NAV", "Navigating to System module...")
    page.wait_for_timeout(1000)
    
    # Ensure 'System' tab is selected
    try:
        sys_tab = page.locator("id=pag_Sys_Root_tab_Detail_tab_Header")
        if sys_tab.is_visible():
            sys_tab.click(force=True)
            _wait_for_page_ready(page, TIMEOUT_MS, ui_log, "System tab")
            page.wait_for_timeout(800)
    except:
        pass

    ui_log("NAV", "Searching for Import/Export Job module in DOM...")
    
    target_id = "pag_Sys_Root_tab_Detail_itm_Job"
    
    # Wait for it to be attached (doesn't have to be visible)
    try:
        page.wait_for_selector(f"id={target_id}", state="attached", timeout=TIMEOUT_MS)
        ui_log("NAV", "Module found in DOM. Executing JS click bypass...")
        
        # JS Click bypass: ignores visibility and parent menu states
        page.evaluate(f"document.getElementById('{target_id}').click()")
        _wait_for_page_ready(page, TIMEOUT_MS, ui_log, "Import/Export menu")
        page.wait_for_timeout(1500)
        
    except Exception as e:
        ui_log("WARN", "ID-based JS click failed, trying brute-force...")
        try:
            # Try clicking the parent SysAdminSetup if we can find it
            parent = page.locator("[id*='itm_SysAdminSetup']").first
            if parent.is_visible():
                parent.click(force=True)
                page.wait_for_timeout(1000)
            
            # Final attempt: direct text click
            page.get_by_text("Import/Export Job").first.click(force=True)
        except:
            ui_log("ERROR", "Navigation failed. System menu might be blocked.")
            raise e

    page.wait_for_timeout(1000)
    
    ui_log("NAV", "Opening new job [Add Value]...")
    btn_add = page.locator("id=pag_FW_SYS_INTF_JOB_btn_Add_Value")
    btn_add.wait_for(state="visible", timeout=TIMEOUT_MS)
    btn_add.click(force=True)
    page.wait_for_timeout(500)

def _dispatch_extraction_job(page, TIMEOUT_MS, WAREHOUSE, ui_log, browser, dry_run=False):
    ui_log("INJECT", "Setting job type: Export [E], desc: Text Inventory Master...")
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_TYPE_Value").select_option("E")
    page.wait_for_timeout(1000)
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_DESC_Value").fill("Text Inventory Master")
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_TIMEOUT_Value").fill("9999999")
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_EXE_TYPE_Value").select_option("M")
    page.wait_for_timeout(1000)
    
    ui_log("NAV", "Proceeding to next step...")
    page.locator("id=pag_FW_SYS_INTF_JOB_RootNew_btn_Next_Value").click(force=True)
    _wait_for_page_ready(page, TIMEOUT_MS, ui_log, "extraction Next")
    page.wait_for_timeout(1000)
    
    ui_log("SYS", "Bypassing disclaimer prompt...")
    ok_btn = page.locator("id=pag_FW_DisclaimerMessage_btn_okay_Value")
    ok_btn.wait_for(state="visible", timeout=TIMEOUT_MS)
    ok_btn.click(force=True)
    page.wait_for_timeout(500)
    
    ui_log("NAV", "Opening interface selection popup...")
    page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_INTF_ID_SelectButton").click(force=True)
    page.wait_for_timeout(1000)
    
    ui_log("INJECT", "Searching target interface: E_20150315090000028...")
    search_field = page.locator("id=pop_Dynamic_gft_List_2_FilterField_Value")
    # Popups are extremely heavy and slow to load on the Newspage server. Increase search field wait timeout to 180s.
    search_field.wait_for(state="visible", timeout=max(TIMEOUT_MS, 180000))
    search_field.fill("E_20150315090000028")
    page.locator("id=pop_Dynamic_grd_Main_SearchForm_ButtonSearch_Value").click(force=True)
    page.wait_for_timeout(800)
    
    ui_log("INJECT", "Selecting target interface from results...")
    target_text = page.get_by_text("E_20150315090000028", exact=True)
    target_text.wait_for(state="visible", timeout=max(TIMEOUT_MS, 180000))
    target_text.click(force=True)
    page.wait_for_timeout(800)
    
    ui_log("INJECT", "Setting file type: Delimited [D], separator: standard...")
    page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_FILE_TYPE_Value").select_option("D")
    page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_FLD_SEPARATOR_STD_Value_0").check()
    page.wait_for_timeout(2000)
    
    ui_log("INJECT", f"Applying warehouse filter: [{WAREHOUSE}]...")
    page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_grd_DynamicFilter_ctl02_dyn_Field_txt_Value").fill(WAREHOUSE)
    page.wait_for_timeout(1500)
    
    ui_log("SYS", "Committing parameters to job definition...")
    page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_btn_Add_Value").click(force=True)
    _wait_for_page_ready(page, TIMEOUT_MS, ui_log, "extraction Add commit")
    page.wait_for_timeout(2000)
    
    ui_log("SERVER", "Saving job and dispatching execution to server...")
    if dry_run:
        ui_log("DRY_RUN", "Dry run active - bypassed save click")
        return None, None
    page.locator("id=pag_FW_SYS_INTF_JOB_RootNew_btn_Save_Value").click(force=True)
    
    ui_log("SERVER", "Awaiting server confirmation prompt...")
    page.locator("id=TF_Prompt_btn_Ok_Value").wait_for(state="visible", timeout=TIMEOUT_MS)
    page.locator("id=TF_Prompt_btn_Ok_Value").click(force=True)
    
    ui_log("SERVER", "Intercepting download link — this may take up to 4 minutes...")
    with page.expect_download(timeout=240000) as download_info:
        download_btn = page.locator("id=pag_FW_SYS_INTF_STATUS_JOB_btn_Download_Value")
        download_btn.wait_for(state="visible", timeout=240000)
        download_btn.click(force=True)
    
    download = download_info.value
    real_filename = download.suggested_filename
    file_path = f"temp_ext_{real_filename}"
    ui_log("SUCCESS", f"Download captured: {real_filename}. Saving to environment...")
    download.save_as(file_path)
    
    return real_filename, file_path

def run_extract(user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, WAREHOUSE, ext_ui_log, alert_callback, supabase, current_user, dry_run=None):
    if dry_run is None: dry_run = st.session_state.get('dry_run_enabled', False)
    try:
        with managed_browser_session(user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, ext_ui_log) as (page, browser):
            _navigate_to_import_export(page, TIMEOUT_MS, ext_ui_log)
            
            # Fetch distributor exception from DB
            exception_dict = database.get_distributor_warehouse_exceptions(supabase)
            target_whs = exception_dict.get(user_id_np)
            
            actual_warehouse = target_whs if target_whs and WAREHOUSE == "GOOD_WHS" else WAREHOUSE
            
            real_filename, file_path = _dispatch_extraction_job(page, TIMEOUT_MS, actual_warehouse, ext_ui_log, browser, dry_run)
            
            if dry_run:
                ext_ui_log("DRY_RUN", "Dry run complete - extraction skipped.")
                return pd.DataFrame(), ""
                
            ext_ui_log("SYS", f"Parsing payload file: {real_filename}...")
            
            df_ext = None
            if real_filename.lower().endswith('.zip'):
                with zipfile.ZipFile(file_path) as z:
                    target = next((n for n in z.namelist() if "INVT_MASTER" in n and n.lower().endswith((".csv", ".txt"))), None)
                    if not target: target = next((n for n in z.namelist() if n.lower().endswith((".csv", ".txt"))), None)
                    if target:
                        ext_ui_log("SYS", f"ZIP target identified: {target}")
                        with z.open(target) as f:
                            df_ext = pd.read_csv(f, sep='\t', dtype=str, on_bad_lines='skip')
                            if df_ext.shape[1] <= 1: f.seek(0); df_ext = pd.read_csv(f, sep=',', dtype=str, on_bad_lines='skip')
            elif real_filename.lower().endswith(('.xls', '.xlsx')): 
                df_ext = pd.read_excel(file_path, dtype=str)
            else:
                for enc in ['utf-8', 'iso-8859-1', 'cp1252']:
                    for separator in ['\t', ',', ';', '|']:
                        try:
                            temp_df = pd.read_csv(file_path, sep=separator, dtype=str, encoding=enc, on_bad_lines='skip')
                            if temp_df is not None and temp_df.shape[1] > 1: df_ext = temp_df; break
                        except Exception: continue
                    if df_ext is not None and df_ext.shape[1] > 1: break

            # Cleanup temp file after reading
            try:
                os.remove(file_path)
            except OSError:
                pass

            if df_ext is not None and not df_ext.empty and df_ext.shape[1] > 1:
                df_ext.columns = [str(c).strip() for c in df_ext.columns]
                ext_ui_log("SUCCESS", f"Payload Secured! {len(df_ext)} items loaded. Flushing to session...")
                st.session_state.np_df = df_ext
                database.log_extraction_history(supabase, selected_distributor, current_user)
                st.session_state.is_bot_running = False
                st.rerun()
            else: 
                st.session_state.is_bot_running = False
                ext_ui_log("ERROR", "DataFrame validation failed.")
                st.error("Gagal membaca file dari server.")
                alert_callback(f"[WARN] <b>EXTRACT FAILED</b>\nUser: {current_user}\nDist: {selected_distributor}\nReason: Invalid DataFrame")
                
    except PlaywrightTimeoutError: 
        st.session_state.is_bot_running = False
        ext_ui_log("ERROR", "TIMEOUT: Server tidak merespon.")
        st.error("Operation Timeout.")
        alert_callback(f"[ALERT] <b>EXTRACT TIMEOUT</b>\nUser: {current_user}\nDist: {selected_distributor}\nReason: Playwright Timeout")
    except Exception as e: 
        st.session_state.is_bot_running = False
        ext_ui_log("ERROR", f"SYSTEM FAILURE: {str(e).split(chr(10))[0]}")
        st.error(f"System error: {e}")
        alert_callback(f"[ALERT] <b>SYSTEM ERROR (EXTRACT)</b>\nDist: {selected_distributor}\nError: <code>{str(e)[:100]}</code>", getattr(e, "screenshot_path", None))

def _dispatch_sales_job(page, TIMEOUT_MS, start_date, end_date, ui_log, browser, dry_run=False):
    ui_log("NAV", "Initiating sales export job sequence...")
    # The _navigate_to_import_export function already clicked Add Job, so we are now on the New General page.
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_TYPE_Value").wait_for(state="visible", timeout=TIMEOUT_MS)
    
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_TYPE_Value").select_option("E")
    page.wait_for_timeout(1000)
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_DESC_Value").fill("Invoice Detail")
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_TIMEOUT_Value").fill("9999999")
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_EXE_TYPE_Value").select_option("M")
    page.wait_for_timeout(1000)
    
    page.locator("id=pag_FW_SYS_INTF_JOB_RootNew_btn_Next_Value").click(force=True)
    _wait_for_page_ready(page, TIMEOUT_MS, ui_log, "sales Next")
    page.wait_for_timeout(2000)
    page.locator("id=pag_FW_DisclaimerMessage_btn_okay_Value").wait_for(state="visible", timeout=TIMEOUT_MS)
    page.locator("id=pag_FW_DisclaimerMessage_btn_okay_Value").click(force=True)
    _wait_for_page_ready(page, TIMEOUT_MS, ui_log, "sales disclaimer")
    page.wait_for_timeout(2000)
    
    interfaces = [
        {"id": "E_28880804000000001", "status": "Invoiced"},
        {"id": "E_28880804000000000", "status": "Invoiced"},
        {"id": "E_28880804000000002", "status": "I"},
        {"id": "E_28880804000000003", "status": "I"},
        {"id": "E_28880804000000006", "status": None}
    ]
    
    for idx, intf in enumerate(interfaces):
        intf_id = intf["id"]
        status_val = intf["status"]
        
        ui_log("INJECT", f"Binding interface target {idx+1}/{len(interfaces)}: {intf_id}")
        
        if idx > 0:
            ui_log("SYS", "Triggering NEW interface formulation...")
            page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_btn_New_Value").click(force=True)
            page.wait_for_timeout(2000)
            
        page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_INTF_ID_SelectButton").click(force=True)
        page.wait_for_timeout(2000)
        
        # Target elements in the interface selection popup - slow loading popups on laggy server
        page.locator("id=pop_Dynamic_gft_List_2_FilterField_Value").wait_for(state="visible", timeout=max(TIMEOUT_MS, 180000))
        page.locator("id=pop_Dynamic_gft_List_2_FilterField_Value").fill(intf_id)
        page.locator("id=pop_Dynamic_grd_Main_SearchForm_ButtonSearch_Value").click(force=True)
        page.wait_for_timeout(2000)
        page.locator("id=pop_Dynamic_grd_Main_ctl02_DynCol_INTF_ID_Value").click(force=True)
        _wait_for_page_ready(page, TIMEOUT_MS, ui_log, f"sales intf select {intf_id}")
        page.wait_for_timeout(2000)
        
        ui_log("INJECT", f"Applying parameters for {intf_id}")
        page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_FILE_TYPE_Value").select_option("D")
        page.wait_for_timeout(1500)
        page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_FLD_SEPARATOR_STD_Value_0").check()
        page.wait_for_timeout(1500)
        
        if status_val:
            drps = page.locator("select[id$='_dyn_Field_drp_Value']")
            drps.first.wait_for(state="attached", timeout=5000)
            success = False
            for i in range(drps.count()):
                try:
                    drps.nth(i).select_option(status_val, timeout=2000)
                    success = True
                    break
                except:
                    pass
            if success:
                ui_log("SYS", f"Waiting for server to apply {status_val} filter (PostBack)...")
                page.wait_for_timeout(3500)
        
        # Use JavaScript to directly set dates via CalendarExtender API
        # By querying suffix '_dyn_Field_dat_Value', we don't need to hardcode ctl15/ctl16
        ui_log("INJECT", f"Setting date range: {start_date} to {end_date}")
        sd_d, sd_m, sd_y = start_date.split('/')
        ed_d, ed_m, ed_y = end_date.split('/')
        
        page.evaluate(f"""() => {{
            function setCalDate(el, dateStr, day, month, year) {{
                if (el) {{
                    el.value = dateStr;
                    el.dispatchEvent(new Event('change', {{bubbles: true}}));
                }}
                try {{
                    var extId = el.id + "_ajax_CalendarExtender";
                    var ce = $find(extId);
                    if (ce) {{
                        ce._selectedDate = new Date(year, month - 1, day);
                        ce._textbox.set_Value(dateStr);
                    }}
                }} catch(e) {{}}
            }}
            
            var dateInputs = document.querySelectorAll('input[id$="_dyn_Field_dat_Value"]');
            if(dateInputs.length >= 2) {{
                setCalDate(dateInputs[0], '{start_date}', {int(sd_d)}, {int(sd_m)}, {int(sd_y)});
                setCalDate(dateInputs[1], '{end_date}', {int(ed_d)}, {int(ed_m)}, {int(ed_y)});
            }} else if(dateInputs.length === 1) {{
                // fallback if only 1 date field exists
                setCalDate(dateInputs[0], '{start_date}', {int(sd_d)}, {int(sd_m)}, {int(sd_y)});
            }}
        }}""")
        page.wait_for_timeout(1500)
        
        page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_btn_Add_Value").click(force=True)
        page.wait_for_timeout(2000)
        
    ui_log("SERVER", "Executing multi-interface job sequence...")
    if dry_run:
        ui_log("DRY_RUN", "Dry run active - bypassed save click")
        return None, None
    page.locator("id=pag_FW_SYS_INTF_JOB_RootNew_btn_Save_Value").click(force=True)
    page.wait_for_timeout(2000)
    
    ui_log("SERVER", "Awaiting server confirmation prompt...")
    page.locator("id=TF_Prompt_btn_Ok_Value").wait_for(state="visible", timeout=TIMEOUT_MS)
    page.locator("id=TF_Prompt_btn_Ok_Value").click(force=True)
    
    ui_log("SERVER", "Awaiting file synthesis...")
    with page.expect_download(timeout=240000) as download_info:
        download_btn = page.locator("id=pag_FW_SYS_INTF_STATUS_JOB_btn_Download_Value")
        download_btn.wait_for(state="visible", timeout=240000)
        download_btn.click(force=True)
    
    download = download_info.value
    real_filename = download.suggested_filename
    file_path = f"temp_sales_{real_filename}"
    ui_log("SUCCESS", f"Download captured: {real_filename}. Saving to environment...")
    download.save_as(file_path)
    
    return real_filename, file_path

def run_sales_extract(user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, start_date, end_date, ext_ui_log, alert_callback, supabase, current_user, dry_run=None):
    if dry_run is None: dry_run = st.session_state.get('dry_run_enabled', False)
    try:
        with managed_browser_session(user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, ext_ui_log) as (page, browser):
            _navigate_to_import_export(page, TIMEOUT_MS, ext_ui_log)
            real_filename, file_path = _dispatch_sales_job(page, TIMEOUT_MS, start_date, end_date, ext_ui_log, browser, dry_run)
            if dry_run:
                ext_ui_log("DRY_RUN", "Dry run complete - extraction skipped.")
                st.session_state.sales_csv_data = None
                st.session_state.sales_csv_name = ""
                return True
            
            ext_ui_log("SYS", "Browser closed. Ready for download.")
            
            with open(file_path, "rb") as f:
                st.session_state.sales_csv_data = f.read()
                st.session_state.sales_csv_filename = real_filename

            # Cleanup temp file after reading
            try:
                os.remove(file_path)
            except OSError:
                pass
                
            database.log_extraction_history(supabase, selected_distributor, current_user, status="Success (Sales)")
            st.session_state.is_bot_running = False
            st.rerun()
                
    except PlaywrightTimeoutError: 
        st.session_state.is_bot_running = False
        ext_ui_log("ERROR", "TIMEOUT: Server tidak merespon.")
        st.error("Operation Timeout.")
        alert_callback(f"[ALERT] <b>SALES EXTRACT TIMEOUT</b>\nUser: {current_user}\nDist: {selected_distributor}")
    except Exception as e: 
        st.session_state.is_bot_running = False
        ext_ui_log("ERROR", f"SYSTEM FAILURE: {str(e).split(chr(10))[0]}")
        st.error(f"System error: {e}")
        alert_callback(f"[ALERT] <b>SYSTEM ERROR (SALES EXTRACT)</b>\nDist: {selected_distributor}\nError: <code>{str(e)[:100]}</code>", getattr(e, "screenshot_path", None))

def _navigate_to_stock_adjustment(page, TIMEOUT_MS, WAREHOUSE, REASON_CODE, ui_log, remark_text=""):
    ui_log("NAV", "Navigating to Stock Adjustment module...")
    page.wait_for_timeout(3000)
    page.locator("id=pag_InventoryRoot_tab_Main_itm_StkAdj").first.dispatch_event("click")
    _wait_for_page_ready(page, TIMEOUT_MS, ui_log, "StockAdj menu")
    
    add_btn = page.locator("id=pag_I_StkAdj_btn_Add_Value")
    add_btn.wait_for(state="attached", timeout=TIMEOUT_MS)
    add_btn.click(force=True)
    
    warehouse_link = page.locator(f"a:text-is('{WAREHOUSE}')").first
    warehouse_link.wait_for(state="visible", timeout=TIMEOUT_MS)
    warehouse_link.click(force=True)
    
    page.locator("id=pag_I_StkAdj_NewGeneral_sel_PRD_CD_Value").wait_for(state="visible")
    
    dropdown = page.locator("id=pag_I_StkAdj_NewGeneral_drp_n_REASON_HDR_Value")
    if dropdown.is_enabled(): 
        dropdown.select_option(REASON_CODE)
        
    if remark_text:
        remark_input = page.locator("id=pag_I_StkAdj_NewGeneral_txt_REMARK_Value")
        if remark_input.is_enabled():
            remark_input.fill(remark_text[:50])
            
    ui_log("SYS", "Ready. Opening data stream for payload injection...")

def _inject_adjustment_row(page, sku, qty, TIMEOUT_MS, ui_log):
    sku_input = page.locator("id=pag_I_StkAdj_NewGeneral_sel_PRD_CD_Value")
    ui_log("INJECT", f"Locking target node for SKU [{sku}]...")
    sku_input.fill(sku)
    ui_log("INJECT", "Triggering system lookup (Tab event)...")
    sku_input.press("Tab")
    page.wait_for_timeout(1500)
    
    qty_input = page.locator("id=pag_I_StkAdj_NewGeneral_txt_QTY1_Value")
    qty_input.wait_for(state="visible", timeout=TIMEOUT_MS)
    
    # For negative adjustments, cross-check live available stock on screen
    if qty.startswith('-'):
        try:
            ui_log("INJECT", "Negative adjustment detected. Verifying live screen stock...")
            stock_lbl = page.locator("id=pag_I_StkAdj_NewGeneral_lbl_Adjustable_Qty_Value")
            stock_lbl.wait_for(state="visible", timeout=5000)
            stock_text = stock_lbl.inner_text().strip().upper()
            
            req_qty = abs(int(qty))
            numbers = re.findall(r'\d+', stock_text)
            is_zero = not numbers or all(int(n) == 0 for n in numbers)
            
            insufficient = False
            if is_zero:
                insufficient = True
            elif 'PAC' not in stock_text and 'CAR' not in stock_text:
                match = re.search(r'(\d+)\s*EA', stock_text)
                if match:
                    live_ea = int(match.group(1))
                    if live_ea < req_qty:
                        insufficient = True
            
            if insufficient:
                raise Exception(f"Insufficient Stock (Has {stock_text}, wants {qty} EA)")
        except Exception as e:
            if "Insufficient" in str(e):
                raise e
            
    ui_log("INJECT", f"Node resolved. Assigning adjustment quantity: {qty} EA")
    qty_input.fill(qty)
    page.wait_for_timeout(500)
    
    ui_log("INJECT", "Dispatching Add command to grid...")
    page.locator("id=pag_I_StkAdj_NewGeneral_btn_Add_Value").click(force=True)
    _wait_for_page_ready(page, TIMEOUT_MS, ui_log, "stkadj add")
    ui_log("SYS", "Awaiting DOM form reset confirmation...")
    page.wait_for_function("document.getElementById('pag_I_StkAdj_NewGeneral_sel_PRD_CD_Value').value === ''", timeout=TIMEOUT_MS)


def _render_progress_label(placeholder, dist, user, current, total):
    """Render the Active Account / Processed progress label above the terminal."""
    if not placeholder:
        return
    with placeholder.container():
        c1, c2, c3 = st.columns([5, 2, 3], vertical_alignment="center")
        with c1:
            st.markdown(f"""
                <div id='terminate-target-col' style='display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-top: 8px;'>
                    <div style='background: #0068C9; color: #FFFFFF; font-family: "Source Sans 3", sans-serif; font-size: 0.85rem; font-weight: 800; padding: 6px 12px; border: 2px solid #0F172A; box-shadow: 3px 3px 0px 0px #0F172A; text-transform: uppercase; letter-spacing: 0.05em;'>ACTIVE ACCOUNT</div>
                    <div style='background: #FFFFFF; color: #0F172A; font-family: "Source Sans 3", sans-serif; font-size: 0.85rem; font-weight: 800; padding: 6px 12px; border: 2px solid #0F172A; box-shadow: 3px 3px 0px 0px #0F172A; text-transform: uppercase; letter-spacing: 0.05em;'>{dist} ({user})</div>
                </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown("<div id='terminate-btn-anchor'></div>", unsafe_allow_html=True)
            def terminate_callback():
                st.session_state.is_bot_running = False
                st.session_state.execute_done = False
                
            st.button("TERMINATE", key=f"term_bot_{current}_{total}", use_container_width=True, type="primary", on_click=terminate_callback)
        with c3:
            st.markdown(f"""
                <div style='display: flex; align-items: center; gap: 12px; flex-wrap: wrap; justify-content: flex-end; margin-top: 8px;'>
                    <div style='background: #FFDE59; color: #0F172A; font-family: "Source Sans 3", sans-serif; font-size: 0.85rem; font-weight: 800; padding: 6px 12px; border: 2px solid #0F172A; box-shadow: 3px 3px 0px 0px #0F172A; text-transform: uppercase; letter-spacing: 0.05em;'>PROCESSED</div>
                    <div style='background: #FFFFFF; color: #0F172A; font-family: "Source Sans 3", sans-serif; font-size: 0.85rem; font-weight: 800; padding: 6px 12px; border: 2px solid #0F172A; box-shadow: 3px 3px 0px 0px #0F172A; text-transform: uppercase; letter-spacing: 0.05em;'>{current}/{total}</div>
                </div>
            """, unsafe_allow_html=True)


def _log_df_to_supabase(supabase, df_view, bot_user, current_user, qty_col='Qty', pack_mode=False):
    """Log all non-Invalid rows from df_view to the adjustment_logs table."""
    if not supabase:
        return
    for _, row in df_view.iterrows():
        if row.get('Status') == 'Invalid':
            continue
        sku = str(row['SKU']).strip()
        status = str(row['Status']).strip()
        ket = str(row.get('Keterangan', '')).strip()
        if pack_mode:
            pac = str(row.get('PAC', 0)).strip()
            car = str(row.get('CAR', 0)).strip()
            ea = str(row.get('EA', 0)).strip()
            qty = f"PAC:{pac} CAR:{car} EA:{ea}"
        else:
            try:
                q_raw = row.get(qty_col, 0)
                if pd.isna(q_raw): qty = ''
                else:
                    f = float(q_raw)
                    qty = str(int(f)) if f.is_integer() else str(f)
            except:
                qty = str(row.get(qty_col, '')).strip()
        try:
            database.log_adjustment(supabase, sku, qty, status, ket, bot_user, run_by=current_user)
        except Exception:
            pass


def run_execution(df_view, bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, WAREHOUSE, REASON_CODE, TABLE_UPDATE_INTERVAL, ui_log, alert_callback, table_placeholder, log_label_placeholder, supabase, current_user=None, dry_run=None):
    if dry_run is None: dry_run = st.session_state.get('dry_run_enabled', False)
    ensure_playwright()
    global_start_time = time.time(); success_count, failed_count = 0, 0
    ui_log("SYS", "Allocating memory and initializing Chromium headless core...")
    if supabase: ui_log("SYS", "Supabase client active.")

    alert_callback(f"<b>BOT STARTED</b>\nTask: Reconcile Stock\nDist: {selected_distributor}\nTotal SKU: {len(df_view)}")

    try:
        with managed_browser_session(bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, ui_log) as (page, browser):
            # Fetch distributor exception from DB
            exception_dict = database.get_distributor_warehouse_exceptions(supabase)
            target_whs = exception_dict.get(bot_user)
            actual_warehouse = target_whs if target_whs and WAREHOUSE == "GOOD_WHS" else WAREHOUSE
            
            _navigate_to_stock_adjustment(page, TIMEOUT_MS, actual_warehouse, REASON_CODE, ui_log)

            progress_bar = st.progress(0)
            total_rows = len(df_view)
            _render_progress_label(log_label_placeholder, selected_distributor, bot_user, 0, total_rows)
            
            for i, (idx, row) in enumerate(df_view.iterrows()):
                _render_progress_label(log_label_placeholder, selected_distributor, bot_user, i + 1, total_rows)
                sku = str(row['SKU']).strip()

                if row.get('Status') == 'Invalid':
                    ui_log("WARN", f"SKU [{sku}] skipped: {row.get('Keterangan', 'Invalid Qty')}")
                    if supabase:
                        try:
                            database.log_adjustment(supabase, sku, str(row.get('Qty')), "Invalid", f"Skipped: {row.get('Keterangan')}", bot_user, run_by=current_user)
                        except Exception:
                            pass
                    progress_bar.progress((i+1)/total_rows)
                    if i % TABLE_UPDATE_INTERVAL == 0 or i == total_rows-1:
                        utils.render_neo_table(table_placeholder, df_view)
                    continue

                try: qty = str(int(float(row['Qty'])))
                except Exception: qty = str(row['Qty']).strip()

                ui_log("INJECT", f"Processing Payload {i+1}/{total_rows} | Target SKU: [{sku}]")
                try:
                    _inject_adjustment_row(page, sku, qty, TIMEOUT_MS, ui_log)
                    
                    df_view.at[idx, 'Status'] = 'Success'
                    df_view.at[idx, 'Keterangan'] = f'Input {qty} EA'
                    success_count += 1
                    ui_log("SUCCESS", f"Transaction {i+1} committed. Grid updated.")
                except Exception as loop_err: 
                    err_msg = str(loop_err)
                    df_view.at[idx, 'Status'] = 'Failed'
                    
                    if "Insufficient" in err_msg:
                        df_view.at[idx, 'Keterangan'] = 'Insufficient Stock'
                        failed_count += 1
                        ui_log("ERROR", f"Failed on SKU [{sku}]: {err_msg}. Skipping.")
                    else:
                        df_view.at[idx, 'Keterangan'] = 'Node Timeout'
                        failed_count += 1
                        ui_log("ERROR", f"Timeout on SKU [{sku}]. Node unresponsive. Skipping.")
                    
                progress_bar.progress((i+1)/total_rows)
                if i % TABLE_UPDATE_INTERVAL == 0 or i == total_rows-1: 
                    utils.render_neo_table(table_placeholder, df_view)
                    
            if failed_count > 0:
                ui_log("SERVER", f"Aborting save. {failed_count} failures detected. Document will not be written to database.")
                _log_df_to_supabase(supabase, df_view, bot_user, current_user)
            else:
                ui_log("SERVER", "Finalizing batch. Saving document to main server...")
                if dry_run:
                    ui_log("DRY_RUN", "Dry run active - bypassed save click")
                    # Fallback to update statuses directly
                    for idx, row in df_view.iterrows():
                        if row.get('Status') == 'Success':
                            df_view.at[idx, 'Keterangan'] = "Input successfully (Dry Run)"
                    utils.render_neo_table(table_placeholder, df_view)
                    ui_log("AUTH", "Initiating system logout sequence...")
                    page.once("dialog", lambda dialog: dialog.accept())
                    page.locator("id=btnLogout").click(timeout=10000)
                    browser.close()
                    elapsed = int(time.time() - global_start_time)
                    box_html = utils.make_success_box(f"DRY RUN SUCCESS — Processed: {success_count} | Time: {elapsed//60}m {elapsed%60}s")
                    st.markdown(box_html, unsafe_allow_html=True)
                    alert_callback(f"[OK] <b>DRY RUN FINISHED</b>\nDist: {selected_distributor}\nSuccess: {success_count} | Failed: {failed_count}\nRuntime: {elapsed//60}m {elapsed%60}s")
                    st.session_state.is_bot_running = False
                    return success_count, failed_count, elapsed
                page.locator("id=pag_I_StkAdj_NewGeneral_btn_Save_Value").click()
                _wait_for_page_ready(page, TIMEOUT_MS, ui_log, "stkadj save")
                try: 
                    yes_btn = page.locator("id=pag_PopUp_YesNo_btn_Yes_Value")
                    yes_btn.wait_for(state="visible", timeout=5000)
                    ui_log("SERVER", "Confirming save dialog...")
                    yes_btn.click()
                    _wait_for_page_ready(page, TIMEOUT_MS, ui_log, "stkadj save yes")
                    ui_log("SERVER", "Document physically written to database.")
                except Exception: 
                    ui_log("SERVER", "Auto-save confirmed. Document written to database.")
                    
                ui_log("SYS", "Holding session for 5 seconds to ensure Newspage database write...")
                page.wait_for_timeout(5000)

                ui_log("SUCCESS", "Document saved successfully!")

                # Update descriptions in df_view
                for idx, row in df_view.iterrows():
                    if row.get('Status') == 'Success':
                        try:
                            q_raw = row.get('Qty', 0)
                            if pd.isna(q_raw): q = ''
                            else:
                                f = float(q_raw)
                                q = str(int(f)) if f.is_integer() else str(f)
                        except:
                            q = str(row.get('Qty', '')).strip()
                        df_view.at[idx, 'Keterangan'] = f"Input {q} EA"

                _log_df_to_supabase(supabase, df_view, bot_user, current_user)

                # Refresh the final dataframe view in the UI
                utils.render_neo_table(table_placeholder, df_view)
            
            ui_log("AUTH", "Initiating system logout sequence...")
            try:
                page.once("dialog", lambda dialog: dialog.accept())
                page.locator("id=btnLogout").click(timeout=10000)
                _wait_for_page_ready(page, TIMEOUT_MS, ui_log, "logout")
                ui_log("AUTH", "Pop up confirm logout...")
                page.wait_for_timeout(2000)
                ui_log("SUCCESS", "Logged out successfully.")
            except Exception as e:
                ui_log("ERROR", "Logout button not found or timeout.")
                
            ui_log("SYS", "Closing browser and releasing memory...")
            browser.close()
            elapsed = int(time.time() - global_start_time)
            
            if failed_count > 0:
                ui_log("ERROR", f"Aborted. Total runtime: {elapsed//60}m {elapsed%60}s")
                box_html = utils.make_error_box(f"ABORTED — Success: {success_count} | Failed: {failed_count} | Time: {elapsed//60}m {elapsed%60}s")
                st.markdown(box_html, unsafe_allow_html=True)
                failed_skus = df_view[df_view["Status"] == "Failed"]["SKU"].tolist()
                sku_str = ("\nFailed SKUs: " + ", ".join(failed_skus[:5]) + ("..." if len(failed_skus) > 5 else "")) if failed_skus else ""
                alert_callback(f"[WARNING] <b>BOT ABORTED</b>\nDist: {selected_distributor}\nSuccess: {success_count} | Failed: {failed_count}\nRuntime: {elapsed//60}m {elapsed%60}s{sku_str}")
                st.toast('Execution aborted due to errors!', icon="🚨")
            else:
                ui_log("SUCCESS", f"Complete. Total runtime: {elapsed//60}m {elapsed%60}s")
                box_html = utils.make_success_box(f"SUCCESS — Processed: {success_count} | Time: {elapsed//60}m {elapsed%60}s")
                alert_msg = f"[OK] <b>BOT FINISHED</b>\nDist: {selected_distributor}\nSuccess: {success_count} | Failed: {failed_count}\nRuntime: {elapsed//60}m {elapsed%60}s"
                st.markdown(box_html, unsafe_allow_html=True)
                alert_callback(alert_msg)
                st.toast('System override complete!')
                st.session_state.reconcile_result = None

            st.session_state.is_bot_running = False

    except Exception as e:
        st.session_state.is_bot_running = False
        st.error("System halted.")
        ui_log("ERROR", f"FAILURE: {e}")
        alert_callback(f"[ALERT] <b>FATAL ERROR (EXECUTE)</b>\nDist: {selected_distributor}\nError: <code>{str(e)[:100]}</code>", getattr(e, "screenshot_path", None))

# --- PROMOTION SYNC ENGINE ---

def _dispatch_promotion_job(page, TIMEOUT_MS, start_date, end_date, ui_log, browser, dry_run=False):
    promo_ids = [
        "E_20150417000000043", "E_20150417000000044", 
        "E_20150417000000050", "E_20150417000000048", 
        "E_20150417000000093"
    ]
    
    ui_log("NAV", "Initiating promotion sync job sequence...")
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_TYPE_Value").wait_for(state="visible", timeout=TIMEOUT_MS)
    
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_TYPE_Value").select_option("E")
    page.wait_for_timeout(1000)
    job_desc = f"PROMO_SYNC_{time.strftime('%Y%m%d_%H%M%S')}"
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_DESC_Value").fill(job_desc)
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_TIMEOUT_Value").fill("9999999")
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_EXE_TYPE_Value").select_option("M")
    page.wait_for_timeout(1000)
    
    page.locator("id=pag_FW_SYS_INTF_JOB_RootNew_btn_Next_Value").click(force=True)
    _wait_for_page_ready(page, TIMEOUT_MS, ui_log, "promo Next")
    page.wait_for_timeout(2000)
    page.locator("id=pag_FW_DisclaimerMessage_btn_okay_Value").wait_for(state="visible", timeout=TIMEOUT_MS)
    page.locator("id=pag_FW_DisclaimerMessage_btn_okay_Value").click(force=True)
    _wait_for_page_ready(page, TIMEOUT_MS, ui_log, "promo disclaimer")
    page.wait_for_timeout(2000)

    for i, target_id in enumerate(promo_ids):
        ui_log("INJECT", f"[{i+1}/{len(promo_ids)}] Binding interface: {target_id}")
        page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_INTF_ID_SelectButton").click(force=True)
        page.wait_for_timeout(2000)
        
        # Popup selection - slow loading popups on laggy server
        page.locator("id=pop_Dynamic_gft_List_2_FilterField_Value").wait_for(state="visible", timeout=max(TIMEOUT_MS, 180000))
        page.locator("id=pop_Dynamic_gft_List_2_FilterField_Value").fill(target_id)
        page.locator("id=pop_Dynamic_grd_Main_SearchForm_ButtonSearch_Value").click(force=True)
        page.wait_for_timeout(2000)
        page.get_by_text(target_id, exact=True).click(force=True)
        _wait_for_page_ready(page, TIMEOUT_MS, ui_log, f"promo intf select [{i+1}]")
        page.wait_for_timeout(2000)
        
        ui_log("INJECT", f"[{i+1}/{len(promo_ids)}] Setting file params and dates...")
        page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_FILE_TYPE_Value").select_option("D")
        page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_FLD_SEPARATOR_STD_Value_0").check()
        
        # JS Date Injection
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
                'pag_FW_SYS_INTF_JOB_DTL_PopupNew_grd_DynamicFilter_ctl03_dyn_Field_dat_Value',
                'pag_FW_SYS_INTF_JOB_DTL_PopupNew_grd_DynamicFilter_ctl03_dyn_Field_dat_ajax_CalendarExtender',
                {int(sd_d)}, {int(sd_m)}, {int(sd_y)}, '{start_date}'
            );
            setCalDate(
                'pag_FW_SYS_INTF_JOB_DTL_PopupNew_grd_DynamicFilter_ctl04_dyn_Field_dat_Value',
                'pag_FW_SYS_INTF_JOB_DTL_PopupNew_grd_DynamicFilter_ctl04_dyn_Field_dat_ajax_CalendarExtender',
                {int(ed_d)}, {int(ed_m)}, {int(ed_y)}, '{end_date}'
            );
        }}""")
        page.wait_for_timeout(1000)
        
        ui_log("INJECT", f"[{i+1}/{len(promo_ids)}] Committing interface to queue...")
        page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_btn_Add_Value").click(force=True)
        _wait_for_page_ready(page, TIMEOUT_MS, ui_log, f"promo Add commit [{i+1}]")
        page.wait_for_timeout(2000)
        
        if i < len(promo_ids) - 1:
            ui_log("NAV", "Preparing next interface slot...")
            page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_btn_New_Value").click(force=True)
            page.wait_for_timeout(2000)

    ui_log("SERVER", "Executing multi-interface job...")
    if dry_run:
        ui_log("DRY_RUN", "Dry run active - bypassed save click")
        return None, None
    page.locator("id=pag_FW_SYS_INTF_JOB_RootNew_btn_Save_Value").click(force=True)
    page.wait_for_timeout(2000)
    
    ui_log("SERVER", "Awaiting server confirmation...")
    page.locator("id=TF_Prompt_btn_Ok_Value").wait_for(state="visible", timeout=TIMEOUT_MS)
    page.locator("id=TF_Prompt_btn_Ok_Value").click(force=True)
    
    ui_log("SERVER", "Intercepting batch download...")
    with page.expect_download(timeout=300000) as download_info:
        download_btn = page.locator("id=pag_FW_SYS_INTF_STATUS_JOB_btn_Download_Value")
        download_btn.wait_for(state="visible", timeout=300000)
        download_btn.click(force=True)
    
    download = download_info.value
    real_filename = download.suggested_filename
    file_path = f"temp_promo_{real_filename}"
    ui_log("SUCCESS", f"Download captured: {real_filename}")
    download.save_as(file_path)
    
    return real_filename, file_path

def run_promotion_sync(user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, start_date, end_date, ext_ui_log, alert_callback, supabase, current_user, dry_run=None):
    if dry_run is None: dry_run = st.session_state.get('dry_run_enabled', False)
    ensure_playwright()
    try:
        with managed_browser_session(user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, ext_ui_log) as (page, browser):
            _navigate_to_import_export(page, TIMEOUT_MS, ext_ui_log)
            real_filename, file_path = _dispatch_promotion_job(page, TIMEOUT_MS, start_date, end_date, ext_ui_log, browser, dry_run)
            if dry_run:
                ext_ui_log("DRY_RUN", "Dry run complete - sync skipped.")
                st.session_state.promo_csv_data = None
                st.session_state.promo_csv_name = ""
                return True
            
            with open(file_path, "rb") as f:
                st.session_state.promo_zip_data = f.read()
                st.session_state.promo_zip_filename = real_filename

            try:
                os.remove(file_path)
            except OSError:
                pass
                
            st.session_state.is_promo_bot_running = False
            st.rerun()
                
    except PlaywrightTimeoutError: 
        st.session_state.is_promo_bot_running = False
        ext_ui_log("ERROR", "TIMEOUT: Server tidak merespon.")
        st.error("Operation Timeout.")
    except Exception as e: 
        st.session_state.is_promo_bot_running = False
        ext_ui_log("ERROR", f"SYSTEM FAILURE: {str(e)}")
        st.error(f"System error: {e}")


def _inject_manual_adjustment_row(page, sku, pac, car, ea, TIMEOUT_MS, ui_log):
    sku_input = page.locator("id=pag_I_StkAdj_NewGeneral_sel_PRD_CD_Value")
    ui_log("INJECT", f"Locking target node for SKU [{sku}]...")
    sku_input.fill(sku)
    ui_log("INJECT", "Triggering system lookup (Tab event)...")
    sku_input.press("Tab")
    page.wait_for_timeout(1500)
    
    if str(pac).strip() and str(pac).strip() != '0':
        pac_input = page.locator("id=pag_I_StkAdj_NewGeneral_txt_QTY3_Value")
        pac_input.wait_for(state="visible", timeout=TIMEOUT_MS)
        ui_log("INJECT", f"Assigning PAC quantity: {pac}")
        pac_input.fill(str(pac))
        
    if str(car).strip() and str(car).strip() != '0':
        car_input = page.locator("id=pag_I_StkAdj_NewGeneral_txt_QTY2_Value")
        car_input.wait_for(state="visible", timeout=TIMEOUT_MS)
        ui_log("INJECT", f"Assigning CAR quantity: {car}")
        car_input.fill(str(car))
        
    if str(ea).strip() and str(ea).strip() != '0':
        ea_input = page.locator("id=pag_I_StkAdj_NewGeneral_txt_QTY1_Value")
        ea_input.wait_for(state="visible", timeout=TIMEOUT_MS)
        ui_log("INJECT", f"Assigning EA quantity: {ea}")
        ea_input.fill(str(ea))
        
    ui_log("INJECT", "Dispatching Add command to grid...")
    page.locator("id=pag_I_StkAdj_NewGeneral_btn_Add_Value").click(force=True)
    _wait_for_page_ready(page, TIMEOUT_MS, ui_log, "manual stkadj add")
    ui_log("SYS", "Awaiting DOM form reset confirmation...")
    page.wait_for_function("document.getElementById('pag_I_StkAdj_NewGeneral_sel_PRD_CD_Value').value === ''", timeout=TIMEOUT_MS)

def run_execution_manual(df_view, bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, WAREHOUSE, REASON_CODE, TABLE_UPDATE_INTERVAL, ui_log, alert_callback, table_placeholder, log_label_placeholder, supabase, remark_text="", progress_placeholder=None, show_status_box=True, current_user=None, dry_run=None):
    if dry_run is None: dry_run = st.session_state.get('dry_run_enabled', False)
    ensure_playwright()
    try:
        global_start_time = time.time()
        success_count, failed_count = 0, 0
        
        with managed_browser_session(bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, ui_log) as (page, browser):
            # Resolve actual warehouse from distributor_exceptions
            exception_dict = database.get_distributor_warehouse_exceptions(supabase)
            target_whs = exception_dict.get(bot_user)
            actual_warehouse = target_whs if target_whs and WAREHOUSE == "GOOD_WHS" else WAREHOUSE
            
            _navigate_to_stock_adjustment(page, TIMEOUT_MS, actual_warehouse, REASON_CODE, ui_log, remark_text)
            
            total_rows = len(df_view)
            _render_progress_label(log_label_placeholder, selected_distributor, bot_user, 0, total_rows)
            
            for i, (idx, row) in enumerate(df_view.iterrows()):
                _render_progress_label(log_label_placeholder, selected_distributor, bot_user, i + 1, total_rows)
                if progress_placeholder:
                    progress_placeholder.progress((i + 1) / total_rows)
                def fmt(v):
                    try:
                        if pd.isna(v): return ''
                        f = float(v)
                        if f == 0: return ''
                        return str(int(f)) if f.is_integer() else str(f)
                    except:
                        return str(v).strip()

                sku = str(row['SKU']).strip()
                pac = fmt(row.get('PAC', 0))
                car = fmt(row.get('CAR', 0))
                ea = fmt(row.get('EA', 0))
                
                # Fallback: if PAC, CAR, and EA are all empty, but Qty is present in the row, use Qty as EA
                if not pac and not car and not ea and 'Qty' in row:
                    ea = fmt(row['Qty'])

                ui_log("INJECT", f"Processing Payload {i+1}/{total_rows} | Target SKU: [{sku}]")
                try:
                    _inject_manual_adjustment_row(page, sku, pac, car, ea, TIMEOUT_MS, ui_log)
                    
                    df_view.at[idx, 'Status'] = 'Success'
                    df_view.at[idx, 'Keterangan'] = 'Input successfully'
                    success_count += 1
                    ui_log("SUCCESS", f"Transaction {i+1} committed. Grid updated.")
                except Exception as loop_err: 
                    err_msg = str(loop_err)
                    df_view.at[idx, 'Status'] = 'Failed'
                    df_view.at[idx, 'Keterangan'] = 'Node Timeout'
                    failed_count += 1
                    ui_log("ERROR", f"Timeout on SKU [{sku}]. Node unresponsive. Skipping.")
                    
                if i % TABLE_UPDATE_INTERVAL == 0 or i == total_rows-1: 
                    utils.render_neo_table(table_placeholder, df_view)
                    
            if failed_count > 0:
                ui_log("SERVER", f"Aborting save. {failed_count} failures detected. Document will not be written to database.")
                _log_df_to_supabase(supabase, df_view, bot_user, current_user, pack_mode=True)
            else:
                ui_log("SERVER", "Finalizing batch. Saving document to main server...")
                if dry_run:
                    ui_log("DRY_RUN", "Dry run active - bypassed save click")
                    # Fallback to update statuses directly
                    for idx, row in df_view.iterrows():
                        if row.get('Status') == 'Success':
                            df_view.at[idx, 'Keterangan'] = "Input successfully (Dry Run)"
                    utils.render_neo_table(table_placeholder, df_view)
                    ui_log("AUTH", "Initiating system logout sequence...")
                    page.once("dialog", lambda dialog: dialog.accept())
                    page.locator("id=btnLogout").click(timeout=10000)
                    browser.close()
                    elapsed = int(time.time() - global_start_time)
                    box_html = utils.make_success_box(f"DRY RUN SUCCESS — Processed: {success_count} | Time: {elapsed//60}m {elapsed%60}s")
                    st.markdown(box_html, unsafe_allow_html=True)
                    alert_callback(f"[OK] <b>DRY RUN FINISHED</b>\nDist: {selected_distributor}\nSuccess: {success_count} | Failed: {failed_count}\nRuntime: {elapsed//60}m {elapsed%60}s")
                    st.session_state.is_bot_running = False
                    return success_count, failed_count, elapsed
                page.locator("id=pag_I_StkAdj_NewGeneral_btn_Save_Value").click()
                _wait_for_page_ready(page, TIMEOUT_MS, ui_log, "manual stkadj save")
                try: 
                    yes_btn = page.locator("id=pag_PopUp_YesNo_btn_Yes_Value")
                    yes_btn.wait_for(state="visible", timeout=5000)
                    ui_log("SERVER", "Confirming save dialog...")
                    yes_btn.click()
                    _wait_for_page_ready(page, TIMEOUT_MS, ui_log, "manual stkadj save yes")
                    ui_log("SERVER", "Document physically written to database.")
                except Exception: 
                    ui_log("SERVER", "Auto-save confirmed. Document written to database.")
                    
                ui_log("SYS", "Holding session for 5 seconds to ensure Newspage database write...")
                page.wait_for_timeout(5000)

                ui_log("SUCCESS", "Document saved successfully!")

                # Update descriptions in df_view
                for idx, row in df_view.iterrows():
                    if row.get('Status') == 'Success':
                        df_view.at[idx, 'Keterangan'] = "Input successfully"

                _log_df_to_supabase(supabase, df_view, bot_user, current_user, pack_mode=True)

                # Refresh the final dataframe view in the UI
                utils.render_neo_table(table_placeholder, df_view)
            
            ui_log("AUTH", "Initiating system logout sequence...")
            try:
                page.once("dialog", lambda dialog: dialog.accept())
                page.locator("id=btnLogout").click(timeout=10000)
                _wait_for_page_ready(page, TIMEOUT_MS, ui_log, "manual logout")
                ui_log("AUTH", "Pop up confirm logout...")
                page.wait_for_timeout(2000)
                ui_log("SUCCESS", "Logged out successfully.")
            except Exception as e:
                ui_log("ERROR", "Logout button not found or timeout.")
                
            ui_log("SYS", "Closing browser and releasing memory...")
            browser.close()
            elapsed = int(time.time() - global_start_time)
            
            if failed_count > 0:
                ui_log("ERROR", f"Aborted. Total runtime: {elapsed//60}m {elapsed%60}s")
                box_html = utils.make_error_box(f"ABORTED — Success: {success_count} | Failed: {failed_count} | Time: {elapsed//60}m {elapsed%60}s")
                if show_status_box:
                    st.markdown(box_html, unsafe_allow_html=True)
                failed_skus = df_view[df_view["Status"] == "Failed"]["SKU"].tolist()
                sku_str = ("\nFailed SKUs: " + ", ".join(failed_skus[:5]) + ("..." if len(failed_skus) > 5 else "")) if failed_skus else ""
                alert_callback(f"[WARNING] <b>BOT ABORTED</b>\nDist: {selected_distributor}\nSuccess: {success_count} | Failed: {failed_count}\nRuntime: {elapsed//60}m {elapsed%60}s{sku_str}")
                st.toast('Execution aborted due to errors!', icon="🚨")
                st.session_state.is_bot_running = False
                return success_count, failed_count, elapsed
            else:
                ui_log("SUCCESS", f"Complete. Total runtime: {elapsed//60}m {elapsed%60}s")
                box_html = utils.make_success_box(f"SUCCESS — Processed: {success_count} | Time: {elapsed//60}m {elapsed%60}s")
                alert_msg = f"[OK] <b>BOT FINISHED</b>\nDist: {selected_distributor}\nSuccess: {success_count} | Failed: {failed_count}\nRuntime: {elapsed//60}m {elapsed%60}s"
                if show_status_box:
                    st.markdown(box_html, unsafe_allow_html=True)
                alert_callback(alert_msg)
                st.toast('System override complete!')
                st.session_state.is_bot_running = False
                return success_count, failed_count, elapsed

    except PlaywrightTimeoutError: 
        st.session_state.is_bot_running = False
        ui_log("ERROR", "TIMEOUT: Server tidak merespon.")
        st.error("Operation Timeout. Target element tidak ditemukan.")
        return 0, len(df_view), 0
    except Exception as e: 
        st.session_state.is_bot_running = False
        ui_log("ERROR", f"SYSTEM FAILURE: {str(e).split(chr(10))[0]}")
        st.error(f"System error: {e}")
        return 0, len(df_view), 0
def run_mutasi_execution(
    df_mutasi,
    bot_user_a, bot_pass_a, dist_a,
    bot_user_b, bot_pass_b, dist_b,

    URL_LOGIN, TIMEOUT_MS, whs_a, whs_b,
    REASON_CODE, TABLE_UPDATE_INTERVAL,
    alert_callback,
    table_a_ph, table_b_ph,
    prog_a_ph, prog_b_ph,
    log_a_ph, log_b_ph,
    supabase,
    remark_text="",
    current_user=None,
    dry_run=None
):
    ui_log_a, _ = utils.make_terminal_logger(log_a_ph)
    ui_log_b, _ = utils.make_terminal_logger(log_b_ph)
    
    ui_log_a('SYS', 'Memulai Deduct Mutasi untuk Pengirim...')
    df_deduct = df_mutasi.copy()
    df_deduct['Qty'] = -abs(df_deduct['Qty'].astype(float))
    df_deduct['Status'] = 'Pending'
    df_deduct['Keterangan'] = 'Ready'
    
    res_a = run_execution_manual(
        df_view=df_deduct, bot_user=bot_user_a, bot_pass=bot_pass_a, 
        selected_distributor=dist_a, URL_LOGIN=URL_LOGIN, TIMEOUT_MS=TIMEOUT_MS, 
        WAREHOUSE=whs_a, REASON_CODE=REASON_CODE, TABLE_UPDATE_INTERVAL=TABLE_UPDATE_INTERVAL, 
        ui_log=ui_log_a, alert_callback=alert_callback, 
        table_placeholder=table_a_ph, log_label_placeholder=None, supabase=supabase,
        remark_text=remark_text, progress_placeholder=prog_a_ph, show_status_box=False, current_user=current_user, dry_run=dry_run
    )
    success_a, failed_a, elapsed_a = res_a if res_a else (0, len(df_deduct), 0)
    
    ui_log_b('SYS', 'Memulai Add Mutasi untuk Penerima...')
    df_add = df_mutasi.copy()
    df_add['Qty'] = abs(df_add['Qty'].astype(float))
    df_add['Status'] = 'Pending'
    df_add['Keterangan'] = 'Ready'
    
    res_b = run_execution_manual(
        df_view=df_add, bot_user=bot_user_b, bot_pass=bot_pass_b, 
        selected_distributor=dist_b, URL_LOGIN=URL_LOGIN, TIMEOUT_MS=TIMEOUT_MS, 
        WAREHOUSE=whs_b, REASON_CODE=REASON_CODE, TABLE_UPDATE_INTERVAL=TABLE_UPDATE_INTERVAL, 
        ui_log=ui_log_b, alert_callback=alert_callback, 
        table_placeholder=table_b_ph, log_label_placeholder=None, supabase=supabase,
        remark_text=remark_text, progress_placeholder=prog_b_ph, show_status_box=False, current_user=current_user, dry_run=dry_run
    )
    success_b, failed_b, elapsed_b = res_b if res_b else (0, len(df_add), 0)

    # Render a single consolidated success/error box
    total_elapsed = elapsed_a + elapsed_b
    if failed_a > 0 or failed_b > 0:
        box_html = utils.make_error_box(f"ABORTED — Deduct: {success_a} S, {failed_a} F | Add: {success_b} S, {failed_b} F | Time: {total_elapsed//60}m {total_elapsed%60}s")
        st.markdown(box_html, unsafe_allow_html=True)
    else:
        box_html = utils.make_success_box(f"SUCCESS — Processed: {success_a} | Time: {total_elapsed//60}m {total_elapsed%60}s")
        st.markdown(box_html, unsafe_allow_html=True)

def run_element_crawler(user_id_np, pass_np, selected_distributor, URL_LOGIN, target_path, ext_ui_log):
    TIMEOUT_MS = 60000
    try:
        with managed_browser_session(user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, ext_ui_log) as (page, browser):
            
            if target_path:
                ext_ui_log("SYS", f"Navigating to {target_path}...")
                page.goto(f"{URL_LOGIN.rstrip('/')}/{target_path.lstrip('/')}")
            
            # Selalu tunggu networkidle untuk mencegah Execution context was destroyed
            page.wait_for_load_state("networkidle")
                
            ext_ui_log("SYS", "Extracting interactive elements from DOM...")
            
            elements = page.evaluate("""() => {
                const els = document.querySelectorAll('button, input, select, textarea, a, [role="button"], [role="link"], [role="checkbox"]');
                return Array.from(els).map(el => {
                    let text = el.innerText || el.value || el.placeholder || el.title || '';
                    if (typeof text === 'string') text = text.trim();
                    return {
                        Tag: el.tagName.toLowerCase(),
                        ID: el.id || '',
                        Name: el.getAttribute('name') || '',
                        Class: el.className || '',
                        Text: text.substring(0, 100)
                    };
                });
            }""")
            
            ext_ui_log("SUCCESS", f"Found {len(elements)} elements.")
            return elements
    except Exception as e:
        ext_ui_log("ERROR", f"Crawler failed: {e}")
        raise e

def run_interactive_inspector(user_id_np, pass_np, selected_distributor, URL_LOGIN, target_path, ext_ui_log):
    TIMEOUT_MS = 60000
    if dry_run is None: dry_run = st.session_state.get('dry_run_enabled', False)
    ensure_playwright()
    import sys, asyncio
    from playwright.sync_api import sync_playwright
    
    if sys.platform == "win32": 
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    recorded_elements = []
    
    with sync_playwright() as p:
        ext_ui_log("SYS", "Spawning browser for Interactive Inspector (Headless=False)...")
        
        # Check if running on Linux/Cloud which doesn't support GUI
        if sys.platform == "linux" or sys.platform == "linux2":
            error_msg = "Interactive Inspector tidak bisa dijalankan di server Cloud (Streamlit Cloud/Linux headless) karena tidak ada layar GUI. Fitur ini hanya bisa digunakan jika aplikasi dijalankan di komputer lokal (Windows/Mac)."
            ext_ui_log("ERROR", error_msg)
            raise Exception(error_msg)
            
        # Start in headed mode
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(no_viewport=True)
        page = context.new_page()
        
        # Expose binding to python
        def handle_record(info):
            recorded_elements.append(info)
            ext_ui_log("SUCCESS", f"Recorded Element: &lt;{info.get('Tag', '')} id='{info.get('ID', '')}'&gt;")
            
        page.expose_function("recordElement", handle_record)
        
        # Inject script into all pages
        page.add_init_script("""
            document.addEventListener("click", (e) => {
                if (e.altKey) {
                    e.preventDefault();
                    e.stopPropagation();
                    const el = e.target;
                    let className = "";
                    try {
                        className = typeof el.className === "string" ? el.className : (el.getAttribute("class") || "");
                    } catch(err) {}

                    const info = {
                        Tag: el.tagName ? el.tagName.toLowerCase() : "",
                        ID: el.id || "",
                        Name: el.name || el.getAttribute("name") || "",
                        Class: className,
                        Text: (el.innerText || el.value || "").substring(0, 100).trim()
                    };
                    
                    let oldOutline = el.style.outline;
                    el.style.outline = "2px solid red";
                    setTimeout(() => el.style.outline = oldOutline, 500);

                    window.recordElement(info).catch(e => console.error(e));
                }
            }, true);
        """)

        try:
            _login(page, user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, ext_ui_log)
            
            if target_path:
                ext_ui_log("SYS", f"Navigating to {target_path}...")
                page.goto(f"{URL_LOGIN.rstrip('/')}/{target_path.lstrip('/')}")
            
            page.wait_for_load_state("networkidle")
            
            ext_ui_log("SUCCESS", "✅ Interactive mode ready! ALT+Click in the browser to record elements. Close the browser when done.")
            
            # Wait until page is closed by the user
            try:
                page.wait_for_event("close", timeout=0)
            except Exception:
                pass
                
        except Exception as e:
            ext_ui_log("ERROR", f"Inspector failed: {e}")
            raise e
        finally:
            try:
                browser.close()
            except Exception:
                pass
            
    return recorded_elements
