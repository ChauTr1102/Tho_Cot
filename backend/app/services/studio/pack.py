"""
Packaging a finished campaign as a zip a seller can actually use.

The filenames are the deliverable. Someone downloads this, opens it beside a
Shopee upload form at eleven at night, and has to know which file goes in which
box without opening any of them. So names carry the marketplace, the slot and
the shape — `shopee/main_1x1.jpg`, `tiktok_shop/video_9x16_20s.mp4` — and the
grouping is by marketplace, because that is the order the work gets done in.

MANIFEST.md is not decoration either. BP-01's submission checklist asks for a
short explanation of model usage, and a generated manifest answers it with what
actually happened on this run — which model produced each file, which images
were the brand's own photographs rather than generated, and what the visual QA
pass found. Written by hand it would be a claim; generated, it is a record.
"""
from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Iterable

from app.schemas.campaign import AssetBundle, AssetOrigin, ImageAsset, VideoAsset

ORIGIN_LABEL = {
    AssetOrigin.REUSE: "ảnh thật của thương hiệu",
    AssetOrigin.REMIX: "image-to-image từ ảnh thật",
    AssetOrigin.GENERATE: "dựng mới, neo theo ảnh sản phẩm",
}


def _ratio_tag(width: int, height: int) -> str:
    """A filename-safe shape tag. Approximate on purpose — 1638x2048 is 4:5."""
    if not width or not height:
        return "img"
    ratio = width / height
    for tag, value in (("1x1", 1.0), ("9x16", 0.5625), ("4x5", 0.8),
                       ("2x1", 2.0), ("16x9", 1.7778)):
        if abs(ratio - value) < 0.06:
            return tag
    return f"{width}x{height}"


def _image_name(image: ImageAsset) -> str:
    slot = (image.slot or image.kind.value).strip().lower().replace(" ", "_")
    # The platform is already the folder, so repeating it in the filename is noise.
    for prefix in ("shopee_", "tiktok_shop_", "tiktok_"):
        if slot.startswith(prefix):
            slot = slot[len(prefix):]
            break
    return f"{slot}_{_ratio_tag(image.width, image.height)}.jpg"


def _video_name(video: VideoAsset, suffix: str = "") -> str:
    shape = video.aspect_ratio.replace(":", "x")
    seconds = f"{video.duration_sec:.0f}s" if video.duration_sec else "video"
    return f"video_{shape}_{seconds}{suffix}.mp4"


def _folder(platform) -> str:
    return platform.value if platform is not None else "shared"


def build_manifest(bundle: AssetBundle, files: list[tuple[str, str]]) -> str:
    """The record that doubles as BP-01's model-usage explanation."""
    reused = [i for i in bundle.images if i.origin is AssetOrigin.REUSE]
    generated = [i for i in bundle.images if i.origin is not AssetOrigin.REUSE]
    flagged = [i for i in bundle.images if i.qa_passed is False]

    lines = [
        f"# Bộ kit — {bundle.campaign_id}",
        "",
        f"{len(bundle.images)} ảnh · {len(bundle.videos)} video · "
        f"{len(reused)} ô dùng ảnh thật của thương hiệu",
        "",
        "## Model đã dùng",
        "",
        "| Việc | Model | Vì sao |",
        "|---|---|---|",
        "| Ảnh sản phẩm, poster, keyframe | `dola-seedream-5-0-pro-260628` "
        "(Seedream 5.0 Pro) | Bắt buộc theo đề. Nhận ảnh sản phẩm thật làm "
        "reference nên giữ đúng bao bì, và render chữ tiếng Việt có dấu chính xác. |",
        "| Video ngắn | `dreamina-seedance-2-5-260628` (Seedance 2.5) | Bắt buộc "
        "theo đề. Tỉ lệ video bám theo ảnh first-frame, nên khung dọc/vuông có "
        "được mà không phải cắt. |",
        "| Lồng tiếng | `seed-audio-1.0` | Đọc tiếng Việt đúng. Không dùng audio "
        "của Seedance vì model đó viết sai dấu tiếng Việt. |",
        "| Đạo diễn chiến dịch, soi lỗi chữ | `dola-seed-2-1-turbo-260628` | "
        "Model duy nhất key này gọi được cho cả văn bản lẫn thị giác. |",
        "",
        "## Ba đường một asset có thể đi",
        "",
    ]
    for origin, label in ORIGIN_LABEL.items():
        count = sum(1 for i in bundle.images if i.origin is origin)
        lines.append(f"- **{origin.value}** — {label}: {count} ảnh")
    lines += [
        "",
        "Chỗ nào người mua soi sản phẩm trước khi trả tiền thì dùng ảnh thật; chỗ "
        "nào người xem đang lướt thì dựng mới. Ảnh AI sai một chi tiết là hàng trả về.",
        "",
        "## File trong gói",
        "",
        "| Đường dẫn | Nguồn | Chữ trên ảnh |",
        "|---|---|---|",
    ]

    by_name = {n: i for n, i in files}
    for name, key in files:
        image = next((i for i in bundle.images if (i.local_path or i.url) == key), None)
        if image is not None:
            origin = image.origin.value if image.origin else "—"
            texts = ", ".join(image.text_rendered[:3]) or "—"
            lines.append(f"| `{name}` | {origin} | {texts} |")
        else:
            lines.append(f"| `{name}` | video | — |")

    if flagged:
        lines += ["", "## Cảnh báo từ vòng kiểm chữ", ""]
        for image in flagged:
            lines.append(f"- `{image.slot or image.kind.value}`: "
                         f"{'; '.join(image.qa_notes[:3]) or 'chữ không khớp'}")

    fallbacks = [s for v in bundle.videos for s in v.shots if s.used_fallback]
    if fallbacks:
        lines += ["", "## Shot phải dùng đường lùi", ""]
        for shot in fallbacks:
            lines.append(f"- shot {shot.index} ({shot.role}): "
                         f"{shot.fallback_reason or 'không rõ'}")

    del by_name, generated
    return "\n".join(lines) + "\n"


def build_zip(bundle: AssetBundle, out_path: str | Path) -> str:
    """Write the campaign to a zip grouped by marketplace. Returns the path."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    files: list[tuple[str, str]] = []

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for image in bundle.images:
            source = Path(image.local_path or image.url)
            if not source.is_file():
                continue
            name = f"{_folder(image.platform)}/{_image_name(image)}"
            archive.write(source, name)
            files.append((name, str(source)))

        for video in bundle.videos:
            source = Path(video.local_path or video.url)
            if source.is_file():
                name = f"{_folder(video.platform)}/{_video_name(video)}"
                archive.write(source, name)
                files.append((name, str(source)))
            for cut in video.cutdowns:
                cut_source = Path(cut.local_path)
                if cut_source.is_file():
                    name = f"{_folder(video.platform)}/{_video_name(video, f'_{cut.label}')}"
                    archive.write(cut_source, name)
                    files.append((name, str(cut_source)))

        archive.writestr("MANIFEST.md", build_manifest(bundle, files))

    return str(out)


def zip_names(bundle: AssetBundle) -> Iterable[str]:
    """The names `build_zip` would write, without writing anything.

    Useful for showing a seller what they are about to download.
    """
    for image in bundle.images:
        yield f"{_folder(image.platform)}/{_image_name(image)}"
    for video in bundle.videos:
        yield f"{_folder(video.platform)}/{_video_name(video)}"
        for cut in video.cutdowns:
            yield f"{_folder(video.platform)}/{_video_name(video, f'_{cut.label}')}"
