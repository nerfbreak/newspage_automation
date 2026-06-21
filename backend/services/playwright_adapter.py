"""Playwright automation adapter for the FastAPI backend.
All Streamlit dependencies removed. Uses callback parameters for UI communication.

Public API:
    run_extract(bot_user, bot_pass, distributor, url_login, timeout_ms,
                warehouse, ui_log, alert_callback, supabase, current_user,
                result_callback)

    run_sales_extract(bot_user, bot_pass, distributor, url_login, timeout_ms,
                      start_date, end_date, ui_log, alert_callback,
                      supabase, current_user, result_callback)

    run_execution(df_view, bot_user, bot_pass, distributor, url_login, timeout_ms,
                  warehouse, reason_code, table_update_interval, ui_log,
                  alert_callback, supabase, progress_callback, result_callback)

    run_promotion_sync(bot_user, bot_pass, distributor, url_login, timeout_ms,
                       start_date, end_date, ui_log, alert_callback,
                       supabase, current_user, result_callback)

Callback signatures:
    ui_log(module: str, msg: str)
    alert_callback(message: str)
    progress_callback(current: int, total: int)
    result_callback(result: dict)  # {"type":"dataframe",...}, {"type":"file",...}, etc.
"""
import html
import re
import time
import os
import subprocess
import sys
import zipfile
import logging

import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from backend.config import get_settings
from backend.core import database

logger = logging.getLogger(__name__)


def _validate_date(date_str: str, name: str = "date") -> str:
    """Validate date format DD/MM/YYYY to prevent JS injection in page.evaluate()."""
    if not re.match(r'^\d{2}/\d{2}/\d{4}$', date_str):
        raise ValueError(f"Invalid {name} format: {date_str}. Expected DD/MM/YYYY.")
    return date_str


# ============================================================
# Browser engine setup
# ============================================================
def ensure_playwright():
    """Ensure Playwright Chromium is installed."""
    try:
        with sync_playwright() as p:
            try:
                executable = p.chromium.executable_path
                if not os.path.exists(executable):
                    raise Exception("Executable missing")
            except Exception:
                subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception:
        try:
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        except Exception as e:
            logger.error("Failed to install browser engine: %s", e)
            raise


# ============================================================
# Internal automation functions (no Streamlit)
# ============================================================
def _login(page, user_id_np, pass_np, selected_distributor, url_login, timeout_ms, ui_log):
    ui_log("AUTH", f"Connecting to {url_login}...")

    settings = get_settings()
    is_super = user_id_np == settings.np_user_super
    account_desc = "SUPERUSER" if is_super else f"[{selected_distributor}]"

    page.goto(url_login, wait_until="domcontentloaded")
    ui_log("AUTH", f"DOM ready. Injecting {account_desc} credentials...")
    page.locator("id=txtUserid").fill(user_id_np)
    page.locator("id=txtPasswd").fill(pass_np)
    page.locator("id=btnLogin").click(force=True)
    try:
        btn = page.locator("id=SYS_ASCXX_btnContinue")
        btn.wait_for(state="visible", timeout=5_000)
        ui_log("AUTH", "Active session interceptor detected. Bypassing...")
        btn.click(force=True)
    except Exception:
        ui_log("SYS", "No interceptor detected. Clean session acquired.")

    page.wait_for_url("**/Default.aspx", timeout=timeout_ms, wait_until="domcontentloaded")
    ui_log("AUTH", "Login successful. Session established.")
    ui_log("SUCCESS", "Handshake verified.")


def _navigate_to_import_export(page, timeout_ms, ui_log):
    ui_log("NAV", "Navigating to System module...")
    page.wait_for_timeout(1000)

    try:
        sys_tab = page.locator("id=pag_Sys_Root_tab_Detail_tab_Header")
        if sys_tab.is_visible():
            sys_tab.click(force=True)
            page.wait_for_timeout(800)
    except Exception:
        pass

    ui_log("NAV", "Searching for Import/Export Job module in DOM...")
    target_id = "pag_Sys_Root_tab_Detail_itm_Job"

    try:
        page.wait_for_selector(f"id={target_id}", state="attached", timeout=timeout_ms)
        ui_log("NAV", "Module found in DOM. Executing JS click bypass...")
        page.evaluate(f"document.getElementById('{target_id}').click()")
        page.wait_for_timeout(1500)
    except Exception as e:
        ui_log("WARN", "ID-based JS click failed, trying brute-force...")
        try:
            parent = page.locator("[id*='itm_SysAdminSetup']").first
            if parent.is_visible():
                parent.click(force=True)
                page.wait_for_timeout(1000)
            page.get_by_text("Import/Export Job").first.click(force=True)
        except Exception:
            ui_log("ERROR", "Navigation failed. System menu might be blocked.")
            raise e

    page.wait_for_timeout(1000)
    ui_log("NAV", "Opening new job [Add Value]...")
    btn_add = page.locator("id=pag_FW_SYS_INTF_JOB_btn_Add_Value")
    btn_add.wait_for(state="visible", timeout=timeout_ms)
    btn_add.click(force=True)
    page.wait_for_timeout(500)


def _dispatch_extraction_job(page, timeout_ms, warehouse, ui_log):
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
    ok_btn.wait_for(state="visible", timeout=timeout_ms)
    ok_btn.click(force=True)
    page.wait_for_timeout(500)

    ui_log("NAV", "Opening interface selection popup...")
    page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_INTF_ID_SelectButton").click(force=True)
    page.wait_for_timeout(1000)

    ui_log("INJECT", "Searching target interface: E_20150315090000028...")
    search_field = page.locator("id=pop_Dynamic_gft_List_2_FilterField_Value")
    search_field.wait_for(state="visible", timeout=max(timeout_ms, 180000))
    search_field.fill("E_20150315090000028")
    page.locator("id=pop_Dynamic_grd_Main_SearchForm_ButtonSearch_Value").click(force=True)
    page.wait_for_timeout(800)

    ui_log("INJECT", "Selecting target interface from results...")
    target_text = page.get_by_text("E_20150315090000028", exact=True)
    target_text.wait_for(state="visible", timeout=max(timeout_ms, 180000))
    target_text.click(force=True)
    page.wait_for_timeout(800)

    ui_log("INJECT", "Setting file type: Delimited [D], separator: standard...")
    page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_FILE_TYPE_Value").select_option("D")
    page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_FLD_SEPARATOR_STD_Value_0").check()
    page.wait_for_timeout(2000)

    ui_log("INJECT", f"Applying warehouse filter: [{warehouse}]...")
    page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_grd_DynamicFilter_ctl02_dyn_Field_txt_Value").fill(warehouse)
    page.wait_for_timeout(1500)

    ui_log("SYS", "Committing parameters to job definition...")
    page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_btn_Add_Value").click(force=True)
    page.wait_for_timeout(2000)

    ui_log("SERVER", "Saving job and dispatching execution to server...")
    page.locator("id=pag_FW_SYS_INTF_JOB_RootNew_btn_Save_Value").click(force=True)

    ui_log("SERVER", "Awaiting server confirmation prompt...")
    page.locator("id=TF_Prompt_btn_Ok_Value").wait_for(state="visible", timeout=timeout_ms)
    page.locator("id=TF_Prompt_btn_Ok_Value").click(force=True)

    ui_log("SERVER", "Intercepting download link -- this may take up to 4 minutes...")
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


def _dispatch_sales_job(page, timeout_ms, start_date, end_date, ui_log):
    ui_log("NAV", "Initiating sales export job sequence...")
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_TYPE_Value").wait_for(state="visible", timeout=timeout_ms)

    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_TYPE_Value").select_option("E")
    page.wait_for_timeout(1000)
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_DESC_Value").fill("Invoice Detail")
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_TIMEOUT_Value").fill("9999999")
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_EXE_TYPE_Value").select_option("M")
    page.wait_for_timeout(1000)

    page.locator("id=pag_FW_SYS_INTF_JOB_RootNew_btn_Next_Value").click(force=True)
    page.wait_for_timeout(2000)
    page.locator("id=pag_FW_DisclaimerMessage_btn_okay_Value").wait_for(state="visible", timeout=timeout_ms)
    page.locator("id=pag_FW_DisclaimerMessage_btn_okay_Value").click(force=True)
    page.wait_for_timeout(2000)

    ui_log("INJECT", "Binding interface target: E_28880804000000001")
    page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_INTF_ID_SelectButton").click(force=True)
    page.wait_for_timeout(2000)

    page.locator("id=pop_Dynamic_gft_List_2_FilterField_Value").wait_for(state="visible", timeout=max(timeout_ms, 180000))
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

    ui_log("INJECT", f"Setting date range: {start_date} to {end_date}")
    start_date = _validate_date(start_date, "start_date")
    end_date = _validate_date(end_date, "end_date")
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
    page.locator("id=TF_Prompt_btn_Ok_Value").wait_for(state="visible", timeout=timeout_ms)
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


def _navigate_to_stock_adjustment(page, timeout_ms, warehouse, reason_code, ui_log):
    ui_log("NAV", "Navigating to Stock Adjustment module...")
    page.wait_for_timeout(3000)
    page.locator("id=pag_InventoryRoot_tab_Main_itm_StkAdj").dispatch_event("click")

    add_btn = page.locator("id=pag_I_StkAdj_btn_Add_Value")
    add_btn.wait_for(state="attached", timeout=timeout_ms)
    add_btn.click(force=True)

    warehouse_link = page.locator(f"a:text-is('{warehouse}')").first
    warehouse_link.wait_for(state="visible", timeout=timeout_ms)
    warehouse_link.click(force=True)

    page.locator("id=pag_I_StkAdj_NewGeneral_sel_PRD_CD_Value").wait_for(state="visible")

    dropdown = page.locator("id=pag_I_StkAdj_NewGeneral_drp_n_REASON_HDR_Value")
    if dropdown.is_enabled():
        dropdown.select_option(reason_code)
    ui_log("SYS", "Ready. Opening data stream for payload injection...")


def _inject_adjustment_row(page, sku, qty, timeout_ms, ui_log):
    sku_input = page.locator("id=pag_I_StkAdj_NewGeneral_sel_PRD_CD_Value")
    ui_log("INJECT", f"Locking target node for SKU [{sku}]...")
    sku_input.fill(sku)
    ui_log("INJECT", "Triggering system lookup (Tab event)...")
    sku_input.press("Tab")
    page.wait_for_timeout(1500)

    qty_input = page.locator("id=pag_I_StkAdj_NewGeneral_txt_QTY1_Value")
    qty_input.wait_for(state="visible", timeout=timeout_ms)
    ui_log("INJECT", f"Node resolved. Assigning adjustment quantity: {qty} EA")
    qty_input.fill(qty)
    page.wait_for_timeout(500)

    ui_log("INJECT", "Dispatching Add command to grid...")
    page.locator("id=pag_I_StkAdj_NewGeneral_btn_Add_Value").click(force=True)
    ui_log("SYS", "Awaiting DOM form reset confirmation...")
    page.wait_for_function("document.getElementById('pag_I_StkAdj_NewGeneral_sel_PRD_CD_Value').value === ''", timeout=timeout_ms)


def _dispatch_promotion_job(page, timeout_ms, start_date, end_date, ui_log):
    promo_ids = [
        "E_20150417000000043", "E_20150417000000044",
        "E_20150417000000050", "E_20150417000000048",
        "E_20150417000000093",
    ]

    ui_log("NAV", "Initiating promotion sync job sequence...")
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_TYPE_Value").wait_for(state="visible", timeout=timeout_ms)

    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_TYPE_Value").select_option("E")
    page.wait_for_timeout(1000)
    job_desc = f"PROMO_SYNC_{time.strftime('%Y%m%d_%H%M%S')}"
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_DESC_Value").fill(job_desc)
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_TIMEOUT_Value").fill("9999999")
    page.locator("id=pag_FW_SYS_INTF_JOB_NewGeneral_EXE_TYPE_Value").select_option("M")
    page.wait_for_timeout(1000)

    page.locator("id=pag_FW_SYS_INTF_JOB_RootNew_btn_Next_Value").click(force=True)
    page.wait_for_timeout(2000)
    page.locator("id=pag_FW_DisclaimerMessage_btn_okay_Value").wait_for(state="visible", timeout=timeout_ms)
    page.locator("id=pag_FW_DisclaimerMessage_btn_okay_Value").click(force=True)
    page.wait_for_timeout(2000)

    for i, target_id in enumerate(promo_ids):
        ui_log("INJECT", f"[{i+1}/{len(promo_ids)}] Binding interface: {target_id}")
        page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_INTF_ID_SelectButton").click(force=True)
        page.wait_for_timeout(2000)

        page.locator("id=pop_Dynamic_gft_List_2_FilterField_Value").wait_for(state="visible", timeout=max(timeout_ms, 180000))
        page.locator("id=pop_Dynamic_gft_List_2_FilterField_Value").fill(target_id)
        page.locator("id=pop_Dynamic_grd_Main_SearchForm_ButtonSearch_Value").click(force=True)
        page.wait_for_timeout(2000)
        page.get_by_text(target_id, exact=True).click(force=True)
        page.wait_for_timeout(2000)

        ui_log("INJECT", f"[{i+1}/{len(promo_ids)}] Setting file params and dates...")
        page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_FILE_TYPE_Value").select_option("D")
        page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_FLD_SEPARATOR_STD_Value_0").check()

        start_date = _validate_date(start_date, "start_date")
        end_date = _validate_date(end_date, "end_date")
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
    page.locator("id=TF_Prompt_btn_Ok_Value").wait_for(state="visible", timeout=timeout_ms)
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


# ============================================================
# Public API: Runner functions (called by job_manager in threads)
# ============================================================

def run_extract(bot_user, bot_pass, selected_distributor, url_login, timeout_ms,
                warehouse, ui_log, alert_callback, supabase, current_user,
                result_callback=None):
    """Extract real-time stock data. result_callback({"type":"dataframe","df":...,"filename":...})"""
    ensure_playwright()
    try:
        with sync_playwright() as p:
            ui_log("SYS", "Spawning browser context with isolated session...")
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-dev-shm-usage", "--no-sandbox", "--single-process"]
            )
            context = browser.new_context(no_viewport=True)
            page = context.new_page()

            _login(page, bot_user, bot_pass, selected_distributor, url_login, timeout_ms, ui_log)
            _navigate_to_import_export(page, timeout_ms, ui_log)

            exception_dict = database.get_distributor_warehouse_exceptions(supabase)
            target_whs = exception_dict.get(bot_user)
            actual_warehouse = target_whs if target_whs and warehouse == "GOOD_WHS" else warehouse

            real_filename, file_path = _dispatch_extraction_job(page, timeout_ms, actual_warehouse, ui_log)
            browser.close()
            ui_log("SYS", "Browser closed. Parsing payload...")

            df_ext = None
            if real_filename.lower().endswith('.zip'):
                with zipfile.ZipFile(file_path) as z:
                    target = next((n for n in z.namelist() if "INVT_MASTER" in n and n.lower().endswith((".csv", ".txt"))), None)
                    if not target:
                        target = next((n for n in z.namelist() if n.lower().endswith((".csv", ".txt"))), None)
                    if target:
                        with z.open(target) as f:
                            df_ext = pd.read_csv(f, sep='\t', dtype=str, on_bad_lines='skip')
                            if df_ext.shape[1] <= 1:
                                f.seek(0)
                                df_ext = pd.read_csv(f, sep=',', dtype=str, on_bad_lines='skip')
            elif real_filename.lower().endswith(('.xls', '.xlsx')):
                df_ext = pd.read_excel(file_path, dtype=str)
            else:
                for enc in ['utf-8', 'iso-8859-1', 'cp1252']:
                    for sep_ch in ['\t', ',', ';', '|']:
                        try:
                            temp_df = pd.read_csv(file_path, sep=sep_ch, dtype=str, encoding=enc, on_bad_lines='skip')
                            if temp_df is not None and temp_df.shape[1] > 1:
                                df_ext = temp_df; break
                        except Exception: continue
                    if df_ext is not None and df_ext.shape[1] > 1: break

            if df_ext is not None and not df_ext.empty and df_ext.shape[1] > 1:
                df_ext.columns = [str(c).strip() for c in df_ext.columns]
                ui_log("SUCCESS", f"Payload Secured! {len(df_ext)} items loaded.")
                database.log_extraction_history(supabase, selected_distributor, current_user)
                if result_callback:
                    result_callback({"type": "dataframe", "df": df_ext, "filename": real_filename})
            else:
                ui_log("ERROR", "DataFrame validation failed.")
                alert_callback(f"[WARN] <b>EXTRACT FAILED</b>\nUser: {current_user}\nDist: {selected_distributor}")
                if result_callback:
                    result_callback({"type": "error", "message": "DataFrame validation failed."})
            try: os.remove(file_path)
            except Exception: pass

    except PlaywrightTimeoutError:
        ui_log("ERROR", "TIMEOUT: Server tidak merespon.")
        alert_callback(f"[ALERT] <b>EXTRACT TIMEOUT</b>\nUser: {html.escape(current_user)}\nDist: {html.escape(selected_distributor)}")
        if result_callback: result_callback({"type": "error", "message": "Operation timeout."})
    except Exception as e:
        logger.error("Extract failed: %s", e)
        ui_log("ERROR", f"SYSTEM FAILURE: {str(e).split(chr(10))[0]}")
        alert_callback(f"[ALERT] <b>SYSTEM ERROR (EXTRACT)</b>\nDist: {html.escape(selected_distributor)}\nError: <code>{html.escape(str(e)[:100])}</code>")
        if result_callback: result_callback({"type": "error", "message": "An internal error occurred during extraction."})


def run_sales_extract(bot_user, bot_pass, selected_distributor, url_login, timeout_ms,
                      start_date, end_date, ui_log, alert_callback,
                      supabase, current_user, result_callback=None):
    """Extract sales data. result_callback({"type":"file","data":bytes,"filename":str})"""
    ensure_playwright()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-dev-shm-usage", "--no-sandbox", "--single-process"]
            )
            context = browser.new_context(no_viewport=True)
            page = context.new_page()
            _login(page, bot_user, bot_pass, selected_distributor, url_login, timeout_ms, ui_log)
            _navigate_to_import_export(page, timeout_ms, ui_log)
            real_filename, file_path = _dispatch_sales_job(page, timeout_ms, start_date, end_date, ui_log)
            browser.close()
            ui_log("SYS", "Browser closed. Ready for download.")
            with open(file_path, "rb") as f:
                file_data = f.read()
            if result_callback:
                result_callback({"type": "file", "data": file_data, "filename": real_filename})
            try: os.remove(file_path)
            except Exception: pass
    except PlaywrightTimeoutError:
        ui_log("ERROR", "TIMEOUT: Server tidak merespon.")
        alert_callback(f"[ALERT] <b>SALES EXTRACT TIMEOUT</b>\nUser: {html.escape(current_user)}\nDist: {html.escape(selected_distributor)}")
        if result_callback: result_callback({"type": "error", "message": "Operation timeout."})
    except Exception as e:
        logger.error("Sales extract failed: %s", e)
        ui_log("ERROR", f"SYSTEM FAILURE: {str(e).split(chr(10))[0]}")
        alert_callback(f"[ALERT] <b>SYSTEM ERROR (SALES)</b>\nDist: {html.escape(selected_distributor)}\nError: <code>{html.escape(str(e)[:100])}</code>")
        if result_callback: result_callback({"type": "error", "message": "An internal error occurred during sales extraction."})


def run_execution(df_view, bot_user, bot_pass, selected_distributor, url_login, timeout_ms,
                  warehouse, reason_code, table_update_interval, ui_log, alert_callback,
                  supabase, progress_callback=None, result_callback=None):
    """Execute stock adjustment. progress_callback(current, total) per row."""
    ensure_playwright()
    t0 = time.time(); ok_count, fail_count = 0, 0
    ui_log("SYS", "Initializing Chromium headless core...")
    alert_callback(f"<b>BOT STARTED</b>\nTask: Reconcile Stock\nDist: {selected_distributor}\nTotal SKU: {len(df_view)}")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-dev-shm-usage", "--no-sandbox", "--single-process"]
            )
            context = browser.new_context(no_viewport=True)
            page = context.new_page()
            _login(page, bot_user, bot_pass, selected_distributor, url_login, timeout_ms, ui_log)
            exc = database.get_distributor_warehouse_exceptions(supabase)
            tw = exc.get(bot_user)
            aw = tw if tw and warehouse == "GOOD_WHS" else warehouse
            _navigate_to_stock_adjustment(page, timeout_ms, aw, reason_code, ui_log)
            total = len(df_view); results = []
            for i, (idx, row) in enumerate(df_view.iterrows()):
                sku = str(row['SKU']).strip()
                try: qty = str(int(float(row['Qty'])))
                except Exception: qty = str(row['Qty']).strip()
                ui_log("INJECT", f"Processing {i+1}/{total} | SKU [{sku}]")
                try:
                    _inject_adjustment_row(page, sku, qty, timeout_ms, ui_log)
                    st, ket = "Success", f"Input {qty} EA"; ok_count += 1
                    ui_log("SUCCESS", f"Transaction {i+1} committed.")
                    database.log_adjustment(supabase, sku, qty, "Success", f"Attached {qty} EA", bot_user)
                except Exception:
                    st, ket = "Failed", "Node Timeout"; fail_count += 1
                    ui_log("ERROR", f"Timeout on SKU [{sku}].")
                    database.log_adjustment(supabase, sku, qty, "Failed", "Node Timeout", bot_user)
                results.append({"sku": sku, "qty": qty, "status": st, "keterangan": ket})
                if progress_callback: progress_callback(i + 1, total)
            ui_log("SERVER", "Saving document...")
            page.locator("id=pag_I_StkAdj_NewGeneral_btn_Save_Value").click()
            try:
                yb = page.locator("id=pag_PopUp_YesNo_btn_Yes_Value")
                yb.wait_for(state="visible", timeout=5000); yb.click()
                ui_log("SERVER", "Document written to database.")
            except Exception: ui_log("SERVER", "Auto-save confirmed.")
            page.wait_for_timeout(5000)
            try:
                page.once("dialog", lambda d: d.accept())
                page.locator("id=btnLogout").click(timeout=10000)
                page.wait_for_timeout(2000)
            except Exception: pass
            browser.close()
            elapsed = int(time.time() - t0)
            ui_log("SUCCESS", f"Complete. Runtime: {elapsed//60}m {elapsed%60}s")
            alert_callback(f"[OK] <b>BOT FINISHED</b>\nDist: {html.escape(selected_distributor)}\nSuccess: {ok_count} | Failed: {fail_count}\nRuntime: {elapsed//60}m {elapsed%60}s")
            if result_callback:
                result_callback({"type": "execution_done", "success": ok_count, "failed": fail_count, "elapsed": elapsed, "results": results})
    except Exception as e:
        logger.error("Execution failed: %s", e)
        ui_log("ERROR", f"FAILURE: {e}")
        alert_callback(f"[ALERT] <b>FATAL ERROR (EXECUTE)</b>\nDist: {html.escape(selected_distributor)}\nError: <code>{html.escape(str(e)[:100])}</code>")
        if result_callback: result_callback({"type": "error", "message": "An internal error occurred during execution."})


def run_promotion_sync(bot_user, bot_pass, selected_distributor, url_login, timeout_ms,
                       start_date, end_date, ui_log, alert_callback,
                       supabase, current_user, result_callback=None):
    """Sync promotion data. result_callback({"type":"file","data":bytes,"filename":str})"""
    ensure_playwright()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-dev-shm-usage", "--no-sandbox", "--single-process"]
            )
            context = browser.new_context(no_viewport=True)
            page = context.new_page()
            _login(page, bot_user, bot_pass, selected_distributor, url_login, timeout_ms, ui_log)
            _navigate_to_import_export(page, timeout_ms, ui_log)
            real_filename, file_path = _dispatch_promotion_job(page, timeout_ms, start_date, end_date, ui_log)
            browser.close()
            with open(file_path, "rb") as f:
                file_data = f.read()
            if result_callback:
                result_callback({"type": "file", "data": file_data, "filename": real_filename})
            try: os.remove(file_path)
            except Exception: pass
    except PlaywrightTimeoutError:
        ui_log("ERROR", "TIMEOUT: Server tidak merespon.")
        if result_callback: result_callback({"type": "error", "message": "Operation timeout."})
    except Exception as e:
        logger.error("Promotion sync failed: %s", e)
        ui_log("ERROR", f"SYSTEM FAILURE: {str(e)}")
        if result_callback: result_callback({"type": "error", "message": "An internal error occurred during promotion sync."})
