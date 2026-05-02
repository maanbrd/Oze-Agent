"""Google Drive operations for OZE-Agent — client photo storage.

All public functions are async and use asyncio.to_thread() for sync Google API calls.
Returns None / empty list on failure — never raises.
"""

import asyncio
import io
import logging
import re
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from shared.database import get_user_by_id, update_user
from shared.google_auth import get_google_credentials

logger = logging.getLogger(__name__)

FOLDER_URL_PREFIX = "https://drive.google.com/drive/folders/"


# ── Internal helpers ──────────────────────────────────────────────────────────


def _get_drive_service_sync(user_id: str):
    """Build and return a Google Drive API service (sync)."""
    creds = get_google_credentials(user_id)
    if not creds:
        return None
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _escape_drive_query_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def extract_folder_id(value: str) -> Optional[str]:
    """Extract a Drive folder ID from a folder URL or raw ID-like value."""
    if not value:
        return None
    match = re.search(r"/folders/([A-Za-z0-9_-]+)", value)
    if match:
        return match.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{10,}", value.strip()):
        return value.strip()
    return None


def build_client_folder_name(client: dict) -> str:
    """Build a user-facing Drive folder name from Sheets client fields."""
    parts = [
        client.get("Imię i nazwisko", ""),
        client.get("Miasto", client.get("Miejscowość", "")),
        client.get("Adres", ""),
    ]
    return " — ".join(part.strip() for part in parts if part and part.strip())


# ── Public async API ──────────────────────────────────────────────────────────


async def get_drive_service(user_id: str):
    """Return a Drive API service for this user, or None."""
    return await asyncio.to_thread(_get_drive_service_sync, user_id)


async def create_root_folder(user_id: str) -> Optional[str]:
    """Create 'OZE Klienci — [name]' root folder in user's Drive.

    Stores folder ID in users.google_drive_folder_id.
    Returns folder ID or None.
    """
    try:
        user = get_user_by_id(user_id)
        if not user:
            return None
        folder_name = f"OZE Klienci — {user.get('name', user_id)}"

        def _create():
            service = _get_drive_service_sync(user_id)
            if not service:
                return None
            metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
            }
            folder = service.files().create(
                body=metadata, fields="id"
            ).execute()
            return folder.get("id")

        folder_id = await asyncio.to_thread(_create)
        if folder_id:
            update_user(user_id, {"google_drive_folder_id": folder_id})
        return folder_id
    except Exception as e:
        logger.error("create_root_folder(%s): %s", user_id, e)
        return None


async def create_client_folder(
    user_id: str, client_name: str, city: str
) -> Optional[str]:
    """Create '[Client] — [City]' subfolder inside the user's root OZE folder.

    Returns folder ID or None.
    """
    try:
        user = get_user_by_id(user_id)
        if not user:
            return None
        root_folder_id = user.get("google_drive_folder_id")
        if not root_folder_id:
            root_folder_id = await create_root_folder(user_id)
        if not root_folder_id:
            return None

        folder_name = f"{client_name} — {city}"

        def _create():
            service = _get_drive_service_sync(user_id)
            if not service:
                return None
            metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [root_folder_id],
            }
            folder = service.files().create(
                body=metadata, fields="id"
            ).execute()
            return folder.get("id")

        return await asyncio.to_thread(_create)
    except Exception as e:
        logger.error("create_client_folder(%s, %s, %s): %s", user_id, client_name, city, e)
        return None


async def get_or_create_client_folder(
    user_id: str, client_name: str, city: str
) -> Optional[str]:
    """Find existing client folder or create a new one. Returns folder ID or None."""
    try:
        user = get_user_by_id(user_id)
        if not user:
            return None
        root_folder_id = user.get("google_drive_folder_id")
        if not root_folder_id:
            root_folder_id = await create_root_folder(user_id)
        if not root_folder_id:
            return None

        folder_name = f"{client_name} — {city}"

        def _find():
            service = _get_drive_service_sync(user_id)
            if not service:
                return None
            query = (
                f"name = '{folder_name}' "
                f"and '{root_folder_id}' in parents "
                f"and mimeType = 'application/vnd.google-apps.folder' "
                f"and trashed = false"
            )
            result = service.files().list(
                q=query, fields="files(id, name)"
            ).execute()
            files = result.get("files", [])
            return files[0]["id"] if files else None

        existing_id = await asyncio.to_thread(_find)
        if existing_id:
            return existing_id
        return await create_client_folder(user_id, client_name, city)
    except Exception as e:
        logger.error("get_or_create_client_folder(%s): %s", user_id, e)
        return None


async def get_or_create_client_photo_folder(
    user_id: str,
    client: dict,
) -> Optional[dict]:
    """Return client photo folder metadata, creating it under root if needed.

    Existing Sheets column O is preferred when it contains a Drive folder link.
    """
    try:
        user = get_user_by_id(user_id)
        if not user:
            return None

        root_folder_id = user.get("google_drive_folder_id")
        if not root_folder_id:
            root_folder_id = await create_root_folder(user_id)
        if not root_folder_id:
            return None

        existing_folder_id = extract_folder_id(client.get("Link do zdjęć", ""))
        folder_name = build_client_folder_name(client)
        if not folder_name:
            folder_name = client.get("Imię i nazwisko", "Klient")

        def _find_or_create():
            service = _get_drive_service_sync(user_id)
            if not service:
                return None

            if existing_folder_id:
                try:
                    existing = service.files().get(
                        fileId=existing_folder_id,
                        fields="id, name, webViewLink",
                    ).execute()
                    if existing:
                        return existing
                except Exception as e:
                    logger.warning(
                        "get_or_create_client_photo_folder: existing folder %s invalid: %s",
                        existing_folder_id,
                        e,
                    )

            escaped_name = _escape_drive_query_value(folder_name)
            query = (
                f"name = '{escaped_name}' "
                f"and '{root_folder_id}' in parents "
                f"and mimeType = 'application/vnd.google-apps.folder' "
                f"and trashed = false"
            )
            result = service.files().list(
                q=query,
                fields="files(id, name, webViewLink)",
            ).execute()
            files = result.get("files", [])
            if files:
                return files[0]

            metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [root_folder_id],
            }
            return service.files().create(
                body=metadata,
                fields="id, name, webViewLink",
            ).execute()

        folder = await asyncio.to_thread(_find_or_create)
        if not folder:
            return None
        folder_id = folder.get("id")
        return {
            "id": folder_id,
            "name": folder.get("name", folder_name),
            "webViewLink": folder.get("webViewLink") or f"{FOLDER_URL_PREFIX}{folder_id}",
        }
    except Exception as e:
        logger.error("get_or_create_client_photo_folder(%s): %s", user_id, e)
        return None


async def upload_photo(
    user_id: str,
    folder_id: str,
    file_bytes: bytes,
    filename: str,
    description: str = "",
) -> Optional[str]:
    """Upload a photo to the specified folder. Returns web view link or None."""
    try:
        def _upload():
            service = _get_drive_service_sync(user_id)
            if not service:
                return None
            file_stream = io.BytesIO(file_bytes)
            mime_type = "image/jpeg" if filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg") else "image/png"
            media = MediaIoBaseUpload(file_stream, mimetype=mime_type)
            metadata = {"name": filename, "parents": [folder_id]}
            if description:
                metadata["description"] = description
            uploaded = service.files().create(
                body=metadata,
                media_body=media,
                fields="id, webViewLink",
            ).execute()
            return uploaded.get("webViewLink")

        return await asyncio.to_thread(_upload)
    except Exception as e:
        logger.error("upload_photo(%s, folder=%s, file=%s): %s", user_id, folder_id, filename, e)
        return None


async def count_photos_in_folder(user_id: str, folder_id: str) -> Optional[int]:
    """Count image files in a client folder. None means the Drive call failed."""
    try:
        def _count():
            service = _get_drive_service_sync(user_id)
            if not service:
                return None
            query = (
                f"'{folder_id}' in parents "
                f"and mimeType contains 'image/' "
                f"and trashed = false"
            )
            result = service.files().list(
                q=query,
                fields="files(id)",
            ).execute()
            return len(result.get("files", []))

        return await asyncio.to_thread(_count)
    except Exception as e:
        logger.error("count_photos_in_folder(%s, folder=%s): %s", user_id, folder_id, e)
        return None


async def get_client_photos(user_id: str, folder_id: str) -> list[dict]:
    """List all photos in a client folder with their names and view links."""
    try:
        def _list():
            service = _get_drive_service_sync(user_id)
            if not service:
                return []
            query = (
                f"'{folder_id}' in parents "
                f"and mimeType contains 'image/' "
                f"and trashed = false"
            )
            result = service.files().list(
                q=query,
                fields="files(id, name, webViewLink, createdTime)",
                orderBy="createdTime desc",
            ).execute()
            return result.get("files", [])

        return await asyncio.to_thread(_list)
    except Exception as e:
        logger.error("get_client_photos(%s, folder=%s): %s", user_id, folder_id, e)
        return []
