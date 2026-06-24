# Daftar Elemen HTML & Selector Newspage untuk Otomasi

Dokumen ini berisi daftar lengkap *HTML IDs* dan *Selectors* yang digunakan oleh bot Playwright (`playwright_engine.py`) untuk berinteraksi dengan DOM (Document Object Model) dari sistem web Newspage. Daftar ini berguna untuk *maintenance* apabila pihak prinsipal (Newspage) melakukan pembaruan antarmuka atau perubahan ID elemen.

---

## 1. Modul Autentikasi (Login & Sesi)
Digunakan pada fungsi `_login` dan eksekusi logout.
| Deskripsi Elemen | Selector / ID | Aksi Bot |
| :--- | :--- | :--- |
| **Input User ID** | `id=txtUserid` | `.fill()` |
| **Input Password** | `id=txtPasswd` | `.fill()` |
| **Tombol Login** | `id=btnLogin` | `.click()` |
| **Bypass Sesi Ganda** | `id=SYS_ASCX_btnContinue` | `.click()` jika muncul pop-up interceptor |
| **Tombol Logout** | `id=btnLogout` | `.click()` |

## 2. Modul Navigasi Utama (Menu Kiri)
Digunakan pada fungsi `_navigate_to_import_export` dan `_navigate_to_stock_adjustment`.
| Deskripsi Elemen | Selector / ID | Aksi Bot |
| :--- | :--- | :--- |
| **Tab System** | `id=pag_Sys_Root_tab_Detail_tab_Header` | `.click()` |
| **Menu Import/Export Job** | `id=pag_Sys_Root_tab_Detail_itm_Job` | `.evaluate()` (JS click bypass) |
| **Fallback SysAdminSetup** | `[id*='itm_SysAdminSetup']` | `.click()` |
| **Menu Stock Adjustment** | `id=pag_InventoryRoot_tab_Main_itm_StkAdj` | `.dispatch_event("click")` |

## 3. Ekstraksi Data (Import / Export Job)
Digunakan pada fungsi `_dispatch_extraction_job`, `_dispatch_sales_job`, dan `_dispatch_promotion_job`.
| Deskripsi Elemen | Selector / ID | Aksi Bot |
| :--- | :--- | :--- |
| **Tombol Add Job** | `id=pag_FW_SYS_INTF_JOB_btn_Add_Value` | `.click()` |
| **Dropdown Job Type** | `id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_TYPE_Value` | `.select_option("E")` |
| **Input Job Desc** | `id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_DESC_Value` | `.fill()` |
| **Input Job Timeout** | `id=pag_FW_SYS_INTF_JOB_NewGeneral_JOB_TIMEOUT_Value` | `.fill("9999999")` |
| **Dropdown Exe Type** | `id=pag_FW_SYS_INTF_JOB_NewGeneral_EXE_TYPE_Value` | `.select_option("M")` |
| **Tombol Next** | `id=pag_FW_SYS_INTF_JOB_RootNew_btn_Next_Value` | `.click()` |
| **Pop-up Disclaimer OK** | `id=pag_FW_DisclaimerMessage_btn_okay_Value` | `.click()` |

### Pemilihan Interface (Popup)
| Deskripsi Elemen | Selector / ID | Aksi Bot |
| :--- | :--- | :--- |
| **Tombol Pilih Interface** | `id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_INTF_ID_SelectButton` | `.click()` |
| **Filter ID Search Box** | `id=pop_Dynamic_gft_List_2_FilterField_Value` | `.fill()` |
| **Tombol Search Filter** | `id=pop_Dynamic_grd_Main_SearchForm_ButtonSearch_Value` | `.click()` |
| **Klik Baris Interface (Text)**| `text="E_20150315090000028"` (Contoh) | `.click()` |

### Parameter Job
| Deskripsi Elemen | Selector / ID | Aksi Bot |
| :--- | :--- | :--- |
| **Dropdown File Type** | `id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_FILE_TYPE_Value` | `.select_option("D")` |
| **Checkbox Separator** | `id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_FLD_SEPARATOR_STD_Value_0`| `.check()` |
| **Input Warehouse (Filter)** | `id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_grd_DynamicFilter_ctl02_dyn_Field_txt_Value` | `.fill()` |
| **Dropdown Invoiced (Filter)**| `id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_grd_DynamicFilter_ctl13_dyn_Field_drp_Value` | `.select_option("Invoiced")` |
| **Tombol Add Param** | `id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_btn_Add_Value` | `.click()` |
| **Tombol New Param (Promo)**| `id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_btn_New_Value` | `.click()` |
| **Tombol Save Job** | `id=pag_FW_SYS_INTF_JOB_RootNew_btn_Save_Value` | `.click()` |
| **Prompt OK (Server)** | `id=TF_Prompt_btn_Ok_Value` | `.click()` |
| **Tombol Download** | `id=pag_FW_SYS_INTF_STATUS_JOB_btn_Download_Value` | `.click()` |

### Filter Kalender (Ekstraksi Sales & Promosi)
*Catatan: Bot menggunakan JS injection ke `CalendarExtender` API karena popup kalender bawaan rentan error.*
| Deskripsi Elemen | ID Target JS (Input Date) | ID Target Extender |
| :--- | :--- | :--- |
| **Sales Start Date** | `..._ctl15_dyn_Field_dat_Value` | `..._ctl15_dyn_Field_dat_ajax_CalendarExtender` |
| **Sales End Date** | `..._ctl16_dyn_Field_dat_Value` | `..._ctl16_dyn_Field_dat_ajax_CalendarExtender` |
| **Promo Start Date** | `..._ctl03_dyn_Field_dat_Value` | `..._ctl03_dyn_Field_dat_ajax_CalendarExtender` |
| **Promo End Date** | `..._ctl04_dyn_Field_dat_Value` | `..._ctl04_dyn_Field_dat_ajax_CalendarExtender` |

## 4. Injeksi Stock Adjustment
Digunakan pada fungsi `_inject_adjustment_row` dan siklus utamanya.
| Deskripsi Elemen | Selector / ID | Aksi Bot |
| :--- | :--- | :--- |
| **Tombol Add Adj** | `id=pag_I_StkAdj_btn_Add_Value` | `.click()` |
| **Link Pilih Warehouse** | `a:text-is('{WAREHOUSE}')` | `.click()` |
| **Dropdown Reason Code** | `id=pag_I_StkAdj_NewGeneral_drp_n_REASON_HDR_Value` | `.select_option()` |
| **Input Kode SKU** | `id=pag_I_StkAdj_NewGeneral_sel_PRD_CD_Value` | `.fill()` dan `.press("Tab")` |
| **Label Stok Live (Screen)**| `id=pag_I_StkAdj_NewGeneral_lbl_Adjustable_Qty_Value` | `.inner_text()` (Mencek stok EA/PAC/CAR) |
| **Input Qty EA (Pcs)** | `id=pag_I_StkAdj_NewGeneral_txt_QTY1_Value` | `.fill()` |
| **Input Qty CAR (Karton)** | `id=pag_I_StkAdj_NewGeneral_txt_QTY2_Value` | `.fill()` |
| **Input Qty PAC (Pack)** | `id=pag_I_StkAdj_NewGeneral_txt_QTY3_Value` | `.fill()` |
| **Tombol Tambah SKU (Grid)** | `id=pag_I_StkAdj_NewGeneral_btn_Add_Value` | `.click()` |
| **Tombol Final Save Adj** | `id=pag_I_StkAdj_NewGeneral_btn_Save_Value` | `.click()` |
| **Pop-up Konfirmasi Save** | `id=pag_PopUp_YesNo_btn_Yes_Value` | `.click()` |

---
**Rekomendasi Pemeliharaan (Maintenance):**
Apabila skrip mulai mengalami `TimeoutError`, segera periksa daftar selector ini pada DOM Newspage melalui Developer Tools (`F12`). Prioritas utama pemeriksaan adalah elemen di modul kalender (`CalendarExtender`) dan selector ID popup yang dinamis (`id=pop_Dynamic_gft_List_2...`).
