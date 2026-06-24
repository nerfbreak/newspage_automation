# PRD: Optimize Newspage — Version 2.0

## 1. Product Overview

**Product Name:** Optimize Newspage  
**Version:** 2.0 (Proposed)  
**Type:** Internal Automation Tool  
**Target Users:** IT Support / Stock Controllers / Admin at Newspage distributors  
**Core Value:** Mengembangkan versi 1.0 yang sudah stabil dengan menambahkan otomasi terjadwal, akses berbasis peran (RBAC), multi-warehouse, serta perbaikan *technical debt* menuju arsitektur yang lebih modern dan skalabel.

---

## 2. Problem Statement & Motivation v2.0

Pada v1.0, alat ini telah sukses mengeliminasi rekonsiliasi manual dan entry data melalui Streamlit dan Playwright. Namun, terdapat tantangan baru seiring dengan bertambahnya penggunaan:
- Ekstraksi masih harus dipicu (*trigger*) secara manual oleh user setiap bulan.
- *Technical debt* seperti modul caching yang tidak *thread-safe* mulai berisiko pada penggunaan *multi-user* yang simultan.
- Semua pengguna memiliki hak akses penuh (tidak ada pemisahan antara Admin dan Operator).
- Membutuhkan antarmuka API (*Headless Mode*) agar bisa diintegrasikan dengan sistem internal lain.

---

## 3. User Personas (Updated)

| Persona | Role | Needs | Akses v2.0 |
|---------|------|-------|------------|
| **Operator (Stock Controller)** | Operations | Menjalankan ekstraksi, upload file, review diffs, eksekusi | Hanya modul eksekusi & ekstraksi |
| **Viewer (Auditor/Manager)** | Management | Melihat dashboard KPI dan riwayat audit | Read-only Dashboard & Logs |
| **Admin (IT Support)** | Technical | Mengelola *credentials* distributor, *Role Management*, konfigurasi Supabase | Full Access |

---

## 4. Functional Requirements (New for v2.0)

### 4.1 Role-Based Access Control (RBAC)
- **FR-AUTH-05:** Menambahkan tabel `roles` di Supabase dan mengaitkannya dengan `users_auth`.
- **FR-AUTH-06:** Restriksi modul Streamlit berdasarkan peran (Operator tidak bisa masuk ke menu konfigurasi).

### 4.2 Automation & Scheduler
- **FR-AUTO-01:** Fitur **Cron-style Scheduler** untuk menjalankan ekstraksi stok dan promosi harian/bulanan secara otomatis di *background*.
- **FR-AUTO-02:** Mengirimkan hasil ekstraksi otomatis via Telegram atau Email kepada user yang ditugaskan.

### 4.3 Multi-Warehouse Support
- **FR-WHS-01:** Kemampuan untuk memetakan dan mengeksekusi penyesuaian ke gudang selain `GOOD_WHS` (misal: gudang BS, gudang transit).
- **FR-WHS-02:** Opsi *dropdown* pemilihan target *warehouse* sebelum eksekusi pada UI.

### 4.4 API Layer (Headless Mode)
- **FR-API-01:** Membungkus `playwright_engine.py` ke dalam REST API internal (FastAPI/Flask) agar sistem lain bisa memanggil bot tanpa melalui UI Streamlit.

---

## 5. Non-Functional Requirements & Tech Debt Resolution

| Category | Requirement / Refactoring |
|----------|---------------------------|
| **Thread Safety** | Mengganti *module-level cache* pada `database.py` menggunakan `@st.cache_resource` atau session state untuk *multi-user safety*. |
| **Singleton Fix** | Menghapus penggunaan `importlib.reload(playwright_engine)` yang mematahkan *singleton caching* antar halaman. |
| **Testing** | Implementasi *Test Suite* menggunakan `pytest` untuk `data_processor.py`, `utils.py`, dan `database.py`. |
| **Maintainability** | (Opsional) Memulai migrasi bertahap dari Streamlit ke *Reflex* jika UI mulai terlalu kompleks. |
| **Memory System**| AI-Facing Memory System (`docs/memory/`) digunakan untuk melacak semua keputusan arsitektur. |

---

## 6. Data Model Updates (Supabase)

Tabel baru atau modifikasi yang dibutuhkan:
- **`roles` (New):** `role_id`, `role_name`, `permissions_json`
- **Alter `users_auth`:** Tambah kolom `role_id`
- **`scheduled_jobs` (New):** `job_id`, `distributor_id`, `cron_schedule`, `last_run`, `status`
- **Alter `distributor_exceptions`:** Perluas tabel ini untuk mendukung pemetaan multi-gudang dinamis.

---

## 7. Acceptance Criteria for v2.0

- [ ] Arsitektur aman untuk banyak *user* secara bersamaan (*Thread-safe* DB calls).
- [ ] Terdapat minimal 3 peran (Admin, Operator, Viewer) dengan UI yang menyesuaikan.
- [ ] Pengguna bisa mengatur jadwal ekstraksi otomatis.
- [ ] Tersedia endpoint API lokal untuk `run_execution`.
- [ ] Unit testing (Pytest) mencakup minimal 70% *code coverage* dari fungsi logik.
