# AI-assisted Distributed Project Memory System

## 1. Pendahuluan
**AI-assisted Distributed Project Memory System** (Sistem Memori Proyek Terdistribusi Berbantuan AI) adalah sebuah konsep dan arsitektur sistem yang dirancang untuk menjadi "otak terpusat" (atau *shared brain*) dari suatu proyek peranti lunak. Sistem ini bertugas merekam, mengelola, menyortir, dan mendistribusikan konteks dan pengetahuan proyek agar dapat diakses dengan mudah, baik oleh tim developer (manusia) maupun berbagai Agen AI (*Autonomous Agents*) yang bekerja dalam ekosistem proyek tersebut.

## 2. Visi dan Tujuan
*   **Single Source of Truth yang Dinamis:** Menyediakan satu sumber informasi yang terus diperbarui secara otomatis seiring perkembangan proyek (meliputi PRD, arsitektur, *codebase*, hingga log percakapan).
*   **Optimalisasi *Context Window* AI:** Mencegah *overloading* pada *prompt* AI dengan cara hanya mengambil (*retrieve*) informasi yang benar-benar relevan untuk tugas yang sedang dikerjakan.
*   **Kolaborasi Multi-Agent:** Memungkinkan berbagai agen (misalnya agen pembuat kode, agen peneliti, agen penguji) untuk saling berbagi temuan dan status tanpa harus mengulang pekerjaan.
*   **Penyimpanan Pengetahuan Jangka Panjang:** Merekam jejak pengambilan keputusan (*Architecture Decision Records*), *bug* yang pernah diperbaiki, dan pedoman gaya pengkodean agar tidak hilang (amnesia proyek).

## 3. Arsitektur Sistem Memori
Sistem memori ini terdiri dari tiga lapisan (layer) penyimpanan memori yang meniru kognisi manusia:

### A. Short-term Memory (Memori Jangka Pendek)
*   **Fungsi:** Menyimpan status pekerjaan saat ini, log obrolan sementara, file yang sedang diedit, dan *task list* harian.
*   **Teknologi:** Log sistem JSON/JSONL, *scratchpad* dalam memori RAM, atau dokumen Markdown statis seperti `task.md`.

### B. Long-term Semantic Memory (Memori Jangka Panjang Semantik)
*   **Fungsi:** Menyimpan seluruh dokumentasi, seluruh *source code*, standar proyek, dan riwayat referensi yang dapat dicari maknanya, bukan hanya sekadar kata kuncinya.
*   **Teknologi:** Vector Database (misalnya: ChromaDB, Qdrant, Pinecone) digabungkan dengan RAG (*Retrieval-Augmented Generation*).

### C. Knowledge Graph Memory (Memori Relasional)
*   **Fungsi:** Memetakan hubungan antar komponen. Contoh: "Fungsi A" -> *dipanggil oleh* -> "Modul B" -> *berhubungan dengan* -> "Tabel Database C".
*   **Teknologi:** Graph Database (misalnya: Neo4j) atau kamus relasional yang diekstrak oleh AI.

## 4. Alur Kerja (Workflow)

1.  **Ingestion (Penyusupan Data):**
    Secara berkala atau saat ada perubahan *commit*, sistem membaca fail proyek terbaru (seperti `app.py`, `playwright_engine.py`, `database.py`, dan `README.md`).
2.  **Summarization & Embedding (Peringkasan & Vektorisasi):**
    Agen AI membaca data besar, merangkumnya (agar lebih hemat token), lalu mengubah teks menjadi representasi vektor numerik (*embeddings*).
3.  **Storage (Penyimpanan):**
    Vektor disimpan di Vector DB, dan hubungan semantiknya ditambahkan ke Knowledge Graph.
4.  **Retrieval & Injection (Pencarian & Injeksi Konteks):**
    Ketika manusia atau Agen AI lain akan melakukan *coding*, *Orchestrator* akan mencari dokumen paling relevan menggunakan pencarian *cosine similarity*. Hasilnya disuntikkan (*injected*) ke dalam *prompt* Agen sebagai konteks tambahan.
5.  **Memory Consolidation (Konsolidasi):**
    Pada malam hari atau setiap akhir *"sprint"*, agen administrator otomatis akan menggabungkan memori jangka pendek menjadi memori jangka panjang, mengarsipkan konteks lama, dan memperbarui struktur proyek.

## 5. Fitur Utama yang Harus Dibangun
*   **Automated Context Fetching:** Saat agen dipanggil untuk "perbaiki bug X", agen akan otomatis mengambil detail tentang fungsi X beserta file yang saling terkait tanpa disuruh.
*   **Memory Decay:** Pengetahuan yang sudah kedaluwarsa (misalnya versi API lama yang sudah tidak dipakai) diturunkan prioritasnya secara sistematis agar tidak mengacaukan pemahaman agen.
*   **Global Project Rules:** Direktori kustom (misal `.agents/skills` atau konfigurasi global) yang memuat instruksi tentang cara AI harus bersikap dan standar pengkodean pada proyek tertentu.
*   **Agentic Handoff State:** Sebuah catatan (misal `walkthrough.md` atau `handoff.json`) yang memberitahu agen selanjutnya tentang apa yang sudah dikerjakan agen sebelumnya dan apa yang masih kurang.

## 6. Rencana Implementasi di Proyek Ini (Optimize / Newspage Automation)

Mengingat proyek saat ini sudah memiliki berbagai komponen (*Playwright Engine*, *Streamlit UI*, *SQLite/PostgreSQL DB*), implementasi Memori Terdistribusi ini dapat dilakukan secara bertahap:

**Fase 1: Standarisasi Memori Berbasis Berkas (.md)**
*   Menyempurnakan `product_requirements_document.md` dan `elements_yang_dipakai_dinewspage_sebagai_otomasi.md` sebagai *core semantic memory*.
*   Mewajibkan penggunaan `task.md` untuk melacak *progress* secara detail bagi sub-agen.

**Fase 2: Integrasi RAG Lokal**
*   Menyematkan *skrip* sederhana yang membangun indeks menggunakan `chromadb` atau LlamaIndex agar agen dapat melakukan tanya-jawab terhadap seluruh fail `*.py` dan `*.md`.

**Fase 3: Otomatisasi Pengetahuan Silang**
*   Membangun sub-agen "Research" dan "Coder" terpisah, di mana "Research" menyajikan penemuan tentang *XPath* suatu elemen web, kemudian menyimpannya ke *shared memory*, yang selanjutnya dibaca oleh agen "Coder" untuk ditambahkan ke *Playwright Engine*.
