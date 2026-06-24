# Engineering Skills & Competencies Matrix
**Project Name:** Optimize Newspage - Stock Adjustment Automation Engine

Dokumen ini memetakan keahlian teknis (technical skills) yang dibutuhkan oleh tim pengembang (Developer/Engineer) untuk memelihara, mengembangkan, dan memecahkan masalah (troubleshoot) pada sistem **Optimize Newspage**.

---

## 1. Core Programming
| Keterampilan (Skill) | Tingkat Kemahiran | Penggunaan dalam Sistem |
| :--- | :--- | :--- |
| **Python 3.10+** | Advanced | Bahasa pemrograman utama untuk seluruh backend, logika automasi, dan pemrosesan data (`playwright_engine.py`, `data_processor.py`, `utils.py`). |
| **Asynchronous Programming** | Intermediate | Menangani *async/await* untuk Playwright jika dibutuhkan pengembangan lebih lanjut secara konkuren. |

## 2. Frontend & UI
| Keterampilan (Skill) | Tingkat Kemahiran | Penggunaan dalam Sistem |
| :--- | :--- | :--- |
| **Streamlit** | Advanced | Framework utama untuk antarmuka web. Diperlukan pemahaman mendalam tentang `st.session_state`, Streamlit Pages (`st.navigation`, `st.Page`), dan optimasi *rerun*. |
| **HTML & CSS (Vanilla)** | Intermediate | Modifikasi tema antarmuka dan penyuntikan kustom CSS (`inject_css`) untuk menyamakan *styling* halaman web (misal: `style.css` dan `login.css`). |

## 3. Automation & Web Scraping
| Keterampilan (Skill) | Tingkat Kemahiran | Penggunaan dalam Sistem |
| :--- | :--- | :--- |
| **Playwright (Python API)** | Advanced | Mengendalikan *headless browser* (Chromium), navigasi DOM, ekstraksi elemen, *handling timeout*, dan *bypass* sistem deteksi pada sistem Newspage. |
| **DOM Manipulation & XPath/CSS Selectors** | Advanced | Mengidentifikasi dan menargetkan elemen HTML di dalam sistem Newspage secara presisi untuk proses ekstraksi dan injeksi data. |

## 4. Database & Cloud Backend
| Keterampilan (Skill) | Tingkat Kemahiran | Penggunaan dalam Sistem |
| :--- | :--- | :--- |
| **Supabase (Python SDK)** | Intermediate | Mengintegrasikan aplikasi dengan Supabase (`database.py`), menjalankan kueri *Select, Insert, Update* pada tabel konfigurasi dan vault. |
| **PostgreSQL & SQL** | Intermediate | Memahami relasi tabel, tipe data, desain skema database (`users_auth`, `distributor_vault`, `system_config`), serta *Row Level Security* (RLS). |

## 5. Security & Cryptography
| Keterampilan (Skill) | Tingkat Kemahiran | Penggunaan dalam Sistem |
| :--- | :--- | :--- |
| **Cryptography (AES-256 Fernet)** | Intermediate | Mengimplementasikan enkripsi dan dekripsi untuk kredensial sensitif milik distributor (`distributor_vault`) secara *on-the-fly*. |
| **Bcrypt Hashing** | Basic - Intermediate | Pembuatan dan verifikasi *hash* untuk sistem otentikasi kata sandi pengguna web. |
| **Session & Lockout Management** | Intermediate | Merancang logika keamanan seperti *brute-force throttling*, pembatasan percobaan login, dan *session timeout*. |

## 6. Data Processing
| Keterampilan (Skill) | Tingkat Kemahiran | Penggunaan dalam Sistem |
| :--- | :--- | :--- |
| **Pandas** | Intermediate | Pemrosesan, rekonsiliasi, penyaringan (filtering), dan pembersihan (*cleaning*) data dalam format CSV atau XLSX hasil ekstraksi (`data_processor.py`). |

## 7. DevOps & Infrastructure
| Keterampilan (Skill) | Tingkat Kemahiran | Penggunaan dalam Sistem |
| :--- | :--- | :--- |
| **Environment Management** | Basic | Mengelola `requirements.txt` dan `.streamlit/secrets.toml`. |
| **Telegram Bot API** | Basic | Konfigurasi sistem peringatan (*alerting*) untuk notifikasi insiden keamanan atau status bot. |

---

## Ringkasan Profil Pengembang yang Ideal
Seorang pengembang yang akan berkontribusi pada proyek ini idealnya adalah seorang **Python Fullstack / Automation Engineer** dengan keahlian kuat di bidang bot automation (Playwright), antarmuka data interaktif (Streamlit), dan manajemen keamanan kredensial (Cryptography & Supabase).
