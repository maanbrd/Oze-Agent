"""Google Sheets marketing review queue for Agent-OZE content factory.

Sibling of ``shared/google_sheets.py`` — but for marketing carousels, not CRM.

Single tab ``marketing_queue`` lives on a separate spreadsheet (owned by the
admin@agent-oze.pl Google account) and is referenced from
``users.marketing_sheets_id``. Generator pushes PENDING rows, Maan reviews
inside Sheets (sets ``status=APPROVED`` / fills ``feedback_prompt``), publisher
cron picks APPROVED+due rows.

All public functions are async and use ``asyncio.to_thread()`` for sync Google
API calls. They return ``None`` / ``False`` / ``[]`` on failure — never raise.

The single exception is "Sheet not bootstrapped": a ``RuntimeError`` is raised
loudly there so a cron that runs without a target sheet does not silently
no-op week after week (per Maan's call).

Bootstrap once with::

    railway run --service bot --environment production \\
        python -m scripts.content_factory.bootstrap_marketing_sheet \\
        --user-id bd381405-66d2-4544-b817-117f8f8de441
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from shared.database import get_user_by_id, update_user
from shared.google_auth import get_google_credentials

logger = logging.getLogger(__name__)


# ── Schema constants ──────────────────────────────────────────────────────────

MARKETING_TAB = "marketing_queue"
WARSAW_TZ = ZoneInfo("Europe/Warsaw")

# 20 columns A..T — order matters (used as row template + header writer).
#
# FIFO architecture pivot 2026-05-22: the auto-publisher
# (``scripts/marketing/auto_publish.py``) pops the oldest APPROVED row at
# each cron tick. The legacy ``scheduled_at`` column (was col C) has been
# permanently removed on 2026-05-22 — explicit dated publishing is no
# longer supported. ``list_approved_due`` is kept as a no-op deprecated
# stub for backward compatibility.
#
# ``uwagi_do_agenta`` (now col T, added 2026-05-22) is global guidance Maan
# writes anywhere — the daily generator reads every non-empty cell across
# the sheet via ``get_global_directives`` when picking the next mentor/topic.
MARKETING_COLUMNS = [
    "campaign_id",       # A  — primary key, unique, immutable
    "status",            # B  — dropdown (PENDING / APPROVED / REJECTED / PUBLISHED / FAILED)
    "platform",          # C  — dropdown (instagram / facebook / both)
    "caption_ig",        # D  — multi-line IG caption
    "caption_fb",        # E  — multi-line FB caption with clickable link
    "first_comment",     # F  — extra hashtags for IG
    "hashtags",          # G  — comma-separated
    "drive_folder",      # H  — Drive folder URL (6 PNG + preview.mp4)
    "thumbnail_url",     # I  — direct link to slide_01.png (Sheets renders preview)
    "post_id",           # J  — Meta post ID (populated by publisher)
    "published_at",      # K  — actual publish timestamp (populated by publisher)
    "saves_7d",          # L  — populated 7d post-publish
    "shares_7d",         # M  — populated 7d post-publish
    "comments_7d",       # N  — populated 7d post-publish
    "reach_7d",          # O  — populated 7d post-publish
    "subjective_perf",   # P  — dropdown (win / mid / flop) — Maan fills
    "error_message",     # Q  — populated on FAILED / REJECTED reasons
    "feedback_prompt",   # R  — per-row correction Maan writes; agent regenerates
    "feedback_history",  # S  — JSON array of past {timestamp, prompt}
    "uwagi_do_agenta",   # T  — global directive Maan writes anywhere; generator reads
]

# Status constants (canonical).
STATUS_PENDING = "PENDING"
STATUS_APPROVED = "APPROVED"
STATUS_REJECTED = "REJECTED"
STATUS_PUBLISHED = "PUBLISHED"
STATUS_FAILED = "FAILED"

STATUS_OPTIONS = [
    STATUS_PENDING,
    STATUS_APPROVED,
    STATUS_REJECTED,
    STATUS_PUBLISHED,
    STATUS_FAILED,
]

PLATFORM_OPTIONS = ["instagram", "facebook", "both"]
SUBJECTIVE_OPTIONS = ["win", "mid", "flop"]

# Generous — ~10 posts/week × 52 weeks ≈ 520. Rotate via export+trim yearly.
MARKETING_ROW_LIMIT = 1000

# Column widths (pixels) — captions wide, urls narrower, metrics tight.
_COLUMN_WIDTHS = [
    240,  # A  campaign_id
    115,  # B  status
    105,  # C  platform
    420,  # D  caption_ig
    420,  # E  caption_fb
    260,  # F  first_comment
    260,  # G  hashtags
    230,  # H  drive_folder
    230,  # I  thumbnail_url
    180,  # J  post_id
    145,  # K  published_at
    80,   # L  saves_7d
    80,   # M  shares_7d
    90,   # N  comments_7d
    80,   # O  reach_7d
    115,  # P  subjective_perf
    280,  # Q  error_message
    360,  # R  feedback_prompt
    360,  # S  feedback_history
    360,  # T  uwagi_do_agenta
]

# Conditional formatting palette for status column (B = index 1).
_STATUS_COLORS: dict[str, tuple[str, str]] = {
    STATUS_PENDING:   ("#FFE3A0", "#050806"),  # yellow — needs review
    STATUS_APPROVED:  ("#6DFF7A", "#050806"),  # brand light green — green-lit
    STATUS_REJECTED:  ("#E0E0E0", "#050806"),  # muted grey — discarded
    STATUS_PUBLISHED: ("#3DFF7A", "#050806"),  # saturated brand green — done
    STATUS_FAILED:    ("#FFB0B0", "#050806"),  # red — needs attention
}


# ── Internal helpers ──────────────────────────────────────────────────────────


def _rgb(hex_color: str) -> dict[str, float]:
    value = hex_color.removeprefix("#")
    return {
        "red": int(value[0:2], 16) / 255,
        "green": int(value[2:4], 16) / 255,
        "blue": int(value[4:6], 16) / 255,
    }


def _grid_range(
    sheet_id: int,
    *,
    start_row: int | None = None,
    end_row: int | None = None,
    start_col: int | None = None,
    end_col: int | None = None,
) -> dict:
    range_body: dict[str, int] = {"sheetId": sheet_id}
    if start_row is not None:
        range_body["startRowIndex"] = start_row
    if end_row is not None:
        range_body["endRowIndex"] = end_row
    if start_col is not None:
        range_body["startColumnIndex"] = start_col
    if end_col is not None:
        range_body["endColumnIndex"] = end_col
    return range_body


def _data_validation_rule(options: list[str], *, strict: bool = True) -> dict:
    return {
        "condition": {
            "type": "ONE_OF_LIST",
            "values": [{"userEnteredValue": option} for option in options],
        },
        "inputMessage": "Wybierz wartość z listy.",
        "strict": strict,
        "showCustomUi": True,
    }


def _conditional_text_eq_rule(
    sheet_id: int,
    *,
    column_index: int,
    value: str,
    background: str,
    foreground: str = "#050806",
) -> dict:
    return {
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [
                    _grid_range(
                        sheet_id,
                        start_row=1,
                        end_row=MARKETING_ROW_LIMIT,
                        start_col=column_index,
                        end_col=column_index + 1,
                    )
                ],
                "booleanRule": {
                    "condition": {
                        "type": "TEXT_EQ",
                        "values": [{"userEnteredValue": value}],
                    },
                    "format": {
                        "backgroundColor": _rgb(background),
                        "textFormat": {
                            "bold": True,
                            "foregroundColor": _rgb(foreground),
                        },
                    },
                },
            },
            "index": 0,
        }
    }


def _border(color: str, style: str = "SOLID") -> dict:
    return {
        "style": style,
        "width": 1,
        "color": _rgb(color),
    }


def _col_letter(index: int) -> str:
    """0-indexed column number → A1 letter (handles A..ZZ)."""
    letters = ""
    n = index
    while True:
        letters = chr(ord("A") + (n % 26)) + letters
        n = n // 26 - 1
        if n < 0:
            return letters


def _get_sheets_service_sync(user_id: str):
    """Build and return a Google Sheets API service (sync)."""
    creds = get_google_credentials(user_id)
    if not creds:
        return None
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def _is_auth_error(error: HttpError) -> bool:
    return error.resp.status in (401, 403)


def _require_marketing_sheet_id(user_id: str) -> str:
    """Look up users.marketing_sheets_id; raise loudly if missing.

    Per Maan's call: generator/publisher should NOT silently no-op when the
    target sheet has not been bootstrapped. A loud RuntimeError surfaces in
    Railway logs and breaks the cron, which is the desired signal.
    """
    user = get_user_by_id(user_id)
    if not user:
        raise RuntimeError(
            f"Marketing Sheet not bootstrapped for user {user_id}: user not found"
        )
    sheet_id = user.get("marketing_sheets_id")
    if not sheet_id:
        raise RuntimeError(
            f"Marketing Sheet not bootstrapped for user {user_id}: "
            f"users.marketing_sheets_id is empty — run "
            f"scripts/content_factory/bootstrap_marketing_sheet.py"
        )
    return sheet_id


def _pad_row(row: list[Any]) -> list[Any]:
    """Pad/truncate a row to MARKETING_COLUMNS length."""
    if len(row) < len(MARKETING_COLUMNS):
        row = row + [""] * (len(MARKETING_COLUMNS) - len(row))
    return row[: len(MARKETING_COLUMNS)]


def _row_to_dict(row: list[Any], row_index: int) -> dict[str, Any]:
    """Convert a Sheets row list to a dict keyed by header name.

    Adds ``_row`` (1-indexed sheet row) for downstream callers that need to
    issue a targeted update.
    """
    padded = _pad_row(row)
    result = dict(zip(MARKETING_COLUMNS, padded))
    result["_row"] = row_index
    return result


def _build_marketing_template_requests(sheet_id: int) -> list[dict]:
    """Visual + validation + protection requests for the marketing_queue tab.

    Mirrors ``google_sheets.py::_build_operational_crm_template_requests``:
    - Frozen header, brand-locked dark header (#050806 bg, #6DFF7A bold text)
    - Conditional formatting for status (col B): 5 colors
    - Data validations: status (B), platform (C), subjective_perf (P)
    - Datetime format on published_at (K)
    - Number format on metric columns (L..O)
    - Wrap on long-text columns (D, E, F, G, Q, R, S)
    - Protected header row + protected publisher-owned columns (J, K)
    """
    n_cols = len(MARKETING_COLUMNS)
    requests: list[dict] = [
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "gridProperties": {
                        "frozenRowCount": 1,
                        "hideGridlines": True,
                    },
                    "tabColor": _rgb("#3DFF7A"),
                },
                "fields": "gridProperties.frozenRowCount,gridProperties.hideGridlines,tabColor",
            }
        },
        {
            "setBasicFilter": {
                "filter": {
                    "range": _grid_range(
                        sheet_id, start_row=0, start_col=0, end_col=n_cols
                    ),
                }
            }
        },
        # Header row formatting — brand-locked.
        {
            "repeatCell": {
                "range": _grid_range(
                    sheet_id, start_row=0, end_row=1, start_col=0, end_col=n_cols
                ),
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": _rgb("#050806"),
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE",
                        "wrapStrategy": "WRAP",
                        "textFormat": {
                            "bold": True,
                            "fontSize": 10,
                            "foregroundColor": _rgb("#6DFF7A"),
                        },
                    }
                },
                "fields": (
                    "userEnteredFormat(backgroundColor,horizontalAlignment,"
                    "verticalAlignment,wrapStrategy,textFormat)"
                ),
            }
        },
        # Body row default formatting — soft mint with wrap.
        {
            "repeatCell": {
                "range": _grid_range(
                    sheet_id,
                    start_row=1,
                    end_row=MARKETING_ROW_LIMIT,
                    start_col=0,
                    end_col=n_cols,
                ),
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": _rgb("#F4FAF6"),
                        "verticalAlignment": "TOP",
                        "wrapStrategy": "WRAP",
                        "textFormat": {
                            "foregroundColor": _rgb("#101815"),
                            "fontSize": 10,
                        },
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,verticalAlignment,wrapStrategy,textFormat)",
            }
        },
        # Subtle borders across the table.
        {
            "updateBorders": {
                "range": _grid_range(
                    sheet_id,
                    start_row=0,
                    end_row=MARKETING_ROW_LIMIT,
                    start_col=0,
                    end_col=n_cols,
                ),
                "top": _border("#C7D8CC"),
                "bottom": _border("#C7D8CC"),
                "left": _border("#C7D8CC"),
                "right": _border("#C7D8CC"),
                "innerHorizontal": _border("#C7D8CC"),
                "innerVertical": _border("#C7D8CC"),
            }
        },
        # Brand-accent thick underline beneath header.
        {
            "updateBorders": {
                "range": _grid_range(
                    sheet_id, start_row=0, end_row=1, start_col=0, end_col=n_cols
                ),
                "bottom": _border("#3DFF7A", "SOLID_THICK"),
            }
        },
        # Datetime format on published_at (col K, idx 10).
        {
            "repeatCell": {
                "range": _grid_range(
                    sheet_id,
                    start_row=1,
                    end_row=MARKETING_ROW_LIMIT,
                    start_col=10,
                    end_col=11,
                ),
                "cell": {
                    "userEnteredFormat": {
                        "numberFormat": {
                            "type": "DATE_TIME",
                            "pattern": "yyyy-mm-dd hh:mm",
                        }
                    }
                },
                "fields": "userEnteredFormat.numberFormat",
            }
        },
        # Number format on insight columns (L..O, idx 11..14).
        {
            "repeatCell": {
                "range": _grid_range(
                    sheet_id,
                    start_row=1,
                    end_row=MARKETING_ROW_LIMIT,
                    start_col=11,
                    end_col=15,
                ),
                "cell": {
                    "userEnteredFormat": {
                        "numberFormat": {"type": "NUMBER", "pattern": "#,##0"}
                    }
                },
                "fields": "userEnteredFormat.numberFormat",
            }
        },
        # Data validation: status (B, idx 1).
        {
            "repeatCell": {
                "range": _grid_range(
                    sheet_id,
                    start_row=1,
                    end_row=MARKETING_ROW_LIMIT,
                    start_col=1,
                    end_col=2,
                ),
                "cell": {"dataValidation": _data_validation_rule(STATUS_OPTIONS)},
                "fields": "dataValidation",
            }
        },
        # Data validation: platform (C, idx 2).
        {
            "repeatCell": {
                "range": _grid_range(
                    sheet_id,
                    start_row=1,
                    end_row=MARKETING_ROW_LIMIT,
                    start_col=2,
                    end_col=3,
                ),
                "cell": {"dataValidation": _data_validation_rule(PLATFORM_OPTIONS)},
                "fields": "dataValidation",
            }
        },
        # Data validation: subjective_perf (P, idx 15), non-strict so it can stay blank.
        {
            "repeatCell": {
                "range": _grid_range(
                    sheet_id,
                    start_row=1,
                    end_row=MARKETING_ROW_LIMIT,
                    start_col=15,
                    end_col=16,
                ),
                "cell": {
                    "dataValidation": _data_validation_rule(
                        SUBJECTIVE_OPTIONS, strict=False
                    )
                },
                "fields": "dataValidation",
            }
        },
        # Protected header row.
        {
            "addProtectedRange": {
                "protectedRange": {
                    "description": "Agent OZE marketing schema header — do not edit",
                    "range": _grid_range(
                        sheet_id, start_row=0, end_row=1, start_col=0, end_col=n_cols
                    ),
                    "warningOnly": False,
                }
            }
        },
        # Protected publisher-owned columns: post_id (J, idx 9) + published_at (K, idx 10).
        {
            "addProtectedRange": {
                "protectedRange": {
                    "description": "Publisher-owned columns — do not edit manually",
                    "range": _grid_range(
                        sheet_id, start_row=1, start_col=9, end_col=11
                    ),
                    "warningOnly": True,
                }
            }
        },
        # Protected feedback_history (S, idx 18) — append-only, agent-managed.
        {
            "addProtectedRange": {
                "protectedRange": {
                    "description": "Feedback history — append-only, do not edit",
                    "range": _grid_range(
                        sheet_id, start_row=1, start_col=18, end_col=19
                    ),
                    "warningOnly": True,
                }
            }
        },
    ]

    # Column widths.
    for index, width in enumerate(_COLUMN_WIDTHS):
        requests.append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": index,
                    "endIndex": index + 1,
                },
                "properties": {"pixelSize": width},
                "fields": "pixelSize",
            }
        })

    # Conditional formatting per status value (col B = idx 1).
    for status, (background, foreground) in _STATUS_COLORS.items():
        requests.append(_conditional_text_eq_rule(
            sheet_id,
            column_index=1,
            value=status,
            background=background,
            foreground=foreground,
        ))

    return requests


async def _read_all_rows(user_id: str) -> tuple[str, list[list[Any]]]:
    """Fetch every populated row from the marketing_queue tab.

    Returns ``(spreadsheet_id, rows_including_header)``. Raises RuntimeError
    if the user has no ``marketing_sheets_id``.
    """
    spreadsheet_id = _require_marketing_sheet_id(user_id)
    end_col = _col_letter(len(MARKETING_COLUMNS) - 1)

    def _read():
        service = _get_sheets_service_sync(user_id)
        if not service:
            return []
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{MARKETING_TAB}!A1:{end_col}",
        ).execute()
        return result.get("values", [])

    rows = await asyncio.to_thread(_read)
    return spreadsheet_id, rows


async def _find_row_by_campaign_id(
    user_id: str, campaign_id: str
) -> Optional[tuple[str, int, dict]]:
    """Linear scan column A. Returns (spreadsheet_id, 1-indexed row, dict) or None."""
    spreadsheet_id, rows = await _read_all_rows(user_id)
    if len(rows) < 2:
        return None
    for i, row in enumerate(rows[1:], start=2):
        if row and row[0] == campaign_id:
            return spreadsheet_id, i, _row_to_dict(row, i)
    return None


async def _batch_update_row(
    user_id: str,
    spreadsheet_id: str,
    row_number: int,
    updates: dict[str, Any],
) -> bool:
    """Apply column-name → value updates to a single row via batchUpdate."""

    def _update():
        service = _get_sheets_service_sync(user_id)
        if not service:
            return False
        data = []
        for col_name, value in updates.items():
            if col_name not in MARKETING_COLUMNS:
                logger.warning(
                    "marketing_sheets._batch_update_row: unknown column %r — skipped",
                    col_name,
                )
                continue
            col_idx = MARKETING_COLUMNS.index(col_name)
            letter = _col_letter(col_idx)
            data.append({
                "range": f"{MARKETING_TAB}!{letter}{row_number}",
                "values": [[value]],
            })
        if not data:
            return False
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"valueInputOption": "USER_ENTERED", "data": data},
        ).execute()
        return True

    return await asyncio.to_thread(_update)


# ── Public async API — bootstrap ─────────────────────────────────────────────


async def create_marketing_spreadsheet(
    user_id: str, name: str = "Agent OZE — Marketing Queue"
) -> Optional[str]:
    """Create the marketing review queue spreadsheet for this user.

    Idempotent: if ``users.marketing_sheets_id`` is already populated, returns
    the existing spreadsheet id without creating a new one.

    Creates a fresh spreadsheet with the ``marketing_queue`` tab, writes the
    20-column header (post 2026-05-22 ``scheduled_at`` removal), applies the
    operational template (validations, formatting, protection), persists the
    id to Supabase, and returns it.

    Returns ``None`` only on an API failure during creation. Never raises.
    """
    try:
        user = get_user_by_id(user_id)
        if not user:
            logger.error("create_marketing_spreadsheet: user %s not found", user_id)
            return None

        existing = user.get("marketing_sheets_id")
        if existing:
            logger.info(
                "create_marketing_spreadsheet: user %s already has sheet %s",
                user_id,
                existing,
            )
            return existing

        def _create():
            service = _get_sheets_service_sync(user_id)
            if not service:
                return None
            spreadsheet = service.spreadsheets().create(
                body={
                    "properties": {
                        "title": name,
                        "locale": "pl_PL",
                        "timeZone": "Europe/Warsaw",
                    },
                    "sheets": [{
                        "properties": {
                            "title": MARKETING_TAB,
                            "gridProperties": {
                                "rowCount": MARKETING_ROW_LIMIT,
                                "columnCount": len(MARKETING_COLUMNS),
                                "frozenRowCount": 1,
                            },
                        }
                    }],
                }
            ).execute()
            spreadsheet_id = spreadsheet["spreadsheetId"]
            sheet_id = spreadsheet["sheets"][0]["properties"]["sheetId"]

            # Header row.
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{MARKETING_TAB}!A1",
                valueInputOption="RAW",
                body={"values": [MARKETING_COLUMNS]},
            ).execute()

            # Operational template — visual + validation + protection.
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"requests": _build_marketing_template_requests(sheet_id)},
            ).execute()

            return spreadsheet_id

        spreadsheet_id = await asyncio.to_thread(_create)
        if not spreadsheet_id:
            return None

        update_user(user_id, {"marketing_sheets_id": spreadsheet_id})
        logger.info(
            "create_marketing_spreadsheet: created %s for user %s",
            spreadsheet_id,
            user_id,
        )
        return spreadsheet_id

    except Exception as e:
        logger.error("create_marketing_spreadsheet(%s): %s", user_id, e)
        return None


# ── Public async API — CRUD ──────────────────────────────────────────────────


async def push_row(
    user_id: str,
    *,
    campaign_id: str,
    platform: str,
    caption_ig: str,
    caption_fb: str,
    hashtags: str,
    drive_folder: str,
    thumbnail_url: str,
    first_comment: str = "",
    status: str = STATUS_PENDING,
) -> Optional[int]:
    """Append a new row (or update existing) keyed by ``campaign_id``.

    Idempotent: if a row with the same ``campaign_id`` already exists, this
    updates the editable fields rather than appending a duplicate. Useful when
    the generator retries.

    Args:
        user_id: Supabase user UUID (typically Maan / OZE_OWNER_USER_ID).
        campaign_id: Unique, immutable. Generator must not reuse.
        platform: One of PLATFORM_OPTIONS.
        caption_ig / caption_fb: Full multi-line captions, stored verbatim.
        hashtags: Comma-separated string.
        drive_folder / thumbnail_url: Public URLs.
        first_comment: IG-only first comment text.
        status: Defaults to PENDING — override only for backfill.

    Returns the 1-indexed sheet row on success, ``None`` on failure.

    Note: the legacy ``scheduled_at`` parameter was permanently removed
    on 2026-05-22 (FIFO architecture pivot — see module docstring).
    """
    try:
        if platform not in PLATFORM_OPTIONS:
            logger.error(
                "push_row(%s, %s): invalid platform %r",
                user_id,
                campaign_id,
                platform,
            )
            return None
        if status not in STATUS_OPTIONS:
            logger.error(
                "push_row(%s, %s): invalid status %r",
                user_id,
                campaign_id,
                status,
            )
            return None

        spreadsheet_id = _require_marketing_sheet_id(user_id)
        existing = await _find_row_by_campaign_id(user_id, campaign_id)
        if existing is not None:
            _, row_number, _ = existing
            ok = await _batch_update_row(
                user_id,
                spreadsheet_id,
                row_number,
                {
                    "status": status,
                    "platform": platform,
                    "caption_ig": caption_ig,
                    "caption_fb": caption_fb,
                    "first_comment": first_comment,
                    "hashtags": hashtags,
                    "drive_folder": drive_folder,
                    "thumbnail_url": thumbnail_url,
                },
            )
            if ok:
                logger.info(
                    "push_row: updated existing campaign %s at row %d",
                    campaign_id,
                    row_number,
                )
                return row_number
            return None

        # Brand-new row — append.
        row = [
            campaign_id,        # A
            status,             # B
            platform,           # C
            caption_ig,         # D
            caption_fb,         # E
            first_comment,      # F
            hashtags,           # G
            drive_folder,       # H
            thumbnail_url,      # I
            "",                 # J post_id
            "",                 # K published_at
            "",                 # L saves_7d
            "",                 # M shares_7d
            "",                 # N comments_7d
            "",                 # O reach_7d
            "",                 # P subjective_perf
            "",                 # Q error_message
            "",                 # R feedback_prompt
            "",                 # S feedback_history
            "",                 # T uwagi_do_agenta
        ]

        def _append():
            service = _get_sheets_service_sync(user_id)
            if not service:
                return None
            end_col = _col_letter(len(MARKETING_COLUMNS) - 1)
            result = service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=f"{MARKETING_TAB}!A1:{end_col}",
                valueInputOption="USER_ENTERED",
                insertDataOption="OVERWRITE",
                body={"values": [row]},
            ).execute()
            updated_range = result.get("updates", {}).get("updatedRange", "")
            try:
                # e.g. "marketing_queue!A5:T5" → row 5 (T = 20th column)
                cell = updated_range.split("!")[1].split(":")[0]
                digits = "".join(c for c in cell if c.isdigit())
                return int(digits) if digits else None
            except Exception as e:
                logger.error(
                    "push_row: row_num parse failed, updatedRange=%r: %s",
                    updated_range,
                    e,
                )
                return None

        row_num = await asyncio.to_thread(_append)
        if row_num:
            logger.info(
                "push_row: appended campaign %s at row %d", campaign_id, row_num
            )
        return row_num
    except RuntimeError:
        raise
    except Exception as e:
        logger.error("push_row(%s, %s): %s", user_id, campaign_id, e)
        return None


async def get_row(user_id: str, campaign_id: str) -> Optional[dict]:
    """Return a single row as dict, or None if not found."""
    try:
        found = await _find_row_by_campaign_id(user_id, campaign_id)
        if found is None:
            return None
        _, _, row_dict = found
        return row_dict
    except RuntimeError:
        raise
    except Exception as e:
        logger.error("get_row(%s, %s): %s", user_id, campaign_id, e)
        return None


async def list_pending(user_id: str) -> list[dict]:
    """Return rows where ``status == PENDING`` (review queue for Maan)."""
    try:
        _, rows = await _read_all_rows(user_id)
        if len(rows) < 2:
            return []
        result: list[dict] = []
        for i, row in enumerate(rows[1:], start=2):
            d = _row_to_dict(row, i)
            if d.get("status") == STATUS_PENDING:
                result.append(d)
        return result
    except RuntimeError:
        raise
    except Exception as e:
        logger.error("list_pending(%s): %s", user_id, e)
        return []


async def list_with_feedback(user_id: str) -> list[dict]:
    """Return rows where ``feedback_prompt`` is non-empty (iteration queue)."""
    try:
        _, rows = await _read_all_rows(user_id)
        if len(rows) < 2:
            return []
        result: list[dict] = []
        for i, row in enumerate(rows[1:], start=2):
            d = _row_to_dict(row, i)
            prompt = (d.get("feedback_prompt") or "").strip()
            if prompt:
                result.append(d)
        return result
    except RuntimeError:
        raise
    except Exception as e:
        logger.error("list_with_feedback(%s): %s", user_id, e)
        return []


def _parse_scheduled_at(value: str) -> Optional[datetime]:
    """DEPRECATED (2026-05-22). Parse a ``scheduled_at`` string to a
    Europe/Warsaw datetime.

    The ``scheduled_at`` column was permanently removed on 2026-05-22 — this
    helper is retained only because external scripts may still pass legacy
    timestamps. New code must not call it.

    Accepts ``YYYY-MM-DD HH:MM`` (the canonical format we used to write).
    Returns ``None`` for blank or unparseable values rather than raising.
    """
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.replace(tzinfo=WARSAW_TZ)
        except ValueError:
            continue
    return None


async def list_approved_fifo(
    user_id: str, limit: int = 10
) -> list[dict]:
    """Return APPROVED rows in sheet-row order (oldest first = FIFO).

    Ignores ``scheduled_at`` entirely. The auto-publisher cron
    (``scripts/marketing/auto_publish.py``) calls this with ``limit=1`` to
    pop the next-to-publish row at each tick (07:30 / 19:00 Warsaw).

    Why FIFO not scheduled: Maan's 2026-05-22 architecture pivot. Setting a
    per-row publish time was friction (he had to check the sheet, set times,
    and any drift left gaps). Now the machine just publishes the head of the
    APPROVED queue twice a day — Maan only sets ``status=APPROVED`` and the
    cron pops them in order.
    """
    try:
        _, rows = await _read_all_rows(user_id)
        if len(rows) < 2:
            return []
        result: list[dict] = []
        for i, row in enumerate(rows[1:], start=2):
            d = _row_to_dict(row, i)
            if d.get("status") == STATUS_APPROVED:
                result.append(d)
                if len(result) >= limit:
                    break
        return result
    except RuntimeError:
        raise
    except Exception as e:
        logger.error("list_approved_fifo(%s): %s", user_id, e)
        return []


async def get_global_directives(user_id: str) -> list[str]:
    """Return every non-empty ``uwagi_do_agenta`` value across the sheet.

    Maan writes general guidance (e.g. „więcej Cialdiniego", „mniej Pink",
    „dodaj typ D memes") on any row. The daily generator
    (``scripts/marketing/generate_daily.py``) reads all of them before picking
    the next carousel topic / mentor / type.

    Returns a list of strings in sheet-row order (oldest first). Whitespace
    is stripped; duplicates are NOT deduplicated — the caller decides whether
    repetition is signal (more emphasis) or noise.
    """
    try:
        _, rows = await _read_all_rows(user_id)
        if len(rows) < 2:
            return []
        directives: list[str] = []
        uwagi_idx = MARKETING_COLUMNS.index("uwagi_do_agenta")
        for row in rows[1:]:
            if len(row) <= uwagi_idx:
                continue
            value = (row[uwagi_idx] or "").strip()
            if value:
                directives.append(value)
        return directives
    except RuntimeError:
        raise
    except Exception as e:
        logger.error("get_global_directives(%s): %s", user_id, e)
        return []


async def ensure_uwagi_column(user_id: str) -> bool:
    """Write the ``uwagi_do_agenta`` header into col U if missing.

    Migration helper for sheets bootstrapped before 2026-05-22. Idempotent:
    if the header already says ``uwagi_do_agenta`` it returns True without
    rewriting. Returns False on any API failure.

    NB: this only updates the header cell — column widths and validation
    rules baked in during the original bootstrap will not be retro-applied.
    For a fresh sheet, re-run ``create_marketing_spreadsheet`` on a user
    with ``marketing_sheets_id=NULL``.
    """
    try:
        spreadsheet_id = _require_marketing_sheet_id(user_id)
        col_idx = MARKETING_COLUMNS.index("uwagi_do_agenta")
        letter = _col_letter(col_idx)

        def _ensure():
            service = _get_sheets_service_sync(user_id)
            if not service:
                return False
            # Read current value at U1.
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=f"{MARKETING_TAB}!{letter}1",
            ).execute()
            current = (result.get("values") or [[""]])[0]
            current_value = current[0] if current else ""
            if (current_value or "").strip() == "uwagi_do_agenta":
                return True
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{MARKETING_TAB}!{letter}1",
                valueInputOption="RAW",
                body={"values": [["uwagi_do_agenta"]]},
            ).execute()
            return True

        return await asyncio.to_thread(_ensure)
    except RuntimeError:
        raise
    except Exception as e:
        logger.error("ensure_uwagi_column(%s): %s", user_id, e)
        return False


async def list_approved_due(
    user_id: str, now: Optional[datetime] = None
) -> list[dict]:
    """DEPRECATED (2026-05-22). Return every APPROVED row, no time filter.

    Historically returned APPROVED rows whose ``scheduled_at`` was at or
    before ``now``. The ``scheduled_at`` column was permanently removed on
    2026-05-22 (FIFO architecture pivot), so the time filter is no longer
    possible. This function is preserved for backward compatibility and
    now behaves identically to ``list_approved_fifo`` (without the limit).

    ``now`` is accepted but ignored. New code must call
    ``list_approved_fifo`` directly.
    """
    try:
        _ = now  # accepted for legacy API parity; no longer used.
        _, rows = await _read_all_rows(user_id)
        if len(rows) < 2:
            return []
        result: list[dict] = []
        for i, row in enumerate(rows[1:], start=2):
            d = _row_to_dict(row, i)
            if d.get("status") == STATUS_APPROVED:
                result.append(d)
        return result
    except RuntimeError:
        raise
    except Exception as e:
        logger.error("list_approved_due(%s): %s", user_id, e)
        return []


# ── Public async API — status transitions ────────────────────────────────────


async def mark_approved(user_id: str, campaign_id: str) -> bool:
    """Set ``status=APPROVED`` for the given campaign."""
    try:
        spreadsheet_id = _require_marketing_sheet_id(user_id)
        found = await _find_row_by_campaign_id(user_id, campaign_id)
        if found is None:
            logger.warning(
                "mark_approved(%s): campaign %s not found", user_id, campaign_id
            )
            return False
        _, row_number, _ = found
        return await _batch_update_row(
            user_id, spreadsheet_id, row_number, {"status": STATUS_APPROVED}
        )
    except RuntimeError:
        raise
    except Exception as e:
        logger.error("mark_approved(%s, %s): %s", user_id, campaign_id, e)
        return False


async def mark_rejected(
    user_id: str, campaign_id: str, reason: str = ""
) -> bool:
    """Set ``status=REJECTED`` (and ``error_message`` if a reason is supplied)."""
    try:
        spreadsheet_id = _require_marketing_sheet_id(user_id)
        found = await _find_row_by_campaign_id(user_id, campaign_id)
        if found is None:
            logger.warning(
                "mark_rejected(%s): campaign %s not found", user_id, campaign_id
            )
            return False
        _, row_number, _ = found
        updates: dict[str, Any] = {"status": STATUS_REJECTED}
        if reason:
            updates["error_message"] = reason
        return await _batch_update_row(
            user_id, spreadsheet_id, row_number, updates
        )
    except RuntimeError:
        raise
    except Exception as e:
        logger.error("mark_rejected(%s, %s): %s", user_id, campaign_id, e)
        return False


async def mark_published(
    user_id: str,
    campaign_id: str,
    *,
    post_id: str,
    published_at: str,
) -> bool:
    """Atomically write ``status=PUBLISHED`` + ``post_id`` + ``published_at``."""
    try:
        spreadsheet_id = _require_marketing_sheet_id(user_id)
        found = await _find_row_by_campaign_id(user_id, campaign_id)
        if found is None:
            logger.warning(
                "mark_published(%s): campaign %s not found", user_id, campaign_id
            )
            return False
        _, row_number, _ = found
        return await _batch_update_row(
            user_id,
            spreadsheet_id,
            row_number,
            {
                "status": STATUS_PUBLISHED,
                "post_id": post_id,
                "published_at": published_at,
            },
        )
    except RuntimeError:
        raise
    except Exception as e:
        logger.error("mark_published(%s, %s): %s", user_id, campaign_id, e)
        return False


async def mark_failed(
    user_id: str, campaign_id: str, error_message: str
) -> bool:
    """Set ``status=FAILED`` + write ``error_message`` for cron debugging."""
    try:
        spreadsheet_id = _require_marketing_sheet_id(user_id)
        found = await _find_row_by_campaign_id(user_id, campaign_id)
        if found is None:
            logger.warning(
                "mark_failed(%s): campaign %s not found", user_id, campaign_id
            )
            return False
        _, row_number, _ = found
        return await _batch_update_row(
            user_id,
            spreadsheet_id,
            row_number,
            {
                "status": STATUS_FAILED,
                "error_message": error_message,
            },
        )
    except RuntimeError:
        raise
    except Exception as e:
        logger.error("mark_failed(%s, %s): %s", user_id, campaign_id, e)
        return False


async def update_insights(
    user_id: str,
    campaign_id: str,
    *,
    saves: int,
    shares: int,
    comments: int,
    reach: Optional[int] = None,
) -> bool:
    """Populate the 7d insight columns. Idempotent (overwrites)."""
    try:
        spreadsheet_id = _require_marketing_sheet_id(user_id)
        found = await _find_row_by_campaign_id(user_id, campaign_id)
        if found is None:
            logger.warning(
                "update_insights(%s): campaign %s not found", user_id, campaign_id
            )
            return False
        _, row_number, _ = found
        updates: dict[str, Any] = {
            "saves_7d": saves,
            "shares_7d": shares,
            "comments_7d": comments,
        }
        if reach is not None:
            updates["reach_7d"] = reach
        return await _batch_update_row(
            user_id, spreadsheet_id, row_number, updates
        )
    except RuntimeError:
        raise
    except Exception as e:
        logger.error("update_insights(%s, %s): %s", user_id, campaign_id, e)
        return False


# ── Public async API — feedback loop ─────────────────────────────────────────


_EDITABLE_FEEDBACK_FIELDS = {
    "platform",
    "caption_ig",
    "caption_fb",
    "first_comment",
    "hashtags",
    "drive_folder",
    "thumbnail_url",
}


def _parse_feedback_history(raw: str) -> list[dict]:
    """Parse the JSON-encoded feedback_history cell into a list (or [])."""
    raw = (raw or "").strip()
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        logger.warning(
            "marketing_sheets: feedback_history not valid JSON, treating as empty"
        )
    return []


async def append_feedback_history(
    user_id: str, campaign_id: str, prompt: str
) -> bool:
    """Append ``{timestamp, prompt}`` to the JSON ``feedback_history`` cell.

    Stays idempotent for retries — duplicates are allowed because the
    history is append-only and timestamped; the caller is responsible for
    deduping if they care.
    """
    try:
        spreadsheet_id = _require_marketing_sheet_id(user_id)
        found = await _find_row_by_campaign_id(user_id, campaign_id)
        if found is None:
            logger.warning(
                "append_feedback_history(%s): campaign %s not found",
                user_id,
                campaign_id,
            )
            return False
        _, row_number, row_dict = found
        history = _parse_feedback_history(row_dict.get("feedback_history", ""))
        history.append({
            "timestamp": datetime.now(WARSAW_TZ).strftime("%Y-%m-%d %H:%M"),
            "prompt": prompt,
        })
        return await _batch_update_row(
            user_id,
            spreadsheet_id,
            row_number,
            {"feedback_history": json.dumps(history, ensure_ascii=False)},
        )
    except RuntimeError:
        raise
    except Exception as e:
        logger.error(
            "append_feedback_history(%s, %s): %s", user_id, campaign_id, e
        )
        return False


async def update_from_feedback(
    user_id: str, campaign_id: str, **updates: Any
) -> bool:
    """Apply an iteration after the agent processed ``feedback_prompt``.

    - Updates the editable fields supplied in ``**updates`` (caption_ig,
      caption_fb, hashtags, first_comment, platform, drive_folder,
      thumbnail_url).
    - Snapshots the current ``feedback_prompt`` into ``feedback_history``
      with a timestamp (append-only).
    - Clears ``feedback_prompt`` so the row falls out of
      ``list_with_feedback``.
    - Leaves ``status`` untouched (Maan re-reviews — still PENDING by design).

    Unknown kwargs are silently ignored with a warning to keep callers safe
    when the agent invents a key.
    """
    try:
        spreadsheet_id = _require_marketing_sheet_id(user_id)
        found = await _find_row_by_campaign_id(user_id, campaign_id)
        if found is None:
            logger.warning(
                "update_from_feedback(%s): campaign %s not found",
                user_id,
                campaign_id,
            )
            return False
        _, row_number, row_dict = found

        # Snapshot the current feedback_prompt into history (only if present).
        current_prompt = (row_dict.get("feedback_prompt") or "").strip()
        history = _parse_feedback_history(row_dict.get("feedback_history", ""))
        if current_prompt:
            history.append({
                "timestamp": datetime.now(WARSAW_TZ).strftime("%Y-%m-%d %H:%M"),
                "prompt": current_prompt,
            })

        clean_updates: dict[str, Any] = {}
        for key, value in updates.items():
            if key in _EDITABLE_FEEDBACK_FIELDS:
                clean_updates[key] = value
            else:
                logger.warning(
                    "update_from_feedback: ignoring unknown / non-editable field %r",
                    key,
                )

        clean_updates["feedback_prompt"] = ""
        clean_updates["feedback_history"] = json.dumps(history, ensure_ascii=False)

        return await _batch_update_row(
            user_id, spreadsheet_id, row_number, clean_updates
        )
    except RuntimeError:
        raise
    except Exception as e:
        logger.error(
            "update_from_feedback(%s, %s): %s", user_id, campaign_id, e
        )
        return False
