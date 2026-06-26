import os
import sys
from cryptography.fernet import Fernet

# Set PYTHONPATH so we can import database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database

def main():
    print("=== Newspage Password Encrypter ===")
    
    # Check if MASTER_KEY is available
    try:
        key = database.get_encryption_key()
        print("MASTER_KEY loaded successfully.")
    except Exception as e:
        print(f"Error: {e}")
        print("Please make sure MASTER_KEY is configured in your environment or .streamlit/secrets.toml")
        return
        
    password = input("Masukkan password plain text yang ingin dienkripsi: ").strip()
    if not password:
        print("Password tidak boleh kosong.")
        return
        
    try:
        encrypted = database.encrypt_data(password)
        print("\n=== HASIL ENKRIPSI ===")
        print("Salin kode di bawah ini dan paste ke kolom 'np_password' di Supabase:")
        print("-" * 60)
        print(encrypted)
        print("-" * 60)
    except Exception as e:
        print(f"Gagal melakukan enkripsi: {e}")

if __name__ == "__main__":
    main()
