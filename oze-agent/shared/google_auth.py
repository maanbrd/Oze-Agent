"""Google OAuth token management for OZE-Agent.

Tokens are stored encrypted in Supabase users table.
All functions use the service key via shared.database.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from bot.config import Config
from shared.database import get_user_by_id, update_user
from shared.encryption import decrypt_token, encrypt_token

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive.file",
]


def get_google_credentials(user_id: str) -> Optional[Credentials]:
    """Return valid Google credentials for this user, or None.

    Automatically refreshes the access token if expired.
    Returns None if tokens are missing or refresh fails (caller triggers re-auth).
    """
    try:
        user = get_user_by_id(user_id)
        if not user:
            logger.error("get_google_credentials: user %s not found", user_id)
            return None

        access_token = user.get("google_access_token")
        refresh_token = user.get("google_refresh_token")
        token_expiry = user.get("google_token_expiry")

        if not refresh_token:
            logger.info("get_google_credentials: no refresh token for user %s", user_id)
            return None

        try:
            decrypted_access = decrypt_token(access_token) if access_token else None
            decrypted_refresh = decrypt_token(refresh_token)
        except Exception as e:
            logger.error("get_google_credentials: decryption failed for user %s: %s", user_id, e)
            return None

        if token_expiry:
            expiry = datetime.fromisoformat(token_expiry.replace("Z", "+00:00"))
            # google-auth compares expiry with datetime.utcnow() (naive) — must be naive UTC
            expiry = expiry.replace(tzinfo=None)
        else:
            expiry = None

        creds = Credentials(
            token=decrypted_access,
            refresh_token=decrypted_refresh,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=Config.GOOGLE_CLIENT_ID,
            client_secret=Config.GOOGLE_CLIENT_SECRET,
            scopes=SCOPES,
            expiry=expiry,
        )

        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                store_google_tokens(user_id, creds)
                logger.info("get_google_credentials: refreshed token for user %s", user_id)
            except Exception as e:
                logger.error("get_google_credentials: refresh failed for user %s: %s", user_id, e)
                return None

        return creds

    except Exception as e:
        logger.error("get_google_credentials: unexpected error for user %s: %s", user_id, e)
        return None


def store_google_tokens(user_id: str, credentials: Credentials) -> None:
    """Encrypt and store Google tokens in Supabase users table."""
    try:
        data = {
            "google_access_token": encrypt_token(credentials.token),
            "google_refresh_token": encrypt_token(credentials.refresh_token),
            "google_token_expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        }
        update_user(user_id, data)
    except Exception as e:
        logger.error("store_google_tokens: failed for user %s: %s", user_id, e)


def build_oauth_url(user_id: str, state: str | None = None) -> str:
    """Generate Google OAuth authorization URL.

    Uses plain OAuth2 without PKCE — correct for server-side web app flows.
    state=user_id so the callback can identify the user.
    """
    from requests_oauthlib import OAuth2Session

    oauth = OAuth2Session(
        client_id=Config.GOOGLE_CLIENT_ID,
        scope=SCOPES,
        redirect_uri=Config.GOOGLE_REDIRECT_URI,
        state=state or user_id,
    )
    auth_url, _ = oauth.authorization_url(
        "https://accounts.google.com/o/oauth2/auth",
        access_type="offline",
    )
    return auth_url


def handle_oauth_callback(code: str, state: str) -> Optional[dict]:
    """Exchange OAuth code for tokens and store them.

    state is the user_id set in build_oauth_url.
    Returns user dict on success, None on failure.
    """
    try:
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": Config.GOOGLE_CLIENT_ID,
                    "client_secret": Config.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES,
            redirect_uri=Config.GOOGLE_REDIRECT_URI,
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials
        user_id = state
        store_google_tokens(user_id, credentials)
        user = get_user_by_id(user_id)
        return user
    except Exception as e:
        logger.error("handle_oauth_callback: failed for state=%s: %s", state, e)
        return None


def revoke_google_tokens(user_id: str) -> bool:
    """Revoke Google tokens and clear them from Supabase.

    Returns True if revoked successfully, False otherwise.
    """
    import httpx

    try:
        user = get_user_by_id(user_id)
        if not user or not user.get("google_access_token"):
            return False

        token = decrypt_token(user["google_access_token"])
        response = httpx.post(
            "https://oauth2.googleapis.com/revoke",
            params={"token": token},
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        if response.status_code not in (200, 400):
            logger.warning("revoke_google_tokens: unexpected status %s for user %s", response.status_code, user_id)

        update_user(user_id, {
            "google_access_token": None,
            "google_refresh_token": None,
            "google_token_expiry": None,
        })
        return True
    except Exception as e:
        logger.error("revoke_google_tokens: failed for user %s: %s", user_id, e)
        return False
