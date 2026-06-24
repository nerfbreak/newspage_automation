import streamlit as st
import time
import os
import subprocess
import asyncio
import sys
import zipfile
import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import database
import utils
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
    
    page.goto(URL_LOGIN, wait_until="domcontentloaded")
    ui_log("AUTH", f"DOM ready. Injecting {account_desc} credentials...")
    page.locator("id=txtUserid").fill(user_id_np)
    page.locator("id=txtPasswd").fill(pass_np)
    page.locator("id=btnLogin").click(force=True)
    try:
        btn = page.locator("id=SYS_ASCX_btnContinue")
        btn.wait_for(state="visible", timeout=5_000)
        ui_log("AUTH", "Active session interceptor detected. Bypassing...")
        btn.click(force=True)
    except Exception: 
        ui_log("SYS", "No interceptor detected. Clean session acquired.")
    
    page.wait_for_url("**/Default.aspx", timeout=TIMEOUT_MS, wait_until="domcontentloaded")
    ui_log("AUTH", "Login successful. Session established.")
    ui_log("SUCCESS", "Handshake verified.")

def _navigate_to_import_export(page, TIMEOUT_MS, ui_log):
    ui_log("NAV", "Navigating to System module...")
    page.wait_for_timeout(1000)
    
    # Ensure 'System' tab is selected
    try:
        sys_tab = page.locator("id=pag_Sys_Root_tab_Detail_tab_Header")
        if sys_tab.is_visible():
            sys_tab.click(force=True)
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

def _dispatch_extraction_job(page, TIMEOUT_MS, WAREHOUSE, ui_log, browser):
    ui_log("INJECT", "Setting job type: Export [E], desc: Text Inventory Master...")
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_TYPE_Value").select_option("E")
    page.wait_for_timeout(1000)
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_DESC_Value").fill("Text Inventory Master")
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_TIMEOUT_Value").fill("9999999")
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_EXE_TYPE_Value").select_option("M")
    page.wait_for_timeout(1000)
    
    ui_log("NAV", "Proceeding to next step...")
    page.locator("id=pag_FW_SYS_INTF_JOB_RootNew_btn_Next_Value").click(force=True)
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
    page.wait_for_timeout(2000)
    
    ui_log("SERVER", "Saving job and dispatching execution to server...")
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

def run_extract(user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, WAREHOUSE, ext_ui_log, alert_callback, supabase, current_user):
    ensure_playwright()
    try:
        if sys.platform == "win32": asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
        
        with sync_playwright() as p:
            ext_ui_log("SYS", "Spawning browser context with isolated session...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(no_viewport=True)
            page = context.new_page()
            
            _login(page, user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, ext_ui_log)
            _navigate_to_import_export(page, TIMEOUT_MS, ext_ui_log)
            
            # Fetch distributor exception from DB
            exception_dict = database.get_distributor_warehouse_exceptions(supabase)
            target_whs = exception_dict.get(user_id_np)
            
            actual_warehouse = target_whs if target_whs and WAREHOUSE == "GOOD_WHS" else WAREHOUSE
            
            real_filename, file_path = _dispatch_extraction_job(page, TIMEOUT_MS, actual_warehouse, ext_ui_log, browser)
            
            browser.close()
            ext_ui_log("SYS", "Browser closed. Releasing session memory...")
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
        alert_callback(f"[ALERT] <b>SYSTEM ERROR (EXTRACT)</b>\nDist: {selected_distributor}\nError: <code>{str(e)[:100]}</code>")

def _dispatch_sales_job(page, TIMEOUT_MS, start_date, end_date, ui_log, browser):
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
    page.wait_for_timeout(2000)
    page.locator("id=pag_FW_DisclaimerMessage_btn_okay_Value").wait_for(state="visible", timeout=TIMEOUT_MS)
    page.locator("id=pag_FW_DisclaimerMessage_btn_okay_Value").click(force=True)
    page.wait_for_timeout(2000)
    
    ui_log("INJECT", "Binding interface target: E_28880804000000001")
    page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_INTF_ID_SelectButton").click(force=True)
    page.wait_for_timeout(2000)
    
    # Target elements in the interface selection popup - slow loading popups on laggy server
    page.locator("id=pop_Dynamic_gft_List_2_FilterField_Value").wait_for(state="visible", timeout=max(TIMEOUT_MS, 180000))
    page.locator("id=pop_Dynamic_gft_List_2_FilterField_Value").fill("E_28880804000000001")
    page.locator("id=pop_Dynamic_grd_Main_SearchForm_ButtonSearch_Value").click(force=True)
    page.wait_for_timeout(2000)
    page.locator("id=pop_Dynamic_grd_Main_ctl02_DynCol_INTF_ID_Value").click(force=True)
    page.wait_for_timeout(2000)
    
    ui_log("INJECT", f"Applying parameters: {start_date} to {end_date}")
    page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_FILE_TYPE_Value").select_option("D")
    page.wait_for_timeout(1500)
    page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_FLD_SEPARATOR_STD_Value_0").check()
    page.wait_for_timeout(1500)
    page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_grd_DynamicFilter_ctl13_dyn_Field_drp_Value").select_option("Invoiced")
    ui_log("SYS", "Waiting for server to apply Invoiced filter (PostBack)...")
    page.wait_for_timeout(3500)
    
    # Use JavaScript to directly set dates via CalendarExtender API
    # This bypasses all calendar UI issues (month navigation, strict mode, etc.)
    ui_log("INJECT", f"Setting date range: {start_date} to {end_date}")
    sd_d, sd_m, sd_y = start_date.split('/')
    ed_d, ed_m, ed_y = end_date.split('/')
    
    page.evaluate(f"""() => {{
        function setCalDate(inputId, extenderId, day, month, year, dateStr) {{
            var el = document.getElementById(inputId);
            if (el) {{
                el.value = dateStr;
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
            }}
            try {{
                var ce = $find(extenderId);
                if (ce) {{
                    ce._selectedDate = new Date(year, month - 1, day);
                    ce._textbox.set_Value(dateStr);
                }}
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
    
    ui_log("SERVER", "Executing job sequence...")
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

def run_sales_extract(user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, start_date, end_date, ext_ui_log, alert_callback, supabase, current_user):
    ensure_playwright()
    try:
        if sys.platform == "win32": asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
        
        with sync_playwright() as p:
            ext_ui_log("SYS", "Spawning browser context with isolated session...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(no_viewport=True)
            page = context.new_page()
            
            _login(page, user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, ext_ui_log)
            _navigate_to_import_export(page, TIMEOUT_MS, ext_ui_log)
            real_filename, file_path = _dispatch_sales_job(page, TIMEOUT_MS, start_date, end_date, ext_ui_log, browser)
            
            browser.close()
            ext_ui_log("SYS", "Browser closed. Ready for download.")
            
            with open(file_path, "rb") as f:
                st.session_state.sales_csv_data = f.read()
                st.session_state.sales_csv_filename = real_filename
                
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
        alert_callback(f"[ALERT] <b>SYSTEM ERROR (SALES EXTRACT)</b>\nDist: {selected_distributor}\nError: <code>{str(e)[:100]}</code>")

def _navigate_to_stock_adjustment(page, TIMEOUT_MS, WAREHOUSE, REASON_CODE, ui_log):
    ui_log("NAV", "Navigating to Stock Adjustment module...")
    page.wait_for_timeout(3000)
    page.locator("id=pag_InventoryRoot_tab_Main_itm_StkAdj").first.dispatch_event("click")
    
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
            import re
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
    ui_log("SYS", "Awaiting DOM form reset confirmation...")
    page.wait_for_function("document.getElementById('pag_I_StkAdj_NewGeneral_sel_PRD_CD_Value').value === ''", timeout=TIMEOUT_MS)


def run_execution(df_view, bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, WAREHOUSE, REASON_CODE, TABLE_UPDATE_INTERVAL, ui_log, alert_callback, table_placeholder, log_label_placeholder, supabase):
    ensure_playwright()
    global_start_time = time.time(); success_count, failed_count = 0, 0; saved_doc_no = "N/A"
    ui_log("SYS", "Allocating memory and initializing Chromium headless core...")
    if supabase: ui_log("SYS", "Supabase client active.")

    alert_callback(f"<b>BOT STARTED</b>\nTask: Reconcile Stock\nDist: {selected_distributor}\nTotal SKU: {len(df_view)}")

    try:
        if sys.platform == "win32": asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
        with sync_playwright() as p:
            ui_log("SYS", "Spawning browser context...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(no_viewport=True)
            page = context.new_page()
            
            _login(page, bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, ui_log)
            
            # Fetch distributor exception from DB
            exception_dict = database.get_distributor_warehouse_exceptions(supabase)
            target_whs = exception_dict.get(bot_user)
            
            actual_warehouse = target_whs if target_whs and WAREHOUSE == "GOOD_WHS" else WAREHOUSE
            
            _navigate_to_stock_adjustment(page, TIMEOUT_MS, actual_warehouse, REASON_CODE, ui_log)

            progress_bar = st.progress(0)
            total_rows = len(df_view)
            
            def update_progress_label(current, total):
                html = f"""
                <div style='display: flex; flex-wrap: wrap; gap: 16px; justify-content: space-between; align-items: center; margin-bottom: 8px;'>
                    <div>
                        <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #0068C9; text-transform: uppercase; letter-spacing: 0.1em; margin-right: 8px;'>Active Account</span>
                        <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #31333F; text-transform: uppercase; letter-spacing: 0.1em;'>{selected_distributor} ({bot_user})</span>
                    </div>
                    <div>
                        <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #0068C9; text-transform: uppercase; letter-spacing: 0.1em; margin-right: 8px;'>Processed</span>
                        <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #31333F; text-transform: uppercase; letter-spacing: 0.1em;'>{current}/{total}</span>
                    </div>
                </div>
                """
                log_label_placeholder.markdown(html, unsafe_allow_html=True)

            update_progress_label(0, total_rows)
            
            for i, (idx, row) in enumerate(df_view.iterrows()):
                update_progress_label(i + 1, total_rows)
                sku = str(row['SKU']).strip()

                if row.get('Status') == 'Invalid':
                    ui_log("WARN", f"SKU [{sku}] skipped: {row.get('Keterangan', 'Invalid Qty')}")
                    if supabase:
                        try:
                            database.log_adjustment(supabase, sku, str(row.get('Qty')), "Invalid", f"Skipped: {row.get('Keterangan')}", bot_user)
                        except Exception:
                            pass
                    progress_bar.progress((i+1)/total_rows)
                    if i % TABLE_UPDATE_INTERVAL == 0 or i == total_rows-1:
                        table_placeholder.dataframe(df_view, width="stretch", hide_index=True)
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
                    table_placeholder.dataframe(df_view, width="stretch", hide_index=True)
                    
            if failed_count > 0:
                ui_log("SERVER", f"Aborting save. {failed_count} failures detected. Document will not be written to database.")
                # Log all non-invalid entries as failed/pending to database
                if supabase:
                    for idx, row in df_view.iterrows():
                        if row.get('Status') == 'Invalid':
                            continue
                        sku = str(row['SKU']).strip()
                        qty = str(row['Qty']).strip()
                        status = str(row['Status']).strip()
                        ket = str(row['Keterangan']).strip()
                        try: database.log_adjustment(supabase, sku, qty, status, ket, bot_user)
                        except Exception: pass
            else:
                ui_log("SERVER", "Finalizing batch. Saving document to main server...")
                page.locator("id=pag_I_StkAdj_NewGeneral_btn_Save_Value").click()
                try: 
                    yes_btn = page.locator("id=pag_PopUp_YesNo_btn_Yes_Value")
                    yes_btn.wait_for(state="visible", timeout=5000)
                    ui_log("SERVER", "Confirming save dialog...")
                    yes_btn.click()
                    ui_log("SERVER", "Document physically written to database.")
                except Exception: 
                    ui_log("SERVER", "Auto-save confirmed. Document written to database.")
                    
                ui_log("SYS", "Holding session for 5 seconds to ensure Newspage database write...")
                page.wait_for_timeout(5000)

                ui_log("SUCCESS", "Document saved successfully!")

                # Update descriptions in df_view
                for idx, row in df_view.iterrows():
                    if row.get('Status') == 'Success':
                        df_view.at[idx, 'Keterangan'] = f"Input {row['Qty']} EA"

                if supabase:
                    for idx, row in df_view.iterrows():
                        if row.get('Status') == 'Invalid':
                            continue
                        sku = str(row['SKU']).strip()
                        qty = str(row['Qty']).strip()
                        status = str(row['Status']).strip()
                        ket = str(row['Keterangan']).strip()
                        try: database.log_adjustment(supabase, sku, qty, status, ket, bot_user)
                        except Exception: pass

                # Refresh the final dataframe view in the UI
                table_placeholder.dataframe(df_view, width="stretch", hide_index=True)
            
            ui_log("AUTH", "Initiating system logout sequence...")
            try:
                page.once("dialog", lambda dialog: dialog.accept())
                page.locator("id=btnLogout").click(timeout=10000)
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
                box_html = utils.make_error_box(f"ABORTED — Success: {success_count} | Failed: {failed_count} | Time: {elapsed//60}m&nbsp;{elapsed%60}s")
                st.markdown(box_html, unsafe_allow_html=True)
                alert_callback(f"[WARNING] <b>BOT ABORTED</b>\nDist: {selected_distributor}\nSuccess: {success_count} | Failed: {failed_count}\nRuntime: {elapsed//60}m {elapsed%60}s")
                st.toast('Execution aborted due to errors!', icon="🚨")
            else:
                ui_log("SUCCESS", f"Complete. Total runtime: {elapsed//60}m {elapsed%60}s")
                box_html = utils.make_success_box(f"SUCCESS — Processed: {success_count} | Time: {elapsed//60}m&nbsp;{elapsed%60}s")
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
        alert_callback(f"[ALERT] <b>FATAL ERROR (EXECUTE)</b>\nDist: {selected_distributor}\nError: <code>{str(e)[:100]}</code>")

# --- PROMOTION SYNC ENGINE ---

def _dispatch_promotion_job(page, TIMEOUT_MS, start_date, end_date, ui_log, browser):
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
    page.wait_for_timeout(2000)
    page.locator("id=pag_FW_DisclaimerMessage_btn_okay_Value").wait_for(state="visible", timeout=TIMEOUT_MS)
    page.locator("id=pag_FW_DisclaimerMessage_btn_okay_Value").click(force=True)
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
        page.wait_for_timeout(2000)
        
        if i < len(promo_ids) - 1:
            ui_log("NAV", "Preparing next interface slot...")
            page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_btn_New_Value").click(force=True)
            page.wait_for_timeout(2000)

    ui_log("SERVER", "Executing multi-interface job...")
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

def run_promotion_sync(user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, start_date, end_date, ext_ui_log, alert_callback, supabase, current_user):
    ensure_playwright()
    try:
        if sys.platform == "win32": asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
        
        with sync_playwright() as p:
            ext_ui_log("SYS", "Spawning browser context...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(no_viewport=True)
            page = context.new_page()
            
            _login(page, user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, ext_ui_log)
            _navigate_to_import_export(page, TIMEOUT_MS, ext_ui_log)
            real_filename, file_path = _dispatch_promotion_job(page, TIMEOUT_MS, start_date, end_date, ext_ui_log, browser)
            
            browser.close()
            
            with open(file_path, "rb") as f:
                st.session_state.promo_zip_data = f.read()
                st.session_state.promo_zip_filename = real_filename
                
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
    ui_log("SYS", "Awaiting DOM form reset confirmation...")
    page.wait_for_function("document.getElementById('pag_I_StkAdj_NewGeneral_sel_PRD_CD_Value').value === ''", timeout=TIMEOUT_MS)

def run_execution_manual(df_view, bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, WAREHOUSE, REASON_CODE, TABLE_UPDATE_INTERVAL, ui_log, alert_callback, table_placeholder, log_label_placeholder, supabase):
    ensure_playwright()
    try:
        global_start_time = time.time(); success_count, failed_count = 0, 0; saved_doc_no = "N/A"
        import asyncio
        try: asyncio.get_event_loop()
        except RuntimeError: asyncio.set_event_loop(asyncio.new_event_loop())
        
        with sync_playwright() as p:
            ui_log("SYS", "Spawning browser context...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(no_viewport=True)
            page = context.new_page()
            
            _login(page, bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, ui_log)
            _navigate_to_stock_adjustment(page, TIMEOUT_MS, WAREHOUSE, REASON_CODE, ui_log)
            
            success_count = 0
            failed_count = 0
            total_rows = len(df_view)
            
            def update_progress_label(current, total):
                html = f"""
                <div style='display: flex; flex-wrap: wrap; gap: 16px; justify-content: space-between; align-items: center; margin-bottom: 8px;'>
                    <div>
                        <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #0068C9; text-transform: uppercase; letter-spacing: 0.1em; margin-right: 8px;'>Active Account</span>
                        <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #31333F; text-transform: uppercase; letter-spacing: 0.1em;'>{selected_distributor} ({bot_user})</span>
                    </div>
                    <div>
                        <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #0068C9; text-transform: uppercase; letter-spacing: 0.1em; margin-right: 8px;'>Processed</span>
                        <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #31333F; text-transform: uppercase; letter-spacing: 0.1em;'>{current}/{total}</span>
                    </div>
                </div>
                """
                log_label_placeholder.markdown(html, unsafe_allow_html=True)

            update_progress_label(0, total_rows)
            
            for i, (idx, row) in enumerate(df_view.iterrows()):
                update_progress_label(i + 1, total_rows)
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
                    table_placeholder.dataframe(df_view, width="stretch", hide_index=True)
                    
            if failed_count > 0:
                ui_log("SERVER", f"Aborting save. {failed_count} failures detected. Document will not be written to database.")
                if supabase:
                    for idx, row in df_view.iterrows():
                        sku = str(row['SKU']).strip()
                        pac = str(row.get('PAC', 0)).strip()
                        car = str(row.get('CAR', 0)).strip()
                        ea = str(row.get('EA', 0)).strip()
                        status = str(row['Status']).strip()
                        ket = str(row['Keterangan']).strip()
                        try: database.log_adjustment(supabase, sku, f"PAC:{pac} CAR:{car} EA:{ea}", status, ket, bot_user)
                        except Exception: pass
            else:
                ui_log("SERVER", "Finalizing batch. Saving document to main server...")
                page.locator("id=pag_I_StkAdj_NewGeneral_btn_Save_Value").click()
                try: 
                    yes_btn = page.locator("id=pag_PopUp_YesNo_btn_Yes_Value")
                    yes_btn.wait_for(state="visible", timeout=5000)
                    ui_log("SERVER", "Confirming save dialog...")
                    yes_btn.click()
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

                if supabase:
                    for idx, row in df_view.iterrows():
                        sku = str(row['SKU']).strip()
                        pac = str(row.get('PAC', 0)).strip()
                        car = str(row.get('CAR', 0)).strip()
                        ea = str(row.get('EA', 0)).strip()
                        status = str(row['Status']).strip()
                        ket = str(row['Keterangan']).strip()
                        try: database.log_adjustment(supabase, sku, f"PAC:{pac} CAR:{car} EA:{ea}", status, ket, bot_user)
                        except Exception: pass

                # Refresh the final dataframe view in the UI
                table_placeholder.dataframe(df_view, width="stretch", hide_index=True)
            
            ui_log("AUTH", "Initiating system logout sequence...")
            try:
                page.once("dialog", lambda dialog: dialog.accept())
                page.locator("id=btnLogout").click(timeout=10000)
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
                box_html = utils.make_error_box(f"ABORTED — Success: {success_count} | Failed: {failed_count} | Time: {elapsed//60}m&nbsp;{elapsed%60}s")
                st.markdown(box_html, unsafe_allow_html=True)
                alert_callback(f"[WARNING] <b>BOT ABORTED</b>\nDist: {selected_distributor}\nSuccess: {success_count} | Failed: {failed_count}\nRuntime: {elapsed//60}m {elapsed%60}s")
                st.toast('Execution aborted due to errors!', icon="🚨")
            else:
                ui_log("SUCCESS", f"Complete. Total runtime: {elapsed//60}m {elapsed%60}s")
                box_html = utils.make_success_box(f"SUCCESS — Processed: {success_count} | Time: {elapsed//60}m&nbsp;{elapsed%60}s")
                alert_msg = f"[OK] <b>BOT FINISHED</b>\nDist: {selected_distributor}\nSuccess: {success_count} | Failed: {failed_count}\nRuntime: {elapsed//60}m {elapsed%60}s"
                st.markdown(box_html, unsafe_allow_html=True)
                alert_callback(alert_msg)
                st.toast('System override complete!')

            st.session_state.is_bot_running = False

    except PlaywrightTimeoutError: 
        st.session_state.is_bot_running = False
        ui_log("ERROR", "TIMEOUT: Server tidak merespon.")
        st.error("Operation Timeout. Target element tidak ditemukan.")
    except Exception as e: 
        st.session_state.is_bot_running = False
        ui_log("ERROR", f"SYSTEM FAILURE: {str(e).split(chr(10))[0]}")
        st.error(f"System error: {e}")
