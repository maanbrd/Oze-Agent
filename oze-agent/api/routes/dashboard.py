"""Dashboard API routes."""

from fastapi import APIRouter, Depends

from api.auth import AuthUser, get_current_auth_user
from shared.database import get_supabase_client

router = APIRouter()


@router.get("/me")
async def get_me(auth_user: AuthUser = Depends(get_current_auth_user)):
    """Return the authenticated user's profile.

    FastAPI uses the service key, so RLS is not the authorization boundary here.
    The `auth_user_id` always comes from the verified JWT subject.
    """
    result = (
        get_supabase_client()
        .table("users")
        .select(
            "id, auth_user_id, name, email, phone, subscription_status, "
            "onboarding_completed, google_sheets_id, google_calendar_id, "
            "google_drive_folder_id, telegram_id"
        )
        .eq("auth_user_id", auth_user.user_id)
        .limit(1)
        .execute()
    )

    return {
        "auth_user_id": auth_user.user_id,
        "email": auth_user.email,
        "profile": result.data[0] if result.data else None,
    }
