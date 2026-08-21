
"""
Translation between the team's campaign DTOs and the studio's internal models.

The studio is a middle stage: the research and planning agents upstream speak
`app.schemas.campaign_dto`, and the studio owns exactly two fields of the
`CampaignOutputDTO` they assemble —

    product_collection_image_set : ProductCollectionImageSet
    short_form_video_asset       : ShortFormVideoAsset

Everything else in that DTO belongs to another agent. This module is the seam,
and it exists so the studio's internals can change shape without the contract
moving: nothing outside `app.services.studio` should import the studio's own
`CampaignInput` / `CampaignPlan` / `AssetBundle`.

Two shape differences are worth knowing about, because they are where a naive
`model_validate` would quietly lose information:

* `price_or_promotion` is a flat string internally and a `{price, currency,
  promotion}` object in the DTO. Both halves matter — the price appears on
  badges, the promotion text on banners — so they are joined rather than
  chosen between.
* `restricted_or_forbidden_claims` in the DTO is `forbidden_claims` internally.
  A rename, but a load-bearing one: every string in that list is filtered out
  of prompts, on-screen copy and voiceover, so dropping it silently would put
  a takedown-worthy claim on a live listing.
"""
from __future__ import annotations

from typing import Any

from app.schemas.campaign import (
    ABTestPlan,
    AssetBundle,
    AudienceBrief,
    BrandKit,
    CampaignInput,
    CampaignPlan,
    CreativeRoute,
    ImageKind,
    MarketSignal,
    ProductBrief,
    ProductPositioning,
)
from app.schemas.campaign_dto import (
    CampaignInputDTO,
    ProductCollectionImageSet,
    ShortFormVideoAsset,
)

# Which internal ImageKind fills which DTO field. The first four are required by
# BP-01; the last three are the optional extras the brief allows.
_IMAGE_SLOT_BY_KIND: dict[ImageKind, str] = {
    ImageKind.HERO: "product_hero_image",
    ImageKind.SKU_DETAIL: "sku_detail_image",
    ImageKind.COLLECTION: "campaign_collection_image",
    ImageKind.THUMBNAIL: "marketplace_thumbnail",
    ImageKind.BANNER: "promotion_banner",
    ImageKind.BUNDLE: "bundle_image",
    ImageKind.SEASONAL: "seasonal_sale_image",
}

_REQUIRED_IMAGE_FIELDS = (
    "product_hero_image",
    "sku_detail_image",
    "campaign_collection_image",
    "marketplace_thumbnail",
)


def _price_line(dto: CampaignInputDTO) -> str | None:
    """Flatten `{price, currency, promotion}` into the one line copy is drawn from."""
    p = dto.product_brief.price_or_promotion
    parts: list[str] = []
    if p.price is not None:
        amount = f"{p.price:,.0f}".replace(",", ".")
        parts.append(f"{amount}{p.currency and ' ' + p.currency or ''}".strip())
    if p.promotion:
        parts.append(p.promotion)
    return " · ".join(parts) or None


def _tone(dto: CampaignInputDTO) -> str:
    """Collapse the structured tone object into the sentence a prompt can carry.

    The DTO's `do` / `dont` lists are guidance for a copywriter, not for an
    image model; only the description and attributes describe how a frame
    should *look*.
    """
    tone = dto.brand_kit.tone_of_voice
    bits = [tone.description.strip()] if tone.description else []
    if tone.attributes:
        bits.append(", ".join(tone.attributes))
    return " — ".join(b for b in bits if b)


def _colours(dto: CampaignInputDTO) -> list[str]:
    c = dto.brand_kit.brand_colors
    ordered = [c.primary, c.secondary, *c.accent, *c.palette]
    seen: list[str] = []
    for value in ordered:
        if value and value not in seen:
            seen.append(value)
    return seen


def to_campaign_input(dto: CampaignInputDTO, campaign_id: str,
                      photo_paths: list[str] | None = None) -> CampaignInput:
    """DTO -> the studio's `CampaignInput`.

    `photo_paths` overrides `brand_kit.product_photos` and is how uploaded files
    get in: the DTO carries whatever the caller wrote there, which may be
    original filenames or remote URLs, while the studio needs readable local
    paths to use as Brand Lock references.
    """
    brief = dto.product_brief
    audience = dto.audience_brief
    signal = dto.market_signal
    return CampaignInput(
        campaign_id=campaign_id,
        product_brief=ProductBrief(
            product_name=brief.product_name,
            category=brief.category,
            key_selling_points=list(brief.key_selling_points),
            price_or_promotion=_price_line(dto),
            target_market=brief.target_market,
            required_claims=list(brief.required_claims),
            forbidden_claims=list(brief.restricted_or_forbidden_claims),
        ),
        brand_kit=BrandKit(
            logo_url=dto.brand_kit.logo.path,
            brand_colors=_colours(dto),
            tone_of_voice=_tone(dto),
            product_photo_urls=list(photo_paths if photo_paths is not None
                                    else dto.brand_kit.product_photos),
        ),
        audience_brief=AudienceBrief(
            target_customer=audience.target_customer,
            language=audience.language,
            platform=[audience.platform] if audience.platform else [],
            market=audience.market,
        ),
        market_signal=MarketSignal(
            trend=signal.trend,
            seasonal_moment=signal.seasonal_moment,
            consumer_pain_point=signal.consumer_pain_point,
            search_keyword=", ".join(signal.search_keyword) or None,
            competitor_angle=signal.competitor_angle,
            campaign_objective=signal.campaign_objective,
        ),
    )


def plan_from_positioning(raw: dict[str, Any], campaign_id: str,
                          fallback: CampaignInput | None = None) -> CampaignPlan:
    """A `CampaignPlan` from whatever the planning agent produced.

    Two formats are accepted, because two exist in the repo: the nested research
    output (`product_positioning.main_campaign_angle = {decision, rationale,
    evidence}`) and the flat `CampaignOutputDTO`. `upstream.load_plan` handles
    the nested one; this handles the flat one and falls back to the brief when a
    caller sends only an input and no plan at all.
    """
    from app.services.studio import upstream

    if raw:
        nested = raw.get("product_positioning", {})
        if isinstance(nested.get("main_campaign_angle"), dict):
            return upstream.load_plan(raw, campaign_id)

        pos = nested or {}
        routes = [
            CreativeRoute(
                route_id=chr(ord("A") + i),
                hook_idea=r.get("hook_idea", ""),
                visual_direction=r.get("visual_direction", ""),
                message_angle=r.get("message_angle") or r.get("name", ""),
                suggested_platform_usage=list(r.get("suggested_platform_usage", [])),
            )
            for i, r in enumerate(raw.get("creative_routes", []))
        ]
        if pos and routes:
            ab = raw.get("ab_testing_plan", {})
            return CampaignPlan(
                campaign_id=campaign_id,
                positioning=ProductPositioning(
                    main_campaign_angle=pos.get("main_campaign_angle", ""),
                    target_audience=pos.get("target_audience", ""),
                    key_selling_message=pos.get("key_selling_message", ""),
                    product_benefit_hierarchy=list(pos.get("product_benefit_hierarchy", [])),
                ),
                creative_routes=routes,
                ab_test_plan=ABTestPlan(
                    what_to_test=ab.get("what_to_test", "Góc thông điệp và ngôn ngữ hình"),
                    route_a=routes[0].route_id,
                    route_b=routes[min(1, len(routes) - 1)].route_id,
                    success_metrics=list(ab.get("suggested_success_metrics",
                                                ["CTR", "CVR", "ROAS"])),
                    expected_learning=ab.get("expected_learning", ""),
                ),
            )

    # No usable plan: derive a minimal one from the brief so a caller can ask for
    # assets with an input alone. Thin, but never invented — every field here is
    # copied from something the caller actually sent.
    if fallback is None:
        raise ValueError("cần plan hoặc campaign input để dựng CampaignPlan")
    brief = fallback.product_brief
    routes = [
        CreativeRoute(route_id="A", hook_idea=brief.key_selling_points[0] if brief.key_selling_points else brief.product_name,
                      visual_direction="", message_angle=brief.product_name,
                      suggested_platform_usage=list(fallback.audience_brief.platform)),
        CreativeRoute(route_id="B", hook_idea=fallback.market_signal.consumer_pain_point or brief.product_name,
                      visual_direction="", message_angle=brief.product_name,
                      suggested_platform_usage=list(fallback.audience_brief.platform)),
    ]
    return CampaignPlan(
        campaign_id=campaign_id,
        positioning=ProductPositioning(
            main_campaign_angle=brief.key_selling_points[0] if brief.key_selling_points else brief.product_name,
            target_audience=fallback.audience_brief.target_customer,
            key_selling_message=brief.key_selling_points[0] if brief.key_selling_points else brief.product_name,
            product_benefit_hierarchy=list(brief.key_selling_points),
        ),
        creative_routes=routes,
        ab_test_plan=ABTestPlan(
            what_to_test="Góc thông điệp và ngôn ngữ hình",
            route_a="A", route_b="B",
            success_metrics=["CTR", "CVR", "ROAS"],
            expected_learning="Góc nào giữ chân người xem và chuyển đổi tốt hơn",
        ),
    )


# Where each required DTO field may borrow from when its own kind was not
# produced. The DTO's four required images are BP-01 requirements and therefore
# platform-agnostic, while the studio's slots are platform-specific: a Shopee-only
# run yields HERO, SKU_DETAIL, COLLECTION and BANNER but no THUMBNAIL, because
# the thumbnail slot lives in the TikTok kit. Rather than report four perfectly
# good images as an unfilled set, each field falls back along this order.
#
# Substitution is honest, not cosmetic: a marketplace thumbnail genuinely is a
# square product shot, and a hero genuinely can stand in for one. What is never
# done is inventing a path or reusing an image for a field it cannot serve —
# nothing here borrows a wide banner for a square slot.
_IMAGE_FALLBACKS: dict[str, tuple[ImageKind, ...]] = {
    "product_hero_image": (ImageKind.HERO, ImageKind.THUMBNAIL, ImageKind.SKU_DETAIL),
    "sku_detail_image": (ImageKind.SKU_DETAIL, ImageKind.HERO, ImageKind.COLLECTION),
    "campaign_collection_image": (ImageKind.COLLECTION, ImageKind.BUNDLE, ImageKind.HERO),
    "marketplace_thumbnail": (ImageKind.THUMBNAIL, ImageKind.HERO, ImageKind.SKU_DETAIL),
}


def to_image_set(bundle: AssetBundle,
                 url_for: Any = None) -> ProductCollectionImageSet | None:
    """`AssetBundle` -> the DTO's image set, or None when nothing can fill a required field.

    Optional fields are only ever filled by their own kind; the four required
    ones may borrow along `_IMAGE_FALLBACKS`. None is still returned when a
    required field has no candidate at all, because a placeholder string would
    satisfy the type while failing the brief.
    """
    resolve = url_for or (lambda v: v)

    by_kind: dict[ImageKind, str] = {}
    for image in bundle.images:
        by_kind.setdefault(image.kind, resolve(image.local_path or image.url))

    fields: dict[str, str] = {}
    for kind, field in _IMAGE_SLOT_BY_KIND.items():
        if kind in by_kind:
            fields.setdefault(field, by_kind[kind])

    for field in _REQUIRED_IMAGE_FIELDS:
        if field in fields:
            continue
        for candidate in _IMAGE_FALLBACKS.get(field, ()):
            if candidate in by_kind:
                fields[field] = by_kind[candidate]
                break

    if not all(f in fields for f in _REQUIRED_IMAGE_FIELDS):
        return None
    return ProductCollectionImageSet(**fields)


def to_video_asset(bundle: AssetBundle,
                   url_for: Any = None) -> ShortFormVideoAsset | None:
    """`AssetBundle` -> the DTO's video asset, or None when no video was produced.

    The primary video is the 9:16 one if there is one — BP-01 asks for vertical
    and treats other shapes as optional extra cuts, so a square Shopee video
    becomes an `additional_cut` rather than the headline asset.
    """
    resolve = url_for or (lambda v: v)
    if not bundle.videos:
        return None

    primary = next((v for v in bundle.videos if v.aspect_ratio == "9:16"), bundle.videos[0])
    extras = [resolve(v.local_path or v.url) for v in bundle.videos if v is not primary]
    extras += [resolve(c.local_path) for c in primary.cutdowns]

    return ShortFormVideoAsset(
        generated_video_urls=[resolve(primary.local_path or primary.url)],
        format=primary.aspect_ratio,
        duration=f"{primary.duration_sec:.0f}s",
        additional_cuts=extras,
    )
