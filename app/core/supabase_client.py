import os
from dotenv import load_dotenv
from supabase import create_client

# Load env variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = (
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    or os.getenv("SUPABASE_SERVICE_KEY")
)
PROJECT_NAME = os.getenv("PROJECT_NAME", "AI-Clone")

if not SUPABASE_URL or not (SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY):
    raise RuntimeError("SUPABASE_URL and a Supabase key are missing in .env file")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY)


def save_universal_data(user_id, data_type, data_key, data, email=None, name=None, avatar_url=None):
    row = {
        "user_id": user_id,
        "email": email,
        "name": name,
        "avatar_url": avatar_url,
        "project_name": PROJECT_NAME,
        "data_type": data_type,
        "data_key": data_key,
        "data": data,
    }
    return (
        supabase.table("universal_user_data")
        .upsert(row, on_conflict="user_id,project_name,data_type,data_key")
        .execute()
    )
