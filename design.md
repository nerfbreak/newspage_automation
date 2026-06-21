# Design System: Flat Design Corporativo for Streamlit

Panduan implementasi desain "Flat Design Corporativo" ke dalam aplikasi Streamlit. Dokumen ini berisi aturan, variabel, dan pola komponen untuk memastikan konsistensi visual tanpa mengubah logika bisnis aplikasi.

## 1. Prinsip Utama

- **Clean & Professional:** Hilangkan elemen dekoratif berlebihan. Fokus pada data dan fungsionalitas.
- **Flat & Sharp:** Gunakan sudut tajam (4px atau 0px), hindari border-radius besar.
- **Solid Colors:** Jangan gunakan gradient. Gunakan warna solid dari palet.
- **Typography First:** Hierarki visual dibangun melalui ukuran dan berat font, bukan efek bayangan tebal.
- **No Emojis:** Ganti semua emoji dengan ikon SVG atau teks biasa jika ikon tidak tersedia.

## 2. Palet Warna & Variabel CSS

Inject variabel ini ke dalam `<style>` tag di header Streamlit untuk konsistensi.

```css
:root {
    /* Primary Colors */
    --corporate-blue: #007BFF;
    --dark-grey-flat: #343A40;
    --white-flat: #FFFFFF;
    --light-grey-flat: #F8F9FA;

    /* Secondary/Semantic Colors */
    --success-green: #28A745;
    --warning-orange: #FFC107;
    --danger-red: #DC3545;
    --info-cyan: #17A2B8;

    /* Typography */
    --font-flat: 'Lato', sans-serif;
    --font-mono: 'JetBrains Mono', monospace;

    /* Effects */
    --flat-shadow: 0 2px 4px rgba(0,0,0,0.1);
    --flat-border: 1px solid #E0E0E0;
    --corner-radius: 4px; /* Sharp but slightly softened */
}
```

## 3. Implementasi Teknis (Streamlit)

### A. Injeksi Global (Wajib)

Buat file `utils/theme.py` (atau tambahkan ke `utils.py` yang ada) untuk menginjeksi CSS dan Font.

```python
import streamlit as st

def load_theme():
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Lato:wght@400;500;700&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <style>
        /* Import Variables */
        :root {
            --corporate-blue: #007BFF;
            --dark-grey-flat: #343A40;
            --white-flat: #FFFFFF;
            --light-grey-flat: #F8F9FA;
            --success-green: #28A745;
            --warning-orange: #FFC107;
            --danger-red: #DC3545;
            --info-cyan: #17A2B8;
            --font-flat: 'Lato', sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
            --flat-shadow: 0 2px 4px rgba(0,0,0,0.1);
            --corner-radius: 4px;
        }

        /* Global Typography */
        html, body, [class*="css"] {
            font-family: var(--font-flat);
            color: var(--dark-grey-flat);
            background-color: var(--light-grey-flat);
        }
        
        h1, h2, h3, h4, h5, h6 {
            font-weight: 700;
            color: var(--dark-grey-flat);
            margin-bottom: 0.5em;
        }

        /* Remove Default Streamlit Decorations */
        .stApp > header {
            background-color: var(--white-flat);
            box-shadow: var(--flat-shadow);
            border-bottom: 1px solid #e0e0e0;
        }
        
        /* Force Sharp Corners on Inputs & Containers */
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select,
        .stNumberInput > div > div > input,
        .stDataFrame {
            border-radius: var(--corner-radius) !important;
            border: 1px solid #ced4da !important;
        }

        /* Custom Card Style */
        .corp-card {
            background-color: var(--white-flat);
            padding: 1.5rem;
            border-radius: var(--corner-radius);
            box-shadow: var(--flat-shadow);
            border: 1px solid #e0e0e0;
            margin-bottom: 1rem;
            transition: transform 0.2s ease-out;
        }
        .corp-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.12);
        }

        /* Custom Buttons Override */
        .stButton > button {
            background-color: var(--corporate-blue);
            color: var(--white-flat);
            border: none;
            border-radius: var(--corner-radius);
            font-weight: 600;
            padding: 0.5rem 1rem;
            transition: all 0.2s;
        }
        .stButton > button:hover {
            background-color: #0069d9; /* Darker blue */
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            transform: translateY(-1px);
        }
        
        /* Secondary Button Variant (via custom class if needed, or global override for specific context) */
        .stButton > button.secondary {
            background-color: transparent;
            color: var(--corporate-blue);
            border: 1.5px solid var(--corporate-blue);
        }

        /* Metrics/KPI Cards */
        .metric-card {
            background: var(--white-flat);
            padding: 1rem;
            border-radius: var(--corner-radius);
            border-left: 4px solid var(--corporate-blue);
            box-shadow: var(--flat-shadow);
        }
    </style>
    """, unsafe_allow_html=True)
```

**Cara Pakai:** Panggil `load_theme()` di awal `app.py` (setelah `st.set_page_config`).

### B. Komponen Custom

#### 1. Card Container
Jangan hanya pakai `st.container()`. Bungkus konten dalam HTML div dengan class `.corp-card` untuk efek shadow dan border yang sesuai.

```python
def render_card(title, content):
    st.markdown(f"""
    <div class="corp-card">
        <h3 style="margin-top:0; color: var(--corporate-blue);">{title}</h3>
        {content}
    </div>
    """, unsafe_allow_html=True)
```

#### 2. Ikon (Tanpa Emoji)
Gunakan SVG inline atau library seperti `streamlit-components` jika perlu, tapi untuk ringan, gunakan SVG string langsung.

```python
# Contoh Icon SVG (Heroicons style - Check)
ICON_CHECK = """
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#28A745" stroke-width="2" stroke-linecap="square" stroke-linejoin="miter"><polyline points="20 6 9 17 4 12"></polyline></svg>
"""

st.markdown(f"<div style='display:flex; align-items:center; gap:10px;'>{ICON_CHECK} <span>Status OK</span></div>", unsafe_allow_html=True)
```

#### 3. Layout Grid
Gunakan `st.columns` tetapi pastikan padding dan gap konsisten.

```python
col1, col2, col3 = st.columns(3, gap="large")
with col1:
    st.markdown('<div class="corp-card">Konten 1</div>', unsafe_allow_html=True)
# dst...
```

## 4. Aturan Spesifik (Do's & Don'ts)

| Do ✅ | Don't ❌ |
| :--- | :--- |
| Gunakan warna `#007BFF` untuk aksi utama. | Gunakan gradient atau warna neon. |
| Gunakan `border-radius: 4px` untuk semua input/card. | Gunakan `border-radius: 20px` atau lingkaran penuh. |
| Gunakan font `Lato` untuk semua teks. | Gunakan font default Streamlit (sans-serif standar). |
| Gunakan shadow halus (`0 2px 4px`). | Gunakan shadow tebal/gelap. |
| Gunakan layout berbasis grid/kolom. | Gunakan layout acak atau tumpuk tanpa struktur. |
| Inject CSS via `st.markdown(..., unsafe_allow_html=True)`. | Mengandalkan tema bawaan Streamlit saja. |

## 5. Struktur File yang Disarankan

```text
/workspace
├── app.py                # Entry point, panggil load_theme() di sini
├── utils/
│   ├── theme.py          # Fungsi load_theme() dan helper CSS
│   ├── components.py     # Fungsi render_card, render_icon, dll
│   └── ...
├── pages/
└── static/               # (Opsional) Jika ada aset lokal
```

## 6. Checklist Implementasi

- [ ] Buat file `utils/theme.py` dan pindahkan logic CSS ke sana.
- [ ] Panggil `load_theme()` di `app.py`.
- [ ] Ganti semua `st.metric` atau container biasa dengan `.corp-card` custom jika perlu tampilan lebih menonjol.
- [ ] Hapus semua emoji dari teks UI, ganti dengan SVG atau hapus.
- [ ] Pastikan semua tombol menggunakan style primary (biru) secara default.
- [ ] Verifikasi tampilan di Mobile (kolom harus stack vertikal).

## 7. Catatan Kinerja

- Injeksi CSS via `st.markdown` dilakukan setiap kali rerun, namun dampaknya minimal karena ukurannya kecil.
- Hindari terlalu banyak HTML custom yang kompleks di dalam loop DataFrame besar; gunakan CSS class pada container induk saja.
