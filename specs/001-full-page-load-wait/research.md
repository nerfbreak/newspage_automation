# Research: Full Page Load Wait

**Feature**: 001-full-page-load-wait
**Date**: 2026-06-30

## Temuan & Keputusan Teknis

### 1. Pola Wait yang Ada Saat Ini

**Keputusan**: Existing code menggunakan **static sleep** (`page.wait_for_timeout(N)`) hampir di setiap langkah.

**Temuan konkret dari codebase**:
- `page.wait_for_timeout(1000)` — digunakan 20+ kali di seluruh `playwright_engine.py`
- `page.wait_for_timeout(500)`, `800`, `1500`, `2000`, `3500` — variasi arbitrary
- Beberapa tempat sudah menggunakan `wait_for(state="visible")` dengan benar (best practice)
- Login menggunakan polling loop yang sudah cukup baik (tidak memakai sleep buta)
- Popup loader (`pop_Dynamic_*`) sudah pakai `timeout=max(TIMEOUT_MS, 180000)` untuk kasus slow

**Masalah inti**: Static sleeps tidak adaptif — terlalu cepat di server lambat, terlalu lambat di server cepat.

**Alternatif yang dipertimbangkan**:
- **Option A**: Ganti semua static sleep → ditolak. Terlalu destruktif, menyentuh 100+ baris di frozen module tanpa nilai tambah setimpal.
- **Option B**: Tambahkan helper `_wait_for_page_ready(page, TIMEOUT_MS)` yang dipanggil setelah click navigasi → dipilih. Bedah minimal, terpusat.
- **Option C**: Ubah semua `wait_until` ke `networkidle` global → sudah dilakukan pada `page.goto()` dan `page.wait_for_url()`. Tidak cukup untuk in-page navigation karena tidak ada URL change.

### 2. Strategi Wait yang Dipilih: Multi-Signal Composite Wait

Satu helper function `_wait_for_page_ready(page, timeout_ms, ui_log=None)` yang menunggu **semua sinyal berikut selesai**:

| Sinyal | API Playwright | Alasan |
|--------|---------------|--------|
| Network idle | `page.wait_for_load_state("networkidle")` | Tunggu semua AJAX/XHR selesai |
| No spinner visible | `page.locator(".loading-spinner").wait_for(hidden)` | Tunggu overlay hilang |
| DOM stable | Custom polling: attribute mutation settled | Tunggu dynamic content settle |

**Catatan**: Newspage menggunakan ASP.NET WebForms dengan UpdatePanel. Setelah klik, browser melakukan partial AJAX (PostBack), bukan full page reload. Karena itu `networkidle` adalah sinyal terbaik yang tersedia.

**Rationale dipilih**:
- `networkidle` menunggu 500ms tanpa network activity → sangat relevan untuk PostBack
- Tidak perlu tahu spinner ID spesifik per halaman
- Fallback aman: jika sudah networkidle tapi ada sisa wait, lanjut saja

### 3. Posisi Injection

**Keputusan**: Tambahkan `_wait_for_page_ready()` **tepat sebelum** operasi yang sering gagal:
1. Setelah setiap `dispatch_event("click")` pada menu navigasi
2. Setelah setiap `.click(force=True)` pada tombol "Next", "Save", "OK"
3. Setelah setiap `select_option()` yang memicu PostBack server

**TIDAK mengganti** `page.wait_for_timeout()` yang sudah ada — cukup **prepend** atau **append** helper call di titik-titik kritis.

**Rationale**: Mengurangi scope perubahan seminimal mungkin. Frozen module diubah hanya pada baris yang diperlukan.

### 4. Timeout Configuration

**Keputusan**: Gunakan `TIMEOUT_MS` yang sudah ada (diteruskan dari Streamlit UI) sebagai batas atas.
- Default yang sudah ada: 60.000 ms (60 detik)
- Untuk popup berat: sudah ada override `max(TIMEOUT_MS, 180000)` — pertahankan
- `_wait_for_page_ready` menggunakan `min(timeout_ms, 30000)` untuk networkidle
  (networkidle dalam 30 detik sudah lebih dari cukup; jika lebih lama berarti ada masalah)

**Alternatif ditolak**: Membuat config baru di Streamlit UI untuk mengatur timeout wait → unnecesary complexity.

### 5. Error Reporting

**Keputusan**: Gunakan `ui_log("WAIT", "...")` untuk log saat menunggu, dan biarkan `PlaywrightTimeoutError` yang sudah ada menangani failure — tidak perlu custom exception class baru.

**Rationale**: Error handling sudah ada di setiap `run_*` function dengan `except PlaywrightTimeoutError`. Cukup pastikan `_wait_for_page_ready` melempar `PlaywrightTimeoutError` secara natural (via `.wait_for_load_state()`).
