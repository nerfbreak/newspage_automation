# Apa yang Baru?

Berikut adalah pembaruan terbaru pada sistem otomasi Newspage:

### ✨ Fitur Baru
- **Ekstraksi Sales Multi-Interface**: Bot Ekstraksi Data Sales sekarang mampu menarik 5 jenis interface sekaligus (`E_28880804000000001`, `00`, `02`, `03`, dan `06`) dalam 1 kali tarikan (*Batching*) dan mengemasnya dalam format `.zip`.
- **Alat Ping Server**: Menambahkan fitur "Ping" di menu Dashboard untuk mengecek apakah server portal Newspage sedang online atau merespon lambat, lengkap dengan indikator waktu respons (*Response Time*).
- **Dashboard Riwayat Aktivitas**: Tampilan dashboard baru yang lebih bersih dan rapi untuk memantau seluruh riwayat eksekusi bot secara langsung.
- **Modul Mutasi Stok**: Fitur baru untuk memindahkan kuantitas stok antar distributor secara otomatis dan aman.
- **Modul Clearance Stock**: Fitur baru untuk mereset atau mengosongkan stok dengan cepat.
- **Filter Waktu Fleksibel**: Sekarang Anda bisa melihat riwayat aktivitas berdasarkan hari ini, 7 hari terakhir, atau 30 hari terakhir.
- **Peningkatan Visual & Animasi**: Menambahkan animasi halus (transisi, efek sentuhan pada tombol, dan loading halaman) yang membuat aplikasi terasa lebih premium dan responsif.
- **Tampilan Bebas Gangguan**: Menyembunyikan menu bawaan Streamlit (seperti bar atas dan samping) secara penuh untuk memberikan pengalaman desain yang lebih fokus, luas, dan bersih.

### 🛠️ Perbaikan & Peningkatan
- **Desain UI Neo-Brutalism**: Mengubah total tampilan dan estetika aplikasi menjadi gaya *Neo-Brutalism* berkelas premium dengan kotak bersudut siku 90 derajat, garis tepi (*border*) hitam tebal yang tegas, dan efek bayangan (*drop shadow*) blok hitam pekat bertegangan tinggi di semua tombol, metrik, dan tabel log.
- **Penyempurnaan Tampilan UI**: Merapikan garis bawah pada judul tiap sesi agar pas sesuai panjang teks, memperbaiki ukuran tombol aksi yang terlalu lebar, dan mengubah warna teks log terminal (SYS, NAV, AUTH) agar senada dan serasi dengan tema Streamlit Biru-Abu.
- **Perbaikan Dropdown Otomasi**: Menambal *bug* yang menyebabkan sistem macet (*Timeout* 30 detik) saat opsi "Confirmed" pada kolom *Dynamic Filter* tidak ditemukan di *interface* tertentu pada saat proses ekstraksi data.
- **Stabilitas Bot (Page Load Wait)**: Bot sekarang menunggu halaman benar-benar selesai dimuat 100% sebelum melanjutkan ke langkah berikutnya. Ini mencegah error seperti "elemen tidak ditemukan" yang sering terjadi saat server Newspage sedang lambat.
- **Akurasi Kuantitas**: Memperbaiki sistem input angka saat proses mutasi agar tidak terjadi error atau kekosongan data di portal Newspage.
- **Tampilan Tabel Eksekusi**: Merapikan tabel proses saat bot berjalan agar lebih enak dibaca dan rapi dari awal eksekusi.
- **Indikator Loading**: Memperbaiki loading bar yang sering macet saat proses Mutasi Stok berjalan, sekarang progress terlihat real-time.
- **Notifikasi Rapi**: Menggabungkan notifikasi sukses yang menumpuk menjadi satu ringkasan yang jelas dan bersih.
- **Optimalisasi Tampilan**: Memperbaiki jarak dan spasi di berbagai halaman agar aplikasi lebih responsif dan nyaman digunakan.
- **Responsivitas HP (Mobile)**: Memperbaiki label pada tabel riwayat di Dashboard agar teks tidak terpotong atau berantakan saat dibuka melalui layar HP yang kecil.
- **Keselarasan Halaman Login**: Memperbaiki tata letak teks dan ikon pada halaman *Login* agar posisinya sejajar sempurna dan presisi di tengah layar.
