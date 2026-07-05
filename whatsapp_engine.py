import os
import time
from playwright.sync_api import sync_playwright, TimeoutError

# Konfigurasi Path
PROFILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".playwright", "whatsapp_profile")
QR_CODE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots", "qr_code.png")

def forward_screenshot_to_whatsapp(group_name: str, screenshot_path: str):
    """
    Mengirim screenshot ke grup WhatsApp via Playwright.
    Returns:
        dict: {"status": "success" | "needs_qr" | "error", "message": "...", "qr_path": "..."}
    """
    abs_path = os.path.abspath(screenshot_path)
    cwd = os.getcwd()
    if not os.path.exists(screenshot_path):
        return {"status": "error", "message": f"Screenshot tidak ditemukan di {screenshot_path}. (CWD: {cwd}, AbsPath: {abs_path})"}

    try:
        with sync_playwright() as p:
            # Gunakan persistent context agar sesi (QR login) tersimpan
            browser = p.chromium.launch_persistent_context(
                user_data_dir=PROFILE_DIR,
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            page = browser.new_page()
            page.goto("https://web.whatsapp.com/")

            try:
                # Tunggu salah satu: QR Code ATAU Search Box (Artinya sudah login)
                page.wait_for_selector('canvas[aria-label="Scan me!"], div[contenteditable="true"][data-tab="3"]', timeout=60000)
            except TimeoutError:
                browser.close()
                return {"status": "error", "message": "Timeout menunggu halaman utama WhatsApp Web."}

            # Cek apakah QR Code muncul (belum login)
            if page.locator('canvas[aria-label="Scan me!"]').is_visible() or page.locator('canvas').count() > 0:
                qr_locator = page.locator('canvas').first
                qr_locator.screenshot(path=QR_CODE_PATH)
                browser.close()
                return {
                    "status": "needs_qr", 
                    "message": "Sesi WhatsApp belum ada. Silakan scan QR Code ini.",
                    "qr_path": QR_CODE_PATH
                }

            # Jika sudah login, cari grup
            try:
                search_box = page.locator('div[contenteditable="true"][data-tab="3"]')
                search_box.click()
                search_box.fill(group_name)
                search_box.press("Enter")
                
                # Tunggu sebentar agar chat terbuka
                page.wait_for_timeout(2000)
                
                # Cek apakah grup ditemukan (header muncul)
                if not page.locator('span[data-icon="clip"]').is_visible():
                    browser.close()
                    return {"status": "error", "message": f"Grup '{group_name}' tidak ditemukan."}

                # Klik tombol attach (clip)
                page.locator('span[data-icon="clip"]').click()
                
                # Upload gambar (input type="file" biasanya disembunyikan oleh WA, tapi bisa diset valuenya)
                # WA Web modern menggunakan beberapa input file. Ambil yang pertama (untuk foto/video)
                file_input = page.locator('input[accept="image/*,video/mp4,video/3gpp,video/quicktime"]')
                file_input.set_input_files(screenshot_path)
                
                # Tunggu preview gambar muncul dan tombol send aktif
                page.wait_for_selector('span[data-icon="send"]', timeout=15000)
                
                # Klik send
                page.locator('span[data-icon="send"]').click()
                
                # Tunggu pesan terkirim (indikator jam pasir hilang)
                page.wait_for_timeout(3000)
                
                browser.close()
                return {"status": "success", "message": f"Berhasil meneruskan screenshot ke {group_name}!"}
                
            except TimeoutError as e:
                browser.close()
                return {"status": "error", "message": f"Terjadi kesalahan saat memproses UI WhatsApp: {str(e)}"}

    except Exception as e:
        return {"status": "error", "message": f"Internal Error: {str(e)}"}
