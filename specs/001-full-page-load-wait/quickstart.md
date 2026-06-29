# Quickstart Validation: Full Page Load Wait

**Feature**: 001-full-page-load-wait
**Date**: 2026-06-30

## Prasyarat

- Aplikasi Optimize berjalan (`streamlit run app.py`)
- Credentials distributor valid tersedia di Supabase vault
- Koneksi ke portal Newspage aktif

## Cara Validasi

### Test 1 — Lihat Log WAIT di Terminal Output

1. Buka halaman **Inventory Adjustment** di aplikasi
2. Upload file Excel distributor
3. Klik **Jalankan Otomasi**
4. Amati log di panel terminal bawah layar

**Expected output** (harus muncul di antara step NAV):
```
[WAIT] Waiting for page to settle [System tab]...
[WAIT] Waiting for page to settle [Import/Export menu]...
[WAIT] Waiting for page to settle [extraction Next]...
```

### Test 2 — Simulasi Server Lambat

1. Jalankan modul apapun (Stock Mutation / Inventory Adjustment)
2. Jika server Newspage lambat (>5 detik per navigasi), pastikan bot tetap melanjutkan
   dengan benar tanpa `element not found` atau `element not interactable` error

**Expected**: Run berhasil 100% sampai selesai meski server lambat.

### Test 3 — Data Tidak Berubah

1. Jalankan Inventory Adjustment untuk 1 SKU dengan quantity diketahui
2. Verifikasi di portal Newspage bahwa quantity yang tertulis sama persis
   dengan yang ada di file upload

**Expected**: Hasil data identik dengan sebelum perubahan.

### Kriteria Lulus

- [ ] Log `[WAIT]` muncul di setiap langkah navigasi utama
- [ ] Run selesai tanpa error `element not interactable`
- [ ] Data yang ditulis ke portal identik dengan input file
- [ ] Tidak ada perubahan pada format log existing (NAV, AUTH, SUCCESS, ERROR tetap sama)
