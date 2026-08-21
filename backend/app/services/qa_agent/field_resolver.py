"""Resolve dot-path field references (e.g. "commerce_copy.product_description")
against CampaignInputDTO/CampaignOutputDTO instances, for feeding the actual
relevant content to the per-item verifier agent."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


def resolve_field(root: BaseModel, dot_path: str) -> Any:
    """Walk a dot-path (e.g. 'product_collection_image_set.product_hero_image')
    against a Pydantic model instance. Returns None if any segment is missing
    or the path traverses into a list without an index (in which case the
    whole list is returned instead, since checklist items reference list
    fields directly, e.g. 'creative_routes')."""
    current: Any = root
    for segment in dot_path.split("."):
        if isinstance(current, BaseModel):
            if segment not in current.__class__.model_fields:
                return None
            current = getattr(current, segment)
        elif isinstance(current, dict):
            current = current.get(segment)
        elif isinstance(current, list):
            # Path continued past a list without an index; nothing further
            # to resolve — return the list itself as the closest match.
            return current
        else:
            return None
    return current


def stringify_field(value: Any) -> str:
    """Render a resolved field value as readable text for the verifier
    agent's prompt (lists of Pydantic models, plain strings, etc.)."""
    if value is None:
        return "(không có giá trị)"
    if isinstance(value, BaseModel):
        return value.model_dump_json(indent=2)
    if isinstance(value, list):
        rendered = []
        for item in value:
            if isinstance(item, BaseModel):
                rendered.append(item.model_dump_json(indent=2))
            else:
                rendered.append(str(item))
        return "\n".join(rendered) if rendered else "(danh sách rỗng)"
    return str(value)


# Human-readable Vietnamese labels for CampaignOutputDTO/CampaignInputDTO
# field segments, keyed by the exact schema attribute name. Used to turn a
# raw dot-path like "product_collection_image_set.product_hero_image" into
# "Bộ hình ảnh sản phẩm > Ảnh chính sản phẩm" for anything shown to the end
# user (QA issue "field" label) — nobody outside the codebase should ever
# see a snake_case schema name.
FIELD_LABELS: dict[str, str] = {
    # CampaignOutputDTO
    "product_positioning": "Định vị sản phẩm",
    "main_campaign_angle": "Góc chiến dịch chính",
    "target_audience": "Đối tượng mục tiêu",
    "key_selling_message": "Thông điệp bán hàng chính",
    "product_benefit_hierarchy": "Thứ tự lợi ích sản phẩm",
    "creative_routes": "Phương án sáng tạo",
    "name": "Tên phương án",
    "hook_idea": "Ý tưởng mở đầu",
    "visual_direction": "Định hướng hình ảnh",
    "message_angle": "Góc thông điệp",
    "suggested_platform_usage": "Nền tảng đề xuất sử dụng",
    "short_form_video_asset": "Video ngắn",
    "generated_video_urls": "Video đã tạo",
    "format": "Định dạng",
    "duration": "Thời lượng",
    "additional_cuts": "Bản dựng bổ sung",
    "product_collection_image_set": "Bộ hình ảnh sản phẩm",
    "product_hero_image": "Ảnh chính sản phẩm",
    "sku_detail_image": "Ảnh chi tiết sản phẩm",
    "campaign_collection_image": "Ảnh bộ sưu tập chiến dịch",
    "marketplace_thumbnail": "Ảnh thu nhỏ trên sàn (thumbnail)",
    "promotion_banner": "Banner khuyến mãi",
    "bundle_image": "Ảnh combo sản phẩm",
    "seasonal_sale_image": "Ảnh khuyến mãi theo mùa",
    "commerce_copy": "Nội dung bán hàng",
    "product_title": "Tên sản phẩm hiển thị",
    "product_description": "Mô tả sản phẩm",
    "listing_bullet_points": "Gạch đầu dòng mô tả",
    "ad_caption": "Caption quảng cáo",
    "promotion_copy": "Nội dung khuyến mãi",
    "short_hook_lines": "Câu mở đầu ngắn",
    "ab_testing_plan": "Kế hoạch A/B testing",
    "what_to_test": "Nội dung cần test",
    "route_a_description": "Mô tả phương án A",
    "route_b_description": "Mô tả phương án B",
    "suggested_success_metrics": "Chỉ số đánh giá thành công",
    "expected_learning": "Kỳ vọng rút ra",
    "performance_learning": "Đánh giá hiệu suất",
    "what_to_keep": "Điều nên giữ lại",
    "what_to_change": "Điều nên thay đổi",
    "what_to_stop": "Điều nên dừng",
    "what_to_test_next": "Điều nên test tiếp theo",
    # CampaignInputDTO
    "product_brief": "Thông tin sản phẩm",
    "product_name": "Tên sản phẩm",
    "category": "Ngành hàng",
    "key_selling_points": "Điểm bán hàng chính",
    "price_or_promotion": "Giá / khuyến mãi",
    "price": "Giá",
    "currency": "Đơn vị tiền tệ",
    "promotion": "Khuyến mãi",
    "target_market": "Thị trường mục tiêu",
    "required_claims": "Tuyên bố bắt buộc phải có",
    "restricted_or_forbidden_claims": "Tuyên bố bị cấm",
    "brand_kit": "Bộ nhận diện thương hiệu",
    "logo": "Logo",
    "path": "Đường dẫn tệp",
    "brand_colors": "Màu thương hiệu",
    "primary": "Màu chủ đạo",
    "secondary": "Màu phụ",
    "accent": "Màu nhấn",
    "palette": "Bảng màu",
    "tone_of_voice": "Giọng văn thương hiệu",
    "description": "Mô tả",
    "attributes": "Đặc điểm",
    "do": "Nên làm",
    "dont": "Không nên làm",
    "product_photos": "Ảnh sản phẩm gốc",
    "existing_product_visuals": "Hình ảnh sản phẩm hiện có",
    "audience_brief": "Thông tin đối tượng khách hàng",
    "target_customer": "Khách hàng mục tiêu",
    "language": "Ngôn ngữ",
    "platform": "Nền tảng",
    "market": "Thị trường",
    "market_signal": "Tín hiệu thị trường",
    "trend": "Xu hướng",
    "seasonal_moment": "Thời điểm theo mùa",
    "consumer_pain_point": "Nỗi đau của khách hàng",
    "search_keyword": "Từ khoá tìm kiếm",
    "competitor_angle": "Góc tiếp cận của đối thủ",
    "campaign_objective": "Mục tiêu chiến dịch",
}


def humanize_field_path(dot_path: str) -> str:
    """Turn a schema dot-path (e.g. "product_collection_image_set.product_hero_image")
    into a human-readable Vietnamese label (e.g. "Bộ hình ảnh sản phẩm > Ảnh chính sản
    phẩm"), so raw snake_case field names never reach the end user. Falls back to a
    title-cased, underscore-stripped version of any segment without a known label."""
    labels = [
        FIELD_LABELS.get(segment) or segment.replace("_", " ").strip().capitalize()
        for segment in dot_path.split(".")
        if segment
    ]
    return " > ".join(labels) if labels else dot_path
