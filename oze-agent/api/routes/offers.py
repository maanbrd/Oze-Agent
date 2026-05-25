"""Offer generator API routes.

Routes resolve the internal user id from the authenticated Supabase JWT.
"""

import base64
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from api.auth import AuthUser, get_current_auth_user
from shared.database import get_supabase_client
from shared.offers.email_template import EMAIL_VARIABLES, validate_email_template
from shared.offers.email_utils import sanitize_filename_part
from shared.offers.pdf import TEST_CLIENT, render_offer_pdf
from shared.offers.repository import OfferRepository
from shared.offers.validation import has_pdf_minimum, validate_offer_template

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_LOGO_TYPES = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
}
MAX_LOGO_BYTES = 2 * 1024 * 1024


class TemplatePayload(BaseModel):
    data: dict = Field(default_factory=dict)


class ProfilePayload(BaseModel):
    data: dict = Field(default_factory=dict)


class ReorderPayload(BaseModel):
    ordered_template_ids: list[str]


def _user_id(auth_user: AuthUser = Depends(get_current_auth_user)) -> str:
    result = (
        get_supabase_client()
        .table("users")
        .select("id, auth_user_id")
        .eq("auth_user_id", auth_user.user_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Profil użytkownika nie istnieje.")
    return result.data[0]["id"]


def _repo() -> OfferRepository:
    return OfferRepository()


def _logo_mime_type(path: str | None) -> str:
    ext = (path or "").rsplit(".", 1)[-1].lower()
    if ext in {"jpg", "jpeg"}:
        return "image/jpeg"
    if ext == "webp":
        return "image/webp"
    return "image/png"


def _profile_response(profile: dict | None) -> dict:
    clean = {k: v for k, v in (profile or {}).items() if k != "logo_bytes"}
    logo_bytes = (profile or {}).get("logo_bytes")
    if logo_bytes and len(logo_bytes) <= MAX_LOGO_BYTES:
        encoded = base64.b64encode(logo_bytes).decode("ascii")
        clean["logo_data_url"] = f"data:{_logo_mime_type(clean.get('logo_path'))};base64,{encoded}"
    return clean


def _logo_extension_from_magic(content: bytes) -> str | None:
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if content.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "webp"
    return None


def _validate_profile_payload(data: dict) -> None:
    if "email_body_template" not in data:
        return
    validation = validate_email_template(str(data.get("email_body_template") or ""))
    if not validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail={"errors": [f"Nieznana zmienna emaila: {name}" for name in validation.unknown_variables]},
        )


@router.get("/templates")
async def list_templates(uid: str = Depends(_user_id)):
    repo = _repo()
    return {"templates": repo.list_templates(uid)}


@router.post("/templates")
async def create_template(payload: TemplatePayload, uid: str = Depends(_user_id)):
    repo = _repo()
    created = repo.create_template(uid, payload.data)
    if not created:
        raise HTTPException(status_code=500, detail="Nie udało się utworzyć szkicu.")
    return {"template": created}


@router.patch("/templates/{template_id}")
async def update_template(template_id: UUID, payload: TemplatePayload, uid: str = Depends(_user_id)):
    repo = _repo()
    template_id_str = str(template_id)
    current = repo.get_template(uid, template_id_str)
    if not current:
        raise HTTPException(status_code=404, detail="Oferta nie istnieje.")
    merged = {**current, **payload.data}
    if current.get("status") == "ready":
        validation = validate_offer_template(merged)
        if not validation.is_valid:
            raise HTTPException(status_code=400, detail={"errors": validation.errors})
    updated = repo.update_template(uid, template_id_str, payload.data)
    return {"template": updated}


@router.delete("/templates/{template_id}")
async def delete_template(template_id: UUID, uid: str = Depends(_user_id)):
    repo = _repo()
    repo.delete_template(uid, str(template_id))
    return {"ok": True}


@router.post("/templates/{template_id}/publish")
async def publish_template(template_id: UUID, uid: str = Depends(_user_id)):
    repo = _repo()
    template_id_str = str(template_id)
    current = repo.get_template(uid, template_id_str)
    if not current:
        raise HTTPException(status_code=404, detail="Oferta nie istnieje.")
    validation = validate_offer_template(current)
    if not validation.is_valid:
        raise HTTPException(status_code=400, detail={"errors": validation.errors})
    published = repo.publish_template(uid, template_id_str)
    return {"template": published}


@router.post("/templates/{template_id}/duplicate")
async def duplicate_template(template_id: UUID, uid: str = Depends(_user_id)):
    repo = _repo()
    duplicated = repo.duplicate_as_draft(uid, str(template_id))
    if not duplicated:
        raise HTTPException(status_code=404, detail="Oferta nie istnieje.")
    return {"template": duplicated}


@router.post("/templates/reorder")
async def reorder_templates(payload: ReorderPayload, uid: str = Depends(_user_id)):
    repo = _repo()
    return {"templates": repo.reorder_ready(uid, payload.ordered_template_ids)}


@router.get("/profile")
async def get_profile(uid: str = Depends(_user_id)):
    repo = _repo()
    return {"profile": _profile_response(repo.get_seller_profile(uid))}


@router.put("/profile")
async def upsert_profile(payload: ProfilePayload, uid: str = Depends(_user_id)):
    _validate_profile_payload(payload.data)
    repo = _repo()
    profile = repo.upsert_seller_profile(uid, payload.data)
    return {"profile": _profile_response(profile)}


@router.get("/email-variables")
async def email_variables(_auth_user: AuthUser = Depends(get_current_auth_user)):
    return {"variables": EMAIL_VARIABLES}


@router.post("/profile/logo")
async def upload_logo(file: UploadFile = File(...), uid: str = Depends(_user_id)):
    repo = _repo()
    content_type = file.content_type or ""
    if content_type not in ALLOWED_LOGO_TYPES:
        raise HTTPException(status_code=400, detail="Logo musi być plikiem PNG, JPG albo WebP.")
    content = await file.read()
    if len(content) > MAX_LOGO_BYTES:
        raise HTTPException(status_code=400, detail="Logo może mieć maksymalnie 2 MB.")
    magic_ext = _logo_extension_from_magic(content)
    if magic_ext is None:
        raise HTTPException(status_code=400, detail="Logo ma nieprawidłową zawartość pliku.")
    if magic_ext != ALLOWED_LOGO_TYPES[content_type]:
        raise HTTPException(status_code=400, detail="Typ logo nie zgadza się z zawartością pliku.")
    path = repo.upload_logo(uid, f"logo.{magic_ext}", content, content_type)
    profile = repo.upsert_seller_profile(uid, {"logo_path": path})
    return {"logo_path": path, "profile": _profile_response(repo.get_seller_profile(uid) if profile else profile)}


@router.get("/templates/{template_id}/test-pdf")
async def test_pdf(template_id: UUID, uid: str = Depends(_user_id)):
    repo = _repo()
    template = repo.get_template(uid, str(template_id))
    if not template:
        raise HTTPException(status_code=404, detail="Oferta nie istnieje.")
    if not has_pdf_minimum(template):
        raise HTTPException(status_code=400, detail="Brakuje minimum danych do PDF.")
    profile = repo.get_seller_profile(uid)
    pdf = render_offer_pdf(template, profile, TEST_CLIENT)
    filename = sanitize_filename_part(template.get("name") or "oferta-test")
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Oferta-test-{filename}.pdf"'},
    )
