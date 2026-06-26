import os
import sys
import database

# Initialize Supabase using secrets
supabase = database.init_supabase()

if supabase:
    res = supabase.table("distributor_vault").select("nama_distributor, np_user_id, np_password").execute()
    if res.data:
        print("Checking credentials status:")
        for row in res.data:
            name = row["nama_distributor"]
            user = row["np_user_id"]
            password = row["np_password"]
            
            if not user or not password:
                print(f" - [MISSING CREDENTIALS] {name}: User ID is '{user}', Password is '{'empty' if not password else 'present'}'")
            else:
                dec = database.decrypt_data(password)
                if not dec:
                    print(f" - [DECRYPTION FAILED] {name} (User: {user})")
    else:
        print("No distributors found in database.")
else:
    print("Failed to connect to Supabase.")
