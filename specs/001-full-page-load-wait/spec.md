# Feature Specification: Full Page Load Wait

**Feature Branch**: `001-full-page-load-wait`

**Created**: 2026-06-30

**Status**: Draft

**Input**: User description: "gw mau kalo setiap interaksi bot nya itu menunggu
semua halaman beres loading 100% baru lanjut step nya"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bot Menunggu Halaman Siap Sebelum Klik (Priority: P1)

Ketika bot menjalankan otomasi di portal Newspage, setiap kali terjadi perpindahan
halaman atau navigasi antar menu, bot harus menunggu sampai seluruh konten halaman
benar-benar selesai dimuat sebelum melanjutkan ke langkah berikutnya. Saat ini bot
kadang mencoba klik atau mengisi form sebelum elemen target muncul, menyebabkan
error atau data yang tidak tertulis.

**Why this priority**: Ini adalah masalah reliability inti. Semua modul (Inventory
Adjustment, Stock Mutation, Sales Extraction, dll.) bergantung pada langkah navigasi
yang andal. Kegagalan di sini berarti seluruh run gagal.

**Independent Test**: Dapat diuji dengan menjalankan satu modul (misal Inventory
Adjustment) dan mengamati apakah bot menunggu spinner/loading hilang sebelum
melanjutkan klik berikutnya.

**Acceptance Scenarios**:

1. **Given** bot baru saja mengklik menu navigasi, **When** halaman masih loading
   (spinner terlihat atau DOM belum stabil), **Then** bot menunggu sampai loading
   selesai sebelum melanjutkan aksi berikutnya.
2. **Given** halaman selesai dimuat, **When** elemen target sudah tersedia di DOM,
   **Then** bot langsung melanjutkan tanpa delay tambahan yang tidak perlu.
3. **Given** halaman gagal dimuat dalam batas waktu tertentu, **When** timeout
   tercapai, **Then** bot mencatat error dan menghentikan run dengan pesan yang jelas.

---

### User Story 2 - Bot Menunggu Elemen Interaktif Siap (Priority: P2)

Selain menunggu halaman dimuat, bot harus memastikan elemen target (input field,
tombol, dropdown) sudah dalam kondisi interaktif (tidak disabled, tidak tertutup
overlay loading) sebelum mencoba berinteraksi dengannya.

**Why this priority**: Halaman bisa saja sudah "dimuat" secara teknis tapi elemen
masih dalam kondisi disabled atau tertutup overlay. Ini menyebabkan klik yang tidak
terdeteksi atau isian yang tidak masuk.

**Independent Test**: Dapat diuji dengan mengamati apakah bot berhasil mengisi
form quantity tanpa error meskipun server Newspage lambat merespons setelah navigasi.

**Acceptance Scenarios**:

1. **Given** halaman sudah dimuat tapi ada overlay loading di atas form, **When**
   bot hendak mengisi input, **Then** bot menunggu overlay tersebut hilang terlebih
   dahulu.
2. **Given** elemen input masih dalam kondisi disabled, **When** bot hendak mengisi
   nilai, **Then** bot menunggu elemen menjadi enabled sebelum mengisi.

---

### User Story 3 - Konsistensi di Semua Modul (Priority: P3)

Perilaku "tunggu loading selesai" ini harus berlaku secara konsisten di semua modul
yang ada: Stock Mutation, Inventory Adjustment, Sales Extraction, Promotion
Comparison, Clearance Stock, dan Initial Stock — tanpa mengubah logika bisnis
masing-masing modul.

**Why this priority**: Jika hanya sebagian modul yang diperbaiki, pengalaman akan
tidak konsisten dan debugging menjadi lebih sulit.

**Independent Test**: Dapat diuji dengan menjalankan seluruh modul secara berurutan
dan memverifikasi tidak ada timeout atau elemen-not-found error pada langkah navigasi.

**Acceptance Scenarios**:

1. **Given** modul manapun dijalankan, **When** terjadi navigasi halaman,
   **Then** mekanisme tunggu yang sama diterapkan secara seragam.

---

### Edge Cases

- Apa yang terjadi jika halaman tidak pernah selesai loading (infinite spinner)?
  → Bot harus timeout setelah batas waktu maksimum dan melaporkan error yang jelas.
- Apa yang terjadi jika server Newspage sangat lambat (>30 detik)?
  → Batas waktu tunggu harus bisa dikonfigurasi, bukan nilai hardcoded yang terlalu
  pendek.
- Apa yang terjadi jika elemen muncul tapi segera hilang lagi (transient state)?
  → Bot harus menunggu kondisi stabil, bukan hanya kemunculan sesaat.
- Bagaimana jika koneksi internet terputus di tengah loading?
  → Bot harus mendeteksi kondisi ini dan melaporkannya sebagai network error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Bot HARUS menunggu halaman selesai dimuat sepenuhnya sebelum
  melanjutkan setiap langkah navigasi.
- **FR-002**: Bot HARUS menunggu semua spinner/indikator loading di halaman
  menghilang sebelum berinteraksi dengan elemen.
- **FR-003**: Bot HARUS memverifikasi bahwa elemen target dalam kondisi interaktif
  (visible + enabled + tidak tertutup overlay) sebelum melakukan klik atau pengisian.
- **FR-004**: Bot HARUS memiliki batas waktu maksimum (timeout) untuk setiap
  operasi tunggu, dengan nilai default yang dapat dikonfigurasi.
- **FR-005**: Bot HARUS mencatat log yang jelas ketika timeout terjadi, menyebutkan
  halaman atau elemen mana yang gagal dimuat dalam batas waktu.
- **FR-006**: Mekanisme tunggu ini HARUS diterapkan secara terpusat sehingga semua
  modul mendapatkan perilaku yang sama tanpa duplikasi kode.
- **FR-007**: Perubahan ini TIDAK BOLEH mengubah logika bisnis (data yang ditulis,
  urutan SKU, kalkulasi quantity) dari modul manapun.

### Key Entities

- **Page Navigation Event**: Setiap aksi yang menyebabkan perpindahan atau reload
  halaman di portal Newspage.
- **Loading Indicator**: Elemen visual (spinner, skeleton, overlay) yang menandakan
  halaman sedang dalam proses memuat.
- **Interactive Element**: Elemen DOM yang siap menerima input pengguna (visible,
  enabled, tidak tertutup).
- **Wait Timeout**: Batas waktu maksimum yang ditoleransi untuk setiap operasi
  tunggu sebelum dianggap gagal.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tidak ada error "element not found" atau "element not interactable"
  yang disebabkan oleh kondisi loading di semua run normal.
- **SC-002**: Bot berhasil menyelesaikan full run di semua modul tanpa intervensi
  manual, bahkan ketika server Newspage membutuhkan lebih dari 10 detik untuk
  merespons setiap navigasi.
- **SC-003**: Ketika timeout terjadi, pesan error di UI Streamlit menyebutkan
  secara spesifik halaman atau elemen mana yang gagal (bukan pesan generik).
- **SC-004**: Tidak ada perubahan pada hasil data yang ditulis ke portal
  (quantity, SKU, distributor) — hanya timing yang berubah.

## Assumptions

- Bot beroperasi di lingkungan dengan koneksi internet aktif ke portal Newspage.
- Portal Newspage menggunakan indikator loading standar (spinner atau perubahan
  state DOM) yang dapat dideteksi secara programatik.
- Nilai timeout default yang wajar adalah 60 detik per operasi tunggu (konsisten
  dengan timeout login yang sudah ada).
- Semua modul yang ada saat ini menggunakan fungsi helper yang sama di
  `playwright_engine.py`, sehingga perubahan terpusat akan otomatis berlaku
  ke seluruh modul.
- Perubahan ini dianggap modifikasi modul frozen dan memerlukan password unlock
  (sudah diverifikasi: "Dama").
