"""
byteplus_ark.py — Script mẫu gọi API BytePlus ModelArk cho đề BP-01.
(Đã test chạy OK ngày 21/08/2026 — region ap-southeast.)

── CÀI ĐẶT ─────────────────────────────────────────────
    pip install requests
    Tạo file .env ở thư mục gốc repo với dòng:  ARK_API_KEY=ark-xxxxx
    (file .env được load tự động, không cần export/python-dotenv;
     có thể vẫn dùng export ARK_API_KEY=... nếu muốn, biến môi trường
     có sẵn sẽ được giữ nguyên, không bị .env ghi đè)

── CHẠY THỬ (smoke test cả 3 model) ────────────────────
    python byteplus_ark.py
    # -> in kết quả LLM, lưu ảnh + video vào thư mục ./ark_out/

── 3 MODEL BP-01 ───────────────────────────────────────
    Seedream 5.0 Pro (ảnh)   -> dola-seedream-5-0-pro-260628   [BẮT BUỘC]
    Seedance 2.5     (video) -> dreamina-seedance-2-5-260628   [BẮT BUỘC]
    Seed 2.1         (LLM)   -> dola-seed-2-1-turbo-260628     [tuỳ chọn]
"""

import os
import time
import pathlib
import requests


def _load_dotenv_if_present() -> None:
    """Minimal built-in .env loader (repo root, next to this file) - no
    python-dotenv dependency needed. Does not overwrite variables already
    set in the real environment."""
    env_path = pathlib.Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv_if_present()

BASE = os.environ.get("ARK_BASE_URL", "https://ark.ap-southeast.bytepluses.com/api/v3")
KEY = os.environ.get("ARK_API_KEY")
if not KEY:
    raise SystemExit("Thiếu ARK_API_KEY. Chạy:  export ARK_API_KEY='ark-...'")
HEAD = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}

LLM = "dola-seed-2-1-turbo-260628"
IMAGE = "dola-seedream-5-0-pro-260628"
VIDEO = "dreamina-seedance-2-5-260628"

OUT = pathlib.Path(__file__).parent / "ark_out"
OUT.mkdir(exist_ok=True)


def _post(path, payload, timeout=180):
    r = requests.post(f"{BASE}{path}", headers=HEAD, json=payload, timeout=timeout)
    if not r.ok:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text}")
    return r.json()


def list_models():
    """Liệt kê model mà key được phép gọi (tiện debug 403/404)."""
    r = requests.get(f"{BASE}/models", headers=HEAD, timeout=30)
    r.raise_for_status()
    return [m["id"] for m in r.json()["data"]]


# ── 1) LLM: chiến lược / viết copy ──────────────────────  ✅ đã test
def chat(prompt, system=None, max_tokens=1024):
    msgs = ([{"role": "system", "content": system}] if system else []) + \
           [{"role": "user", "content": prompt}]
    d = _post("/chat/completions", {"model": LLM, "messages": msgs, "max_tokens": max_tokens})
    return d["choices"][0]["message"]["content"]


# ── 2) ẢNH: text-to-image ───────────────────────────────  ✅ đã test (2048x2048)
def text_to_image(prompt, size="2048x2048"):
    d = _post("/images/generations", {"model": IMAGE, "prompt": prompt, "size": size})
    return d["data"][0]["url"]          # ⚠️ URL hết hạn 24h -> tải về lưu (dùng download())


# ── 2b) BRAND LOCK: image-to-image (giữ đúng sản phẩm) ──  ⚠️ param theo doc, xác nhận khi chạy
def image_to_image(prompt, image, size="2048x2048"):
    # image = URL công khai hoặc "data:image/jpeg;base64,...."
    d = _post("/images/generations", {"model": IMAGE, "prompt": prompt, "image": image, "size": size})
    return d["data"][0]["url"]


# ── 3) VIDEO: async (tạo task -> poll) ──────────────────  ✅ đã test (t2v)
def create_video(prompt, image_url=None, resolution="720p", ratio="9:16", duration=5):
    text = f"{prompt} --resolution {resolution} --ratio {ratio} --duration {duration}"
    content = [{"type": "text", "text": text}]
    if image_url:   # ⚠️ image-to-video (Brand Lock video) — theo doc, xác nhận khi chạy
        content.insert(0, {"type": "image_url", "image_url": {"url": image_url}})
    d = _post("/contents/generations/tasks", {"model": VIDEO, "content": content}, timeout=60)
    return d["id"]                       # -> "cgt-..."


def wait_video(task_id, every=15, timeout=600):
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = requests.get(f"{BASE}/contents/generations/tasks/{task_id}", headers=HEAD, timeout=30)
        r.raise_for_status()
        d = r.json()
        st = d.get("status")
        print("   video status:", st)
        if st == "succeeded":
            return d["content"]["video_url"]     # ⚠️ hết hạn 48h
        if st in ("failed", "cancelled"):
            raise RuntimeError(d)
        time.sleep(every)
    raise TimeoutError(task_id)


def download(url, filename):
    """Tải asset về ./ark_out/ (vì URL ký & hết hạn)."""
    p = OUT / filename
    with requests.get(url, stream=True, timeout=180) as r:
        r.raise_for_status()
        p.write_bytes(r.content)
    return p


# ── BP-01 TESTCASE SCENARIO: F&B "Fizzy Roots" sparkling tea ───
#    Cùng scenario với backend/tests/fixtures/bp01_qa_checklist_testcase.json
#    (campaign_id = "camp-bp01-fnb-001"). Prompt dưới đây map trực tiếp vào
#    từng ImageKind / VideoAsset mà gen_assets_agent.py cần sinh ra, để khi
#    nối API thật thay cho mock, output vẫn khớp field "url" trong fixture
#    (chỉ cần đổi biến FNB_OUT thành đường dẫn thật sau khi download()).
#
#    Cách plug vào gen_assets_agent.py:
#      1. Thay các dòng `ImageAsset(kind=..., url=f"mock://...")` bằng:
#           url = download(text_to_image(FNB_IMAGE_PROMPTS[kind]), f"{kind.value}.jpg")
#      2. Thay VideoAsset url bằng:
#           task_id = create_video(FNB_VIDEO_PROMPTS["A"], ratio="9:16", duration=20)
#           url = download(wait_video(task_id), "route_A.mp4")
#      3. Copy title/description/bullets có thể lấy từ chat() với
#         FNB_COPY_SYSTEM_PROMPT + campaign_input làm context (xem
#         run_qa_check_live.py::generate_assets_live cho ví dụ prompt JSON).

FNB_OUT = OUT / "bp01_fnb"
FNB_OUT.mkdir(exist_ok=True)

FNB_BRAND_STYLE = (
    "brand colors deep teal #0E7C61 and warm yellow #F4D35E, playful energetic "
    "Gen Z tone, clean e-commerce product photography, no added text/watermark"
)

FNB_IMAGE_PROMPTS = {
    "product_hero_image": (
        f"a sparkling tea can labeled 'Fizzy Roots Hibiscus Ginger', condensation droplets, "
        f"centered hero product shot on a soft gradient studio background, {FNB_BRAND_STYLE}"
    ),
    "sku_detail_image": (
        f"macro close-up on the can label of a sparkling tea, showing hibiscus flower and ginger "
        f"root ingredient icons and nutrition facts area, sharp focus, {FNB_BRAND_STYLE}"
    ),
    "campaign_collection_image": (
        f"flat-lay of a sparkling tea can surrounded by fresh hibiscus flowers and ginger root, "
        f"overhead shot, e-commerce campaign collection image, {FNB_BRAND_STYLE}"
    ),
    "marketplace_thumbnail": (
        f"square marketplace cover image of a sparkling tea can, bold and eye-catching for a "
        f"Shopee/TikTok Shop listing thumbnail, {FNB_BRAND_STYLE}"
    ),
    "promotion_banner": (
        f"e-commerce promotion banner for 'Buy 4 Get 1 Free launch week', sparkling tea can "
        f"prominently displayed, wide banner layout, {FNB_BRAND_STYLE}"
    ),
}

FNB_VIDEO_PROMPTS = {
    "A": (
        "POV opening on a hand reaching for a soft drink, then swapping it for a Fizzy Roots "
        "hibiscus ginger sparkling tea can, can cracks open with a fizz close-up, quick energetic "
        "cuts, Gen Z UGC style, natural daylight, ends on product hero shot"
    ),
    "B": (
        "macro shots of real hibiscus flowers and ginger root transitioning into a pour of "
        "sparkling tea into a glass with visible bubbles, clean studio gradient background "
        "matching brand teal and yellow, ends on product hero shot"
    ),
}


def generate_fnb_testcase_assets(route: str = "A", duration: int = 20) -> dict:
    """Sinh đủ asset cho scenario BP-01 F&B testcase bằng API thật.

    Trả về dict {image_kind_or_'video': local_path} — dùng để thay các
    `url=f"mock://..."` trong gen_assets_agent.py hoặc để tự tay đối chiếu
    với asset_bundle_happy_case trong bp01_qa_checklist_testcase.json.
    Gọi tốn tiền/token thật — chỉ chạy khi cần kiểm thử end-to-end.
    """
    saved: dict[str, pathlib.Path] = {}

    for kind, prompt in FNB_IMAGE_PROMPTS.items():
        size = "1080x1080" if kind == "marketplace_thumbnail" else "2048x2048"
        url = text_to_image(prompt, size=size)
        saved[kind] = download(url, f"bp01_fnb/{kind}.jpg")

    video_prompt = FNB_VIDEO_PROMPTS.get(route, FNB_VIDEO_PROMPTS["A"])
    task_id = create_video(video_prompt, resolution="720p", ratio="9:16", duration=duration)
    video_url = wait_video(task_id)
    saved["video"] = download(video_url, f"bp01_fnb/route_{route}.mp4")

    return saved


if __name__ == "__main__":
    print("1) LLM  (Seed 2.1) ...")
    print("   ->", chat("Trả lời đúng 1 từ: OK"))

    print("2) ẢNH  (Seedream 5.0 Pro) ...")
    img_url = text_to_image(
        "a red ceramic coffee mug on a wooden table, e-commerce product photo, soft studio light"
    )
    print("   -> đã lưu:", download(img_url, "sample_image.jpg"))

    print("3) VIDEO (Seedance 2.5) — chờ ~2 phút ...")
    vid_url = wait_video(create_video(
        "a red ceramic coffee mug slowly rotating on a wooden table, product ad, studio light"
    ))
    print("   -> đã lưu:", download(vid_url, "sample_video.mp4"))

    print("\nXong! Xem thư mục:", OUT)

    # Bỏ comment dòng dưới để sinh full asset set cho BP-01 F&B testcase
    # (5 ảnh + 1 video, tốn API call thật):
    # print("\n4) BP-01 F&B testcase assets ...")
    # print(generate_fnb_testcase_assets())
