# Tasks: Full Page Load Wait

**Feature**: 001-full-page-load-wait
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Generated**: 2026-06-30

> ⚠️ **Frozen Module** — Unlock password "Dama" telah diverifikasi.
> Perubahan pada `playwright_engine.py` bersifat **additive only**.

---

## Dependencies

```
Phase 1 (Setup) → Phase 2 (Core Helper) → Phase 3 (US1 Injection) → Phase 4 (US2 Injection) → Phase 5 (US3 Polish)
```

US1, US2, US3 bergantung pada Phase 2 (helper harus ada dulu sebelum bisa digunakan).

---

## Phase 1: Setup

- [x] T001 Buka `playwright_engine.py` dan tandai semua lokasi `page.wait_for_timeout(N)` yang muncul setelah operasi navigasi/klik utama — buat komentar inline `# CANDIDATE: replace with _wait_for_page_ready` untuk tracking dalam `playwright_engine.py`

---

## Phase 2: Foundational — Core Helper

- [x] T002 Tambahkan helper function `_wait_for_page_ready(page, timeout_ms, ui_log=None, context="")` tepat setelah definisi `_login()` di `playwright_engine.py`. Implementasi: `page.wait_for_load_state("networkidle", timeout=min(timeout_ms, 30000))` dalam try/except yang graceful (log WAIT jika berhasil, log WAIT warning jika timeout tapi lanjut)

---

## Phase 3: User Story 1 — Bot Menunggu Halaman Siap Sebelum Klik

*Goal: Semua navigasi menu utama menunggu page settle sebelum lanjut.*
*Independent Test: Jalankan Inventory Adjustment di server lambat — tidak ada "element not found" error di step navigasi.*

- [x] T003 [US1] Di `_navigate_to_import_export()` dalam `playwright_engine.py`: tambahkan panggilan `_wait_for_page_ready(page, TIMEOUT_MS, ui_log, "System tab")` tepat setelah `sys_tab.click(force=True)` di blok try (sebelum `page.wait_for_timeout(800)` yang ada)

- [x] T004 [US1] Di `_navigate_to_import_export()` dalam `playwright_engine.py`: tambahkan panggilan `_wait_for_page_ready(page, TIMEOUT_MS, ui_log, "Import/Export menu")` tepat setelah `page.evaluate(f"document.getElementById('{target_id}').click()")` (sebelum `page.wait_for_timeout(1500)` yang ada)

- [x] T005 [US1] Di `_navigate_to_stock_adjustment()` dalam `playwright_engine.py`: tambahkan panggilan `_wait_for_page_ready(page, TIMEOUT_MS, ui_log, "StockAdj menu")` tepat setelah baris `page.locator("id=pag_InventoryRoot_tab_Main_itm_StkAdj").first.dispatch_event("click")` (sebelum baris wait berikutnya)

- [x] T006 [US1] Cari seluruh fungsi `_navigate_to_*` lainnya di `playwright_engine.py` (jika ada), dan tambahkan panggilan `_wait_for_page_ready` dengan context label yang sesuai setelah setiap `dispatch_event("click")` atau `.click(force=True)` pada elemen navigasi menu

---

## Phase 4: User Story 2 — Bot Menunggu Elemen Interaktif Siap

*Goal: Setelah navigasi, pastikan form/tombol siap sebelum berinteraksi.*
*Independent Test: Run Stock Mutation saat server lambat — bot tidak langsung klik sebelum elemen muncul.*

- [x] T007 [US2] Di `_dispatch_extraction_job()` dalam `playwright_engine.py`: tambahkan `_wait_for_page_ready(page, TIMEOUT_MS, ui_log, "extraction Next")` tepat setelah `page.locator("id=pag_FW_SYS_INTF_JOB_RootNew_btn_Next_Value").click(force=True)` (sebelum `page.wait_for_timeout(1000)` yang ada)

- [x] T008 [US2] Di `_dispatch_extraction_job()` dalam `playwright_engine.py`: tambahkan `_wait_for_page_ready(page, TIMEOUT_MS, ui_log, "extraction Add commit")` tepat setelah `page.locator("id=pag_FW_SYS_INTF_JOB_DTL_PopupNew_btn_Add_Value").click(force=True)` (sebelum `page.wait_for_timeout(2000)` yang ada)

- [x] T009 [US2] Di `_dispatch_sales_job()` dalam `playwright_engine.py`: tambahkan `_wait_for_page_ready(page, TIMEOUT_MS, ui_log, "sales Next")` tepat setelah click Next, dan `_wait_for_page_ready(page, TIMEOUT_MS, ui_log, "sales intf select")` setelah klik hasil interface selection

- [x] T010 [US2] Di semua fungsi `_dispatch_*` lainnya (jika ada): periksa pola `.click(force=True)` yang diikuti oleh `page.wait_for_timeout(N>=1000)` — ini adalah kandidat utama untuk prepend `_wait_for_page_ready`. Terapkan secara konsisten

---

## Phase 5: User Story 3 & Polish — Konsistensi & Validasi

*Goal: Semua modul menggunakan mekanisme wait yang sama.*

- [x] T011 [US3] Lakukan audit menyeluruh `playwright_engine.py`: cari semua fungsi yang punya `page.wait_for_timeout(N)` setelah click pada tombol yang memicu PostBack (bukan setelah `fill()` atau `select_option()`). Untuk setiap kandidat yang belum ditangani di T003-T010, tambahkan `_wait_for_page_ready` dengan context label yang deskriptif

- [x] T012 Hapus atau comment-out semua marker `# CANDIDATE: replace with _wait_for_page_ready` yang dibuat di T001 (cleanup tracking markers) dalam `playwright_engine.py`

- [x] T013 Update `.agents/MEMORY.md` dengan changelog entry: implementasi `_wait_for_page_ready()` helper di `playwright_engine.py` (Unlocked via password verification)

---

## Parallel Opportunities

| Group | Tasks | Bisa dikerjakan bersamaan? |
|-------|-------|---------------------------|
| A | T003, T004 | ✅ Ya — titik berbeda di fungsi sama |
| B | T007, T008 | ✅ Ya — titik berbeda di fungsi sama |
| C | T009, T010 | ✅ Ya — fungsi berbeda |
| D | T005, T006 | ✅ Ya — fungsi berbeda |

**Sequential requirement**: T002 harus selesai sebelum T003-T011.

---

## MVP Scope

**Minimum untuk SC-001**: T001 + T002 + T003 + T004 + T005
→ Helper ada + navigasi ke Import/Export dan StockAdj sudah di-guard.
Ini mencakup ~80% kasus failure yang pernah terjadi.

**Full scope**: T001 – T013 (semua modul ter-cover, cleanup, dan memory terupdate).

---

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 13 |
| Phase 2 (blocking) | 1 task (T002) |
| US1 tasks | 4 tasks |
| US2 tasks | 4 tasks |
| US3 + Polish | 3 tasks |
| Cleanup | 1 task |
| Memory update | 1 task |
| File dimodifikasi | 1 (`playwright_engine.py`) |
| File baru | 0 |
