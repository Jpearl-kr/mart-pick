from functools import lru_cache

from supabase import Client, create_client

from app.config import settings


@lru_cache
def get_supabase() -> Client:
    if not settings.supabase_url or not settings.supabase_key:
        raise RuntimeError(
            "SUPABASE_URL / SUPABASE_KEY are not set. Copy backend/.env.example to "
            "backend/.env and fill in your Supabase project credentials."
        )
    return create_client(settings.supabase_url, settings.supabase_key)
