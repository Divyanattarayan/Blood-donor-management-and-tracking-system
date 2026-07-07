import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_supabase_client: Client = None
_supabase_admin_client: Client = None


def get_supabase() -> Client:
    """Returns the Supabase anon client (used for auth and user-scoped queries)."""
    global _supabase_client
    if _supabase_client is None:
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        _supabase_client = create_client(url, key)
    return _supabase_client


def get_supabase_admin() -> Client:
    """Returns the Supabase service-role client (bypasses RLS — admin use only)."""
    global _supabase_admin_client
    if _supabase_admin_client is None:
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_KEY')
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
        _supabase_admin_client = create_client(url, key)
    return _supabase_admin_client
