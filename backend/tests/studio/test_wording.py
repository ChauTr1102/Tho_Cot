"""
Every case here is a string that was measured coming out of the real G7
campaign, not an invented one.

Copy defects are the failure mode this system cannot detect by itself: the graph
succeeds, the image renders, the QA gate reads the text back correctly — and the
text is wrong. "Đặc sản Việt Nam vị đậm Robusta Buôn Ma" is a perfectly rendered
headline naming a city that does not exist. So the assertions are about *shape*:
no stray quote marks, no sentence cut mid-phrase, no field name on the artwork,
no price standing in for an offer.
"""
from __future__ import annotations

import pytest

from app.services.studio import wording

# The two hooks the research agent wrote for G7. Route A is the morning-rush
# angle, route B the Vietnamese-speciality angle; the whole point of having two
# is that they say different things.
HOOK_A = ("Báo thức vừa reo, pha nhanh chỉ trong vài giây có ly cà phê ngon "
          "chuẩn Việt để bắt đầu ngày mới")
HOOK_B = "Đặc sản Việt Nam vị đậm Robusta Buôn Ma Thuột — uống 1 ngụm là nhớ mãi"
PRICE_LINE = "135.000đ / túi 50 gói · Mua 3 tặng 1 trong chiến dịch 9.9"


class TestShorten:
    def test_keeps_a_place_name_whole(self):
        """The bug this module was written for.

        Cutting HOOK_B at 42 characters produced "…Robusta Buôn Ma": Buôn Ma
        Thuột is a city, and dropping its last syllable is not a shorter name,
        it is a wrong one.
        """
        assert wording.shorten(HOOK_B, 42) == "Đặc sản Việt Nam vị đậm Robusta Buôn Ma Thuột"

    def test_drops_a_clause_rather_than_cutting_one(self):
        result = wording.shorten(HOOK_A, 42)
        assert result == "Báo thức vừa reo"
        assert not result.endswith(("cà", "chuẩn", "trong"))

    def test_the_two_routes_still_say_different_things(self):
        """A/B is the reason there are two routes. Shortening must not converge
        them onto one line."""
        assert wording.shorten(HOOK_A, 42) != wording.shorten(HOOK_B, 42)

    def test_preserves_upstream_punctuation(self):
        """Rebuilding from split pieces turned " · " into ", ". The studio
        shortens copy; it does not restyle it."""
        result = wording.shorten(PRICE_LINE, 56)
        assert "·" in result
        assert ", Mua" not in result

    def test_never_ends_on_a_separator(self):
        for text, limit in ((PRICE_LINE, 22), (HOOK_A, 20), (HOOK_B, 30)):
            assert not wording.shorten(text, limit).rstrip().endswith(
                (",", ";", ":", "·", "—", "–", "-")
            )

    def test_a_line_that_already_fits_is_untouched(self):
        assert wording.shorten("Mua 3 tặng 1", 42) == "Mua 3 tặng 1"

    def test_falls_back_to_a_whole_short_clause(self):
        """When the opening clause is itself too long, a shorter complete clause
        beats a cut through the first one. HOOK_B opens with 44 characters and
        closes with 22, so a 20-character target takes the closing clause whole
        rather than the opening one in half."""
        assert wording.shorten(HOOK_B, 20) == "uống 1 ngụm là nhớ mãi"

    def test_cuts_when_even_the_shortest_clause_will_not_fit(self):
        """Truncation is the last resort, not an impossibility — and it still
        lands on a word boundary."""
        assert wording.shorten(HOOK_B, 8) == "uống 1"

    def test_cuts_only_when_there_is_no_clause_boundary(self):
        text = "khôngcódấungắtnàoởđây " * 4
        assert len(wording.shorten(text, 20)) <= 20

    def test_empty_input_is_empty_output(self):
        assert wording.shorten(None, 42) == ""
        assert wording.shorten("   ", 42) == ""


class TestUnquote:
    def test_removes_the_wrapper_upstream_writes(self):
        """`direct._text_for` put the opening quote on the poster: the headline
        rendered as `"Báo thức vừa reo, pha nhanh chỉ trong vài giây có ly cà`."""
        assert wording.unquote(f'"{HOOK_A}"') == HOOK_A
        assert wording.shorten(f'"{HOOK_A}"', 42) == "Báo thức vừa reo"

    @pytest.mark.parametrize("wrapped,bare", [
        ("“Mua ngay”", "Mua ngay"),
        ("'Mua ngay'", "Mua ngay"),
        ("«Mua ngay»", "Mua ngay"),
    ])
    def test_handles_every_quote_style(self, wrapped, bare):
        assert wording.unquote(wrapped) == bare

    def test_leaves_an_apostrophe_inside_the_line_alone(self):
        assert wording.unquote("don't stop") == "don't stop"

    def test_leaves_an_unmatched_quote_alone(self):
        assert wording.unquote('"Mua ngay') == '"Mua ngay'


class TestStripLabel:
    def test_removes_a_field_name_the_planner_wrote_into_its_value(self):
        """Measured on a finished render: display type reading "Thông điệp bán
        hàng cốt lõi: Cà phê đậm"."""
        assert wording.strip_label(
            "Thông điệp bán hàng cốt lõi: Cà phê đậm vị Robusta"
        ) == "Cà phê đậm vị Robusta"

    def test_keeps_a_date_prefix(self):
        """"11.11: giảm 25%" is copy, and the prefix is the whole point."""
        assert wording.strip_label("11.11: giảm 25%") == "11.11: giảm 25%"

    def test_keeps_a_hook_that_opens_with_a_question(self):
        assert wording.strip_label("Mệt buổi sáng? Pha nhanh: xong") == (
            "Mệt buổi sáng? Pha nhanh: xong"
        )

    def test_keeps_a_one_word_prefix(self):
        assert wording.strip_label("G7: cà phê đậm") == "G7: cà phê đậm"


class TestOfferBadge:
    def test_finds_the_offer_inside_a_price_line(self):
        """The divergence that motivated one shared module: the director read
        this line as "MUA 3 TẶNG 1", the worksheet as "135.000Đ / TÚI 50 GÓI ·"."""
        assert wording.offer_badge(PRICE_LINE) == "MUA 3 TẶNG 1"

    def test_diacritics_are_characters_not_marks(self):
        """`t[ăa]ng` does not match "tặng" — ă and ặ are different characters,
        so the pattern silently lost to a weaker offer further down the line."""
        assert wording.offer_badge("mua 3 tặng 1 và miễn phí vận chuyển") == "MUA 3 TẶNG 1"

    @pytest.mark.parametrize("promo,expected", [
        ("11.11: giảm 25% toàn shop", "GIẢM 25%"),
        ("giảm đến 50% cho đơn đầu", "GIẢM ĐẾN 50%"),
        ("freeship toàn quốc", "FREESHIP"),
        ("miễn phí vận chuyển đơn từ 99k", "MIỄN PHÍ VẬN CHUYỂN"),
    ])
    def test_reads_the_common_offer_shapes(self, promo, expected):
        assert wording.offer_badge(promo) == expected

    def test_a_price_with_no_offer_is_not_an_offer(self):
        """Returning "" lets the caller decide. A price badged as though it were
        a promotion promises something the campaign never offered."""
        assert wording.offer_badge("135.000đ / túi 50 gói") == ""
