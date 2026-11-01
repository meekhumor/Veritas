from supabase import create_client, Client
from app.core.config import get_settings


def get_supabase_client() -> Client:
    settings = get_settings()
    key = settings.supabase_service_role_key or settings.supabase_secret_key
    return create_client(settings.supabase_url, key)
