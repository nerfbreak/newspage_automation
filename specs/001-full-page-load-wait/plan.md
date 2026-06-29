# Implementation Plan: Full Page Load Wait

**Branch**: `001-full-page-load-wait` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification dari `specs/001-full-page-load-wait/spec.md`

## Summary

Bot Newspage saat ini menggunakan static sleep (`page.wait_for_timeout(N)`) di semua
langkah navigasi. Pendekatan ini tidak adaptif dan menyebabkan kegagalan saat server
lambat. Solusi: tambahkan helper `_wait_for_page_ready()` berbasis `networkidle`
yang dipanggil di titik-titik kritis navigasi, tanpa mengubah logika bisnis apapun.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright (sync_api) — sudah ada, tidak ada dependency baru

**Storage**: N/A (tidak ada perubahan storage)

**Testing**: Manual — jalankan salah satu modul (misal Inventory Adjustment) dan
amati log; tidak ada lagi error "element not interactable" di langkah navigasi

**Target Platform**: Windows (Streamlit Cloud / lokal), Chromium headless

**Project Type**: Internal automation tool (Streamlit + Playwright)

**Performance Goals**: Bot berhasil menyelesaikan run penuh bahkan saat server
Newspage membutuhkan >10 detik per navigasi

**Constraints**:
- Perubahan HARUS terpusat di satu helper function baru
- TIDAK BOLEH mengubah logika bisnis (quantity, SKU, warehouse mapping)
- TIDAK BOLEH menghapus atau mengubah arti static sleep yang sudah ada
  (hanya tambah panggilan helper di titik-titik kritis)
- Unlock password "Dama" sudah diverifikasi

**Scale/Scope**: 1 helper function baru + ~8-12 panggilan tambahan di fungsi navigasi

## Constitution Check

✅ **Principle I — Feature Freeze**: Perubahan bersifat additive. Helper baru
ditambahkan ke engine; logika bisnis (data, SKU flow, quantity calc) tidak disentuh.
Unlock "Dama" sudah diverifikasi.

✅ **Principle II — Security-First**: Tidak ada perubahan credential handling.

✅ **Principle III — Selector Integrity**: Tidak ada selector baru yang digunakan.
Helper memanfaatkan `load_state` (API level) bukan DOM selector.

✅ **Principle IV — UI Consistency**: Tidak ada perubahan UI Streamlit.

✅ **Principle V — Session & Logging**: Logging tetap dilakukan via `ui_log()`.
Helper memanfaatkan parameter `ui_log` yang sudah ada.

## Project Structure

### Documentation (this feature)

```text
specs/001-full-page-load-wait/
├── spec.md          ✅ selesai
├── research.md      ✅ selesai
├── plan.md          ✅ (ini)
├── data-model.md    ✅ N/A — tidak ada entitas data baru
├── quickstart.md    ✅ selesai
└── tasks.md         ⏳ dibuat oleh /speckit-tasks
```

### Source Code (repository root)

```text
playwright_engine.py   ← satu-satunya file yang dimodifikasi
  └── _wait_for_page_ready()   [BARU — helper terpusat]
  └── _navigate_to_stock_adjustment()   [+2 panggilan helper]
  └── _navigate_to_import_export()      [+2 panggilan helper]
  └── _dispatch_extraction_job()        [+3 panggilan helper di step kritis]
  └── _dispatch_sales_job()             [+3 panggilan helper di step kritis]
  └── (fungsi lain yang punya navigasi) [+panggilan helper sesuai kebutuhan]
```

## Design: Helper Function `_wait_for_page_ready`

```python
def _wait_for_page_ready(page, timeout_ms, ui_log=None, context=""):
    """
    Menunggu halaman/in-page request selesai sepenuhnya sebelum lanjut.
    Menggunakan networkidle (500ms tanpa network activity) sebagai sinyal utama.
    Aman dipanggil kapan saja — fallback graceful jika sudah dalam kondisi idle.
    """
    wait_timeout = min(timeout_ms, 30_000)
    label = f" [{context}]" if context else ""
    if ui_log:
        ui_log("WAIT", f"Waiting for page to settle{label}...")
    try:
        page.wait_for_load_state("networkidle", timeout=wait_timeout)
    except Exception:
        # Jika networkidle timeout (e.g. server terus polling), lanjutkan saja.
        # PlaywrightTimeoutError dari operasi utama akan menangkap kegagalan nyata.
        if ui_log:
            ui_log("WAIT", f"Networkidle timeout{label} — proceeding cautiously.")
```

**Poin penting**:
- Menggunakan `try/except` internal sehingga TIDAK menghentikan run jika server
  punya background polling ringan. Error nyata tetap ditangkap oleh `wait_for(state=...)`
  di baris berikutnya.
- Parameter `context` opsional untuk log yang lebih informatif.
- `min(timeout_ms, 30_000)` — batas 30 detik untuk networkidle; cukup untuk
  semua PostBack normal Newspage.

## Titik Injeksi (di `playwright_engine.py`)

| Lokasi | Setelah aksi apa | Context label |
|--------|-----------------|---------------|
| `_navigate_to_import_export` L.106 | `sys_tab.click(force=True)` | "System tab" |
| `_navigate_to_import_export` L.121 | `page.evaluate(JS click)` | "Import/Export menu" |
| `_navigate_to_stock_adjustment` L.419 | `dispatch_event("click")` StkAdj | "StockAdj menu" |
| `_dispatch_extraction_job` L.157 | click Next | "extraction Next" |
| `_dispatch_extraction_job` L.194 | click Add | "extraction Add" |
| `_dispatch_sales_job` L.296 | click Next | "sales Next" |
| `_dispatch_sales_job` L.300 | click OK disclaimer | "sales disclaimer" |
| `_dispatch_sales_job` L.310 | click search result | "sales intf select" |
| *(tambahan lain ditemukan saat implementasi)* | | |

**CATATAN**: `page.wait_for_timeout(N)` yang sudah ada **TIDAK dihapus** —
helper dipanggil sebagai tambahan, bukan pengganti.

## Quickstart Validation

Lihat [quickstart.md](./quickstart.md) untuk panduan validasi end-to-end.
