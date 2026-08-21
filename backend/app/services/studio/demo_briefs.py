"""
Demo briefs for the six sample brands.

The studio sits downstream of a planning agent that produces the real
`CampaignPlan`. For a demo the screen only sends a brand directory, so this
module fills the gap: it turns `sample_data/<dir>/` into the `CampaignInput` +
`CampaignPlan` pair the studio expects.

Two rules kept it honest:

  * Product photographs are read from disk, never invented. They are the Brand
    Lock reference, and how many usable ones exist decides how much of a kit is
    real photography rather than generated imagery.
  * `forbidden_claims` are real marketplace constraints for each category, not
    decoration. They are filtered out of every rendered string downstream, so a
    lazy entry here becomes a takedown risk on a live listing.

When a real upstream plan exists for a brand it is preferred over the canned
one — `upstream.load_plan` parses the planning agent's actual output format.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.schemas.campaign import (
    ABTestPlan,
    AudienceBrief,
    BrandKit,
    CampaignInput,
    CampaignPlan,
    CreativeRoute,
    MarketSignal,
    ProductBrief,
    ProductPositioning,
)

SAMPLE_DIR = Path(__file__).resolve().parents[4] / "sample_data"
PHOTO_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def sample_root() -> Path:
    """Where the brand directories live. Kept as a function so tests can patch it."""
    return SAMPLE_DIR


def product_photos(brand_dir: str) -> list[str]:
    """Readable product photographs for a brand, in filename order.

    Logos are excluded: they are usually far below the 300px floor the video
    model enforces on reference images, and three of the five in `sample_data`
    fail it outright.
    """
    assets = sample_root() / brand_dir / "assets"
    if not assets.is_dir():
        return []
    return sorted(
        str(p) for p in assets.iterdir()
        if p.suffix.lower() in PHOTO_SUFFIXES and p.stem.startswith("product")
    )


# --- the six brands ---------------------------------------------------------
# Each entry is (product, brand, audience, signal, routes) in the order the
# schemas need them. Vietnamese copy, because that is what gets rendered.

_BRANDS: dict[str, dict] = {
    "01_cosrx_snail_essence": dict(
        name="COSRX Advanced Snail 96 Mucin Power Essence (100ml)",
        category="Skincare / Tinh chất dưỡng da",
        selling=[
            "96% Snail Secretion Filtrate phục hồi hàng rào da",
            "Cấp ẩm sâu, da căng bóng",
            "Kết cấu mỏng nhẹ, thẩm thấu nhanh",
            "Đã kiểm nghiệm lâm sàng",
        ],
        promo="11.11: giảm 25% còn 290.000đ + miễn phí vận chuyển",
        market="Việt Nam / SEA",
        required=["96% snail mucin", "đã kiểm nghiệm lâm sàng", "phục hồi hàng rào da"],
        forbidden=["trị mụn dứt điểm", "chữa khỏi", "trắng da vĩnh viễn", "điều trị y khoa"],
        colors=["#FFFFFF", "#1A1A1A", "#00A19A"],
        tone="Sạch sẽ, khoa học, đáng tin, tối giản",
        customer="Nữ 18-30, da nhạy cảm, mê skincare Hàn",
        trend="Glass skin, phục hồi hàng rào da",
        season="Sale 11.11",
        pain="Da khô căng, xỉn màu, dễ kích ứng",
        keyword="tinh chất ốc sên",
        competitor="Some By Mi, SKIN1004, Anua",
        objective="Conversion",
        angle="96% tinh chất ốc sên phục hồi hàng rào da",
        routes=[
            ("Bằng chứng khoa học", "96% snail mucin, con số không nói dối",
             "phòng lab sạch, trắng, macro texture"),
            ("Người thật kể chuyện", "Da mình xỉn tới mức bạn hỏi có ốm không",
             "bàn trang điểm đời thường, ánh sáng cửa sổ, cầm tay"),
        ],
    ),
    "02_oatside_barista": dict(
        name="Oatside Barista Blend Oat Milk (1L)",
        category="F&B / Sữa yến mạch",
        selling=[
            "Béo ngậy nhờ yến mạch rang, không hấp",
            "100% thực vật, không lactose",
            "Không thêm hương liệu, gum hay chất nhũ hoá",
            "Tạo bọt mịn, pha cà phê chuẩn quán",
        ],
        promo="Ra mắt: mua 5 tặng 1 + miễn phí vận chuyển",
        market="SEA (VN, SG, ID, PH)",
        required=["100% plant-based", "không lactose", "không gum"],
        forbidden=["sữa bò", "chữa bệnh", "ngừa bệnh", "giảm cân"],
        colors=["#F3E7D3", "#4B2E2A", "#E4A93C"],
        tone="Vui nhộn, lầy, meme, relatable Gen Z",
        customer="Gen Z mê cà phê, quan tâm sức khoẻ, không dung nạp lactose",
        trend="Oat milk, barista tại nhà, matcha latte",
        season="Ra mắt sản phẩm",
        pain="Sữa hạt vị dở, sữa bò gây đầy bụng",
        keyword="sữa yến mạch barista",
        competitor="Alpro, Minor Figures, 137 Degrees",
        objective="Awareness + Conversion",
        angle="Béo ngậy như quán, ngay tại nhà",
        routes=[
            ("Barista tại nhà", "Bọt mịn như ngoài quán, pha trong 30 giây",
             "quầy bar gỗ, ánh sáng ban ngày, ly latte đang rót"),
            ("Vị đậm khác biệt", "Yến mạch rang, không hấp, nên mới béo ngậy",
             "macro yến mạch rang, nền kem, ánh sáng ấm"),
        ],
    ),
    "03_anker_powerbank": dict(
        name="Anker Power Bank 10.000mAh 30W",
        category="Điện tử / Sạc dự phòng",
        selling=[
            "10.000mAh, sạc điện thoại khoảng 2 lần",
            "Sạc nhanh 30W",
            "Cáp USB-C tích hợp sẵn",
            "Mỏng nhẹ, bỏ túi gọn",
        ],
        promo="11.11 Flash Sale: giảm 40% còn 349.000đ",
        market="Việt Nam / SEA",
        required=["10.000mAh", "sạc nhanh 30W", "cáp USB-C tích hợp"],
        forbidden=["nhanh nhất thế giới", "100% an toàn", "không bao giờ nóng"],
        colors=["#00AEEF", "#000000", "#FFFFFF"],
        tone="Đáng tin, gọn gàng, thiên công nghệ",
        customer="Người trẻ đi làm, đi học, hay hết pin giữa ngày",
        trend="Sạc nhanh, cáp tích hợp",
        season="Mega Sale 11.11",
        pain="Hết pin giữa ngày, quên mang dây sạc",
        keyword="sạc dự phòng cáp liền",
        competitor="Xiaomi, Baseus, Ugreen",
        objective="Conversion",
        angle="Cáp liền thân, không bao giờ quên dây",
        routes=[
            ("Không cần mang dây", "Cáp nằm sẵn trong thân, rút ra là sạc",
             "bàn làm việc tối giản, ánh sáng gắt, phản chiếu kim loại"),
            ("Ngày dài không lo", "Hết pin lúc 3 giờ chiều? Không còn nữa",
             "bối cảnh di chuyển, ánh sáng tự nhiên, cầm tay"),
        ],
    ),
    "04_cocoon_ca_phe_dak_lak": dict(
        name="Cocoon Tẩy da chết cà phê Đắk Lắk (200ml)",
        category="Mỹ phẩm thuần chay / Tẩy da chết cơ thể",
        selling=[
            "Cà phê Đắk Lắk nguyên chất",
            "100% thuần chay, không thử nghiệm trên động vật",
            "Làm sạch tế bào chết, da mềm mịn",
            "Thương hiệu Việt",
        ],
        promo="Mua 2 tặng 1 túi vải",
        market="Việt Nam",
        required=["100% thuần chay", "cà phê Đắk Lắk"],
        forbidden=["trắng da cấp tốc", "trị nám", "chữa bệnh da liễu"],
        colors=["#3E2723", "#D7CCC8", "#8D6E63"],
        tone="Mộc mạc, tự nhiên, tự hào Việt Nam",
        customer="Nữ 20-35, ưa mỹ phẩm thuần chay, ủng hộ hàng Việt",
        trend="Clean beauty, mỹ phẩm thuần chay, nguyên liệu bản địa",
        season="Quanh năm",
        pain="Da cơ thể khô ráp, sần sùi",
        keyword="tẩy da chết cà phê",
        competitor="The Body Shop, Sabbath Saigon",
        objective="Awareness + Conversion",
        angle="Cà phê Đắk Lắk cho làn da mềm mịn",
        routes=[
            ("Nguyên liệu bản địa", "Cà phê Đắk Lắk, không phải hương liệu",
             "hạt cà phê rang, gỗ mộc, ánh sáng tự nhiên"),
            ("Thuần chay thật", "Không thử nghiệm trên động vật, không đánh đổi",
             "phòng tắm sáng, cây xanh, chất liệu thô mộc"),
        ],
    ),
    "05_trung_nguyen_g7": dict(
        name="Trung Nguyên G7 Cà phê hoà tan 3in1",
        category="F&B / Cà phê hoà tan",
        selling=[
            "Robusta Buôn Ma Thuột, vị đậm đặc trưng cà phê Việt",
            "Công thức 3in1 pha nhanh, tiện mang theo",
            "Thương hiệu Việt xuất khẩu hơn 100 quốc gia",
            "Năng lượng tỉnh táo cho ngày mới",
        ],
        promo="Cross-border 9.9: mua 3 tặng 1 + miễn phí vận chuyển",
        market="Trung Quốc, Hoa Kỳ, Hàn Quốc, Đông Nam Á",
        required=["cà phê hoà tan 3in1", "Robusta Buôn Ma Thuột"],
        forbidden=["ngon nhất thế giới", "chữa bệnh", "tốt hơn Nescafé"],
        colors=["#C8102E", "#000000", "#D4AF37"],
        tone="Mạnh mẽ, năng lượng, tự hào Việt Nam",
        customer="Dân văn phòng, sinh viên, người yêu cà phê Việt vị đậm",
        trend="Cà phê Việt vị đậm, cross-border 9.9",
        season="China 9.9 Shopping Festival",
        pain="Buổi sáng uể oải, cần tỉnh táo nhanh",
        keyword="cà phê hoà tan 3in1",
        competitor="Nescafé, Vinacafé, G7 nhái",
        objective="Awareness + Conversion",
        angle="Vị đậm cà phê Việt, mở đầu ngày bứt tốc",
        routes=[
            ("Vị đậm đúng gu Việt", "Robusta Buôn Ma Thuột, đậm như quán vỉa hè",
             "ly cà phê đang rót, hơi nóng, nền tối, ánh sáng gắt"),
            ("Nhanh cho ngày bận", "Ba mươi giây, một ly, đủ tỉnh cả buổi sáng",
             "bàn làm việc buổi sáng, ánh nắng, nhịp nhanh"),
        ],
    ),
    "06_marou_chocolate": dict(
        name="Marou Chocolate Đắk Lắk 70%",
        category="F&B / Socola cao cấp bean-to-bar",
        selling=[
            "Ca cao Đắk Lắk, làm thủ công tại Việt Nam",
            "Bean-to-bar, kiểm soát toàn bộ quy trình",
            "70% ca cao, vị trái cây đặc trưng vùng trồng",
            "Bao bì in thủ công",
        ],
        promo="Hộp quà 3 thanh: 390.000đ",
        market="Việt Nam / xuất khẩu",
        required=["ca cao Đắk Lắk", "bean-to-bar", "70% ca cao"],
        forbidden=["tốt cho sức khoẻ", "giảm cân", "ngon nhất Việt Nam"],
        colors=["#1B1B1B", "#C9A227", "#F5F0E6"],
        tone="Tinh tế, thủ công, kể chuyện vùng trồng",
        customer="Người sành ăn, mua quà biếu, khách du lịch",
        trend="Bean-to-bar, đặc sản vùng trồng, quà tặng cao cấp",
        season="Quà tặng cuối năm",
        pain="Socola công nghiệp vị ngọt gắt, không có cá tính",
        keyword="socola Marou",
        competitor="Lindt, Godiva, Alluvia",
        objective="Awareness",
        angle="Ca cao Đắk Lắk, làm thủ công tại Việt Nam",
        routes=[
            ("Vùng trồng kể chuyện", "Đắk Lắk trong một thanh socola",
             "gỗ tối, ca cao thô, ánh sáng một nguồn, tương phản sâu"),
            ("Quà tặng tinh tế", "Món quà nói được điều bạn không tiện nói",
             "hộp quà mở hờ, giấy in thủ công, ánh sáng ấm dịu"),
        ],
    ),
}


def available_brands() -> list[str]:
    """Brand directories that exist on disk, in catalogue order."""
    return [d for d in _BRANDS if (sample_root() / d).is_dir()]


def build_input(brand_dir: str, campaign_id: str) -> CampaignInput:
    """Assemble the `CampaignInput` for a brand, with real photo paths attached."""
    b = _BRANDS.get(brand_dir)
    if b is None:
        raise KeyError(f"unknown brand directory: {brand_dir}")
    return CampaignInput(
        campaign_id=campaign_id,
        product_brief=ProductBrief(
            product_name=b["name"], category=b["category"],
            key_selling_points=b["selling"], price_or_promotion=b["promo"],
            target_market=b["market"], required_claims=b["required"],
            forbidden_claims=b["forbidden"],
        ),
        brand_kit=BrandKit(
            logo_url=None, brand_colors=b["colors"], tone_of_voice=b["tone"],
            product_photo_urls=product_photos(brand_dir),
        ),
        audience_brief=AudienceBrief(
            target_customer=b["customer"], language="vi",
            platform=["tiktok_shop", "shopee"], market=b["market"],
        ),
        market_signal=MarketSignal(
            trend=b["trend"], seasonal_moment=b["season"],
            consumer_pain_point=b["pain"], search_keyword=b["keyword"],
            competitor_angle=b["competitor"], campaign_objective=b["objective"],
        ),
    )


def build_plan(brand_dir: str, campaign_id: str) -> CampaignPlan:
    """Assemble a `CampaignPlan`, preferring a real upstream plan when one exists.

    `backend/ark_out/<brand>_campaign_plan.json` is written by the planning
    agent. Its shape differs from the Pydantic model, so it goes through the
    upstream adapter rather than straight into the constructor.
    """
    b = _BRANDS.get(brand_dir)
    if b is None:
        raise KeyError(f"unknown brand directory: {brand_dir}")

    for candidate in (
        Path("ark_out") / f"{brand_dir.split('_', 1)[-1]}_campaign_plan.json",
        Path("ark_out") / "g7_campaign_plan.json" if brand_dir.endswith("g7") else None,
    ):
        if candidate and candidate.is_file():
            try:
                from app.services.studio import upstream
                return upstream.load_plan(json.loads(candidate.read_text("utf-8")), campaign_id)
            except Exception:
                break   # a malformed upstream file must not block the demo

    routes = [
        CreativeRoute(
            route_id=chr(ord("A") + i), hook_idea=hook,
            visual_direction=visual, message_angle=name,
            suggested_platform_usage=["tiktok_shop", "shopee"],
        )
        for i, (name, hook, visual) in enumerate(b["routes"])
    ]
    return CampaignPlan(
        campaign_id=campaign_id,
        positioning=ProductPositioning(
            main_campaign_angle=b["angle"], target_audience=b["customer"],
            key_selling_message=b["selling"][0],
            product_benefit_hierarchy=b["selling"],
        ),
        creative_routes=routes,
        ab_test_plan=ABTestPlan(
            what_to_test="Góc thông điệp và ngôn ngữ hình",
            route_a=routes[0].route_id, route_b=routes[1].route_id,
            success_metrics=["CTR", "CVR", "ROAS", "thời gian xem"],
            expected_learning="Góc nào giữ chân người xem và chuyển đổi tốt hơn",
        ),
    )


def build_pair(brand_dir: str, campaign_id: str) -> tuple[CampaignPlan, CampaignInput]:
    """The pair `run_studio` takes."""
    return build_plan(brand_dir, campaign_id), build_input(brand_dir, campaign_id)
