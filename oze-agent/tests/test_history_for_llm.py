from datetime import timedelta
from unittest.mock import patch


def test_get_history_unless_pending_returns_empty_when_pending_active():
    with patch("shared.history_for_llm.get_pending_flow", return_value={"flow_type": "add_note"}), \
         patch("shared.history_for_llm.get_conversation_history") as get_history:
        from shared.history_for_llm import get_history_unless_pending
        result = get_history_unless_pending(123)

    assert result == []
    get_history.assert_not_called()


def test_get_history_unless_pending_uses_r6_window_without_pending():
    with patch("shared.history_for_llm.get_pending_flow", return_value=None), \
         patch("shared.history_for_llm.get_conversation_history", return_value=["h"]) as get_history:
        from shared.history_for_llm import get_history_unless_pending
        result = get_history_unless_pending(123)

    assert result == ["h"]
    get_history.assert_called_once_with(
        123,
        limit=10,
        since=timedelta(minutes=30),
    )
