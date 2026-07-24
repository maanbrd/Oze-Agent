from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from api.auth import AuthUser, require_active_access


def _client(user_rows, beta_rows=None):
    client = MagicMock()

    def table(name):
        chain = MagicMock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.limit.return_value = chain
        result = MagicMock()
        result.data = user_rows if name == "users" else (beta_rows or [])
        chain.execute.return_value = result
        return chain

    client.table.side_effect = table
    return client


@pytest.mark.asyncio
async def test_active_subscription_is_allowed():
    auth = AuthUser("auth-1", "a@example.com", {})
    with patch("api.auth.get_supabase_client", return_value=_client([{"subscription_status": "active"}])):
        assert await require_active_access(auth) is auth


@pytest.mark.asyncio
async def test_inactive_subscription_is_rejected():
    auth = AuthUser("auth-1", "a@example.com", {})
    with patch("api.auth.get_supabase_client", return_value=_client([{"subscription_status": "canceled"}])):
        with pytest.raises(HTTPException) as exc:
            await require_active_access(auth)
    assert exc.value.status_code == 402


@pytest.mark.asyncio
async def test_claimed_active_beta_grant_remains_compatible():
    auth = AuthUser("auth-1", "a@example.com", {})
    beta = [{"auth_user_id": "auth-1", "status": "active"}]
    with patch("api.auth.get_supabase_client", return_value=_client([{"subscription_status": "pending_payment"}], beta)):
        assert await require_active_access(auth) is auth
