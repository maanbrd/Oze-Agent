from pathlib import Path

from scripts.content_factory.generate_carousel import (
    BRAND_ICON_PATH,
    BRAND_LOGO_PATH,
    BRAND_ASSET_OUTPUT_FILES,
    copy_brand_assets,
)


def test_content_factory_uses_canonical_brand_assets():
    repo_root = Path(__file__).resolve().parents[2]

    assert BRAND_ICON_PATH == repo_root / "assets" / "brand" / "agent-oze-icon.png"
    assert BRAND_LOGO_PATH == repo_root / "assets" / "brand" / "agent-oze-logo.png"
    assert BRAND_ICON_PATH.exists()
    assert BRAND_LOGO_PATH.exists()


def test_copy_brand_assets_adds_icon_and_logo_to_campaign_output(tmp_path):
    copied = copy_brand_assets(tmp_path)

    icon_output = tmp_path / BRAND_ASSET_OUTPUT_FILES[BRAND_ICON_PATH]
    logo_output = tmp_path / BRAND_ASSET_OUTPUT_FILES[BRAND_LOGO_PATH]

    assert icon_output.exists()
    assert logo_output.exists()
    assert copied["agent-oze-icon.png"] == str(icon_output)
    assert copied["agent-oze-logo.png"] == str(logo_output)
    assert icon_output.read_bytes() == BRAND_ICON_PATH.read_bytes()
    assert logo_output.read_bytes() == BRAND_LOGO_PATH.read_bytes()
