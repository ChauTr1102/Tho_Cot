"""The defaults in config.py encode measured API behaviour, several of which
contradict the official BytePlus guide. These tests pin the ones where a wrong
value fails silently or ships a visible defect."""
from app.services.studio.config import StudioSettings


def test_defaults_match_measured_api_behaviour():
    s = StudioSettings(ARK_API_KEY="test-key")
    assert s.SEEDREAM_MODEL == "dola-seedream-5-0-pro-260628"
    assert s.SEEDANCE_MODEL == "dreamina-seedance-2-5-260628"
    assert s.VISION_MODEL == "dola-seed-2-1-turbo-260628"
    # watermark must default off: true stamps "AI generated" onto the image
    assert s.IMAGE_WATERMARK is False
    # vision tiles must be native resolution: downscaling hides text defects
    assert s.QA_TILE_PX == 1024
    # a 30s poll timeout produced "Read timed out" during research
    assert s.POLL_TIMEOUT_SEC >= 90


def test_seedance_is_never_asked_to_render_vietnamese():
    """It renders "Da khô căng, xỉn màu?" as "Da khò cáng, xỉn mau?"."""
    s = StudioSettings(ARK_API_KEY="test-key")
    assert s.VIDEO_SUBTITLES_FROM_SEEDANCE is False
    assert s.VIDEO_GENERATE_AUDIO is False


def test_reference_floor_matches_the_api_rejection():
    """Seedance: "expected the width to be at least 300px"."""
    assert StudioSettings(ARK_API_KEY="k").REF_MIN_PX == 300


def test_shopee_floor_keeps_the_flagship_photos_eligible():
    """COSRX product photos are 800x1067; a 1000px floor would exclude them."""
    assert StudioSettings(ARK_API_KEY="k").SHOPEE_MIN_PX <= 800


def test_env_overrides_are_honoured(monkeypatch):
    monkeypatch.setenv("STUDIO_IMAGE_CONCURRENCY", "3")
    assert StudioSettings(ARK_API_KEY="test-key").IMAGE_CONCURRENCY == 3
