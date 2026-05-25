from scripts.marketing.publish_single import _facebook_post_image_urls


def test_facebook_post_image_urls_uses_only_first_image() -> None:
    urls = ["https://example.com/slide_01.png", "https://example.com/slide_02.png"]

    assert _facebook_post_image_urls(urls) == ["https://example.com/slide_01.png"]


def test_facebook_post_image_urls_keeps_empty_list_empty() -> None:
    assert _facebook_post_image_urls([]) == []
