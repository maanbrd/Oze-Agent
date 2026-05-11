from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_api_me_returns_authenticated_account_profile(monkeypatch):
    from api.auth import AuthUser
    from api.routes import account

    profile = {
        "id": "user-1",
        "auth_user_id": "auth-1",
        "email": "seller@example.com",
        "name": "Seller",
        "activation_paid": True,
    }

    monkeypatch.setattr(account, "_get_account_profile", lambda auth_user: profile)

    response = await account.get_current_account(
        AuthUser(user_id="auth-1", email="auth@example.com", claims={})
    )

    assert response == {
        "auth_user_id": "auth-1",
        "email": "seller@example.com",
        "profile": profile,
    }
