"""Unit tests for shared/google_drive.py."""

from unittest.mock import patch

import pytest


class _Execute:
    def __init__(self, value=None, error=None):
        self.value = value
        self.error = error

    def execute(self):
        if self.error:
            raise self.error
        return self.value


class _Files:
    def __init__(self, list_result=None, list_error=None):
        self.list_result = list_result if list_result is not None else {"files": []}
        self.list_error = list_error
        self.list_kwargs = None

    def list(self, **kwargs):
        self.list_kwargs = kwargs
        return _Execute(self.list_result, self.list_error)


class _DriveService:
    def __init__(self, files):
        self._files = files

    def files(self):
        return self._files


@pytest.mark.asyncio
async def test_count_photos_in_folder_returns_image_count():
    files = _Files(list_result={"files": [{"id": "a"}, {"id": "b"}, {"id": "c"}]})
    with patch(
        "shared.google_drive._get_drive_service_sync",
        return_value=_DriveService(files),
    ):
        from shared.google_drive import count_photos_in_folder

        result = await count_photos_in_folder("user-1", "folder-1")

    assert result == 3
    assert "'folder-1' in parents" in files.list_kwargs["q"]
    assert "mimeType contains 'image/'" in files.list_kwargs["q"]


@pytest.mark.asyncio
async def test_count_photos_in_folder_returns_none_on_api_error():
    files = _Files(list_error=RuntimeError("Drive down"))
    with patch(
        "shared.google_drive._get_drive_service_sync",
        return_value=_DriveService(files),
    ):
        from shared.google_drive import count_photos_in_folder

        result = await count_photos_in_folder("user-1", "folder-1")

    assert result is None
