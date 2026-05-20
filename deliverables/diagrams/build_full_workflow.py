"""Generate the full, unsimplified OZE-Agent workflow diagram (n8n style).

Run:
    python3 deliverables/diagrams/build_full_workflow.py

Writes:
    deliverables/diagrams/oze_agent_n8n_workflow_full.svg
    deliverables/diagrams/oze_agent_n8n_workflow_full.png  (if cairosvg available)

Node and edge data below is sourced from the actual codebase:
    oze-agent/bot/main.py
    oze-agent/bot/handlers/*.py
    oze-agent/bot/utils/telegram_helpers.py
    oze-agent/bot/scheduler/*.py
    oze-agent/shared/intent/*.py
    oze-agent/shared/pending/*.py
    oze-agent/shared/mutations/*.py
    oze-agent/shared/offers/*.py
    oze-agent/shared/proactive/morning_brief.py
    oze-agent/shared/admin_mirror/sync.py
    oze-agent/shared/user_profiles/agent.py
    oze-agent/api/routes/*.py
    web/app/**/*
"""

from dataclasses import dataclass, field
from typing import Iterable

CANVAS_W = 1900
CANVAS_H = 4400

# ----------------------------- colour palette ---------------------------------

CANVAS_BG = "#14141f"
GRID_DOT = "#2a2a40"
LANE_BG = "#1a1a2e"
LANE_STROKE = "#2a2a40"
TITLE_BG = "#1f1f33"
TEXT_FG = "#e3e8ff"
TEXT_MUTED = "#8b94b8"
TEXT_DIM = "#5d6688"

COLOR = {
    "telegram":  "#229ED9",
    "switch":    "#506bda",
    "card":      "#3ecf8e",
    "claude":    "#c89b6c",
    "openai":    "#10a37f",
    "logic":     "#9d6bd9",
    "state":     "#f5b54a",
    "sheets":    "#34a853",
    "calendar":  "#4285f4",
    "drive":     "#fbbc04",
    "gmail":     "#ea4335",
    "trigger":   "#ff6d5a",
    "cancel":    "#e76f6f",
    "service":   "#3b3b58",
    "web":       "#1a78ff",
    "fastapi":   "#22d3a4",
    "vercel":    "#000000",
    "stripe":    "#635bff",
    "supabase":  "#3ecf8e",
    "warn":      "#f59e0b",
    "frame":     "#1f2a4a",
    "frameStroke": "#506bda",
    "offerFrameStroke": "#f59e0b",
}

EDGE_DEFAULT = "#7a86b0"
EDGE_AI = "#b89bff"
EDGE_CONFIRM = "#3ecf8e"
EDGE_CANCEL = "#e76f6f"
EDGE_OFFER = "#f59e0b"


# ----------------------------- data classes -----------------------------------

@dataclass
class Node:
    nid: str
    x: int
    y: int
    label: str
    sub: str = ""
    color: str = COLOR["service"]
    text: str = ""           # text shown inside the box (icon area). Emoji ok.
    text_fill: str = "#ffffff"
    w: int = 92
    h: int = 70
    kind: str = "node"       # "node" | "frame" — frame draws hollow rect with stroke

@dataclass
class Edge:
    src: str
    dst: str
    color: str = EDGE_DEFAULT
    label: str = ""
    dashed: bool = False
    marker: str = "arrow"
    # bend factor: 0..1 (0 = horizontal, higher = more curved); negative dips below
    bend_x: float | None = None  # explicit x for control points (relative shift)
    side_src: str = "right"      # "right" | "bottom" | "top" | "left"
    side_dst: str = "left"

NODES: list[Node] = []
EDGES: list[Edge] = []

def N(nid, x, y, label, sub="", color=COLOR["service"], text="", text_fill="#ffffff", w=92, h=70, kind="node"):
    NODES.append(Node(nid, x, y, label, sub, color, text, text_fill, w, h, kind))

def E(src, dst, color=EDGE_DEFAULT, label="", dashed=False, marker="arrow",
      side_src="right", side_dst="left"):
    EDGES.append(Edge(src, dst, color, label, dashed, marker, side_src=side_src, side_dst=side_dst))


# =============================================================================
# LANE A — INGRESS (Telegram trigger + dispatcher + commands + healthcheck)
# y range: 100 - 460
# =============================================================================
LANE_A_Y = 130
LANE_A_LABEL_Y = 120

# Trigger
N("a_tg",        80,  LANE_A_Y, "Telegram trigger",        "webhook /webhooks/telegram (prod) · polling (dev)", COLOR["telegram"], "TG", w=110)

# Update interceptor + healthcheck + error handler
N("a_seen",     220,  LANE_A_Y, "mark_update_seen",        "TypeHandler · group=-1 · healthcheck heartbeat", COLOR["service"], "👀")
N("a_health",   220,  LANE_A_Y+170, "Healthcheck HTTP",   "create_healthcheck_server · /healthz", COLOR["service"], "❤")
N("a_err",      220,  LANE_A_Y+340, "error_handler",       "logs · reply ⚠️ Wystąpił błąd", COLOR["cancel"], "ERR")

# Commands
N("a_start",    360,  LANE_A_Y,     "/start",         "start_command", COLOR["telegram"], "/start")
N("a_cancel",   360,  LANE_A_Y+85,  "/cancel",        "handle_cancel_command", COLOR["cancel"], "✋")
N("a_debug",    360,  LANE_A_Y+170, "/debug_brief",   "debug_brief_command", COLOR["service"], "🐞")
N("a_cols",     360,  LANE_A_Y+255, "/odswiez_kolumny", "handle_refresh_columns_command", COLOR["service"], "🔁")

# Message filters
N("a_fvoice",   500,  LANE_A_Y,     "filter VOICE|AUDIO", "MessageHandler", COLOR["switch"], "🎙")
N("a_fphoto",   500,  LANE_A_Y+85,  "filter PHOTO|IMAGE", "MessageHandler", COLOR["switch"], "📷")
N("a_ftext",    500,  LANE_A_Y+170, "filter TEXT (no /cmd)", "MessageHandler", COLOR["switch"], "💬")
N("a_fcb",      500,  LANE_A_Y+255, "CallbackQueryHandler", "handle_button (callbacks)", COLOR["switch"], "🔘")
N("a_ffall",    500,  LANE_A_Y+340, "filter ALL (fallback)", "handle_fallback", COLOR["service"], "↩")

# ============== Gates (per-message preconditions) ==============
LANE_A_GATES_X = 660
N("a_g_reg",    LANE_A_GATES_X,     LANE_A_Y,     "check_user_registered", "users.* · Supabase", COLOR["state"], "👤")
N("a_g_sub",    LANE_A_GATES_X+150, LANE_A_Y,     "check_subscription_active", "Stripe-driven · _has_active_live_payment", COLOR["stripe"], "💳", text_fill="#fff")
N("a_g_lim",    LANE_A_GATES_X+300, LANE_A_Y,     "check_interaction_limit", "rate-limit per user", COLOR["state"], "⏱")
N("a_g_inc",    LANE_A_GATES_X+450, LANE_A_Y,     "increment_interaction", "counter bump", COLOR["state"], "+1")

# Gate fail responders
N("a_unreg",    LANE_A_GATES_X,     LANE_A_Y+120, "send_unregistered_message", "→ Telegram reply", COLOR["cancel"], "❌")
N("a_expired",  LANE_A_GATES_X+150, LANE_A_Y+120, "send_subscription_expired", "→ Telegram reply", COLOR["cancel"], "❌")
N("a_ratelim",  LANE_A_GATES_X+300, LANE_A_Y+120, "send_rate_limit_message", "→ Telegram reply", COLOR["cancel"], "❌")
N("a_priv",     LANE_A_GATES_X+450, LANE_A_Y+120, "is_private_chat", "private-only check", COLOR["service"], "🔒")

# Edges in lane A
E("a_tg", "a_seen", label="TypeHandler grp=-1")
E("a_seen", "a_health", dashed=True, label="bumps last_seen")
E("a_tg", "a_start"); E("a_tg", "a_cancel"); E("a_tg", "a_debug"); E("a_tg", "a_cols")
E("a_tg", "a_fvoice"); E("a_tg", "a_fphoto"); E("a_tg", "a_ftext"); E("a_tg", "a_fcb"); E("a_tg", "a_ffall")
E("a_tg", "a_err", color=EDGE_CANCEL, dashed=True, label="any unhandled exception")
E("a_fvoice", "a_g_reg")
E("a_fphoto", "a_g_reg")
E("a_ftext", "a_g_reg")
E("a_g_reg", "a_g_sub")
E("a_g_sub", "a_g_lim")
E("a_g_lim", "a_g_inc")
E("a_g_reg", "a_unreg", color=EDGE_CANCEL, dashed=True, label="missing")
E("a_g_sub", "a_expired", color=EDGE_CANCEL, dashed=True, label="expired")
E("a_g_lim", "a_ratelim", color=EDGE_CANCEL, dashed=True, label="over budget")


# =============================================================================
# LANE B — VOICE PIPELINE (y=520-770)
# =============================================================================
LANE_B_Y = 580

N("b_voice",    80,   LANE_B_Y, "handle_voice",            "bot/handlers/voice.py", COLOR["service"], "🎙")
N("b_dl",       220,  LANE_B_Y, "TG File download",        "voice.get_file · bytes", COLOR["telegram"], "⬇")
N("b_stt",      360,  LANE_B_Y, "Whisper STT",             "shared/whisper_stt.py · transcribe_voice", COLOR["openai"], "Whisper")
N("b_segs",     500,  LANE_B_Y, "_segment_avg_logprob",    "low-confidence guard", COLOR["service"], "σ")
N("b_postpass", 640,  LANE_B_Y, "Polish name post-pass",   "shared/voice_postproc.py · Haiku · normalize_polish_names", COLOR["claude"], "Claude", text_fill="#1a1a2e")
N("b_tokdiff",  780,  LANE_B_Y, "_token_diff_ratio",       "fallback if model drifted", COLOR["service"], "Δ")
N("b_redact",   920,  LANE_B_Y, "_redacted_postproc_summary", "log without PII", COLOR["service"], "🕶")
N("b_vcard",   1060,  LANE_B_Y, "Voice 2-button card",     "build_confirm_cancel_buttons · ✅ Zapisz / ❌ Anuluj", COLOR["card"], "✅❌", text_fill="#0e2c1f")
N("b_vpend",   1200,  LANE_B_Y, "pending CLIENT_CONTEXT",  "save_pending · ClientContextPayload (voice)", COLOR["state"], "📦")
N("b_voverride", 1340, LANE_B_Y, "handle_text(text_override=)", "voice → normal text path", COLOR["service"], "↪")

E("a_g_inc", "b_voice", label="voice", side_src="bottom", side_dst="left")
E("b_voice", "b_dl"); E("b_dl", "b_stt"); E("b_stt", "b_segs"); E("b_segs", "b_postpass", color=EDGE_AI)
E("b_postpass", "b_tokdiff"); E("b_tokdiff", "b_redact"); E("b_redact", "b_vcard")
E("b_vcard", "b_vpend", color=EDGE_CONFIRM, label="Zapisz")
E("b_vpend", "b_voverride", color=EDGE_CONFIRM)


# =============================================================================
# LANE C — PHOTO PIPELINE (y=820-1120)
# =============================================================================
LANE_C_Y = 880

N("c_photo",    80,   LANE_C_Y, "handle_photo",                "bot/handlers/photo.py", COLOR["service"], "📷")
N("c_fileid",   220,  LANE_C_Y, "_file_id_from_update",        "extract file_id", COLOR["service"], "id")
N("c_caption",  220,  LANE_C_Y+90, "_caption_from_update",     "user-supplied caption", COLOR["service"], "📝")
N("c_query",    360,  LANE_C_Y, "_explicit_target_query",      "client name in caption?", COLOR["logic"], "🔍")
N("c_match",    360,  LANE_C_Y+90, "_client_matches_text",     "name/city overlap test", COLOR["logic"], "≈")
N("c_resolve",  500,  LANE_C_Y, "_resolve_clients_from_text",  "search_clients(user_id, …)", COLOR["service"], "👥")
N("c_active",   500,  LANE_C_Y+90, "15-min active session",    "derive_active_client · TTL", COLOR["state"], "⏱15m")

N("c_confirm",  640,  LANE_C_Y, "_show_confirmation",          "single match → R1 card", COLOR["card"], "✅", text_fill="#0e2c1f")
N("c_multi",    640,  LANE_C_Y+90, "_show_multi_match",        "≥2 hits · numeric pick", COLOR["switch"], "1·2·3")
N("c_nfound",   640,  LANE_C_Y+180,"_show_not_found",          "[+ Dodaj klienta]", COLOR["warn"], "?")

N("c_addnew",   780,  LANE_C_Y+180,"start_photo_add_client",    "branch → add_client", COLOR["service"], "➕")
N("c_select",   780,  LANE_C_Y+90, "handle_photo_select_client","row_str callback", COLOR["service"], "→")

N("c_uploadS",  780,  LANE_C_Y, "upload_photo_for_session",   "session route", COLOR["service"], "↑S")
N("c_uploadC",  920,  LANE_C_Y, "upload_photo_for_client",    "client route", COLOR["service"], "↑C")
N("c_confup",  1060,  LANE_C_Y, "confirm_photo_upload",        "callback handler", COLOR["service"], "✓")
N("c_complete",1200,  LANE_C_Y+90,"complete_photo_after_add_client", "post add_client commit", COLOR["service"], "✓+")

N("c_drive",   1200,  LANE_C_Y, "Google Drive folder",         "shared/google_drive.py · per-client folder", COLOR["drive"], "Drive", text_fill="#1a1a2e")
N("c_sheetsN", 1340,  LANE_C_Y, "Sheets N=Zdjęcia",            "photo count cell", COLOR["sheets"], "N", text_fill="#fff")
N("c_sheetsO", 1340,  LANE_C_Y+90, "Sheets O=Link",            "Drive folder URL", COLOR["sheets"], "O", text_fill="#fff")
N("c_reply",   1480,  LANE_C_Y, "Telegram reply",              "MarkdownV2 confirmation", COLOR["telegram"], "TG")

E("a_g_inc", "c_photo", label="photo", side_src="bottom", side_dst="left")
E("c_photo", "c_fileid"); E("c_photo", "c_caption")
E("c_fileid", "c_query"); E("c_caption", "c_query")
E("c_query", "c_resolve"); E("c_query", "c_match", dashed=True)
E("c_resolve", "c_active", dashed=True, label="if empty query")
E("c_resolve", "c_confirm", label="1 hit")
E("c_resolve", "c_multi",   label="≥2 hits")
E("c_resolve", "c_nfound",  label="0 hits")
E("c_nfound", "c_addnew", color=EDGE_OFFER)
E("c_multi", "c_select", color=EDGE_CONFIRM, label="picks #")
E("c_confirm", "c_uploadS", color=EDGE_CONFIRM, label="✅ Zapisać")
E("c_select", "c_uploadC", color=EDGE_CONFIRM)
E("c_addnew", "c_complete", dashed=True, label="after add_client")
E("c_uploadS", "c_uploadC")
E("c_uploadC", "c_confup")
E("c_confup", "c_drive", color=EDGE_CONFIRM, label="upload")
E("c_drive", "c_sheetsN"); E("c_drive", "c_sheetsO")
E("c_sheetsN", "c_reply"); E("c_sheetsO", "c_reply", dashed=True)


# =============================================================================
# LANE D — TEXT INTAKE + INTENT ROUTER (y=1200-1500)
# =============================================================================
LANE_D_Y = 1250

N("d_text",     80,   LANE_D_Y, "handle_text",                 "bot/handlers/text.py · 4056 lines", COLOR["service"], "💬")
N("d_active",   220,  LANE_D_Y, "derive_active_client",        "shared/active_client.py · R6", COLOR["state"], "🧠")
N("d_history",  360,  LANE_D_Y, "get_conversation_history",    "10 msg / 30 min · Supabase", COLOR["state"], "📜")
N("d_history2", 360,  LANE_D_Y+90, "get_history_unless_pending", "skip when in pending flow", COLOR["state"], "📜∅")

N("d_preflight_m", 500, LANE_D_Y,    "_meeting_preflight_hint",    "regex: meeting + temporal", COLOR["logic"], "M+T")
N("d_preflight_c", 500, LANE_D_Y+90, "_add_client_preflight_hint", "regex: dodaj/dopisz", COLOR["logic"], "+kl")
N("d_note_sh", 500,    LANE_D_Y+180, "_NOTE_SHORTHAND_RE",         "name: note shorthand", COLOR["logic"], ": n")
N("d_status_sh", 500,  LANE_D_Y+270, "_STATUS_MARKER_RE",          "podpisał/rezygnuje/zamontowano", COLOR["logic"], "Δst")

N("d_router",   680,  LANE_D_Y, "call_claude_with_tools",      "shared/intent/router.py · Haiku · tool-use", COLOR["claude"], "Claude", text_fill="#1a1a2e", w=110)

# Tool list
N("d_t1", 820, LANE_D_Y-30, "record_add_client", "", COLOR["frame"], "", w=170, h=22, kind="frame")
N("d_t2", 820, LANE_D_Y, "record_show_client", "", COLOR["frame"], "", w=170, h=22, kind="frame")
N("d_t3", 820, LANE_D_Y+30, "record_add_note", "", COLOR["frame"], "", w=170, h=22, kind="frame")
N("d_t4", 820, LANE_D_Y+60, "record_change_status", "", COLOR["frame"], "", w=170, h=22, kind="frame")
N("d_t5", 820, LANE_D_Y+90, "record_add_meeting", "", COLOR["frame"], "", w=170, h=22, kind="frame")
N("d_t6", 820, LANE_D_Y+120, "record_show_day_plan", "", COLOR["frame"], "", w=170, h=22, kind="frame")
N("d_t7", 820, LANE_D_Y+150, "record_general_question", "", COLOR["frame"], "", w=170, h=22, kind="frame")
N("d_t8", 820, LANE_D_Y+180, "record_out_of_scope", "feature_key→category", COLOR["frame"], "", w=170, h=22, kind="frame")
N("d_t9", 820, LANE_D_Y+210, "record_multi_meeting_rejection", "", COLOR["frame"], "", w=170, h=22, kind="frame")

N("d_resolve", 1020, LANE_D_Y, "_to_intent_result",            "tool→IntentType · ScopeTier", COLOR["logic"], "→IT")
N("d_banner",  1020, LANE_D_Y+100, "banner_for(result)",        "POST_MVP / VISION / UNPLANNED / MULTI", COLOR["warn"], "🏷")
N("d_banlegacy", 1020, LANE_D_Y+200, "banner_for_legacy",       "intent_data fallback", COLOR["warn"], "🏷·")

# Entity extractors
N("d_ex_client", 1180, LANE_D_Y, "extract_client_data",        "Claude · structured", COLOR["claude"], "Claude", text_fill="#1a1a2e")
N("d_ex_meet",   1180, LANE_D_Y+90, "extract_meeting_data",     "Claude · structured", COLOR["claude"], "Claude", text_fill="#1a1a2e")
N("d_ex_note",   1180, LANE_D_Y+180,"extract_note_data",        "Claude · structured", COLOR["claude"], "Claude", text_fill="#1a1a2e")
N("d_genresp",   1180, LANE_D_Y+270, "generate_bot_response",   "Claude reply (general_question)", COLOR["claude"], "Claude", text_fill="#1a1a2e")

E("a_g_inc", "d_text", label="text", side_src="bottom", side_dst="left")
E("b_voverride", "d_text", color=EDGE_CONFIRM, dashed=True, label="voice path joins")
E("d_text", "d_active")
E("d_active", "d_history")
E("d_history", "d_history2", dashed=True)
E("d_text", "d_preflight_m", dashed=True)
E("d_text", "d_preflight_c", dashed=True)
E("d_text", "d_note_sh", dashed=True)
E("d_text", "d_status_sh", dashed=True)
E("d_preflight_m", "d_router", color=EDGE_AI, label="forces record_add_meeting if hit")
E("d_preflight_c", "d_router", color=EDGE_AI)
E("d_history", "d_router", color=EDGE_AI, dashed=True, label="context")
E("d_router", "d_t1", dashed=True)
E("d_router", "d_t2", dashed=True)
E("d_router", "d_t3", dashed=True)
E("d_router", "d_t4", dashed=True)
E("d_router", "d_t5", dashed=True)
E("d_router", "d_t6", dashed=True)
E("d_router", "d_t7", dashed=True)
E("d_router", "d_t8", dashed=True)
E("d_router", "d_t9", dashed=True)
E("d_t1", "d_resolve"); E("d_t2", "d_resolve"); E("d_t3", "d_resolve"); E("d_t4", "d_resolve"); E("d_t5", "d_resolve")
E("d_t6", "d_resolve"); E("d_t7", "d_resolve"); E("d_t8", "d_resolve"); E("d_t9", "d_resolve")
E("d_resolve", "d_banner", dashed=True, label="if out-of-scope")
E("d_banner", "d_banlegacy", dashed=True)
E("d_resolve", "d_ex_client", color=EDGE_AI)
E("d_resolve", "d_ex_meet", color=EDGE_AI)
E("d_resolve", "d_ex_note", color=EDGE_AI)
E("d_resolve", "d_genresp", color=EDGE_AI, dashed=True)


# =============================================================================
# LANE E — INTENT SWITCH + R4 + DISAMBIG (y=1580-1900)
# =============================================================================
LANE_E_Y = 1620

N("e_sw", 80, LANE_E_Y+60, "Switch · IntentType", "11 enum values · ScopeTier", COLOR["switch"], "🔀")

intents = [
    ("e_i_addc",   "add_client",       "MVP", COLOR["frameStroke"]),
    ("e_i_showc",  "show_client",      "MVP", COLOR["frameStroke"]),
    ("e_i_addn",   "add_note",         "MVP", COLOR["frameStroke"]),
    ("e_i_chst",   "change_status",    "MVP", COLOR["frameStroke"]),
    ("e_i_addm",   "add_meeting",      "MVP", COLOR["frameStroke"]),
    ("e_i_show",   "show_day_plan",    "MVP", COLOR["frameStroke"]),
    ("e_i_gen",    "general_question", "MVP", COLOR["frameStroke"]),
    ("e_i_post",   "post_mvp_roadmap", "banner", COLOR["offerFrameStroke"]),
    ("e_i_vis",    "vision_only",      "banner", COLOR["offerFrameStroke"]),
    ("e_i_unp",    "unplanned",        "banner", COLOR["offerFrameStroke"]),
    ("e_i_mm",     "multi_meeting",    "rejected", COLOR["cancel"]),
]
for i, (nid, lbl, scope, stroke) in enumerate(intents):
    N(nid, 240, LANE_E_Y + i*38, lbl, scope, COLOR["frame"], "", w=150, h=30, kind="frame")
    E("e_sw", nid, dashed=False)

# R4 identification block
N("e_r4",       440, LANE_E_Y,     "R4 client identify",     "imię+nazwisko+miasto · fuzzy · PL declension", COLOR["switch"], "🔍", w=110)
N("e_search",   590, LANE_E_Y,     "search_clients",          "shared/google_sheets.py", COLOR["sheets"], "Sheets", text_fill="#fff")
N("e_fuzzy",    590, LANE_E_Y+90,  "matching.fuzzy",          "shared/matching.py", COLOR["logic"], "≈")
N("e_declen",   590, LANE_E_Y+180, "Polish declension",       "Krzywińskim → Krzywiński", COLOR["logic"], "PL")
N("e_search2",  590, LANE_E_Y+270, "shared/search.py",        "name+city scoring", COLOR["logic"], "🔍s")

N("e_full",     740, LANE_E_Y,      "match=1",                "single hit → continue", COLOR["card"], "1", text_fill="#0e2c1f", w=70, h=50)
N("e_multi",    740, LANE_E_Y+70,   "match≥2",                "→ multi-match card", COLOR["switch"], "n", w=70, h=50)
N("e_dup",      740, LANE_E_Y+140,  "match=1 on add_client",  "→ duplicate resolution", COLOR["warn"], "Δ", w=70, h=50)
N("e_zero",     740, LANE_E_Y+210,  "match=0",                "ask / fail", COLOR["cancel"], "∅", w=70, h=50)

# Cards from R4
N("e_card_dis", 880, LANE_E_Y+70,  "Multi-match card",        "build_choice_buttons · [1][2][3]", COLOR["switch"], "1·2·3")
N("e_card_dup", 880, LANE_E_Y+140, "Duplicate card",          "build_duplicate_buttons · [Nowy] [Aktualizuj]", COLOR["card"], "N/A", text_fill="#0e2c1f")

# Active client R6 fallback
N("e_r6",       440, LANE_E_Y+180, "Active client R6",        "derive_active_client · 30 min", COLOR["state"], "R6")
N("e_field_up", 440, LANE_E_Y+270, "parse_client_field_update", "shared/behavior/client_field_update.py", COLOR["logic"], "Δfield")

# Helpers shared by intents
N("e_actype",   1040, LANE_E_Y,      "action_type",            "calendar_title · action_label · success", COLOR["logic"], "Atp")
N("e_meetloc",  1040, LANE_E_Y+90,   "resolve_meeting_location", "shared/behavior/meeting_location.py", COLOR["logic"], "📍")
N("e_nxstep",   1040, LANE_E_Y+180,  "classify_next_step_reply", "NextStepDecisionKind", COLOR["logic"], "→?")
N("e_seedmeet", 1040, LANE_E_Y+270,  "build_meeting_seeded_client_data", "meeting_client_flow.py", COLOR["logic"], "🔗")

E("e_i_addc", "e_dup", label="match=1")
E("e_i_addc", "e_r4", label="otherwise (new)", dashed=True)
E("e_i_showc", "e_r4")
E("e_i_addn", "e_r4")
E("e_i_chst", "e_r4")
E("e_i_addm", "e_r4")
E("e_i_show", "e_actype", dashed=True, label="read-only")
E("e_i_gen", "e_actype", dashed=True)
E("e_i_post", "e_actype", color=EDGE_OFFER, dashed=True, label="banner only")
E("e_i_vis", "e_actype", color=EDGE_OFFER, dashed=True)
E("e_i_unp", "e_actype", color=EDGE_OFFER, dashed=True)
E("e_i_mm", "e_actype", color=EDGE_CANCEL, dashed=True, label="rejected w/ msg")

E("e_r4", "e_search"); E("e_r4", "e_fuzzy", dashed=True); E("e_r4", "e_declen", dashed=True); E("e_r4", "e_search2", dashed=True)
E("e_r4", "e_r6", dashed=True, label="R6 fallback")
E("e_search", "e_full"); E("e_search", "e_multi"); E("e_search", "e_dup"); E("e_search", "e_zero")
E("e_multi", "e_card_dis", color=EDGE_CONFIRM)
E("e_dup", "e_card_dup", color=EDGE_CONFIRM)

# next-step prompt feedback
E("e_field_up", "e_actype", dashed=True)


# =============================================================================
# LANE F — PENDING STATE MACHINE + CARD BUILDERS + BUTTON DISPATCH
# y=1980-2330
# =============================================================================
LANE_F_Y = 2000

N("f_store",  80,  LANE_F_Y+120, "pending_flow_store",     "shared/pending/store.py · Supabase pending_flows", COLOR["state"], "📦", w=110, h=90)

ptypes = [
    ("f_p_addc",   "ADD_CLIENT",                   "AddClientPayload"),
    ("f_p_dup",    "ADD_CLIENT_DUPLICATE",         "AddClientDuplicatePayload"),
    ("f_p_addn",   "ADD_NOTE",                     "AddNotePayload"),
    ("f_p_chst",   "CHANGE_STATUS",                "ChangeStatusPayload"),
    ("f_p_addm",   "ADD_MEETING",                  "AddMeetingPayload"),
    ("f_p_mdis",   "ADD_MEETING_DISAMBIGUATION",   "AddMeetingDisambiguationPayload"),
    ("f_p_dis",    "DISAMBIGUATION",               "DisambiguationPayload"),
    ("f_p_ctx",    "CLIENT_CONTEXT",               "ClientContextPayload"),
    ("f_p_fu",     "CLIENT_FIELD_UPDATE_CONFIRM",  "ClientFieldUpdateConfirmPayload"),
    ("f_p_nxt",    "AWAITING_NEXT_STEP",           "AwaitingNextStepPayload"),
]
for i, (nid, name, sub) in enumerate(ptypes):
    N(nid, 240, LANE_F_Y + i*38, name, sub, COLOR["frame"], "", w=210, h=30, kind="frame")
    E(nid, "f_store", dashed=True)

# Save/get/delete
N("f_save",     500, LANE_F_Y,     "save_pending",           "shared/pending/__init__.py", COLOR["state"], "💾")
N("f_get",      500, LANE_F_Y+90,  "get_pending_flow",       "Supabase read", COLOR["state"], "↻")
N("f_del",      500, LANE_F_Y+180, "delete_pending_flow",    "on confirm/cancel", COLOR["state"], "🗑")
N("f_upfu",     500, LANE_F_Y+270, "update_pending_followup",   "phone_call follow-up state", COLOR["state"], "🔁")
E("f_store", "f_save"); E("f_store", "f_get"); E("f_store", "f_del"); E("f_store", "f_upfu")

# Card builders
N("f_mut",      660, LANE_F_Y,     "build_mutation_buttons", "[✅ Zapisać] [➕ Dopisać] [❌ Anulować]", COLOR["card"], "3-btn", text_fill="#0e2c1f")
N("f_cc",       660, LANE_F_Y+90,  "build_confirm_cancel_buttons", "[✅ Zapisz] [❌ Anuluj]", COLOR["card"], "2-btn", text_fill="#0e2c1f")
N("f_dup",      660, LANE_F_Y+180, "build_duplicate_buttons", "[Nowy] [Aktualizuj]", COLOR["card"], "dup", text_fill="#0e2c1f")
N("f_choice",   660, LANE_F_Y+270, "build_choice_buttons",   "generic [1][2][3]", COLOR["switch"], "1·2·3")

E("f_save", "f_mut")
E("f_save", "f_cc")
E("f_save", "f_dup")
E("f_save", "f_choice")

# Reply formatters
N("f_fmtcli", 820, LANE_F_Y,      "format_add_client_card",  "shared/formatting.py", COLOR["service"], "📋")
N("f_fmtshow",820, LANE_F_Y+90,   "format_client_card",      "show_client output", COLOR["service"], "📋")
N("f_fmtcon", 820, LANE_F_Y+180,  "format_confirmation",     "shared mutation card", COLOR["service"], "📋")
N("f_fmtday", 820, LANE_F_Y+270,  "format_daily_schedule",   "show_day_plan", COLOR["service"], "📋")
N("f_fmtedit",820, LANE_F_Y+360,  "format_edit_comparison",  "field update", COLOR["service"], "📋")

# Telegram reply nodes (per card)
N("f_reply",   980, LANE_F_Y,     "reply_markdown_v2",       "bot/utils/conversation_reply.py", COLOR["telegram"], "TG")
N("f_replytxt",980, LANE_F_Y+90,  "reply_text",              "+ persist to conversation_history", COLOR["telegram"], "TG·")
N("f_savemsg", 980, LANE_F_Y+180, "save_conversation_message", "Supabase conversation_history", COLOR["state"], "💬+")

E("f_mut", "f_fmtcon")
E("f_cc", "f_fmtcon")
E("f_dup", "f_fmtcon")
E("f_choice", "f_fmtcon")
E("f_fmtcon", "f_reply"); E("f_fmtcli", "f_reply"); E("f_fmtshow", "f_reply"); E("f_fmtday", "f_reply"); E("f_fmtedit", "f_reply")
E("f_reply", "f_savemsg", dashed=True)
E("f_replytxt", "f_savemsg", dashed=True)

# Callback / button dispatch
N("f_handle_btn", 1140, LANE_F_Y,      "handle_button",       "bot/handlers/buttons.py · 647 lines · CallbackQueryHandler", COLOR["switch"], "🔘", w=110)
N("f_cb_save",  1140, LANE_F_Y+100, "callback save",          "→ commit pipeline", COLOR["card"], "✅", text_fill="#0e2c1f")
N("f_cb_app",   1140, LANE_F_Y+170, "callback append",        "➕ Dopisać", COLOR["card"], "➕", text_fill="#0e2c1f")
N("f_cb_cnc",   1140, LANE_F_Y+240, "callback cancel",        "❌ Anulować · delete_pending", COLOR["cancel"], "❌")
N("f_cb_new",   1140, LANE_F_Y+310, "callback [Nowy]",        "create new client row", COLOR["card"], "N", text_fill="#0e2c1f")
N("f_cb_upd",   1140, LANE_F_Y+380, "callback [Aktualizuj]",  "update existing client", COLOR["card"], "A", text_fill="#0e2c1f")

E("f_handle_btn", "f_cb_save")
E("f_handle_btn", "f_cb_app")
E("f_handle_btn", "f_cb_cnc")
E("f_handle_btn", "f_cb_new")
E("f_handle_btn", "f_cb_upd")
E("a_fcb", "f_handle_btn", color=EDGE_CONFIRM, dashed=True, label="all callbacks")


# =============================================================================
# LANE G — MUTATION COMMIT PIPELINES  (y=2400-2780)
# =============================================================================
LANE_G_Y = 2440

N("g_add_client",      80, LANE_G_Y,       "commit_add_client",            "shared/mutations/add_client.py", COLOR["card"], "✅+kl", text_fill="#0e2c1f")
N("g_upd_client",      80, LANE_G_Y+90,    "commit_update_client_fields", "edit existing", COLOR["card"], "Δkl", text_fill="#0e2c1f")
N("g_add_note",        80, LANE_G_Y+180,   "commit_add_note",             "append to Notatki", COLOR["card"], "✅n", text_fill="#0e2c1f")
N("g_chg_status",      80, LANE_G_Y+270,   "commit_change_status",        "Sheets F + Calendar event", COLOR["card"], "✅Δst", text_fill="#0e2c1f")
N("g_add_meeting",     80, LANE_G_Y+360,   "commit_add_meeting",          "Sheets J/L + Calendar event", COLOR["card"], "✅mtg", text_fill="#0e2c1f")

N("g_seeded",         240, LANE_G_Y+360,   "build_meeting_seeded_client_data", "missing fields for compound meeting+client", COLOR["logic"], "🔗", h=80)
N("g_canon",          240, LANE_G_Y+440,   "canonical_missing_client_fields", "produce add_client follow-up", COLOR["logic"], "🔗·")

# Helpers used inside commits
N("g_default_status", 240, LANE_G_Y,       "with_default_client_status",  "F=Nowy lead", COLOR["logic"], "Fdef")
N("g_format_note",    240, LANE_G_Y+180,   "_format_note_entry",          "[20.05.2026] ...", COLOR["logic"], "fmt")
N("g_merge_note",     240, LANE_G_Y+270,   "_merge_with_existing",        "join existing Notatki", COLOR["logic"], "∪")
N("g_format_date",    240, LANE_G_Y+90,    "format_next_step_date_for_sheets", "DD.MM.YYYY", COLOR["logic"], "📅")

# Sheets / Calendar / Drive writes
N("g_sheets_add",     400, LANE_G_Y,       "google_sheets.add_client",     "new row", COLOR["sheets"], "Sheets", text_fill="#fff", w=110)
N("g_sheets_upd",     400, LANE_G_Y+90,    "google_sheets.update_client",  "cell update", COLOR["sheets"], "Sheets", text_fill="#fff", w=110)
N("g_sheets_get",     400, LANE_G_Y+180,   "get_all_clients · get_sheet_headers", "schema read", COLOR["sheets"], "Sheets·r", text_fill="#fff", w=110)

N("g_cal_create",     560, LANE_G_Y,       "google_calendar.create_event", "lead / phone_call / offer_email / in_person", COLOR["calendar"], "Cal+", text_fill="#fff", w=110)
N("g_cal_conf",       560, LANE_G_Y+90,    "check_conflicts",              "before create_event", COLOR["calendar"], "Cal?", text_fill="#fff", w=110)
N("g_cal_day",        560, LANE_G_Y+180,   "get_events_for_date",          "show_day_plan", COLOR["calendar"], "Cal d", text_fill="#fff", w=110)
N("g_cal_range",      560, LANE_G_Y+270,   "get_events_for_range",         "morning brief", COLOR["calendar"], "Cal r", text_fill="#fff", w=110)

# Post-commit
N("g_nxprompt",   720, LANE_G_Y+90,  "next_action_prompt",      "after add_client · open prose ask", COLOR["state"], "?→", w=110)
N("g_awaiting",   720, LANE_G_Y+180, "save AWAITING_NEXT_STEP",  "AwaitingNextStepPayload", COLOR["state"], "📦?", w=110)
N("g_clientctx",  720, LANE_G_Y+270, "save CLIENT_CONTEXT",      "ClientContextPayload (active client)", COLOR["state"], "📦·", w=110)
N("g_succmsg",    720, LANE_G_Y,     "action success message",   "shared/behavior/action_type.success_message", COLOR["telegram"], "TG✓", w=110)

E("f_cb_save", "g_add_client", color=EDGE_CONFIRM, label="add_client", dashed=True)
E("f_cb_save", "g_add_note", color=EDGE_CONFIRM, dashed=True)
E("f_cb_save", "g_chg_status", color=EDGE_CONFIRM, dashed=True)
E("f_cb_save", "g_add_meeting", color=EDGE_CONFIRM, dashed=True)
E("f_cb_upd",  "g_upd_client", color=EDGE_CONFIRM, dashed=True)

E("g_add_client", "g_default_status", dashed=True)
E("g_add_client", "g_sheets_add")
E("g_add_client", "g_cal_create", dashed=True, label="if follow-up date")
E("g_upd_client", "g_sheets_upd")
E("g_add_note", "g_format_note", dashed=True)
E("g_add_note", "g_merge_note", dashed=True)
E("g_add_note", "g_sheets_upd")
E("g_chg_status", "g_sheets_upd")
E("g_chg_status", "g_cal_create")
E("g_add_meeting", "g_cal_conf", dashed=True, label="conflict pre-check")
E("g_add_meeting", "g_format_date", dashed=True)
E("g_add_meeting", "g_sheets_upd")
E("g_add_meeting", "g_cal_create")
E("g_add_meeting", "g_seeded", dashed=True, label="compound meeting+client")
E("g_seeded", "g_canon", dashed=True)
E("g_canon", "g_add_client", dashed=True)

E("g_add_client", "g_nxprompt", color=EDGE_CONFIRM, dashed=True, label="ask next step")
E("g_nxprompt", "g_awaiting", color=EDGE_CONFIRM)
E("e_nxstep", "g_awaiting", dashed=True, label="reply classified")
E("g_add_client", "g_clientctx", dashed=True, label="mark active")
E("g_add_client", "g_succmsg")
E("g_add_note", "g_succmsg")
E("g_chg_status", "g_succmsg")
E("g_add_meeting", "g_succmsg")
E("g_upd_client", "g_succmsg")


# =============================================================================
# LANE H — SCHEDULERS  (y=2900-3260)
# =============================================================================
LANE_H_Y = 2940

# Morning brief
N("h_cron_mb", 80, LANE_H_Y, "Cron 07:00 Warsaw", "register_morning_brief · run_daily", COLOR["trigger"], "07:00")
N("h_mb_cb",   220, LANE_H_Y, "_morning_brief_callback", "bot/scheduler/morning_brief_job.py", COLOR["service"], "🌅")
N("h_run_mb",  360, LANE_H_Y, "run_morning_brief", "shared/proactive/morning_brief.py", COLOR["service"], "🚀")
N("h_fetch_ns",500, LANE_H_Y, "_fetch_open_next_steps", "Sheets + Calendar today", COLOR["sheets"], "→ns", text_fill="#fff")
N("h_dedup",   640, LANE_H_Y, "_already_sent_today", "Supabase sent_morning_briefs", COLOR["state"], "1/d")
N("h_format",  780, LANE_H_Y, "format_morning_brief", "Claude · shared/claude_ai.py", COLOR["claude"], "Claude", text_fill="#1a1a2e")
N("h_push_mb", 920, LANE_H_Y, "bot.send_message", "Telegram push to handlowiec", COLOR["telegram"], "TG")

# Admin mirror
N("h_cron_am", 80, LANE_H_Y+110, "Cron 03:00 Warsaw", "register_admin_mirror · daily", COLOR["trigger"], "03:00")
N("h_am_cb",   220, LANE_H_Y+110, "_admin_mirror_callback", "bot/scheduler/admin_mirror_job.py", COLOR["service"], "🪞")
N("h_am_sync", 360, LANE_H_Y+110, "admin_mirror.sync", "shared/admin_mirror/sync.py", COLOR["service"], "↻")
N("h_am_fetch",500, LANE_H_Y+110, "_fetch_active_user_contacts", "Sheets + Supabase per user", COLOR["sheets"], "→c", text_fill="#fff")
N("h_am_io",   640, LANE_H_Y+110, "admin_mirror.google_io", "OAuth-as-owner writes", COLOR["service"], "io")
N("h_am_rows", 780, LANE_H_Y+110, "admin_mirror.rows / calendar / data", "tab builders", COLOR["service"], "rows")
N("h_am_sh",   920, LANE_H_Y+110, "Owner Sheets snapshot", "writes owner spreadsheet", COLOR["sheets"], "OwnS", text_fill="#fff")
N("h_am_cal", 1060, LANE_H_Y+110, "Owner Calendar copy", "future appointments mirror", COLOR["calendar"], "OwnC", text_fill="#fff")

# User profile agent
N("h_cron_up", 80, LANE_H_Y+220, "Cron 02:15 Warsaw", "register_user_profile_agent · daily", COLOR["trigger"], "02:15")
N("h_up_cb",   220, LANE_H_Y+220, "_user_profile_agent_callback", "bot/scheduler/user_profile_agent_job.py", COLOR["service"], "👤")
N("h_up_run",  360, LANE_H_Y+220, "run_user_profile_agent", "shared/user_profiles/agent.py", COLOR["service"], "🚀")
N("h_up_each", 500, LANE_H_Y+220, "_run_for_user", "iterate active users", COLOR["service"], "∀u")
N("h_up_hist", 640, LANE_H_Y+220, "_format_messages · _last_message_at", "recent conversation_history", COLOR["state"], "hist")
N("h_up_llm",  780, LANE_H_Y+220, "Claude analyze tone/habits", "_system_prompt · _user_prompt", COLOR["claude"], "Claude", text_fill="#1a1a2e")
N("h_up_parse",920, LANE_H_Y+220, "parse_profile_response", "ProfileDraft · _strip_json_fence", COLOR["logic"], "JSON")
N("h_up_store",1060, LANE_H_Y+220, "user_profiles.store",  "Supabase user_profiles upsert", COLOR["state"], "📦u")
N("h_up_fail", 1200, LANE_H_Y+220, "_safe_insert_failed_run", "audit row on exception", COLOR["cancel"], "✗")

# Edges
E("h_cron_mb", "h_mb_cb"); E("h_mb_cb", "h_run_mb"); E("h_run_mb", "h_fetch_ns"); E("h_fetch_ns", "h_dedup"); E("h_dedup", "h_format", color=EDGE_AI); E("h_format", "h_push_mb")
E("h_cron_am", "h_am_cb"); E("h_am_cb", "h_am_sync"); E("h_am_sync", "h_am_fetch"); E("h_am_fetch", "h_am_io"); E("h_am_io", "h_am_rows"); E("h_am_rows", "h_am_sh"); E("h_am_sh", "h_am_cal")
E("h_cron_up", "h_up_cb"); E("h_up_cb", "h_up_run"); E("h_up_run", "h_up_each"); E("h_up_each", "h_up_hist"); E("h_up_hist", "h_up_llm", color=EDGE_AI); E("h_up_llm", "h_up_parse"); E("h_up_parse", "h_up_store"); E("h_up_each", "h_up_fail", color=EDGE_CANCEL, dashed=True)


# =============================================================================
# LANE I — OFFER GENERATOR FULL SLICE  (y=3290-3700)
# =============================================================================
LANE_I_Y = 3320

# Web
N("i_oferty",   80,  LANE_I_Y,       "Web /oferty",            "Next.js 15 · dark app shell", COLOR["web"], "Web", text_fill="#fff")
N("i_ed",      210,  LANE_I_Y,       "offer-generator.tsx",     "web/components/offers", COLOR["web"], "Edit", text_fill="#fff")
N("i_proxy",   340,  LANE_I_Y,       "web proxy.ts",            "→ FastAPI", COLOR["service"], "↔")
# 14 FastAPI routes
N("i_r_list",   470, LANE_I_Y,         "GET /offers/templates",       "list", COLOR["fastapi"], "GET", text_fill="#073d2a", h=30, w=180)
N("i_r_create", 470, LANE_I_Y+35,      "POST /offers/templates",      "create", COLOR["fastapi"], "POST", text_fill="#073d2a", h=30, w=180)
N("i_r_upd",    470, LANE_I_Y+70,      "PATCH /offers/templates/{id}", "update", COLOR["fastapi"], "PATCH", text_fill="#073d2a", h=30, w=180)
N("i_r_del",    470, LANE_I_Y+105,     "DELETE /offers/templates/{id}", "delete", COLOR["fastapi"], "DEL", text_fill="#073d2a", h=30, w=180)
N("i_r_pub",    470, LANE_I_Y+140,     "POST /offers/templates/{id}/publish", "publish", COLOR["fastapi"], "POST", text_fill="#073d2a", h=30, w=180)
N("i_r_dup",    470, LANE_I_Y+175,     "POST /offers/templates/{id}/duplicate", "duplicate", COLOR["fastapi"], "POST", text_fill="#073d2a", h=30, w=180)
N("i_r_re",     470, LANE_I_Y+210,     "POST /offers/templates/reorder", "reorder", COLOR["fastapi"], "POST", text_fill="#073d2a", h=30, w=180)
N("i_r_prof_g", 470, LANE_I_Y+245,     "GET /offers/profile",        "seller profile", COLOR["fastapi"], "GET", text_fill="#073d2a", h=30, w=180)
N("i_r_prof_p", 470, LANE_I_Y+280,     "PUT /offers/profile",        "save profile", COLOR["fastapi"], "PUT", text_fill="#073d2a", h=30, w=180)
N("i_r_ev",     470, LANE_I_Y+315,     "GET /offers/email-variables", "available tokens", COLOR["fastapi"], "GET", text_fill="#073d2a", h=30, w=180)
N("i_r_logo",   470, LANE_I_Y+350,     "POST /offers/profile/logo",  "upload logo", COLOR["fastapi"], "POST", text_fill="#073d2a", h=30, w=180)
N("i_r_pdf",    470, LANE_I_Y+385,     "GET /offers/templates/{id}/test-pdf", "test PDF", COLOR["fastapi"], "GET", text_fill="#073d2a", h=30, w=180)

# Shared offers
N("i_repo",    690, LANE_I_Y,      "OfferRepository",        "shared/offers/repository.py", COLOR["state"], "📦o", w=110)
N("i_val",     690, LANE_I_Y+90,   "validation",              "shared/offers/validation.py", COLOR["logic"], "✓val")
N("i_pri",     690, LANE_I_Y+180,  "pricing",                 "shared/offers/pricing.py", COLOR["logic"], "💰")
N("i_num",     690, LANE_I_Y+270,  "numbering",               "list_ready_with_numbers · get_ready_offer_by_number", COLOR["logic"], "#")
N("i_st",      690, LANE_I_Y+360,  "status_policy",           "should_mark_offer_sent", COLOR["logic"], "Δst")

N("i_et_val",  830, LANE_I_Y,      "validate_email_template", "extract + block unknown tokens", COLOR["logic"], "✓et")
N("i_et_ren",  830, LANE_I_Y+90,   "render_email_template",   "_value_for_variable", COLOR["logic"], "→et")
N("i_pdf",     830, LANE_I_Y+180,  "render_offer_pdf",        "reportlab · _component_lines", COLOR["logic"], "PDF")
N("i_pdfctx",  830, LANE_I_Y+270,  "build_offer_pdf_context", "_client_display · _display_date", COLOR["logic"], "PDF·")
N("i_gm_msg",  830, LANE_I_Y+360,  "build_offer_email_message", "MIME · subject · body · attachment", COLOR["logic"], "MIME")

# Telegram offer command flow (in handle_text via intent flow)
N("i_tg_list",  970, LANE_I_Y,     "Telegram \"jakie mam oferty?\"", "lists numbered ready offers", COLOR["telegram"], "TG")
N("i_tg_send",  970, LANE_I_Y+90,  "Telegram \"wyślij ofertę...\"",   "instant send command", COLOR["telegram"], "TG")
N("i_tg_resc",  970, LANE_I_Y+180, "R4 for offer target",     "single client resolved", COLOR["switch"], "🔍")
N("i_tg_card",  970, LANE_I_Y+270, "Offer card",              "[✅ Wysłać] [❌ Anulować] · idempotent", COLOR["card"], "✅✈", text_fill="#0e2c1f")

# Pipeline
N("i_pipe",   1130, LANE_I_Y,      "send_offer_after_confirmation", "shared/offers/pipeline.py · idempotent key", COLOR["service"], "⚙", w=110)
N("i_idem",   1130, LANE_I_Y+90,   "idempotency log",         "Supabase offer_send_attempts", COLOR["state"], "1×")
N("i_recip",  1130, LANE_I_Y+180,  "merge_offer_recipients",  "shared/offers/email_utils.py", COLOR["logic"], "to:")

# Gmail + Sheets follow-up
N("i_gm_send",1290, LANE_I_Y,      "Gmail send_offer_email",  "OAuth-as-user · raw MIME", COLOR["gmail"], "Gmail", text_fill="#fff", w=110)
N("i_sh_email",1290, LANE_I_Y+90,  "Sheets email column",     "fill if empty", COLOR["sheets"], "Sheets", text_fill="#fff", w=110)
N("i_sh_st",  1290, LANE_I_Y+180,  "Sheets status update",    "should_mark_offer_sent → Oferta wysłana", COLOR["sheets"], "Sheets", text_fill="#fff", w=110)
N("i_supa_t", 1290, LANE_I_Y+270,  "Supabase offer_templates", "system data only", COLOR["supabase"], "Supabase", text_fill="#0e2c1f", w=110)
N("i_supa_p", 1290, LANE_I_Y+360,  "Supabase offer_seller_profiles", "+ offer-logos bucket", COLOR["supabase"], "Supabase", text_fill="#0e2c1f", w=110)

E("i_oferty", "i_ed"); E("i_ed", "i_proxy")
for rid in ["i_r_list","i_r_create","i_r_upd","i_r_del","i_r_pub","i_r_dup","i_r_re","i_r_prof_g","i_r_prof_p","i_r_ev","i_r_logo","i_r_pdf"]:
    E("i_proxy", rid, dashed=True)
    E(rid, "i_repo", dashed=True)
E("i_repo", "i_supa_t", dashed=True); E("i_repo", "i_supa_p", dashed=True)
E("i_r_create", "i_val"); E("i_r_upd", "i_val")
E("i_r_create", "i_pri", dashed=True)
E("i_r_pub", "i_num", dashed=True)
E("i_r_prof_p", "i_et_val")
E("i_r_pdf", "i_pdfctx"); E("i_pdfctx", "i_pdf")
E("i_et_val", "i_et_ren", dashed=True)

E("e_i_addm", "i_tg_send", color=EDGE_OFFER, dashed=True, label="offer_email event type")
E("d_resolve", "i_tg_list", color=EDGE_OFFER, dashed=True, label="\"jakie mam oferty?\"")
E("d_resolve", "i_tg_send", color=EDGE_OFFER, dashed=True, label="instant \"wyślij\"")
E("i_tg_list", "i_num", dashed=True)
E("i_tg_send", "i_tg_resc"); E("i_tg_resc", "i_tg_card")
E("i_tg_card", "i_pipe", color=EDGE_CONFIRM, label="Wysłać")
E("i_pipe", "i_idem", dashed=True)
E("i_pipe", "i_recip", dashed=True)
E("i_pipe", "i_et_ren", dashed=True)
E("i_pipe", "i_pdf", dashed=True)
E("i_pipe", "i_gm_msg", dashed=True)
E("i_gm_msg", "i_gm_send")
E("i_gm_send", "i_sh_email", color=EDGE_CONFIRM, label="only after Gmail OK")
E("i_sh_email", "i_sh_st")
E("i_st", "i_sh_st", dashed=True)


# =============================================================================
# LANE J — API ROUTES + WEBAPP ROUTE TREE + STRIPE  (y=3760-4120)
# =============================================================================
LANE_J_Y = 3790

# FastAPI route bus
N("j_api_bus",  80,  LANE_J_Y, "FastAPI · api/main.py",  "oze-agent backend (Railway)", COLOR["fastapi"], "API", text_fill="#073d2a", w=110, h=70)
N("j_auth",    210,  LANE_J_Y, "api/auth.py",            "get_current_auth_user · JWT", COLOR["service"], "🔑")

api_routes = [
    ("j_r_me",        340, LANE_J_Y-20, "GET /me",                    "account.py"),
    ("j_r_dash",      340, LANE_J_Y+15, "GET /dashboard/crm",         "dashboard.py"),
    ("j_r_dec",       340, LANE_J_Y+50, "GET/POST /decisions/*",      "5 routes · decisions.py"),
    ("j_r_admin",     340, LANE_J_Y+85, "GET /admin/*",               "3 routes · admin.py (owner-only)"),
    ("j_r_billing",   340, LANE_J_Y+120,"POST /stripe-event",         "billing.py · signed webhook"),
    ("j_r_oauth",     340, LANE_J_Y+155,"GET /google/url/{id} · /google/callback", "google_oauth.py"),
    ("j_r_onb",       340, LANE_J_Y+190,"/onboarding/*",              "7 routes · onboarding.py"),
    ("j_r_ins",       340, LANE_J_Y+225,"/insights/*",                "3 routes · insights.py"),
    ("j_r_off",       340, LANE_J_Y+260,"/offers/*",                  "14 routes · offers.py"),
]
for nid, x, y, lbl, sub in api_routes:
    N(nid, x, y, lbl, sub, COLOR["frame"], "", w=380, h=30, kind="frame")
    E("j_api_bus", nid, dashed=True)

# Webapp route tree
N("j_web_bus", 760, LANE_J_Y, "Next.js · web/app", "Vercel · dark app shell", COLOR["vercel"], "Vercel", text_fill="#fff", w=110, h=70)

web_routes_left = [
    ("j_w_dash",   "/dashboard",              "+ /dashboard/decyzje-preview"),
    ("j_w_faq",    "/faq",                    "FAQ"),
    ("j_w_imp",    "/import",                 "CSV/Excel POST-MVP"),
    ("j_w_ins",    "/instrukcja",             "instructions"),
    ("j_w_kal",    "/kalendarz",              "calendar view"),
    ("j_w_kli",    "/klienci",                "client list"),
    ("j_w_of",     "/oferty",                 "offer generator"),
    ("j_w_pl",     "/platnosci",              "Stripe portal"),
    ("j_w_us",     "/ustawienia",             "user settings"),
]
for i, (nid, lbl, sub) in enumerate(web_routes_left):
    N(nid, 890, LANE_J_Y + i*32 - 10, lbl, sub, COLOR["frame"], "", w=290, h=27, kind="frame")
    E("j_web_bus", nid, dashed=True)

web_routes_right = [
    ("j_w_admin",  "/admin/* (9 sub-routes)", "owner admin"),
    ("j_w_auth",   "/auth · /login · /logout · /rejestracja", "auth"),
    ("j_w_firma",  "/firma",                  "company"),
    ("j_w_hz",     "/healthz",                "ops"),
    ("j_w_onb",    "/onboarding/*",           "8 sub-routes"),
    ("j_w_prev",   "/*-preview",              "design previews"),
    ("j_w_pol",    "/polityka-prywatnosci · /regulamin", "legal"),
    ("j_w_apionb", "/api/onboarding/telegram-status", "internal"),
    ("j_w_apistr", "/api/webhooks/stripe",   "Stripe webhook ingress"),
]
for i, (nid, lbl, sub) in enumerate(web_routes_right):
    N(nid, 1200, LANE_J_Y + i*32 - 10, lbl, sub, COLOR["frame"], "", w=320, h=27, kind="frame")
    E("j_web_bus", nid, dashed=True)

# Stripe edges
N("j_stripe", 1560, LANE_J_Y, "Stripe", "live billing", COLOR["stripe"], "Stripe", text_fill="#fff", w=100, h=70)
N("j_stripe_sig", 1560, LANE_J_Y+90, "_verify_internal_signature", "billing service → oze-agent api", COLOR["service"], "sig")
N("j_stripe_act", 1560, LANE_J_Y+180, "_activate_from_checkout_session", "user.subscription_active=true", COLOR["state"], "✓sub")

E("j_w_apistr", "j_stripe", color=EDGE_OFFER, dashed=True)
E("j_stripe", "j_r_billing", color=EDGE_OFFER, label="event")
E("j_r_billing", "j_stripe_sig", dashed=True)
E("j_stripe_sig", "j_stripe_act", dashed=True)
E("j_stripe_act", "a_g_sub", color=EDGE_CONFIRM, dashed=True, label="updates subscription state")

# Bot health ping
E("d_text", "j_api_bus", dashed=True, label="(legacy: api also serves bot)")

# =============================================================================
# LANE K — EXTERNALS  (y=4180-4350)
# =============================================================================
LANE_K_Y = 4220

externals = [
    ("k_sheets",   80,   "Google Sheets",   "CRM source of truth", COLOR["sheets"],   "Sheets", "#fff"),
    ("k_calendar", 220,  "Google Calendar", "events (action layer)", COLOR["calendar"], "Cal", "#fff"),
    ("k_drive",    360,  "Google Drive",    "client photo folders", COLOR["drive"],    "Drive", "#1a1a2e"),
    ("k_gmail",    500,  "Gmail",            "offer delivery", COLOR["gmail"],   "Gmail", "#fff"),
    ("k_anth",     640,  "Anthropic",        "Claude Haiku · Sonnet", COLOR["claude"],  "Claude", "#1a1a2e"),
    ("k_openai",   780,  "OpenAI",           "Whisper STT", COLOR["openai"], "OpenAI", "#fff"),
    ("k_supabase", 920,  "Supabase",         "system data · pgvector", COLOR["supabase"], "Supabase", "#0e2c1f"),
    ("k_stripe",  1060,  "Stripe",          "live subscription billing", COLOR["stripe"], "Stripe", "#fff"),
    ("k_tg",      1200,  "Telegram BotAPI", "prod bot + bot-test", COLOR["telegram"], "TG", "#fff"),
    ("k_railway",1340,   "Railway",         "bot · bot-test · api", COLOR["service"], "Railway", "#fff"),
    ("k_vercel", 1480,   "Vercel",          "web · proxy", COLOR["vercel"], "Vercel", "#fff"),
    ("k_gcal_ext",1620,  "Google OAuth",    "Sheets·Calendar·Drive·Gmail scopes", COLOR["calendar"], "OAuth", "#fff"),
]
for nid, x, lbl, sub, col, t, tf in externals:
    N(nid, x, LANE_K_Y, lbl, sub, col, t, text_fill=tf, w=120, h=70)


# =============================================================================
# SVG RENDERING
# =============================================================================

def cubic(x1, y1, x2, y2):
    # n8n-like horizontal bezier
    dx = max(40, (x2 - x1) * 0.4)
    return f"M {x1},{y1} C {x1+dx},{y1} {x2-dx},{y2} {x2},{y2}"


def side_anchor(n: Node, side: str):
    cx = n.x + n.w / 2
    cy = n.y + n.h / 2
    if side == "right":
        return n.x + n.w, cy
    if side == "left":
        return n.x, cy
    if side == "top":
        return cx, n.y
    if side == "bottom":
        return cx, n.y + n.h
    return cx, cy


def node_map():
    return {n.nid: n for n in NODES}


def esc(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;"))


def render_svg() -> str:
    nm = node_map()
    out = []
    out.append(f'<?xml version="1.0" encoding="UTF-8"?>')
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_W} {CANVAS_H}" font-family="Inter, \'Segoe UI\', sans-serif">')
    out.append("<defs>")
    out.append('<pattern id="dot-grid" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="1.4" cy="1.4" r="1.4" fill="' + GRID_DOT + '"/></pattern>')
    out.append('<filter id="ns" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur in="SourceAlpha" stdDeviation="2"/><feOffset dx="0" dy="2" result="o"/><feComponentTransfer><feFuncA type="linear" slope="0.4"/></feComponentTransfer><feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    for name, col in (("arrow", EDGE_DEFAULT), ("arrow-c", EDGE_CONFIRM), ("arrow-x", EDGE_CANCEL), ("arrow-a", EDGE_AI), ("arrow-o", EDGE_OFFER)):
        out.append(f'<marker id="{name}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{col}"/></marker>')
    out.append("</defs>")
    # canvas
    out.append(f'<rect width="{CANVAS_W}" height="{CANVAS_H}" fill="{CANVAS_BG}"/>')
    out.append(f'<rect width="{CANVAS_W}" height="{CANVAS_H}" fill="url(#dot-grid)"/>')

    # title bar
    out.append(f'<rect x="0" y="0" width="{CANVAS_W}" height="72" fill="{TITLE_BG}"/>')
    out.append('<text x="32" y="44" fill="#ffffff" font-size="24" font-weight="800">OZE-Agent · workflow (n8n style, 100% unsimplified)</text>')
    out.append('<text x="500" y="44" fill="#8b94b8" font-size="13">every node maps to a real file / function · sourced from bot/, shared/, api/, web/ on 20.05.2026</text>')
    out.append(f'<text x="{CANVAS_W-32}" y="44" fill="#8b94b8" font-size="13" text-anchor="end">~{len(NODES)} nodes · ~{len(EDGES)} edges · branch claude/agent-workflow-diagram-WM0b0</text>')

    # lane backgrounds + labels
    lanes = [
        ("LANE A · INGRESS · Telegram trigger + commands + per-message gates", 100, 470),
        ("LANE B · VOICE PIPELINE · handle_voice → Whisper → Polish post-pass → R1 voice card → text override", 520, 220),
        ("LANE C · PHOTO PIPELINE · handle_photo → resolve client → R1 Drive card → upload → Sheets N/O", 760, 330),
        ("LANE D · TEXT INTAKE + INTENT ROUTER · regex preflights → Haiku tool-use → 9 tools → scope+banner → entity extraction", 1110, 410),
        ("LANE E · INTENT SWITCH + R4 + DISAMBIG · 11 IntentTypes → R4 search → multi-match / duplicate / R6 fallback → behavior helpers", 1540, 410),
        ("LANE F · PENDING STATE MACHINE + CARD BUILDERS + CALLBACK DISPATCH · 10 PendingFlowTypes · 4 card builders · handle_button", 1970, 450),
        ("LANE G · MUTATION COMMIT PIPELINES · 5 commits · Sheets+Calendar dual-write · post-commit next_action_prompt / active client", 2430, 480),
        ("LANE H · BACKGROUND JOBS · 3 daily cron jobs (07:00 morning brief · 03:00 admin mirror · 02:15 user profile agent)", 2920, 380),
        ("LANE I · OFFER GENERATOR FULL SLICE · web /oferty → 14 FastAPI routes → shared/offers/* → Telegram send → Gmail → Sheets follow-up", 3310, 460),
        ("LANE J · FastAPI ROUTES · WEBAPP ROUTE TREE · STRIPE BILLING (Vercel webhook → api signed event → user.subscription_active)", 3780, 380),
        ("LANE K · EXTERNAL SERVICES (brand bar — runtime dependencies)", 4180, 170),
    ]
    for label, top, height in lanes:
        out.append(f'<rect x="20" y="{top}" width="{CANVAS_W-40}" height="{height}" rx="14" fill="{LANE_BG}" stroke="{LANE_STROKE}" stroke-width="1" opacity="0.55"/>')
        out.append(f'<text x="40" y="{top+22}" fill="#9aa3c7" font-size="12" font-weight="700" letter-spacing="1">{esc(label)}</text>')

    # edges
    for ed in EDGES:
        if ed.src not in nm or ed.dst not in nm:
            continue
        a = nm[ed.src]
        b = nm[ed.dst]
        # auto-pick sides based on rough position
        side_src = ed.side_src
        side_dst = ed.side_dst
        if abs(a.y - b.y) > 150 and abs(a.x - b.x) < 200:
            # vertical-ish
            side_src = "bottom" if b.y > a.y else "top"
            side_dst = "top" if b.y > a.y else "bottom"
        x1, y1 = side_anchor(a, side_src)
        x2, y2 = side_anchor(b, side_dst)
        # bezier control points
        if side_src in ("right","left") and side_dst in ("right","left"):
            d = cubic(x1, y1, x2, y2)
        else:
            dy = max(30, abs(y2 - y1) * 0.4)
            cy1 = y1 + dy if side_src == "bottom" else (y1 - dy if side_src == "top" else y1)
            cy2 = y2 - dy if side_dst == "top" else (y2 + dy if side_dst == "bottom" else y2)
            d = f"M {x1},{y1} C {x1},{cy1} {x2},{cy2} {x2},{y2}"
        marker_id = {
            EDGE_CONFIRM: "arrow-c",
            EDGE_CANCEL: "arrow-x",
            EDGE_AI:     "arrow-a",
            EDGE_OFFER:  "arrow-o",
        }.get(ed.color, "arrow")
        dasharray = ' stroke-dasharray="4 4"' if ed.dashed else ""
        out.append(f'<path d="{d}" fill="none" stroke="{ed.color}" stroke-width="1.6" marker-end="url(#{marker_id})"{dasharray}/>')
        if ed.label:
            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2 - 4
            out.append(f'<text x="{mx}" y="{my}" fill="#9aa3c7" font-size="10" text-anchor="middle">{esc(ed.label)}</text>')

    # nodes
    for n in NODES:
        if n.kind == "frame":
            out.append(f'<rect x="{n.x}" y="{n.y}" width="{n.w}" height="{n.h}" rx="6" fill="{COLOR["frame"]}" stroke="{n.color}" stroke-width="1.4"/>')
            out.append(f'<text x="{n.x + 8}" y="{n.y + n.h/2 + 3}" fill="#dde4ff" font-size="11" font-weight="600">{esc(n.label)}</text>')
            if n.sub:
                out.append(f'<text x="{n.x + n.w - 8}" y="{n.y + n.h/2 + 3}" fill="#8b94b8" font-size="10" text-anchor="end">{esc(n.sub)}</text>')
            continue
        out.append(f'<g filter="url(#ns)">')
        out.append(f'<rect x="{n.x}" y="{n.y}" width="{n.w}" height="{n.h}" rx="12" fill="{n.color}"/>')
        if n.text:
            out.append(f'<text x="{n.x + n.w/2}" y="{n.y + n.h/2 + 6}" text-anchor="middle" font-size="18" font-weight="700" fill="{n.text_fill}">{esc(n.text)}</text>')
        out.append('</g>')
        # labels below
        out.append(f'<text x="{n.x + n.w/2}" y="{n.y + n.h + 14}" text-anchor="middle" fill="{TEXT_FG}" font-size="11" font-weight="600">{esc(n.label)}</text>')
        if n.sub:
            out.append(f'<text x="{n.x + n.w/2}" y="{n.y + n.h + 28}" text-anchor="middle" fill="{TEXT_MUTED}" font-size="10">{esc(n.sub)}</text>')

    # legend box (bottom-left)
    lx = 20; ly = CANVAS_H - 160
    out.append(f'<rect x="{lx}" y="{ly}" width="900" height="140" rx="12" fill="#1f1f33" stroke="#2a2a40"/>')
    out.append(f'<text x="{lx+16}" y="{ly+26}" fill="#e3e8ff" font-size="13" font-weight="800" letter-spacing="1">LEGEND</text>')
    legend_rows = [
        [(COLOR["telegram"],"Telegram"), (COLOR["switch"],"Switch/decision"), (COLOR["card"],"Confirm card (R1)"), (COLOR["claude"],"Claude AI"), (COLOR["openai"],"OpenAI")],
        [(COLOR["logic"],"Deterministic logic"), (COLOR["state"],"State / Supabase"), (COLOR["sheets"],"Google Sheets"), (COLOR["calendar"],"Google Calendar"), (COLOR["drive"],"Google Drive")],
        [(COLOR["gmail"],"Gmail"), (COLOR["trigger"],"Cron/trigger"), (COLOR["cancel"],"Cancel/error"), (COLOR["service"],"Helper/service"), (COLOR["fastapi"],"FastAPI route")],
        [(COLOR["web"],"Next.js page"), (COLOR["vercel"],"Vercel"), (COLOR["stripe"],"Stripe"), ("__edge", "→ data flow"), ("__edge_dash","⤍ side effect / persist")],
    ]
    for ri, row in enumerate(legend_rows):
        y = ly + 46 + ri*22
        x = lx + 16
        for item in row:
            col, txt = item
            if col == "__edge":
                out.append(f'<line x1="{x}" y1="{y-4}" x2="{x+24}" y2="{y-4}" stroke="{EDGE_DEFAULT}" stroke-width="2" marker-end="url(#arrow)"/>')
                out.append(f'<text x="{x+30}" y="{y}" fill="#cdd3ee" font-size="11">{txt}</text>')
            elif col == "__edge_dash":
                out.append(f'<line x1="{x}" y1="{y-4}" x2="{x+24}" y2="{y-4}" stroke="{EDGE_DEFAULT}" stroke-width="2" stroke-dasharray="4 4" marker-end="url(#arrow)"/>')
                out.append(f'<text x="{x+30}" y="{y}" fill="#cdd3ee" font-size="11">{txt}</text>')
            else:
                out.append(f'<rect x="{x}" y="{y-12}" width="14" height="14" rx="3" fill="{col}"/>')
                out.append(f'<text x="{x+20}" y="{y}" fill="#cdd3ee" font-size="11">{esc(txt)}</text>')
            x += 180

    # R1 banner (bottom-right)
    bx = CANVAS_W - 720; by = CANVAS_H - 160
    out.append(f'<rect x="{bx}" y="{by}" width="700" height="140" rx="12" fill="#0f2a1d" stroke="#3ecf8e"/>')
    out.append(f'<text x="{bx+20}" y="{by+30}" fill="#3ecf8e" font-size="15" font-weight="800" letter-spacing="1">R1 INVARIANT · NO WRITE WITHOUT CONFIRMATION</text>')
    lines = [
        "Every mutation card uses [✅ Zapisać] [➕ Dopisać] [❌ Anulować] — one-click ❌ Anulować, no \"na pewno?\" loop.",
        "Voice transcription uses a separate 2-button [✅ Zapisz] [❌ Anuluj] card before joining the text path.",
        "Offer send uses [✅ Wysłać] [❌ Anulować] · Gmail-first · Sheets writes only after Gmail success.",
        "Duplicate resolution ([Nowy]/[Aktualizuj]) is a routing decision — not a mutation confirmation.",
        "Multi-match disambiguation ([1] [2] [3]) is a routing decision — not a mutation confirmation.",
    ]
    for i, line in enumerate(lines):
        out.append(f'<text x="{bx+20}" y="{by+56 + i*18}" fill="#cdd3ee" font-size="11">{esc(line)}</text>')

    out.append("</svg>")
    return "\n".join(out)


def main():
    svg = render_svg()
    out_svg = "deliverables/diagrams/oze_agent_n8n_workflow_full.svg"
    with open(out_svg, "w") as f:
        f.write(svg)
    print(f"wrote {out_svg} · {len(svg)//1024} KB")
    # PNG
    try:
        import cairosvg  # noqa
        out_png = "deliverables/diagrams/oze_agent_n8n_workflow_full.png"
        cairosvg.svg2png(url=out_svg, write_to=out_png, output_width=CANVAS_W)
        import os
        print(f"wrote {out_png} · {os.path.getsize(out_png)//1024} KB")
    except ImportError:
        print("(cairosvg not available; PNG skipped)")

if __name__ == "__main__":
    main()
