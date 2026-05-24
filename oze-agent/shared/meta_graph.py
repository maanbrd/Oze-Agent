"""Meta Graph API wrapper for Agent-OZE marketing publisher.

Async HTTP client for Instagram Content Publishing API + Facebook Pages API
(Graph API v20.0). Mirrors the ``shared/google_drive.py`` patterns:

- All public methods are async.
- Network / API failures return ``None`` / ``False`` / ``[]`` — never raise.
- Logging via module logger; ``logger.error`` on failures with full Meta
  response body for debuggability.
- Rate-limit handling with exponential backoff (3 retries: 2s, 4s, 8s).

Environment variables (read at ``__init__``):

- ``META_APP_ID``           — Meta App ID (numeric)
- ``META_APP_SECRET``       — Meta App secret (used for long-token exchange)
- ``META_FB_PAGE_ID``       — Facebook Page numeric ID
- ``META_FB_PAGE_TOKEN``    — Page Access Token (long-lived, 60-day)
- ``META_IG_BUSINESS_ID``   — Instagram Business Account ID linked to the Page
- ``META_IG_USER_TOKEN``    — optional user token for IG Content Publishing

Missing any of these raises ``ValueError`` at construction time so the
publisher cron fails loudly instead of silently no-oping.

Usage::

    client = MetaGraphClient()
    ok = await client.verify_token()
    media_id = await client.publish_ig_carousel(
        image_urls=[url1, url2, ...],
        caption="...",
        first_comment="#hashtag1 #hashtag2",
    )
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


# ── Constants ─────────────────────────────────────────────────────────────────

GRAPH_API_VERSION = "v20.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

# Default insight metrics — chosen to match marketing_queue insight columns.
_DEFAULT_IG_METRICS = [
    "saves",
    "shares",
    "comments",
    "reach",
    "impressions",
    "plays",
]
_DEFAULT_FB_METRICS = [
    "post_impressions",
    "post_engaged_users",
    "post_reactions_by_type_total",
]
_DEFAULT_PAGE_METRICS = [
    "page_impressions",
    "page_engagements",
    "page_followers_count",
]

# Media container polling — IG carousel children take ~1-5s to process.
_MEDIA_READY_TIMEOUT_S = 30
_MEDIA_READY_POLL_INTERVAL_S = 2

# HTTP backoff schedule — 2s, 4s, 8s.
_RETRY_ATTEMPTS = 3
_HTTP_TIMEOUT_S = 60.0


# ── Client ────────────────────────────────────────────────────────────────────


class MetaGraphClient:
    """Async wrapper for Meta Graph API publishing + insights.

    Reads credentials from env vars at construction time. Holds a shared
    ``httpx.AsyncClient`` per call site for connection pooling — callers
    typically construct one client per publisher run.
    """

    def __init__(self) -> None:
        self.app_id = os.environ.get("META_APP_ID", "").strip()
        self.app_secret = os.environ.get("META_APP_SECRET", "").strip()
        self.page_id = os.environ.get("META_FB_PAGE_ID", "").strip()
        self.page_token = os.environ.get("META_FB_PAGE_TOKEN", "").strip()
        self.ig_business_id = os.environ.get("META_IG_BUSINESS_ID", "").strip()
        self.ig_user_token = os.environ.get("META_IG_USER_TOKEN", "").strip()

        missing = [
            name
            for name, value in (
                ("META_APP_ID", self.app_id),
                ("META_APP_SECRET", self.app_secret),
                ("META_FB_PAGE_ID", self.page_id),
                ("META_FB_PAGE_TOKEN", self.page_token),
                ("META_IG_BUSINESS_ID", self.ig_business_id),
            )
            if not value
        ]
        if missing:
            raise ValueError(
                f"MetaGraphClient: missing env vars: {', '.join(missing)}"
            )

    # ── Internal HTTP helpers ────────────────────────────────────────────────

    def _is_rate_limited(self, response: httpx.Response) -> bool:
        """Detect Meta rate-limit responses.

        Two signals:
        - HTTP 429
        - ``X-Business-Use-Case-Usage`` or ``X-App-Usage`` header indicating
          high call_count / total_cputime usage; in practice Meta returns 429
          before throttling fully, so HTTP status is the reliable trigger.
        """
        if response.status_code == 429:
            return True
        # Some endpoints throttle via 4xx + error subcode 4/17/32/613.
        if response.status_code in (400, 403):
            try:
                err = response.json().get("error", {})
                code = err.get("code")
                subcode = err.get("error_subcode")
                if code in (4, 17, 32, 613) or subcode in (2446079, 2207051):
                    return True
            except Exception:
                return False
        return False

    async def _backoff_wait(self, attempt: int) -> None:
        """Sleep for an exponential backoff: attempt=0 → 2s, 1 → 4s, 2 → 8s."""
        delay = 2 ** (attempt + 1)
        logger.info("MetaGraphClient: backing off for %ds (attempt %d)", delay, attempt + 1)
        await asyncio.sleep(delay)

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        access_token: Optional[str] = None,
        retry: int = _RETRY_ATTEMPTS,
    ) -> Optional[dict]:
        """Issue a Graph API request, returning the parsed JSON body or None.

        - Authorization handled by Bearer token in the header.
        - POST bodies sent as form-encoded (Meta accepts both JSON and form,
          form is the documented default for Graph API).
        - On 401 → logs + returns None (token expired/invalid).
        - On rate-limit → exponential backoff up to ``retry`` attempts.
        - On 4xx (non-rate-limit) → logs full response + returns None.
        - On network error → logs + returns None.
        """
        url = endpoint if endpoint.startswith("http") else f"{GRAPH_API_BASE}/{endpoint.lstrip('/')}"
        token = access_token or self.page_token
        headers = {"Authorization": f"Bearer {token}"}

        for attempt in range(retry + 1):
            try:
                async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT_S) as http:
                    response = await http.request(
                        method,
                        url,
                        params=params,
                        data=data,
                        headers=headers,
                    )
            except httpx.HTTPError as e:
                logger.error(
                    "MetaGraphClient._request(%s %s): network error: %s",
                    method,
                    url,
                    e,
                )
                if attempt < retry:
                    await self._backoff_wait(attempt)
                    continue
                return None

            if response.status_code == 401:
                logger.error(
                    "MetaGraphClient._request(%s %s): 401 unauthorized — page token "
                    "expired or revoked. Body: %s",
                    method,
                    url,
                    response.text,
                )
                return None

            if self._is_rate_limited(response):
                logger.warning(
                    "MetaGraphClient._request(%s %s): rate-limited (status=%d, "
                    "attempt %d/%d). Body: %s",
                    method,
                    url,
                    response.status_code,
                    attempt + 1,
                    retry + 1,
                    response.text[:500],
                )
                if attempt < retry:
                    await self._backoff_wait(attempt)
                    continue
                return None

            if response.status_code >= 400:
                logger.error(
                    "MetaGraphClient._request(%s %s): HTTP %d. Body: %s",
                    method,
                    url,
                    response.status_code,
                    response.text,
                )
                return None

            try:
                return response.json()
            except ValueError as e:
                logger.error(
                    "MetaGraphClient._request(%s %s): JSON decode failed: %s. "
                    "Body: %s",
                    method,
                    url,
                    e,
                    response.text[:500],
                )
                return None

        return None

    async def _wait_for_media_ready(
        self,
        creation_id: str,
        timeout: int = _MEDIA_READY_TIMEOUT_S,
        access_token: Optional[str] = None,
    ) -> bool:
        """Poll a media container until status_code is FINISHED.

        Returns False on EXPIRED / ERROR / IN_PROGRESS-past-timeout.
        Per Meta docs, carousel child containers transition through
        IN_PROGRESS → FINISHED (typical) or ERROR / EXPIRED on failure.
        """
        elapsed = 0
        while elapsed < timeout:
            data = await self._request(
                "GET",
                creation_id,
                params={"fields": "status_code,status"},
                access_token=access_token,
            )
            if data is None:
                logger.error(
                    "MetaGraphClient._wait_for_media_ready(%s): status fetch returned None",
                    creation_id,
                )
                return False
            status_code = data.get("status_code") or data.get("status")
            if status_code == "FINISHED":
                return True
            if status_code in ("ERROR", "EXPIRED"):
                logger.error(
                    "MetaGraphClient._wait_for_media_ready(%s): terminal status %s. Full: %s",
                    creation_id,
                    status_code,
                    data,
                )
                return False
            await asyncio.sleep(_MEDIA_READY_POLL_INTERVAL_S)
            elapsed += _MEDIA_READY_POLL_INTERVAL_S

        logger.error(
            "MetaGraphClient._wait_for_media_ready(%s): timed out after %ds",
            creation_id,
            timeout,
        )
        return False

    # ── Token lifecycle ──────────────────────────────────────────────────────

    async def verify_token(self) -> bool:
        """GET /me with the current page token. Returns True if 200 OK."""
        data = await self._request("GET", "me", params={"fields": "id,name"})
        if data is None:
            return False
        logger.info(
            "MetaGraphClient.verify_token: ok — id=%s name=%s",
            data.get("id"),
            data.get("name"),
        )
        return True

    async def exchange_short_for_long_token(
        self, short_token: str
    ) -> Optional[str]:
        """Exchange a short-lived user/page token for a long-lived (60-day) one.

        Uses the public /oauth/access_token endpoint — does NOT require a
        page token in the Authorization header (uses app id + secret instead).
        Returns the long token string, or None on failure.
        """
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "fb_exchange_token": short_token,
        }
        url = f"{GRAPH_API_BASE}/oauth/access_token"
        try:
            async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT_S) as http:
                response = await http.get(url, params=params)
        except httpx.HTTPError as e:
            logger.error("exchange_short_for_long_token: network error: %s", e)
            return None

        if response.status_code >= 400:
            logger.error(
                "exchange_short_for_long_token: HTTP %d. Body: %s",
                response.status_code,
                response.text,
            )
            return None
        try:
            data = response.json()
        except ValueError as e:
            logger.error("exchange_short_for_long_token: JSON decode failed: %s", e)
            return None
        token = data.get("access_token")
        if not token:
            logger.error(
                "exchange_short_for_long_token: no access_token in response: %s", data
            )
            return None
        return token

    # ── Publishing — Instagram ───────────────────────────────────────────────

    async def publish_ig_carousel(
        self,
        image_urls: list[str],
        caption: str,
        first_comment: str = "",
    ) -> Optional[str]:
        """Publish an Instagram carousel via the Content Publishing API.

        Steps:
        1. For each image URL, create a carousel child container.
        2. Wait until every child reports status_code=FINISHED.
        3. Create the carousel parent container referencing the child IDs.
        4. Wait for the parent to become FINISHED.
        5. POST /media_publish to actually publish.
        6. If ``first_comment`` is set, POST it on the resulting media.

        Returns the IG media_id (= post id) on success, or None on any failure.
        """
        if not image_urls:
            logger.error("publish_ig_carousel: no image_urls supplied")
            return None
        if len(image_urls) < 2 or len(image_urls) > 10:
            logger.error(
                "publish_ig_carousel: IG requires 2..10 children, got %d",
                len(image_urls),
            )
            return None

        ig_token = self.ig_user_token or self.page_token

        # 1. Create child containers.
        child_ids: list[str] = []
        for index, image_url in enumerate(image_urls):
            data = await self._request(
                "POST",
                f"{self.ig_business_id}/media",
                data={
                    "image_url": image_url,
                    "is_carousel_item": "true",
                },
                access_token=ig_token,
            )
            if data is None or "id" not in data:
                logger.error(
                    "publish_ig_carousel: child %d (%s) creation failed",
                    index,
                    image_url,
                )
                return None
            child_ids.append(data["id"])

        # 2. Wait for all children to finish processing.
        for child_id in child_ids:
            if not await self._wait_for_media_ready(child_id, access_token=ig_token):
                logger.error(
                    "publish_ig_carousel: child %s never reached FINISHED", child_id
                )
                return None

        # 3. Create the carousel parent container.
        parent = await self._request(
            "POST",
            f"{self.ig_business_id}/media",
            data={
                "media_type": "CAROUSEL",
                "caption": caption,
                "children": ",".join(child_ids),
            },
            access_token=ig_token,
        )
        if parent is None or "id" not in parent:
            logger.error("publish_ig_carousel: parent container creation failed")
            return None
        parent_id = parent["id"]

        # 4. Wait for parent to finish.
        if not await self._wait_for_media_ready(parent_id, access_token=ig_token):
            logger.error(
                "publish_ig_carousel: parent %s never reached FINISHED", parent_id
            )
            return None

        # 5. Publish.
        published = await self._request(
            "POST",
            f"{self.ig_business_id}/media_publish",
            data={"creation_id": parent_id},
            access_token=ig_token,
        )
        if published is None or "id" not in published:
            logger.error("publish_ig_carousel: media_publish failed")
            return None
        media_id = published["id"]
        logger.info("publish_ig_carousel: published media_id=%s", media_id)

        # 6. First comment (optional).
        if first_comment.strip():
            comment = await self._request(
                "POST",
                f"{media_id}/comments",
                data={"message": first_comment},
                access_token=ig_token,
            )
            if comment is None:
                logger.warning(
                    "publish_ig_carousel: first_comment post failed for media %s "
                    "(post still published)",
                    media_id,
                )

        return media_id

    async def publish_ig_reel(
        self,
        video_url: str,
        caption: str,
        thumbnail_url: Optional[str] = None,
        first_comment: str = "",
    ) -> Optional[str]:
        """Publish an Instagram Reel.

        Single-container flow (no children): create REELS container with
        video_url, poll until FINISHED, then /media_publish. Optional first
        comment afterwards.
        """
        if not video_url:
            logger.error("publish_ig_reel: video_url is required")
            return None

        params: dict[str, Any] = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
        }
        if thumbnail_url:
            params["thumb_offset"] = "0"
            params["cover_url"] = thumbnail_url

        ig_token = self.ig_user_token or self.page_token

        container = await self._request(
            "POST",
            f"{self.ig_business_id}/media",
            data=params,
            access_token=ig_token,
        )
        if container is None or "id" not in container:
            logger.error("publish_ig_reel: container creation failed")
            return None
        container_id = container["id"]

        # Reels can take 30-120s to process — extend timeout.
        if not await self._wait_for_media_ready(
            container_id,
            timeout=180,
            access_token=ig_token,
        ):
            logger.error(
                "publish_ig_reel: container %s never reached FINISHED", container_id
            )
            return None

        published = await self._request(
            "POST",
            f"{self.ig_business_id}/media_publish",
            data={"creation_id": container_id},
            access_token=ig_token,
        )
        if published is None or "id" not in published:
            logger.error("publish_ig_reel: media_publish failed")
            return None
        media_id = published["id"]
        logger.info("publish_ig_reel: published media_id=%s", media_id)

        if first_comment.strip():
            comment = await self._request(
                "POST",
                f"{media_id}/comments",
                data={"message": first_comment},
                access_token=ig_token,
            )
            if comment is None:
                logger.warning(
                    "publish_ig_reel: first_comment post failed for media %s",
                    media_id,
                )

        return media_id

    # ── Publishing — Facebook ────────────────────────────────────────────────

    async def publish_fb_carousel(
        self,
        image_urls: list[str],
        caption: str,
    ) -> Optional[str]:
        """Publish a Facebook Page multi-photo post (carousel-style).

        Steps:
        1. Upload each image unpublished: POST /{PAGE_ID}/photos?published=false&url=...
        2. Compose the feed post: POST /{PAGE_ID}/feed with message + attached_media
        Returns post_id (or None).
        """
        if not image_urls:
            logger.error("publish_fb_carousel: no image_urls supplied")
            return None

        # 1. Upload unpublished photos.
        media_fbids: list[str] = []
        for index, image_url in enumerate(image_urls):
            data = await self._request(
                "POST",
                f"{self.page_id}/photos",
                data={
                    "url": image_url,
                    "published": "false",
                },
            )
            if data is None or "id" not in data:
                logger.error(
                    "publish_fb_carousel: photo %d (%s) upload failed",
                    index,
                    image_url,
                )
                return None
            media_fbids.append(data["id"])

        # 2. Compose feed post with attached_media[N]={"media_fbid": ...}.
        feed_payload: dict[str, str] = {"message": caption}
        for i, fbid in enumerate(media_fbids):
            feed_payload[f"attached_media[{i}]"] = (
                '{"media_fbid":"' + fbid + '"}'
            )

        posted = await self._request(
            "POST",
            f"{self.page_id}/feed",
            data=feed_payload,
        )
        if posted is None or "id" not in posted:
            logger.error("publish_fb_carousel: feed post failed")
            return None
        post_id = posted["id"]
        logger.info("publish_fb_carousel: posted id=%s", post_id)
        return post_id

    async def publish_fb_post(
        self,
        text: str,
        image_urls: Optional[list[str]] = None,
        link: Optional[str] = None,
    ) -> Optional[str]:
        """Publish a Page post.

        - Text-only: POST /{PAGE_ID}/feed?message=...
        - Text + link: POST /{PAGE_ID}/feed?message=...&link=...
        - Text + single image: POST /{PAGE_ID}/photos?url=...&message=...&published=true
        - Text + multi image: delegates to ``publish_fb_carousel``.
        """
        if image_urls and len(image_urls) > 1:
            return await self.publish_fb_carousel(image_urls, text)

        if image_urls and len(image_urls) == 1:
            data = await self._request(
                "POST",
                f"{self.page_id}/photos",
                data={
                    "url": image_urls[0],
                    "message": text,
                    "published": "true",
                },
            )
            if data is None:
                logger.error("publish_fb_post: single-photo post failed")
                return None
            # /photos returns {"id": photo_id, "post_id": "PAGEID_POSTID"}
            return data.get("post_id") or data.get("id")

        payload: dict[str, str] = {"message": text}
        if link:
            payload["link"] = link
        data = await self._request(
            "POST",
            f"{self.page_id}/feed",
            data=payload,
        )
        if data is None or "id" not in data:
            logger.error("publish_fb_post: text/link feed post failed")
            return None
        return data["id"]

    # ── Insights ─────────────────────────────────────────────────────────────

    @staticmethod
    def _flatten_insights(payload: dict) -> dict:
        """Flatten Meta insights ``{data: [{name, values:[{value}]}]}`` → ``{name: value}``."""
        out: dict[str, Any] = {}
        for item in payload.get("data", []) or []:
            name = item.get("name")
            if not name:
                continue
            values = item.get("values") or []
            if values:
                out[name] = values[-1].get("value")
            else:
                # Some endpoints (e.g., /insights for non-time-series metrics)
                # return ``"total_value": {"value": N}``.
                total = item.get("total_value", {})
                if isinstance(total, dict) and "value" in total:
                    out[name] = total["value"]
                else:
                    out[name] = None
        return out

    async def get_ig_post_insights(
        self,
        media_id: str,
        metrics: Optional[list[str]] = None,
    ) -> Optional[dict]:
        """Fetch IG post-level insights. Returns flat {metric: value} dict."""
        metric_list = metrics or _DEFAULT_IG_METRICS
        data = await self._request(
            "GET",
            f"{media_id}/insights",
            params={"metric": ",".join(metric_list)},
        )
        if data is None:
            return None
        return self._flatten_insights(data)

    async def get_fb_post_insights(
        self,
        post_id: str,
        metrics: Optional[list[str]] = None,
    ) -> Optional[dict]:
        """Fetch FB post-level insights. Returns flat {metric: value} dict."""
        metric_list = metrics or _DEFAULT_FB_METRICS
        data = await self._request(
            "GET",
            f"{post_id}/insights",
            params={"metric": ",".join(metric_list)},
        )
        if data is None:
            return None
        return self._flatten_insights(data)

    async def get_page_insights(
        self,
        since: str,
        until: str,
        metrics: Optional[list[str]] = None,
    ) -> Optional[dict]:
        """Fetch Page-level insights between ``since`` and ``until`` (ISO date)."""
        metric_list = metrics or _DEFAULT_PAGE_METRICS
        data = await self._request(
            "GET",
            f"{self.page_id}/insights",
            params={
                "metric": ",".join(metric_list),
                "since": since,
                "until": until,
            },
        )
        if data is None:
            return None
        return self._flatten_insights(data)

    # ── Engagement (Phase 1c — stubs) ────────────────────────────────────────

    async def reply_to_comment(self, comment_id: str, text: str) -> bool:
        """Post a reply to an IG/FB comment. Returns True on success."""
        data = await self._request(
            "POST",
            f"{comment_id}/replies",
            data={"message": text},
        )
        if data is None or "id" not in data:
            logger.error("reply_to_comment(%s): failed", comment_id)
            return False
        return True

    async def get_recent_dms(self, since: str) -> list[dict]:
        """List Page conversations updated since the given timestamp.

        Returns the raw list of conversations from
        ``/{PAGE_ID}/conversations``. Returns [] on failure.
        """
        data = await self._request(
            "GET",
            f"{self.page_id}/conversations",
            params={
                "platform": "instagram",
                "fields": "id,updated_time,participants,messages{message,from,created_time}",
                "since": since,
            },
        )
        if data is None:
            return []
        return data.get("data", []) or []

    async def reply_to_dm(self, conversation_id: str, text: str) -> bool:
        """Send a message into an existing conversation. Returns True on success."""
        data = await self._request(
            "POST",
            f"{conversation_id}/messages",
            data={"message": text},
        )
        if data is None:
            logger.error("reply_to_dm(%s): failed", conversation_id)
            return False
        return True
