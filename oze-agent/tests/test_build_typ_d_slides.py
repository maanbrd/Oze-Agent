import json

from PIL import Image

from scripts.content_factory import build_typ_d_slides


def test_build_uses_pil_fallback_when_capture_assets_are_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(build_typ_d_slides, "SHOTS", tmp_path / "missing-shots")
    monkeypatch.setattr(build_typ_d_slides, "PUP_RUNNER", tmp_path / "missing-pup-runner")
    monkeypatch.setattr(
        build_typ_d_slides,
        "PUP_CAPTURE_SCRIPT",
        tmp_path / "missing-pup-runner" / "capture_mobile_cards.mjs",
    )
    monkeypatch.setattr(build_typ_d_slides, "AUDIO", tmp_path / "missing-audio.mp3")

    out_dir = build_typ_d_slides.build("01", tmp_path / "output")

    assert (out_dir / "slide_01.png").exists()
    assert (out_dir / "raw_source.png").exists()
    assert (out_dir / "brand_agent_oze_icon.png").exists()
    assert (out_dir / "brand_agent_oze_logo.png").exists()
    assert (out_dir / "meta.json").exists()
    assert (out_dir / "instagram_post.json").exists()

    with Image.open(out_dir / "slide_01.png") as slide:
        assert slide.size == (build_typ_d_slides.FINAL_W, build_typ_d_slides.FINAL_H)

    manifest = json.loads((out_dir / "instagram_post.json").read_text(encoding="utf-8"))
    scenario = build_typ_d_slides.SCENARIOS["01"]

    assert manifest["campaign_id"].endswith("-typ-d-01-glosowka-po-spotkaniu")
    assert manifest["typ"] == "D-AGENT"
    assert manifest["caption_ig"] == scenario["caption"]
    assert manifest["caption_fb"] == scenario["caption"]
    assert manifest["hashtags"] == scenario["hashtags"]
