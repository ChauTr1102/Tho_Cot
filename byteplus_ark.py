"""
byteplus_ark.py — Script mẫu gọi API BytePlus ModelArk cho đề BP-01.
(Đã test chạy OK ngày 21/08/2026 — region ap-southeast.)

── CÀI ĐẶT ─────────────────────────────────────────────
    pip install requests
    export ARK_API_KEY='ark-xxxxx'      # KHÔNG hardcode key vào file / KHÔNG commit
    # (hoặc tạo file .env rồi bỏ comment 2 dòng load_dotenv bên dưới)

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

# from dotenv import load_dotenv; load_dotenv()   # bật nếu dùng file .env

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
