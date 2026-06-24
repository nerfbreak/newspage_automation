# Product Requirements Document (PRD)
**Project Name:** Optimize Newspage - Stock Adjustment Automation Engine
**Document Version:** 1.0
**Date:** 24 Juni 2026

---

## 1. Executive Summary
**Optimize Newspage** adalah sebuah sistem automasi tingkat produksi (production-grade automation toolkit) yang dirancang untuk menjembatani, membandingkan, dan merekonsiliasi data stok antara sistem sentral (**Newspage**) dengan sistem yang digunakan oleh distributor. Sistem ini dibangun dengan fokus pada akurasi tinggi, keamanan operasional, dan eksekusi *zero-touch* (tanpa campur tangan manusia secara manual) untuk proses penyesuaian inventaris, pelacakan mutasi, ekstraksi penjualan, dan manajemen promosi.

## 2. Product Vision & Goals
### Vision
Menjadi pusat kendali tunggal (single pane of glass) yang mengotomatisasi seluruh proses rekonsiliasi data inventaris dan penjualan antara principal (sistem Newspage) dan distributor, menghilangkan potensi *human error*, serta menghemat waktu operasional secara signifikan.

### Goals & Objectives
1. **Automasi End-to-End:** Mengotomatisasi proses ekstraksi data dari Newspage dan menyuntikkan (inject) hasil penyesuaian (adjustment) kembali ke dalam sistem.
2. **Akurasi Data:** Memastikan tidak ada selisih stok (discrepancy) antara sistem distributor dan Newspage melalui proses perbandingan (reconciliation) yang cerdas.
3. **Keamanan Enterprise:** Melindungi kredensial sensitif distributor dan sistem melalui enkripsi tingkat tinggi (AES-256) dan manajemen sesi yang ketat.
4. **Visibilitas Operasional:** Memberikan metrik dan status basis data secara real-time melalui Dashboard interaktif.

## 3. Target Audience (Pengguna)
1. **Admin / Data Analyst:** Pengguna utama yang bertugas melakukan rekonsiliasi data harian/mingguan, menarik laporan penjualan, dan memonitor pergerakan stok.
2. **System Administrator:** Pengguna yang mengelola konfigurasi sistem, kredensial distributor (distributor vault), dan memonitor keamanan (misal: log akses, lockout).

## 4. System Architecture & Tech Stack
Sistem dibangun menggunakan arsitektur web modern yang dikombinasikan dengan *headless browser automation*.

| Komponen | Teknologi | Fungsi |
| :--- | :--- | :--- |
| **Frontend / Web App** | [Streamlit](https://streamlit.io/) | Menyediakan antarmuka pengguna (UI) yang interaktif, manajemen *state*, dan perutean halaman (routing). |
| **Automation Engine** | [Playwright](https://playwright.dev/) | Menjalankan *headless Chromium* untuk scraping, ekstraksi data, dan injeksi *stock adjustment* langsung ke web Newspage. |
| **Database** | [Supabase](https://supabase.com/) (PostgreSQL) | Menyimpan kredensial pengguna, *distributor vault*, log aktivitas, dan konfigurasi sistem (system config). |
| **Keamanan (Security)**| Bcrypt + Cryptography | Melakukan *hashing* pada password pengguna (`bcrypt`) dan mengenkripsi kredensial Newspage distributor (`AES-256 Fernet`). |
| **Sistem Alert** | Telegram Bot API | Mengirimkan notifikasi *real-time* jika terjadi anomali keamanan (seperti *account lockout*). |

## 5. Key Features & Workflows

### 5.1. Authentication & Security Gatekeeper
- **Login System:** Sistem login terpusat dengan batasan percobaan (maks. 5 kali percobaan gagal).
- **Session Management:** *Timeout* otomatis jika tidak ada aktivitas selama 1 jam (3600 detik).
- **Brute-force Protection:** Penalti waktu tunggu (*lockout* selama 5 menit) dan pengiriman alert ke Telegram jika terjadi indikasi *brute-force*.

### 5.2. Halaman 0: Dashboard (`0_dashboard.py`)
- **Fungsi:** Menampilkan status konektivitas ke database secara *real-time*, KPI metrik operasional (misal: jumlah transaksi sukses, status bot), dan tautan cepat (*quick-launch*) ke modul-modul lainnya.

### 5.3. Halaman 1: Inventory Adjustment (`1_inventory_adjustment.py`)
- **Fungsi:** Alur kerja utama (Extract → Compare → Execute).
- **Extract:** Bot (Playwright) otomatis masuk ke Newspage untuk menarik data stok riil (tanpa perlu *export* manual).
- **Compare (Smart Reconciliation):** Mengunggah data stok dari sistem distributor dan membandingkannya dengan data Newspage menggunakan algoritma *SKU mapping* dan logika pengali (*multiplier*).
- **Execute (Auto-Adjustment Bot):** Jika terdapat selisih (*discrepancy*), bot secara otomatis memasukkan data penyesuaian (adjustment) ke modul Stock Adjustment Newspage secara *live* disertai logging di terminal.

### 5.4. Halaman 2: Sales Extraction (`2_sales_extraction.py`)
- **Fungsi:** Modul ekstraksi data otomatis untuk laporan penjualan (Sales Report) berdasarkan rentang tanggal (*date-range*) dan distributor tertentu. Berguna untuk pelaporan dan analisis tren penjualan.

### 5.5. Halaman 3: Promotion Comparison (`3_promotion_comparison.py`)
- **Fungsi:** Sinkronisasi data promosi dari Newspage dan membandingkannya dengan master data di SharePoint MDM tracker. Sistem mendeteksi konflik atau ketidaksesuaian data promosi secara otomatis.

### 5.6. Halaman 4: Stock Mutation (`4_stock_mutation.py`)
- **Fungsi:** Melacak pergerakan dan mutasi stok di berbagai distributor. Sistem mengekstrak histori mutasi barang masuk, keluar, retur, dan penyesuaian dari Newspage.

### 5.7. Halaman 5: Clearance Stock (`5_clearance_stock.py`)
- **Fungsi:** Modul khusus untuk memonitor dan merekonsiliasi inventaris barang-barang *clearance* (cuci gudang atau mendekati masa kedaluwarsa).

### 5.8. Halaman 6: Initial Stock (`6_initial_stock.py`)
- **Fungsi:** Manajemen data inventaris awal (*baseline*). Digunakan saat *onboarding* distributor baru atau saat melakukan sinkronisasi ulang secara massal untuk menentukan titik nol (*initial stock*).

## 6. Security & Data Privacy
- **Zero-Plaintext Policy:** Semua konfigurasi sensitif (URL sistem klien, token) dan kata sandi distributor disimpan di tabel `system_config` dan `distributor_vault` di dalam **Supabase**, tidak di dalam kode sumber (repository).
- **Password Hashing:** Menggunakan standar `bcrypt` untuk otentikasi admin/user web.
- **Distributor Vault Encryption:** Password login ke Newspage untuk setiap distributor dienkripsi menggunakan algoritma **AES-256 Fernet**. Diperlukan `MASTER_KEY` (disimpan di `.streamlit/secrets.toml`) untuk mendekripsi data secara *on-the-fly* ketika bot akan login.

## 7. Data Models & Database Schema (Supabase)
1. `users_auth`: Menyimpan data kredensial akses ke aplikasi Streamlit (username, bcrypt password hash).
2. `distributor_vault`: Menyimpan ID distributor, nama distributor, dan informasi kredensial Newspage yang terenkripsi.
3. `system_config`: Konfigurasi *runtime* seperti `REASON_CODE` (misal: SA2), `WAREHOUSE` (misal: GOOD_WHS), `URL_LOGIN`, `TIMEOUT_MS`, dll.

## 8. Non-Functional Requirements (NFR)
- **Reliability:** Sistem bot harus memiliki mekanisme percobaan ulang (*retry mechanism*) jika halaman Newspage lambat memuat atau terjadi *timeout*.
- **Performance:** Streamlit *frontend* harus merespons interaksi pengguna dalam waktu kurang dari 2 detik. Proses Playwright (ekstraksi dan eksekusi) harus mengkomunikasikan progresnya secara *real-time* ke UI agar aplikasi tidak terlihat *hang*.
- **Usability:** Antarmuka harus sederhana, menampilkan pesan *error/success* yang jelas (*toast notifications*), dan memastikan proses yang berjalan lama memberikan indikator *spinner* atau *progress bar*.
- **Maintainability:** Komponen UI terpisah dengan logika bot (`playwright_engine.py`) dan pemrosesan data (`data_processor.py`) agar mudah dikembangkan.

## 9. Future Scope / Roadmap
- **Log Audit Trail UI:** Menambahkan halaman khusus untuk melihat riwayat aktivitas pengguna (siapa mengeksekusi penyesuaian apa dan kapan).
- **Advanced Analytics:** Menambahkan visualisasi grafik pergerakan stok dan efektivitas promosi di Dashboard.
- **Multi-tenant Support:** Ekspansi arsitektur agar dapat menangani beberapa sub-organisasi distributor secara lebih tersekat (isolated).
- **Automated Scheduler (Cron):** Integrasi penjadwalan otomatis untuk mengekstrak data penjualan dan mutasi setiap malam tanpa perlu pemicu manual dari antarmuka web.
