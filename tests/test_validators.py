from utils.validators import parse_instagram_url, parse_media_url


def test_reel_url():
    link = parse_instagram_url("https://www.instagram.com/reel/AbC123_-xy/")
    assert link is not None
    assert link.kind == "reels"
    assert link.shortcode == "AbC123_-xy"
    assert link.url == "https://www.instagram.com/reel/AbC123_-xy/"


def test_post_with_query():
    link = parse_instagram_url("https://instagram.com/p/PostCode99/?igsh=abc")
    assert link is not None
    assert link.kind == "post"
    assert link.shortcode == "PostCode99"


def test_tv_and_mobile():
    link = parse_instagram_url("https://m.instagram.com/tv/TvCode11/")
    assert link is not None
    assert link.kind == "video"


def test_without_scheme():
    link = parse_instagram_url("instagram.com/reels/ReelCode1/")
    assert link is not None
    assert link.kind == "reels"


def test_stories_rejected():
    link = parse_instagram_url("https://www.instagram.com/stories/someone/123/")
    assert link is not None
    assert link.kind == "stories"


def test_profile_unsupported():
    link = parse_instagram_url("https://www.instagram.com/someuser/")
    assert link is not None
    assert link.kind == "unsupported"


def test_foreign_domain():
    assert parse_instagram_url("https://youtube.com/watch?v=abc") is None
    assert parse_instagram_url("https://evil-instagram.com/p/abc/") is None


def test_empty_and_garbage():
    assert parse_instagram_url("") is None
    assert parse_instagram_url("hello") is None
    assert parse_instagram_url("javascript:alert(1)") is None


def test_youtube_watch_and_shorts():
    watch = parse_media_url("https://www.youtube.com/watch?v=dQw4w9wgGcQ")
    assert watch is not None
    assert watch.platform == "youtube"
    assert watch.shortcode == "dQw4w9wgGcQ"
    shorts = parse_media_url("https://youtu.be/dQw4w9wgGcQ")
    assert shorts is not None and shorts.platform == "youtube"


def test_tiktok_and_facebook_and_truth():
    tiktok = parse_media_url("https://www.tiktok.com/@user/video/1234567890123456789")
    assert tiktok is not None and tiktok.platform == "tiktok"
    fb = parse_media_url("https://www.facebook.com/reel/1234567890")
    assert fb is not None and fb.platform == "facebook"
    truth = parse_media_url("https://truthsocial.com/@someone/posts/12345")
    assert truth is not None and truth.platform == "truthsocial"
