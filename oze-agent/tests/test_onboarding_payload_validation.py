"""Positive-schema validation for onboarding request bodies (Item 5).

The handlers used to take raw ``dict[str, Any]``. They now take Pydantic models,
so malformed / oversized / wrong-type inputs are rejected before any DB work,
while partial-PATCH semantics and extra-field stripping are preserved.
"""

import pytest
from pydantic import ValidationError

# NOTE: api.routes.onboarding is imported lazily inside each test (not at module
# level) so collection does not freeze this module's bot.config binding ahead of
# tests that reload bot.config (e.g. test_config), which would diverge Config.


def test_account_update_rejects_oversized_name():
    from api.routes.onboarding import AccountUpdateRequest

    with pytest.raises(ValidationError):
        AccountUpdateRequest.model_validate({"name": "x" * 5000})


def test_account_update_rejects_wrong_type():
    from api.routes.onboarding import AccountUpdateRequest

    with pytest.raises(ValidationError):
        AccountUpdateRequest.model_validate({"name": 123})


def test_account_update_strips_unknown_fields():
    from api.routes.onboarding import AccountUpdateRequest

    model = AccountUpdateRequest.model_validate(
        {"name": "Jan", "google_sheets_id": "blocked"}
    )
    assert "google_sheets_id" not in model.model_dump()
    # Only the explicitly-sent supported field is tracked for the PATCH.
    assert model.model_fields_set == {"name"}


def test_as_model_preserves_fields_set_for_partial_patch():
    from api.routes.onboarding import AccountUpdateRequest, _as_model

    # phone-only PATCH must not also clear name.
    model = _as_model({"phone": "600100200"}, AccountUpdateRequest)
    assert model.model_fields_set == {"phone"}


def test_as_model_handles_none_and_instances():
    from api.routes.onboarding import (
        GoogleOAuthUrlRequest,
        GoogleResourcesRequest,
        _as_model,
    )

    empty = _as_model(None, GoogleResourcesRequest)
    assert empty.model_dump() == {
        "sheetsName": None,
        "calendarName": None,
        "driveFolderName": None,
    }
    instance = GoogleOAuthUrlRequest(returnUrl="https://agent-oze.pl/x")
    assert _as_model(instance, GoogleOAuthUrlRequest) is instance


def test_oauth_url_rejects_oversized_return_url():
    from api.routes.onboarding import GoogleOAuthUrlRequest

    with pytest.raises(ValidationError):
        GoogleOAuthUrlRequest.model_validate({"returnUrl": "https://x/" + "a" * 4000})
