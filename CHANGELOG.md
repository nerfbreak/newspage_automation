# Apa yang Baru?

Berikut adalah pembaruan terbaru pada sistem otomasi Newspage:

---

## v2.5 — Juli 2026

### ✨ Fitur Baru

- **Monitor Bot Aktif di Dashboard**: Dashboard kini menampilkan daftar bot yang sedang berjalan secara real-time, termasuk jenis task, distributor yang diproses, dan user yang menjalankan. Mencegah kerja ganda antar user karena semua bisa melihat siapa yang sedang menjalankan bot untuk distributor mana.
- **Penghapusan Tombol Force Terminate**: Menghapus tombol "FORCE KILL" beserta dependensinya dari antarmuka eksekusi untuk mengembalikan alur penghentian standar.
- **Dukungan Upload CSV, XLSX, dan XLS di Semua Modul**: Semua area upload file utama kini menerima format `.csv`, `.xlsx`, dan `.xls`, termasuk Inventory Adjustment, Promotion Comparison, Stock Mutation, dan Initial Stock.
- **Skrip Otomatisasi Pemeriksaan RLS & Indeks Database**: Menambahkan utilitas baru (`scripts/supabase_rls_index_check.py`) untuk memvalidasi status Row Level Security (RLS) dan integritas indeks seluruh tabel Supabase secara otomatis dan read-only tanpa mengekspos data atau kredensial rahasia.
- **File Uploader Manual Entry**: Tambahkan opsi komponen pengunggah file (.csv, .xlsx, .xls) di modul *Manual Entry* beserta pratinjau tabel dan pemetaan (*mapping*) kolom secara otomatis, untuk mempercepat input data stok.
- **Mode Dry Run (Simulasi)**: Tambahkan toggle global di tampilan utama untuk menjalankan semua alur otomasi secara penuh tanpa menekan tombol *Save* di portal Newspage. Berguna untuk menguji konfigurasi sebelum eksekusi nyata.
- **Notifikasi Error + Screenshot**: Bot sekarang otomatis menangkap *screenshot* layar browser saat terjadi error fatal, dan mengirimkannya langsung ke Telegram beserta pesan peringatan.
- **Pelacakan File Upload**: Setiap file distributor yang diunggah sebelum eksekusi kini disimpan di Supabase. Histori file tersedia di kolom baru "File Diunggah" pada tabel Log History di Dashboard.
- **Alat Ping Server**: Menambahkan fitur "Ping" di menu Dashboard untuk mengecek apakah server portal Newspage sedang online atau merespon lambat, lengkap dengan indikator waktu respons.
- **Modul Mutasi Stok**: Fitur untuk memindahkan kuantitas stok antar distributor secara otomatis dan aman.
- **Modul Clearance Stock**: Fitur untuk mereset atau mengosongkan stok dengan cepat.
- **Ekstraksi Sales Multi-Interface**: Bot kini mampu menarik 5 jenis interface sekaligus dalam 1 kali tarikan (*Batching*) dan mengemasnya dalam format `.zip`.
- **Dashboard Riwayat Aktivitas**: Tampilan riwayat eksekusi terpadu dengan filter waktu (Hari Ini, 7 Hari, 30 Hari), badge modul berwarna, dan kolom "Dijalankan Oleh".
- **Filter Waktu Fleksibel**: Lihat riwayat aktivitas berdasarkan hari ini, 7 hari terakhir, atau 30 hari terakhir.
- **Login Persistent (Cookies)**: Sesi login disimpan selama 7 hari. Tidak akan terlogout saat me-refresh halaman.

---

### 🛠️ Perbaikan & Peningkatan

- **Pemulihan Container Mutasi Stok**: Area upload file serta tiga grup pemetaan kolom kembali tampil sebagai card Neo-Brutalist lengkap dengan border tebal, background putih, dan shadow datar.

- **Perbaikan Alignment Mutasi Stok**: Tabel DEDUCT dan ADD beserta progress bar sekarang tetap sejajar selama eksekusi, meskipun teks deskripsi barang membungkus ke jumlah baris yang berbeda.
- **Standarisasi Kode Error UI**: Mengganti pesan error teknis mentah pada notifikasi UI (toast login, timeout sesi, dan ping test) dengan kode taksonomi terstruktur (seperti [AUTH-001], [SESSION-001]) guna mempermudah pelaporan kendala tanpa membocorkan informasi sistem.
- **Pembaruan Mutasi Stok**: Kolom remark (keterangan) kini dipisah untuk masing-masing distributor pengirim dan penerima untuk pelacakan transaksi yang lebih presisi, dan kolom remark global dihapus untuk menghindari redundansi.
- **Kepatuhan Depresiasi Streamlit (Layout Widths)**: Mengimigrasi parameter lebar layout `use_container_width` yang usang ke parameter baru `width='stretch'` di seluruh modul halaman dan mesin otomasi guna mencegah potensi crash sistem di masa depan tanpa mengubah fungsi yang sudah berjalan.
- **Penghapusan Fitur Panduan**: Menghapus seluruh tombol dan modal panduan pengguna dari semua modul aplikasi untuk merapikan antarmuka dan mencegah interupsi saat bot sedang berjalan.
- **Hardening Keamanan Sistem**: Mengenkripsi cookie sesi `auth_user` menggunakan algoritme Fernet AES-256 untuk mencegah eksploitasi pembajakan sesi (Session Hijacking), dan mensanitasi parameter eksekusi subprocess di dashboard ping test menggunakan OS environment variables guna memblokir celah injeksi kode (Remote Code Execution).
- **Stabilitas Bot (Form PostBack & Retry)**: Memperbaiki kendala di mana klik tombol "Next" sering kali terabaikan dan *nyangkut* di halaman pertama karena terpotong oleh proses pemuatan ulang form secara otomatis (ASP.NET AutoPostBack). Bot kini dilengkapi dengan mekanisme *retry loop* cerdas yang akan otomatis mencoba menekan tombol navigasi halaman kembali jika perpindahan halaman gagal terdeteksi.
- **Stabilitas Bot (Page Load Wait)**: Bot kini menunggu halaman benar-benar selesai dimuat 100% sebelum melanjutkan ke langkah berikutnya, mencegah error "elemen tidak ditemukan" saat server Newspage sedang lambat.
- **Stabilitas Bot (Disclaimer Popup)**: Bot tidak lagi macet atau crash (*timeout* 60 detik) saat popup pesan awal (disclaimer) Newspage tidak muncul, memperlancar proses ekstraksi data otomatis.
- **Perbaikan Tombol Terminate & Sign Out**: Tombol *Confirm* pada dialog Terminate eksekusi dan Sign Out kini 100% andal — diperbaiki dari masalah *click-jacking*, event listener yang terputus akibat React re-render, hingga pemblokiran lintas-*iframe* di Streamlit Cloud. Kini menggunakan layout CSS murni tanpa ketergantungan pada JavaScript.
- **Perbaikan Counter Eksekusi (Bug 0/0)**: Memperbaiki bug di mana counter "PROCESSED X/Y" tidak memperbarui angkanya selama bot berjalan.
- **Perbaikan Flickering UI Eksekusi**: Layout progress bar dan tombol Terminate tidak lagi berkedip/*flicker* selama bot berjalan.
- **Perbaikan Alignment Layout Logger**: Kotak log terminal (`SYSTEM ACTIVITY`) sekarang sejajar sempurna secara horizontal di semua modul.
- **Perbaikan Koneksi Ping Superuser**: Fitur ping koneksi di Dashboard untuk kredensial Superuser kini menggunakan Playwright *subprocess* untuk menangani enkripsi RSA ASP.NET.
- **Perbaikan Dropdown Otomasi**: Menambal bug yang menyebabkan sistem macet (*Timeout* 30 detik) saat opsi "Confirmed" tidak ditemukan di interface tertentu.
- **Perbaikan Exception Warehouse**: Distributor dengan kode warehouse khusus (seperti `00GOOD_WHS`) kini ditangani dengan benar melalui tabel `warehouse_exceptions`.
- **Perbaikan Race Condition Login**: Mengganti jeda statis 5 detik dengan polling dinamis hingga 60 detik untuk menangani popup "Same User Already Logged On" yang muncul terlambat.
- **Akurasi Kuantitas Mutasi Stok**: Memperbaiki bug input angka saat mutasi yang menyebabkan kekosongan data di portal Newspage.
- **Desain UI Neo-Brutalism**: Tampilan keseluruhan diubah menjadi gaya *Neo-Brutalism* premium — kotak bersudut 90 derajat, garis tepi hitam tebal, dan efek bayangan blok hitam di semua komponen UI.
- **Perbaikan Layout Neo-Brutalism**: Memperbaiki bug visual di komponen File Uploader, dropdown Selectbox, tabel Dataframe, dan header Stock Mutation yang mengalami penumpukan border (*double border*) akibat bentrok dengan CSS internal Streamlit.
- **Perbaikan Modal Terminate & Sign Out**: Mengganti popup bawaan Streamlit dengan modal CSS murni Neo-Brutalist yang pixel-perfect dan konsisten di seluruh aplikasi.
- **Responsivitas Mobile**: Memperbaiki label tabel di Dashboard agar tidak terpotong di layar HP.
- **Indikator Loading Real-Time**: Loading bar di modul Mutasi Stok kini berjalan real-time, tidak lagi macet di tengah jalan.
- **Notifikasi Terpadu**: Menggabungkan notifikasi sukses yang menumpuk menjadi satu ringkasan yang bersih.
