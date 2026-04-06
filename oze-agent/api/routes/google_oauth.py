"""Google OAuth callback routes for OZE-Agent."""

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from shared.google_auth import build_oauth_url, handle_oauth_callback

logger = logging.getLogger(__name__)

router = APIRouter()

_SUCCESS_HTML = """
<!DOCTYPE html>
<html lang="pl">
<head><meta charset="UTF-8"><title>OZE-Agent — autoryzacja Google</title></head>
<body style="font-family:sans-serif;text-align:center;padding:60px">
  <h2>✅ Google połączony!</h2>
  <p>Autoryzacja zakończona pomyślnie. Wróć do Telegrama i kontynuuj.</p>
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
    """Return the Google OAuth authorization URL for this user."""
    try:
        url = build_oauth_url(user_id)
        return {"url": url}
    except Exception as e:
        logger.error("get_oauth_url(%s): %s", user_id, e)
        raise HTTPException(status_code=500, detail="Nie udało się wygenerować URL autoryzacji.")


@router.get("/google/callback", response_class=HTMLResponse)
async def google_callback(code: str, state: str):
    """Handle Google OAuth redirect. state = user_id."""
    try:
        user = handle_oauth_callback(code=code, state=state)
        if not user:
            logger.error("google_callback: handle_oauth_callback returned None for state=%s", state)
            return HTMLResponse(content=_ERROR_HTML, status_code=400)
        return HTMLResponse(content=_SUCCESS_HTML)
    except Exception as e:
        logger.error("google_callback: %s", e)
        return HTMLResponse(content=_ERROR_HTML, status_code=500)
