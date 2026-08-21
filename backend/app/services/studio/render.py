"""
Image rendering: the hero anchor, the kit images, and the reuse path.

Three ways an image reaches the kit, and the choice between them is the
studio's central commercial judgement rather than a performance tweak:

  reuse_item   the brand's own photograph, cropped and resized. Used where a
               shopper inspects the product before paying. Two reasons: an
               invented pixel there means a mismatch with the parcel and a
               return, and generation redraws the product's own packaging --
               measured on a real COSRX bottle, the vertical wordmark came
               back reading COSRA instead of COSRX, reproducibly, while the
               same string set horizontally was perfect.

  render_hero  one image generated from the real product photo, art-directed
               and QA'd first. It becomes the *style anchor*.

  render_item  everything else, generated from TWO references -- the product
               photo and the hero. Reference 1 fixes what the product is,
               reference 2 fixes how the scene looks. That second reference is
               the whole mechanism by which eight images look like one shoot.

Reference order matters and the API is unforgiving about shape: one reference
goes in `image` as a bare string, two or more as a list. `reference_images`
returns HTTP 200 and is silently ignored -- see ark.generate_image.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from PIL import Image

from app.schemas.campaign import AssetOrigin
from app.services.studio import ark, prompts
from app.services.studio.config import studio_settings


@dataclass
class RenderedImage:
    """One finished image, with enough provenance to explain it to a judge."""
    local_path: str
    width: int
    height: int
    origin: AssetOrigin
    prompt: str = ""
    texts: list[str] = field(default_factory=list)
    source_photo: str | None = None
    gen_seconds: float = 0.0
    qa_passed: bool | None = None
    qa_notes: list[str] = field(default_factory=list)
    attempts: int = 1


def _parse_size(size: str) -> tuple[int, int]:
    """"2048x2048" -> (2048, 2048). Falls back to square 2048 for names like "2K"."""
    if "x" in size.lower():
        w, _, h = size.lower().partition("x")
        try:
            return int(w), int(h)
        except ValueError:
            pass
    return 2048, 2048


def _save(data: bytes, out_dir: Path, name: str) -> tuple[str, int, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.jpg"
    path.write_bytes(data)
    with Image.open(path) as im:
        w, h = im.size
    return str(path), w, h


def reuse_item(item, out_dir: str | Path) -> RenderedImage:
    """Crop and resize one of the brand's real photographs to fill a slot.

    No API call, no generation, no risk of a redrawn label. Centre-crops to the
    slot's aspect ratio rather than stretching, because a distorted product is
    worse than a tighter frame.
    """
    if not item.source_photo:
        raise ValueError(f"{item.slot_id}: REUSE requires a source photo")

    started = time.time()
    target_w, target_h = _parse_size(item.size)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(item.source_photo) as im:
        im = im.convert("RGB")
        src_w, src_h = im.size
        target_ratio = target_w / target_h
        # widest / tallest box with the target ratio that still fits inside
        if src_w / src_h > target_ratio:
            crop_w, crop_h = int(src_h * target_ratio), src_h
        else:
            crop_w, crop_h = src_w, int(src_w / target_ratio)
        left, top = (src_w - crop_w) // 2, (src_h - crop_h) // 2
        im = im.crop((left, top, left + crop_w, top + crop_h))
        im = im.resize((target_w, target_h), Image.LANCZOS)
        path = out_dir / f"{item.slot_id}.jpg"
        im.save(path, quality=92)

    return RenderedImage(
        local_path=str(path), width=target_w, height=target_h,
        origin=AssetOrigin.REUSE, source_photo=item.source_photo,
        gen_seconds=time.time() - started,
    )


def render_hero(item, spine, product_photo: str, label_text: Sequence[str],
                out_dir: str | Path, extra_instruction: str = "") -> RenderedImage:
    """Render the style anchor from the real product photo alone.

    Only one reference here: there is no hero yet to anchor to.
    """
    prompt = prompts.build_image_prompt(
        scene=item.scene, spine=spine, texts=item.texts,
        label_text=label_text, ratio=item.ratio, rule=item.rule,
    )
    if extra_instruction:
        prompt = f"{prompt}\n\n{extra_instruction}"

    started = time.time()
    data = ark.generate_image(prompt, item.size, refs=[ark.to_data_uri(product_photo)])
    path, w, h = _save(data, Path(out_dir), item.slot_id)
    return RenderedImage(
        local_path=path, width=w, height=h, origin=AssetOrigin.GENERATE,
        prompt=prompt, texts=[t for _, t in item.texts],
        source_photo=product_photo, gen_seconds=time.time() - started,
    )


def render_item(item, spine, product_photo: str | None, hero_path: str | None,
                label_text: Sequence[str], out_dir: str | Path,
                extra_instruction: str = "", for_video: bool = False) -> RenderedImage:
    """Render a kit image anchored to both the product and the hero.

    Reference 1 is the product, reference 2 is the hero. Order is contractual:
    swapping them makes the hero's bottle the subject and the real product a
    style hint, which is exactly backwards.
    """
    refs: list[str] = []
    if product_photo:
        refs.append(ark.to_data_uri(product_photo))
    if hero_path:
        refs.append(ark.to_data_uri(hero_path))

    prompt = prompts.build_image_prompt(
        scene=item.scene, spine=spine, texts=item.texts,
        label_text=label_text, ratio=item.ratio, rule=item.rule,
        for_video=for_video,
    )
    if extra_instruction:
        prompt = f"{prompt}\n\n{extra_instruction}"

    started = time.time()
    data = ark.generate_image(prompt, item.size, refs=refs or None)
    path, w, h = _save(data, Path(out_dir), item.slot_id)
    return RenderedImage(
        local_path=path, width=w, height=h, origin=item.origin,
        prompt=prompt, texts=[t for _, t in item.texts],
        source_photo=product_photo, gen_seconds=time.time() - started,
    )


def render_poster(slot_id: str, background: str, spine, texts, label_text: Sequence[str],
                  ratio: str, size: str, product_photo: str | None,
                  hero_path: str | None, out_dir: str | Path,
                  extra_instruction: str = "") -> RenderedImage:
    """Render a sale poster: flat ground, display headline, badges, a CTA button.

    Same two references as `render_item` — the product fixes what it is, the hero
    fixes the light — but a different prompt, because a poster is graphic design
    laid over a photographed product rather than a photograph with a caption.
    """
    refs: list[str] = []
    if product_photo:
        refs.append(ark.to_data_uri(product_photo))
    if hero_path:
        refs.append(ark.to_data_uri(hero_path))

    prompt = prompts.build_poster_prompt(
        background=background, spine=spine, texts=texts,
        label_text=label_text, ratio=ratio,
    )
    if extra_instruction:
        prompt = f"{prompt}\n\n{extra_instruction}"

    started = time.time()
    data = ark.generate_image(prompt, size, refs=refs or None)
    path, w, h = _save(data, Path(out_dir), slot_id)
    return RenderedImage(
        local_path=path, width=w, height=h, origin=AssetOrigin.GENERATE,
        prompt=prompt, texts=[t for _, t in texts],
        source_photo=product_photo, gen_seconds=time.time() - started,
    )


def size_for(ratio: str) -> str:
    """The Seedream size string for a frame shape."""
    return {
        "1:1": studio_settings.IMAGE_SIZE_SQUARE,
        "9:16": studio_settings.IMAGE_SIZE_PORTRAIT,
        "4:5": studio_settings.IMAGE_SIZE_FEED,
        "2:1": studio_settings.IMAGE_SIZE_LANDSCAPE,
    }.get(ratio, studio_settings.IMAGE_SIZE_SQUARE)


def keyframe_size(ratio: str) -> str:
    """Pick the Seedream size that produces a given video aspect ratio.

    Seedance's output ratio follows its first frame, so the keyframe's shape is
    how a platform-native video ratio is obtained -- there is no cropping step.
    """
    return {
        "9:16": studio_settings.IMAGE_SIZE_PORTRAIT,
        "1:1": studio_settings.IMAGE_SIZE_SQUARE,
        "4:5": studio_settings.IMAGE_SIZE_FEED,
        "2:1": studio_settings.IMAGE_SIZE_LANDSCAPE,
    }.get(ratio, studio_settings.IMAGE_SIZE_SQUARE)
