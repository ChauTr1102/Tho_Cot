"""The model transcribes; Python judges.

Asked to render a verdict itself, the vision model failed a perfectly correct
image because it counted the product's own bottle label as unexpected text. So
every assertion below exercises the Python judge against a fixed transcript:
`ark.describe_image` is monkeypatched in every test, nothing here touches the
network, and no API key is needed to run the file.

Two kinds of test live here. The first six pin the defects that were actually
observed in generated output on 21/08/2026 — wrong diacritics, an invented
brand name, a redrawn product label, a forbidden claim. The rest pin the ways a
*correct* image can be made to look broken by the gate's own machinery, because
a false failure costs a 50-second regeneration and is the failure mode that
quietly eats a demo.
"""
import io
import json
import threading
import unicodedata

import pytest
from PIL import Image, ImageDraw

from app.services.studio import qa_visual


# --------------------------------------------------------------------------
# fixtures
#
# Defined here rather than in a conftest: this module is the only consumer, and
# other agents own the shared fixture file.
# --------------------------------------------------------------------------

def _write_jpeg(path, size, text=None):
    """A real JPEG on disk. Pillow must be able to open and crop it for real —
    the tiling assertions are meaningless against a stub."""
    image = Image.new("RGB", size, (245, 245, 245))
    if text:
        ImageDraw.Draw(image).text((size[0] // 4, size[1] // 2), text, fill=(0, 0, 0))
    image.save(path, format="JPEG", quality=92)
    return str(path)


@pytest.fixture
def jpeg_2048(tmp_path):
    """The canonical studio image: 2048x2048, exactly four native 1024 tiles."""
    return _write_jpeg(tmp_path / "asset_2048.jpg", (2048, 2048), "SAMPLE")


@pytest.fixture
def jpeg_portrait(tmp_path):
    """A 9:16 keyframe at IMAGE_SIZE_PORTRAIT. Not a multiple of the tile size,
    which is the ordinary case for TikTok covers."""
    return _write_jpeg(tmp_path / "asset_portrait.jpg", (1440, 2560))


@pytest.fixture
def jpeg_small(tmp_path):
    """A reused brand photo smaller than one tile — must be padded, not scaled."""
    return _write_jpeg(tmp_path / "photo_small.jpg", (800, 1067))


def _fake_transcript(strings):
    """Stand in for `ark.describe_image`, returning a fixed JSON transcript."""
    return lambda image_bytes, prompt, max_tokens=600: json.dumps(strings)


def _tiled_transcript(per_tile):
    """A transcript that differs per tile, handed out in tile order.

    Used to reproduce a string sheared in half by a tile boundary, which is the
    gate's own worst enemy: it turns correct work into apparent missing text.
    """
    calls = {"n": 0}

    def describe(image_bytes, prompt, max_tokens=600):
        index = calls["n"]
        calls["n"] += 1
        return json.dumps(per_tile[index] if index < len(per_tile) else [])

    return describe


# --------------------------------------------------------------------------
# the four observed defects
# --------------------------------------------------------------------------

def test_exact_match_passes(monkeypatch, tmp_path, jpeg_2048):
    monkeypatch.setattr(qa_visual.ark, "describe_image",
                        _fake_transcript(["PHỤC HỒI HÀNG RÀO DA", "COSRX", "100ml"]))
    v = qa_visual.inspect_image(jpeg_2048, expected_texts=["PHỤC HỒI HÀNG RÀO DA"],
                                label_text=["COSRX", "100ml"], forbidden_claims=[])
    assert v.passed and not v.missing_text


def test_wrong_diacritic_is_reported_missing(monkeypatch, jpeg_2048):
    """Seedream renders Vietnamese correctly when the string is named in the
    prompt, so this is a regression check — but an unaccented rendering is a
    different string and must never be accepted as the one that was asked for."""
    monkeypatch.setattr(qa_visual.ark, "describe_image",
                        _fake_transcript(["PHUC HOI HANG RAO DA"]))
    v = qa_visual.inspect_image(jpeg_2048, expected_texts=["PHỤC HỒI HÀNG RÀO DA"],
                                label_text=[], forbidden_claims=[])
    assert not v.passed
    assert "PHỤC HỒI HÀNG RÀO DA" in v.missing_text


def test_invented_brand_name_is_flagged(monkeypatch, jpeg_2048):
    monkeypatch.setattr(qa_visual.ark, "describe_image",
                        _fake_transcript(["RESTORE YOUR SKIN BARRIER", "LUNAÁIRA",
                                          "CLEAN. GENTLE. EFFFECTIVE."]))
    v = qa_visual.inspect_image(jpeg_2048, expected_texts=["RESTORE YOUR SKIN BARRIER"],
                                label_text=["COSRX"], forbidden_claims=[])
    assert not v.passed
    assert "LUNAÁIRA" in v.unexpected_brandlike


def test_product_label_text_is_never_treated_as_unexpected(monkeypatch, jpeg_2048):
    """Mistake one, written down as a test. The model failed a correct image
    because it counted the bottle's own printed label as unexpected text."""
    monkeypatch.setattr(qa_visual.ark, "describe_image",
                        _fake_transcript(["COSRX", "ADVANCED SNAIL 96", "100ml"]))
    v = qa_visual.inspect_image(jpeg_2048, expected_texts=[],
                                label_text=["COSRX", "ADVANCED SNAIL 96", "100ml"],
                                forbidden_claims=[])
    assert v.passed


def test_forbidden_claim_in_the_image_fails_hard(monkeypatch, jpeg_2048):
    monkeypatch.setattr(qa_visual.ark, "describe_image",
                        _fake_transcript(["TRỊ MỤN DỨT ĐIỂM"]))
    v = qa_visual.inspect_image(jpeg_2048, expected_texts=[], label_text=[],
                                forbidden_claims=["trị mụn dứt điểm"])
    assert not v.passed
    assert v.forbidden_hits


def test_image_is_tiled_at_native_resolution_not_downscaled(monkeypatch, jpeg_2048):
    """Downscaling a 2048px image to 1024 made the model silently correct
    EFFFECTIVE to EFFECTIVE, destroying the signal the gate exists to find."""
    sizes = []

    def spy(image_bytes, prompt, max_tokens=600):
        sizes.append(Image.open(io.BytesIO(image_bytes)).size)
        return "[]"

    monkeypatch.setattr(qa_visual.ark, "describe_image", spy)
    qa_visual.inspect_image(jpeg_2048, [], [], [])
    assert len(sizes) == 4                        # four quadrants
    assert all(s == (1024, 1024) for s in sizes)  # native crops, not resizes


# --------------------------------------------------------------------------
# the redrawn-label defect: COSRX rendered as COSRA on the vertical black band
# --------------------------------------------------------------------------

def test_corrupted_brand_name_is_caught_even_when_a_correct_copy_exists(monkeypatch, jpeg_2048):
    """The measured failure: in every generated frame of a real COSRX bottle the
    vertical wordmark read `COSRA` while the same string set horizontally on the
    gold label was perfect. `missing_text` cannot see this — the correct copy
    satisfies it — so the corrupted copy has to be caught as unexpected text."""
    monkeypatch.setattr(qa_visual.ark, "describe_image",
                        _fake_transcript(["COSRA", "Advanced", "Snail 96", "Mucin",
                                          "Power", "Essence", "COSRX", "100ml"]))
    v = qa_visual.inspect_image(
        jpeg_2048, expected_texts=[],
        label_text=["COSRX", "ADVANCED SNAIL 96", "MUCIN POWER ESSENCE", "100ml"],
        forbidden_claims=[])
    assert not v.passed
    assert "COSRA" in v.unexpected_brandlike
    assert not v.missing_text          # every label string is genuinely present
    assert any("COSRX" in note for note in v.notes)   # named, not just counted


def test_label_split_over_several_rendered_lines_is_still_present(monkeypatch, jpeg_2048):
    """`MUCIN POWER ESSENCE` is printed on the bottle as three stacked lines and
    comes back as three transcript entries. Reporting it missing would send a
    correct render back for regeneration."""
    monkeypatch.setattr(qa_visual.ark, "describe_image",
                        _fake_transcript(["Advanced", "Snail 96", "Mucin", "Power",
                                          "Essence", "COSRX", "100ml"]))
    v = qa_visual.inspect_image(
        jpeg_2048, expected_texts=[],
        label_text=["COSRX", "ADVANCED SNAIL 96", "MUCIN POWER ESSENCE", "100ml"],
        forbidden_claims=[])
    assert v.passed, v.missing_text


# --------------------------------------------------------------------------
# false failures caused by the gate's own tiling
# --------------------------------------------------------------------------

def test_headline_sheared_by_a_tile_boundary_still_counts_as_present(monkeypatch, jpeg_2048):
    """A headline crossing the seam between two quadrants is read twice, in
    halves, and neither half is the whole string. The transcripts are joined in
    reading order and matched token-wise so the string is still recognised —
    with its diacritics intact, which is what keeps this from being a loophole."""
    monkeypatch.setattr(qa_visual.ark, "describe_image", _tiled_transcript([
        ["PHỤC HỒ", "HÀNG RÀO D"],   # left tiles, cut at x=1024
        ["HỤC HỒI", "NG RÀO DA"],    # right tiles, cut at x=1024
        [], [],
    ]))
    v = qa_visual.inspect_image(jpeg_2048,
                                expected_texts=["PHỤC HỒI HÀNG RÀO DA"],
                                label_text=[], forbidden_claims=[])
    assert v.passed, (v.missing_text, v.unexpected_brandlike)


def test_a_fragment_of_a_requested_string_is_not_an_invented_name(monkeypatch, jpeg_2048):
    """The other half of the same problem: the halves must not be reported as
    text nobody asked for."""
    monkeypatch.setattr(qa_visual.ark, "describe_image", _tiled_transcript([
        ["PHỤC HỒ"], ["HỤC HỒI"], ["HÀNG RÀO D"], ["NG RÀO DA"],
    ]))
    v = qa_visual.inspect_image(jpeg_2048,
                                expected_texts=["PHỤC HỒI HÀNG RÀO DA"],
                                label_text=[], forbidden_claims=[])
    assert v.unexpected_brandlike == []


def test_short_label_sheared_in_half_is_still_present(monkeypatch, jpeg_2048):
    """`COSRX` sitting across the vertical seam comes back as `COSR` and `X`.
    Failing a listing image over a crop the gate itself made is unacceptable."""
    monkeypatch.setattr(qa_visual.ark, "describe_image", _tiled_transcript([
        ["COSR"], ["X"], [], [],
    ]))
    v = qa_visual.inspect_image(jpeg_2048, expected_texts=[],
                                label_text=["COSRX"], forbidden_claims=[])
    assert v.passed, v.missing_text


# --------------------------------------------------------------------------
# normalisation and the invented-name heuristic
# --------------------------------------------------------------------------

def test_decomposed_and_composed_vietnamese_compare_equal(monkeypatch, jpeg_2048):
    """`Ụ` is one code point or two depending on which tokenizer emitted it.
    The model returns whichever it likes; a naive `==` fails correct work."""
    decomposed = unicodedata.normalize("NFD", "PHỤC HỒI")
    assert decomposed != "PHỤC HỒI"      # the fixture is only useful if it differs
    monkeypatch.setattr(qa_visual.ark, "describe_image", _fake_transcript([decomposed]))
    v = qa_visual.inspect_image(jpeg_2048, expected_texts=["PHỤC HỒI"],
                                label_text=[], forbidden_claims=[])
    assert v.passed, v.missing_text


def test_units_and_numerals_are_not_invented_names(monkeypatch, jpeg_2048):
    """`100ml` and `30ml / 1.01 fl.oz.` are on every product shot and are not
    brands. Flagging them would fail every image the studio makes."""
    monkeypatch.setattr(qa_visual.ark, "describe_image",
                        _fake_transcript(["100ml", "30ml / 1.01 fl.oz.", "96%", "50ML"]))
    v = qa_visual.inspect_image(jpeg_2048, [], [], [])
    assert v.unexpected_brandlike == []


def test_vietnamese_sentence_case_body_copy_is_not_an_invented_name(monkeypatch, jpeg_2048):
    """Only strings that read as a *name* are flagged. Sentence case is body
    copy; treating it as a brand would flag every subtitle the studio renders."""
    monkeypatch.setattr(qa_visual.ark, "describe_image",
                        _fake_transcript(["Tinh chất ốc sên 96%"]))
    v = qa_visual.inspect_image(jpeg_2048, [], [], [])
    assert v.unexpected_brandlike == []


def test_invented_english_tagline_is_flagged(monkeypatch, jpeg_2048):
    """`CLEAN. GENTLE. EFFFECTIVE.` — a three-F typo in English, produced
    unprompted. The failure axis is specified vs invented, not language, so an
    English tagline nobody asked for is caught the same way `LUNAÁIRA` is."""
    monkeypatch.setattr(qa_visual.ark, "describe_image",
                        _fake_transcript(["CLEAN. GENTLE. EFFFECTIVE."]))
    v = qa_visual.inspect_image(jpeg_2048, [], [], [])
    assert "CLEAN. GENTLE. EFFFECTIVE." in v.unexpected_brandlike


def test_transcript_is_kept_on_the_verdict(monkeypatch, jpeg_2048):
    """When the gate is wrong, the transcript is the only way to tell whether
    the model misread the image or the judge misread the model."""
    monkeypatch.setattr(qa_visual.ark, "describe_image",
                        _fake_transcript(["COSRX", "100ml"]))
    v = qa_visual.inspect_image(jpeg_2048, [], ["COSRX", "100ml"], [])
    assert v.transcript == ["COSRX", "100ml"]


def test_a_dead_tile_degrades_the_gate_instead_of_killing_it(monkeypatch, jpeg_2048):
    """One flaky vision call must not block an asset that is probably fine, but
    a partial inspection can miss a defect, so the gap is written down."""
    lock, state = threading.Lock(), {"first": True}

    def sometimes(image_bytes, prompt, max_tokens=600):
        with lock:
            first, state["first"] = state["first"], False
        if first:
            raise RuntimeError("Read timed out")
        return json.dumps(["COSRX"])

    monkeypatch.setattr(qa_visual.ark, "describe_image", sometimes)
    v = qa_visual.inspect_image(jpeg_2048, [], ["COSRX"], [])
    assert v.passed
    assert any("transcription failed" in note for note in v.notes)


# --------------------------------------------------------------------------
# tiling geometry
# --------------------------------------------------------------------------

def test_portrait_keyframe_is_covered_without_resizing(jpeg_portrait):
    """A 1440x2560 TikTok cover is not a multiple of the tile size. Tiles are
    anchored to the edges so they overlap in the middle rather than leaving a
    band of the image uninspected."""
    tiles = qa_visual.tile_image(jpeg_portrait)
    assert len(tiles) == 6                                    # 2 columns x 3 rows
    assert all(Image.open(io.BytesIO(t)).size == (1024, 1024) for t in tiles)


def test_tile_origins_cover_every_pixel_and_never_scale():
    """The property that matters: no gap on either axis, at native resolution."""
    for size in (800, 1024, 1440, 2048, 2560):
        origins = qa_visual._tile_origins(size, 1024)
        assert origins[0] == 0
        assert origins[-1] + 1024 >= size
        for a, b in zip(origins, origins[1:]):
            assert b - a <= 1024        # consecutive tiles touch or overlap


def test_photo_smaller_than_one_tile_is_padded_not_upscaled(monkeypatch, jpeg_small):
    """A reused 800x1067 brand photo still gets inspected. Upscaling it would
    invent detail the model would then read back as text."""
    sizes = []

    def spy(image_bytes, prompt, max_tokens=600):
        sizes.append(Image.open(io.BytesIO(image_bytes)).size)
        return "[]"

    monkeypatch.setattr(qa_visual.ark, "describe_image", spy)
    qa_visual.inspect_image(jpeg_small, [], [], [])
    assert sizes == [(1024, 1024), (1024, 1024)]   # one column, two rows, padded


def test_raw_bytes_are_accepted_as_well_as_a_path(monkeypatch, jpeg_2048):
    """The pipeline holds a freshly rendered image in memory; forcing a disk
    round trip before QA would be pure ceremony."""
    monkeypatch.setattr(qa_visual.ark, "describe_image", _fake_transcript([]))
    with open(jpeg_2048, "rb") as fh:
        v = qa_visual.inspect_image(fh.read(), [], [], [])
    assert v.passed


def test_transcription_asks_only_for_a_transcription(monkeypatch, jpeg_2048):
    """Mistake one is a property of the prompt. If the word 'verdict' or a list
    of expected strings ever reaches the model, the gate has regressed."""
    prompts = []

    def spy(image_bytes, prompt, max_tokens=600):
        prompts.append(prompt)
        return "[]"

    monkeypatch.setattr(qa_visual.ark, "describe_image", spy)
    qa_visual.inspect_image(jpeg_2048, expected_texts=["PHỤC HỒI HÀNG RÀO DA"],
                            label_text=["COSRX"], forbidden_claims=["trị mụn"])
    assert prompts and all("transcribe" in p.lower() for p in prompts)
    for p in prompts:
        assert "PHỤC HỒI HÀNG RÀO DA" not in p
        assert "COSRX" not in p
        assert "verdict" not in p.lower()
        assert "trị mụn" not in p


# --------------------------------------------------------------------------
# transcript parsing
# --------------------------------------------------------------------------

@pytest.mark.parametrize("raw, expected", [
    ('["A", "B"]', ["A", "B"]),
    ('```json\n["A", "B"]\n```', ["A", "B"]),
    ('Here is the text:\n["A", "B"]', ["A", "B"]),
    ("[]", []),
    ("", []),
])
def test_model_replies_are_parsed_however_they_arrive(raw, expected):
    """A transcription costs 41-109 seconds. Throwing one away because the model
    wrapped it in a code fence is not acceptable."""
    assert qa_visual.parse_transcript(raw) == expected


# --------------------------------------------------------------------------
# corrective hints
# --------------------------------------------------------------------------

def test_first_attempt_reduces_and_enlarges_the_text():
    v = qa_visual.VisualVerdict(passed=False, missing_text=["PHỤC HỒI HÀNG RÀO DA"])
    hint = qa_visual.corrective_hint(v, attempt=1)
    assert "Reduce the amount of text" in hint
    assert "PHỤC HỒI HÀNG RÀO DA" in hint
    assert "larger" in hint


def test_second_attempt_keeps_one_string_and_forbids_the_rest():
    """The model renders text reliably in proportion to how little of it there
    is. Repeating the first instruction reproduced the same defect."""
    v = qa_visual.VisualVerdict(passed=False,
                                missing_text=["PHỤC HỒI HÀNG RÀO DA", "Tinh chất ốc sên 96%"])
    hint = qa_visual.corrective_hint(v, attempt=2)
    assert "exactly one text string" in hint
    assert "No other text anywhere" in hint
    assert "Tinh chất ốc sên 96%" not in hint


def test_an_invented_name_is_quoted_back_in_the_negative_instruction():
    """"Do not add extra text" is ignored by the model. Naming the string is not."""
    v = qa_visual.VisualVerdict(passed=False, unexpected_brandlike=["LUNAÁIRA"])
    hint = qa_visual.corrective_hint(v, attempt=1)
    assert "LUNAÁIRA" in hint
    assert "Do not render" in hint


def test_a_forbidden_claim_is_named_in_the_hint():
    v = qa_visual.VisualVerdict(passed=False, forbidden_hits=["trị mụn dứt điểm"])
    assert "trị mụn dứt điểm" in qa_visual.corrective_hint(v, attempt=1)


def test_a_passing_verdict_produces_no_hint():
    """Callers append the hint unconditionally."""
    assert qa_visual.corrective_hint(qa_visual.VisualVerdict(passed=True), attempt=1) == ""
