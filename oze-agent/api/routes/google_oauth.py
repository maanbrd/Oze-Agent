"""Google OAuth callback routes for OZE-Agent."""

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from bot.config import Config
from shared.google_auth import build_oauth_url, handle_oauth_callback

logger = logging.getLogger(__name__)

router = APIRouter()

_SUCCESS_HTML = """
<!DOCTYPE html>
<html lang="pl">
<head><meta charset="UTF-8"><title>OZE-Agent — autoryzacja Google</title></head>
<body style="font-family:sans-serif;text-align:center;padding:60px">
  <h2>✅ Google połączony!</h2>
  <p>Autoryzacja zakończona pomyślnie. Wróć do panelu i kontynuuj onboarding.</p>
</body>
</html>
"""

_ERROR_HTML = """
<!DOCTYPE html>
<html lang="pl">
<head><meta charset="UTF-8"><title>OZE-Agent — błąd</title></head>
<body style="font-family:sans-serif;text-align:center;padding:60px">
  <h2>❌ Błąd autoryzacji</h2>
  <p>Coś poszło nie tak. Spróbuj ponownie lub skontaktuj się z pomocą techniczną.</p>
</body>
</html>
"""


@router.get("/google/url/{user_id}")
async def get_oauth_url(user_id: str):
    """Legacy public OAuth URL endpoint retired for user-id spoofing safety."""
    raise HTTPException(status_code=410, detail="Use authenticated onboarding OAuth endpoint.")


def _configured_dashboard_google_success_url() -> str | None:
    base_url = (Config.DASHBOARD_URL or "").strip().rstrip("/")
    if not base_url:
        return None
    return f"{base_url}/onboarding/google/sukces"


@router.get("/google/callback")
async def google_callback(code: str, state: str):
    """Handle Google OAuth redirect. state = user_id."""
    try:
        user = handle_oauth_callback(code=code, state=state)
        if not user:
            logger.error("google_callback: handle_oauth_callback returned None for state=%s", state)
            return HTMLResponse(content=_ERROR_HTML, status_code=400)
        return_url = user.get("_oauth_return_url") or _configured_dashboard_google_success_url()
        if return_url:
            return RedirectResponse(str(return_url))
        return HTMLResponse(content=_SUCCESS_HTML)
    except Exception as e:
        logger.error("google_callback: %s", e)
        return HTMLResponse(content=_ERROR_HTML, status_code=500)
