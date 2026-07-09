# Optimize Newspage Automation — Main Specification

**Last Updated**: 2026-07-06
**Revision**: Archived 017-mobile-responsive into main project memory

## User Stories & Integration Scenarios

### US-001: Prevent Deprecation Crashes and Maintain Layout Alignment (Priority: P1)
[Source: specs/016-replace-use-container-width]

Operations staff use the automation tool daily to manage inventory, mutations, and extraction history. The layout components (buttons, data editors, charts) must render correctly without visual corruption, and the application must continue running reliably without deprecation crashes or layout drift when transitioning to newer Streamlit library versions.

**Acceptance Scenarios**:
1. **Given** a user is viewing any dashboard or module page with interactive widgets, **When** the page loads, **Then** all widgets that previously had `use_container_width=True` are rendered with full container width using `width='stretch'` and align perfectly.
2. **Given** the Streamlit server console output, **When** any page runs or is refreshed, **Then** no warnings regarding the deprecation of `use_container_width` are logged.

### US-002: Mobile-First Responsive Operation (Priority: P1)
[Source: specs/017-mobile-responsive]

Mobile users must be able to view forms, data tables, and action buttons clearly on small screens without overlapping, clipping, or hunting horizontally for key actions.

**Acceptance Scenarios**:
1. **Given** a user opens the application on a mobile phone viewport under 768px, **When** they view a main execution page, **Then** input fields and execution buttons stack vertically with precise spacing and no overlap.
2. **Given** a page contains multiple action buttons, **When** the viewport is narrow, **Then** the buttons fit the screen or stack cleanly without squishing text.

### US-003: Mobile Data Grid Readability (Priority: P2)
[Source: specs/017-mobile-responsive]

Mobile users viewing reports or data grids must be able to read each row comfortably without wide tables breaking the page layout.

**Acceptance Scenarios**:
1. **Given** a user generates a data table with many columns, **When** viewing on a mobile screen, **Then** each row is transformed into a readable stacked card layout without requiring horizontal scrolling or breaking the overall page layout.

### US-004: Menjalankan Audit Keamanan Menyeluruh (Priority: P1)
[Source: specs/018-security-audit]

Sebagai pemilik atau pengelola aplikasi, saya ingin mendapatkan audit keamanan menyeluruh atas area paling berisiko sehingga saya dapat mengetahui apakah aplikasi aman digunakan untuk pekerjaan operasional harian.

**Acceptance Scenarios**:
1. **Given** audit dimulai oleh pengelola aplikasi, **When** proses audit selesai, **Then** laporan menampilkan ringkasan status keamanan keseluruhan beserta daftar temuan yang diprioritaskan.
2. **Given** audit menemukan risiko tinggi atau kritis, **When** laporan dibuat, **Then** setiap temuan memiliki dampak, bukti, tingkat keparahan, dan rekomendasi tindak lanjut yang jelas.
3. **Given** audit tidak menemukan risiko tinggi atau kritis, **When** laporan dibuat, **Then** laporan tetap mencatat area yang diperiksa dan bukti bahwa area tersebut lulus.

### US-005: Memverifikasi Perlindungan Kredensial dan Sesi (Priority: P1)
[Source: specs/018-security-audit]

Sebagai pengelola keamanan, saya ingin memastikan kredensial, data rahasia, dan sesi login terlindungi sehingga penyalahgunaan akun atau akses distributor dapat dicegah.

**Acceptance Scenarios**:
1. **Given** data rahasia tersimpan di sistem, **When** auditor meninjau sumber penyimpanan, log, dan tampilan pengguna, **Then** nilai rahasia tidak muncul sebagai teks terbaca.
2. **Given** sesi pengguna aktif, **When** batas waktu tidak aktif tercapai, **Then** pengguna harus diminta masuk kembali sebelum dapat mengakses fitur aplikasi.
3. **Given** percobaan login gagal berulang terjadi, **When** batas percobaan tercapai, **Then** akun atau sesi terkait dibatasi sesuai kebijakan penguncian.

### US-006: Memverifikasi Ketahanan Input dan Output (Priority: P2)
[Source: specs/018-security-audit]

Sebagai pengelola keamanan, saya ingin memastikan input pengguna, file unggahan, dan nilai yang ditampilkan ulang aman sehingga pengguna tidak dapat menyisipkan perintah berbahaya atau konten yang menipu.

**Acceptance Scenarios**:
1. **Given** pengguna memasukkan teks berbahaya, **When** nilai tersebut ditampilkan kembali, **Then** konten ditampilkan sebagai teks aman dan tidak dieksekusi.
2. **Given** pengguna mengunggah file dengan format, isi, atau ukuran tidak sesuai, **When** file diproses, **Then** sistem menolak file tersebut dengan pesan yang jelas tanpa memproses data berisiko.
3. **Given** nilai input akan digunakan dalam proses otomatis, **When** nilai mengandung karakter atau pola berbahaya, **Then** sistem menolak nilai tersebut atau menandainya sebagai tidak aman.

### US-007: Mengelola Tindak Lanjut Temuan Audit (Priority: P3)
[Source: specs/018-security-audit]

Sebagai pengelola aplikasi, saya ingin setiap temuan audit memiliki status tindak lanjut sehingga risiko yang ditemukan dapat diselesaikan secara terukur.

**Acceptance Scenarios**:
1. **Given** laporan audit memiliki temuan, **When** laporan ditinjau, **Then** setiap temuan memiliki rekomendasi, prioritas, dan kriteria penyelesaian.
2. **Given** temuan sudah diperbaiki, **When** audit ulang dilakukan, **Then** status temuan berubah menjadi selesai hanya jika bukti validasi tersedia.

### US-008: Clear Data Extracted Sales Button Color (Priority: P1)
[Source: specs/024-clear-sales-btn-color]

As a user, I want the "Clear Data Extracted Sales" button to be colored red, so that I can easily identify it as a destructive action and distinguish it from other buttons.

**Acceptance Scenarios**:
1. **Given** the user is viewing the page with the extracted sales data, **When** the page renders, **Then** the "Clear Data Extracted Sales" button must have a red background color.
2. **Given** the user hovers over the red "Clear Data Extracted Sales" button, **When** hovered, **Then** it must exhibit the appropriate hover effects according to the global design system.

### US-009: Remove the FORCE KILL button and functionality (Priority: P1)
[Source: specs/028-remove-force-kill]

The user wants to remove the "FORCE KILL" feature from the automation UI so that it can no longer be triggered to instantly kill Playwright OS-level processes. This reverses the changes introduced in Spec 025.

**Acceptance Scenarios**:
1. **Given** an active execution in the `playwright_engine.py`, **When** the execution is running, **Then** the "FORCE KILL" button does not appear in the Streamlit UI.
2. **Given** the codebase, **When** checking for `psutil` integration related to force killing browsers, **Then** all code related to `force_kill_callback` and `psutil` should be removed.

## Functional Requirements

### FR-001: Layout Width Parameter Migration — `use_container_width=True` → `width='stretch'`
[Source: specs/016-replace-use-container-width]
The system MUST replace all occurrences of `use_container_width=True` with `width='stretch'` inside all Python scripts under the project root (`app.py`, `utils.py`, `playwright_engine.py`, and all sub-pages under `pages/`).

### FR-002: Layout Width Parameter Migration — `use_container_width=False` → `width='content'`
[Source: specs/016-replace-use-container-width]
The system MUST replace all occurrences of `use_container_width=False` with `width='content'` inside all Python scripts.

### FR-003: Layout Integrity Preservation
[Source: specs/016-replace-use-container-width]
The updated application MUST preserve the Neo-Brutalist grid and card structure, guaranteeing zero layout shifting or visual drift.

### FR-004: Syntax and Runtime Validity
[Source: specs/016-replace-use-container-width]
All page scripts MUST load and compile without syntax errors or runtime exceptions.

### FR-005: Responsive Container Layout
[Source: specs/017-mobile-responsive]
The system MUST dynamically adjust container widths, margins, and paddings based on viewport size using CSS media queries or Streamlit-native responsive parameters.

### FR-006: Mobile Overlap Prevention
[Source: specs/017-mobile-responsive]
The system MUST prevent buttons, inputs, text areas, and table/card containers from overlapping vertically or horizontally on screen widths under 768px.

### FR-007: Touch-Friendly Controls
[Source: specs/017-mobile-responsive]
Interactive elements MUST remain easily tappable on touch screens with adequate minimum height and width, preventing accidental activation of adjacent controls.

### FR-008: Responsive Neo-Brutalism Preservation
[Source: specs/017-mobile-responsive]
Responsive mobile layouts MUST preserve the locked Neo-Brutalism design system: solid colors, thick borders, sharp corners, and distinct no-blur shadows.

### FR-009: Mobile Data Grid Transformation
[Source: specs/017-mobile-responsive]
Wide data grids MUST be rendered on mobile as readable vertical stacked cards rather than requiring horizontal scrolling.

### FR-010: Security Audit Reporting
[Source: specs/018-security-audit]
Sistem MUST menghasilkan laporan audit keamanan yang mencakup ringkasan status, area yang diperiksa, temuan, bukti, tingkat keparahan (kritis, tinggi, sedang, rendah, informasi), dan rekomendasi tindak lanjut. Laporan MUST membedakan temuan yang membutuhkan penghentian segera dari perbaikan normal, dan mencatat area yang gagal diperiksa. Laporan MUST NOT membocorkan kredensial.

### FR-011: Credential & Secret Protection Audit
[Source: specs/018-security-audit]
Sistem MUST memverifikasi bahwa kredensial dan rahasia tidak tersimpan, tampil, tercatat, atau tersedia dalam bentuk teks terbaca di area yang dapat diakses pengguna atau artefak aplikasi.

### FR-012: Session Protection Audit
[Source: specs/018-security-audit]
Sistem MUST memverifikasi bahwa sesi pengguna berakhir sesuai kebijakan tidak aktif, percobaan login gagal dibatasi (lockout), dan akses setelah sesi kedaluwarsa ditolak.

### FR-013: Input Sanitization Audit
[Source: specs/018-security-audit]
Sistem MUST memverifikasi bahwa input teks, file unggahan, dan nilai konfigurasi yang berisiko ditolak atau dinetralkan sebelum diproses atau di-render ulang.

### FR-014: Clear Sales Button Red Styling
[Source: specs/024-clear-sales-btn-color]
System MUST style the "Clear Data Extracted Sales" button with a red color.

### FR-015: Clear Sales Button Neo-Brutalism Styling
[Source: specs/024-clear-sales-btn-color]
System MUST ensure the button's styling adheres to the locked Neo-Brutalism design system (e.g., hard borders, sharp corners, solid shadow).

### FR-016: Preserved Functionality
[Source: specs/024-clear-sales-btn-color]
System MUST NOT alter the existing functionality of the button.

### FR-017: Remove Force Kill Button UI
[Source: specs/028-remove-force-kill]
System MUST NOT display the "FORCE KILL" button during any browser automation execution.

### FR-018: Remove Force Kill Logic
[Source: specs/028-remove-force-kill]
System MUST remove the underlying logic (`psutil` integration and session state flags) associated with the Force Kill feature.

## Key Entities

- **Viewport** [Source: specs/017-mobile-responsive]: The visible browser area that determines mobile, tablet, or desktop layout behavior.
- **UI Container** [Source: specs/017-mobile-responsive]: Streamlit columns, expanders, forms, tables, and card blocks that must resize or stack responsively.
- **Audit Report** [Source: specs/018-security-audit]: Laporan hasil audit berisi ringkasan keamanan, cakupan, temuan, bukti aman, dan rekomendasi.
- **Audit Finding** [Source: specs/018-security-audit]: Temuan individual dengan area, tingkat keparahan, dampak, bukti, rekomendasi, dan status.

## Edge Cases & Error Handling

- **Mismatched Streamlit Version**: If a developer runs the application on an old local Streamlit version that does not support the `width` parameter yet, it could cause layout issues or launch errors. Mitigated by ensuring Streamlit is pinned to a version supporting the `width` parameter.
- **Custom Components**: Third-party custom components that use a custom wrapper might not support the new parameter. Mitigated: All standard Streamlit elements in the codebase are native widgets.
- **Very Wide Data Tables** [Source: specs/017-mobile-responsive]: Wide rows must remain readable on narrow screens by transforming into stacked card layouts.
- **Orientation Changes** [Source: specs/017-mobile-responsive]: Portrait-to-landscape viewport changes should preserve button/input visibility and prevent overlapping.
- **Third-Party Embeds** [Source: specs/017-mobile-responsive]: Any embeds present in responsive areas must either resize correctly or be confirmed out of scope for the feature.
- **Audit Access Limitation** [Source: specs/018-security-audit]: Jika audit tidak dapat memeriksa satu area karena konfigurasi atau akses, laporan harus mencatatnya secara eksplisit.
- **Secret Spill Detection** [Source: specs/018-security-audit]: Jika data rahasia bocor di log atau unduhan, hal tersebut diangkat sebagai temuan berisiko. Laporan yang dihasilkan harus diedit agar tidak memuat ulang bukti bocornya secara mentah.

- **Design System Constraint** [Source: specs/024-clear-sales-btn-color]: What happens if the global design system dictates a specific hover color for red buttons? It should be applied correctly.

## Success Criteria

- **SC-001**: 100% of files containing `use_container_width` are successfully migrated to use the `width` parameter.
- **SC-002**: The application console is free of `use_container_width` deprecation warnings on server startup and runtime usage.
- **SC-003**: A visual audit of all Streamlit pages confirms that no container borders or button margins shift or break, keeping layout integrity intact.
- **SC-004** [Source: specs/017-mobile-responsive]: 100% of primary execution buttons and input fields are visible and clickable without horizontal scrolling on a 320px viewport.
- **SC-005** [Source: specs/017-mobile-responsive]: No UI elements visually overlap or overflow their parent containers on screens down to 320px width.
- **SC-006** [Source: specs/017-mobile-responsive]: Neo-Brutalism borders, shadows, and colors remain consistent between desktop and mobile views.
- **SC-007** [Source: specs/018-security-audit]: 100% area audit wajib memiliki status lulus, gagal, atau tidak dapat diperiksa. 100% temuan kritis memiliki tindak lanjut.
- **SC-008** [Source: specs/018-security-audit]: 0 rahasia mentah muncul dalam laporan audit, log audit, atau artefak.
- **SC-009** [Source: specs/018-security-audit]: 100% skenario sesi kedaluwarsa, pencegahan input (XSS/RCE), dan enkripsi AES memiliki hasil verifikasi yang terdokumentasi dan aman.

- **SC-010** [Source: specs/024-clear-sales-btn-color]: 100% of page loads display the "Clear Data Extracted Sales" button in red.
- **SC-011** [Source: specs/024-clear-sales-btn-color]: The button maintains existing click functionality with 0 regressions.
- **SC-012** [Source: specs/028-remove-force-kill]: The "FORCE KILL" button is absent from the execution UI in 100% of automation runs.
- **SC-013** [Source: specs/028-remove-force-kill]: The `psutil` dependency or specific usage for force-killing Playwright browsers is removed from `playwright_engine.py`.

## Revision Notes

- **2026-07-06**: Archived mobile-first responsive design from `specs/017-mobile-responsive`, adding US-002, US-003, FR-005 through FR-009, SC-004 through SC-006, responsive entities, and mobile edge cases.
- **2026-07-06**: Archived System Security Audit from `specs/018-security-audit`, adding US-004 through US-007, FR-010 through FR-013, Audit entities, SC-007 through SC-009, and security edge cases.
- **2026-07-08**: Archived Clear Sales Button Color from `specs/024-clear-sales-btn-color`, adding US-008, FR-014 through FR-016, and SC-010, SC-011.
- **2026-07-09**: Archived Remove Force Kill Feature from `specs/028-remove-force-kill`, adding US-009, FR-017, FR-018, SC-012, SC-013.
