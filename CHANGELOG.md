# Changelog

All notable changes to this project will be documented in this file.

### Fitur Baru
- Enkripsi Otomatis Kredensial: Sandi teks biasa yang disimpan di Supabase akan otomatis dienkripsi pada penggunaan pertama.
- Membaca Changelog Dinamis: Changelog dibaca langsung dari berkas sistem dan ditampilkan di halaman login Streamlit.
- Kustomisasi Favicon Web: Menggunakan ikon kucing lucu di depan laptop sebagai logo tab situs web.

### Perbaikan Bug
- Perbaikan input kuantitas Mutasi Stock: Menambahkan pencarian cadangan pada kolom `Qty` saat kolom `PAC`, `CAR`, dan `EA` kosong, sehingga kuantitas terisi dengan benar di portal Newspage.
- Perbaikan visual tabel eksekusi Mutasi Stock: Melakukan inisialisasi awal pada kolom Status dan Keterangan untuk menghindari tampilan kosong atau glitch visual.
- Perbaikan `SyntaxError` pada berkas `database.py` akibat penulisan docstring tanda kutip tiga yang tidak ter-escape dengan benar.
- Perbaikan error argumen posisi (`AttributeError`) saat mengirimkan parameter `WAREHOUSE` ganda ke fungsi `run_mutasi_execution`.
- Pengembalian fungsi eksekusi mutasi yang hilang di dalam `playwright_engine.py`.
- Peningkatan gaya visual antarmuka: Menghilangkan border bawah h1 bawaan Streamlit yang mengganggu, serta merapikan tautan kembali.
- Perbaikan progress bar Mutasi Stock yang membeku selama eksekusi dengan memperbarui status secara real-time.
- Penggabungan kotak status sukses eksekusi Mutasi Stock yang bertumpuk menjadi satu kotak ringkasan tunggal yang rapi.
