# Asset Studio — module sinh ảnh + video

> **Chủ:** Châu · **Đề:** BP-01 BytePlus — Commerce Campaign Launch Copilot
> **Trạng thái:** thiết kế đã chốt, mọi khả năng API đã đo thực nghiệm ngày 21/08/2026.
> **Ai cần đọc gì:** Minh+Nhật → mục *Hợp đồng ①* · Duy → mục *Hợp đồng ②* · Nam → mục *ảnh sản phẩm*.

---

## 1. Module này làm gì

Nhận **một gói brief đã đầy đủ** (positioning, creative route, copy, ảnh sản phẩm thật) và trả về
**bộ asset hoàn chỉnh, sẵn đăng, đúng chuẩn từng sàn** — ảnh + video + cutdown.

Không nghiên cứu thị trường, không viết chiến lược, không viết copy. Chỉ biến chữ thành hình.

Ba yêu cầu chất lượng, theo đúng thứ tự ưu tiên:

1. **Nhất quán** — mọi asset trong một chiến dịch phải trông như cùng một ê-kíp chụp trong cùng một buổi
2. **Chuyên nghiệp** — nhìn không ra là AI làm
3. **Bản địa theo sàn** — TikTok khác Shopee khác Amazon, không phải resize

---

## 2. Sự thật đã ĐO — đừng đoán lại

Mọi con số dưới đây đo bằng thực nghiệm trên key BTC, ngày 21/08/2026.
Script trong `probe_*.py` (repo BHN), log trong `probe_out/`.

### Khả năng

| Khả năng | Kết quả | Payload đúng |
|---|---|---|
| Seedream text→image | ✅ 2048² và 1440×2560 | `size`, `watermark:false` |
| Seedream **image→image** (Brand Lock) | ✅ giữ đúng sản phẩm | `image: "data:image/jpeg;base64,…"` |
| Seedream **2 ảnh reference** | ✅ dùng **cả hai** | `image: [ref_sản_phẩm, ref_phong_cách]` |
| Seedream vẽ **chữ tiếng Việt có dấu** | ✅ chuẩn, kể cả `Ễ Ậ Ể Ụ Ồ` | phải ghi `reading exactly "…"` |
| Seedance text→video | ✅ 720×1280, **có audio native** | `--ratio 9:16 --duration N` |
| Seedance **image→video** (Brand Lock) | ✅ nhận **data URI** trực tiếp | `--ratio adaptive` ⚠️ **BẮT BUỘC** |
| Seedance duration | ✅ 5s · 10s · 15s | |
| **Chữ trong ảnh sống sót qua i2v** | ✅ nguyên vẹn, không méo | |
| **Tỉ lệ video = tỉ lệ ảnh first-frame** | ✅ ảnh vuông → video 960×960 | |
| Seed Audio TTS tiếng Việt | ✅ 48kHz, mức âm chuẩn | host riêng + header `X-Api-Key` |
| **Seed 2.1 Turbo NHÌN ĐƯỢC ẢNH** | ✅ | `/chat/completions` + `image_url` |
| ffmpeg nối clip Seedance | ✅ `-c copy` tức thì | mọi clip cùng 720×1280/24fps/h264/aac |
| DeepSeek `web_search` | ❌ 403 | key không mở |
| Mọi model vision khác | ❌ 403/404 | chỉ Seed 2.1 nhìn được |

### Thời gian

| Việc | Thời gian |
|---|---|
| 1 ảnh Seedream | 35–60s |
| **10 ảnh đồng thời** | **44s** — song song hoàn toàn ✅ |
| 1 clip 5s | 134–543s ⚠️ **phương sai rất lớn** |
| 4 clip đồng thời | 543s (bị clip chậm nhất kéo) |
| clip 10s / 15s | 266s / 307s |
| QA vision, ảnh 1024² | 41–109s |
| ffmpeg nối `-c copy` | tức thì |

**Một route ≈ 6 phút nếu may, ≈ 12 phút nếu xui.** Demo là video quay sẵn nên không sao.

### Model ID

```
ảnh    dola-seedream-5-0-pro-260628      ep-m-20260821110659-llx2f
video  dreamina-seedance-2-5-260628      ep-m-20260821091145-n28xt
LLM    dola-seed-2-1-turbo-260628        ep-m-20260821111024-tq7zn   ← cũng là model vision
TTS    seed-audio-1.0   @ https://voice.ap-southeast-1.bytepluses.com/api/v3/tts/create
```
Dự phòng nếu 2.5 chậm/lỗi: `seedance-1-5-pro-251215`, `dreamina-seedance-2-0-fast-260128` (bản nhanh, dựng nháp).
Có thể hữu ích: `seededit-3-0-i2i-250628` (sửa ảnh thay vì gen lại).

---

## 3. Luật vàng

> **Không chừa chỗ trống nào cho model tự nghĩ.**

Đo được: mọi chuỗi ghi rõ trong prompt → render đúng 100%, kể cả dấu tiếng Việt khó nhất.
Mọi chuỗi để model tự bịa → hỏng: `LUNAÁIRA`, `EFFFECTIVE`, ba tên brand ma trong bốn ảnh.

Hệ quả: prompt phải liệt kê **toàn bộ** chữ xuất hiện trong khung — headline, sub, badge, CTA,
**và cả chữ trên nhãn sản phẩm**. Chỗ nào bỏ trống, model điền rác vào đó.

---

## 4. Ba tầng nhất quán

| Tầng | Nghĩa | Cơ chế |
|---|---|---|
| **L1** danh tính sản phẩm | đúng cái chai đó ở mọi khung | i2i với ảnh sản phẩm thật |
| **L2** art direction | cùng ánh sáng / palette / chất liệu / ống kính | **style spine** + **HERO làm ref neo** |
| **L3** chữ & layout | font, vị trí, nội dung | Seedream vẽ vào ảnh, ảnh làm first-frame video |

**Style spine** — mỗi route sinh **một** mô tả phong cách, nhét vào đuôi **mọi** prompt của route đó:

```
route A (science-led)  85mm macro · khuếch tán lạnh từ trái · travertine ướt · neutral, low contrast, airy
route B (testimonial)  35mm handheld · nắng cửa sổ ấm · bàn gỗ đời thường · ấm, contrast cao, hơi grain
```

Hai spine **cố tình khác nhau** — A/B test mà hai route nhìn giống nhau thì test vô nghĩa.
Nhất quán *trong* route, tương phản *giữa* route.

**HERO làm ref neo:** ảnh hero được art-direct kỹ nhất và duyệt trước. Sau đó mọi asset còn lại
gen bằng `image: [ảnh_sản_phẩm, HERO]` → thừa hưởng **cả** danh tính sản phẩm **lẫn** art direction.

---

## 5. Dây chuyền 5 chặng

```
CampaignBrief (Minh+Nhật)  +  ảnh sản phẩm thật (Nam)
        │
 ① DIRECT ─ thuần logic, KHÔNG gọi API
    route → StyleSpine · Storyboard (4 shot Hook→Product→Benefit→CTA) · AssetPlan
        │
 ② ANCHOR ─ HERO trước, chặn đường                                    ~60s
    Seedream i2i(ảnh_sp) + spine → HERO → [QA gate] → retry ≤2
        │
 ③ FAN-OUT ─ song song                                                ~90s
    ảnh sàn       : i2i([ảnh_sp, HERO]) × N slot
    keyframe shot : i2i([ảnh_sp, HERO]) × 4   ← CHỮ được vẽ vào đây
        │
 ④ MOTION ─ song song                                            ~230-540s
    Seedance i2v(keyframe, --ratio adaptive) × 4
    Seed Audio TTS × N lời VO
        │
 ⑤ ASSEMBLE ─ ffmpeg                                                  ~30s
    nối shot (-c copy) → master + VO + phụ đề + nhạc
    cutdown: 15s · 30s · theo tỉ lệ từng sàn
        │
   AssetPack JSON + file → Duy
```

**Xuống cấp mềm:** mỗi shot có deadline (300s). Quá hạn/lỗi → **không bỏ shot**, lấy chính keyframe
đã Brand Lock của shot đó cho ffmpeg đẩy Ken Burns 5s rồi ghép vào đúng chỗ. Video luôn ra đủ độ dài,
đúng cấu trúc, không bao giờ treo.

---

## 6. Ma trận sàn

Không resize. Mỗi sàn có ngôn ngữ hình riêng — **cùng spine, khác cách kể**.
Tỉ lệ video lấy theo tỉ lệ ảnh first-frame nên video cũng bản địa hoá được, không tốn thêm.

| Sàn | Slot | Tỉ lệ | Ngôn ngữ hình | Ràng buộc cứng |
|---|---|---|---|---|
| TikTok Shop | video ad | 9:16 | thô, cầm tay, UGC, chữ to đập mặt | né UI phải 15% + đáy 20% · hook ≤3s |
| TikTok Shop | cover | 9:16 | như trên | |
| Shopee | ảnh chính | 1:1 | catalogue sạch, thông tin rõ | **nền trắng thuần** |
| Shopee | SKU detail | 1:1 | macro chất liệu, cận nhãn | |
| Shopee | collection | 1:1 | bày combo / bundle | |
| Shopee | banner KM | 2:1 | badge giá to | |
| FB / IG | feed | 4:5 | editorial, tĩnh, sang | |

Bốn ảnh **đề bắt buộc** (hero · SKU · collection · thumbnail) nằm gọn trong ma trận này.

---

## 7. QA gate

**Nguyên tắc: model chỉ CHÉP chữ, code mới PHÁN.**
Đo được: giao phán xét cho model thì ảnh đúng hoàn toàn vẫn bị FAIL vì nó coi chữ trên nhãn chai là "chữ lạ".

**Cách soi:** ảnh 2048² **cắt thành 4 mảnh 1024²**, soi song song bằng Seed 2.1.
Gửi nguyên ảnh 2048² thì timeout; thu nhỏ về 1024² thì model *tự sửa lỗi hộ* (`EFFFECTIVE` → `EFFECTIVE`)
và gate mất tác dụng. Cắt mảnh giữ được cả tốc độ lẫn độ tinh.

| # | Kiểm | Ai làm | Bắt lỗi gì |
|---|---|---|---|
| C1 | sản phẩm khớp ref | vision | i2i trôi hình |
| C2 | **mọi chuỗi mong đợi có mặt, đúng từng ký tự** | vision chép → **code so** | sai dấu, `EFFFECTIVE` |
| C3 | có chữ lạ giống tên brand bịa | vision chép → **code so** | `LUNAÁIRA` |
| C4 | claim cấm | **code** so với `forbidden_claims` | |
| C5 | vùng an toàn | **code** so toạ độ | chữ lọt dưới UI TikTok |

Danh sách chuỗi mong đợi = **copy marketing ∪ chữ trên nhãn sản phẩm**.
Thiếu vế sau là báo động giả liên tục.

Trượt → gen lại kèm prompt sửa, tối đa 2 lần.

**Giao với Minh+Nhật:** họ giữ checklist **nội dung/claim**, Studio giữ checklist **hình**.
Studio xuất kết quả C1–C5 ra JSON để checklist của họ nuốt vào — không ai làm trùng ai.

---

## 8. Chống rớt mạng

DNS đã chết một lần lúc 12:00 và làm hỏng nguyên một phép đo 200 giây. Wifi hội trường sẽ tệ hơn.

- Mọi call bọc **retry + backoff** (mẫu sẵn trong `probe_dur.py::resilient`)
- **`task_id` video ghi xuống đĩa NGAY khi tạo** → mất mạng vẫn poll lại được, không mất công render
- Poll timeout **≥90s** (30s là quá ngắn, đã bị `Read timed out`)
- URL ký hết hạn (ảnh 24h, video 48h) → **tải về ngay**, tuyệt đối không lưu URL làm nguồn
- Cache theo hash nội dung → chạy lại cùng brief trả kết quả tức thì

---

## 9. HỢP ĐỒNG ① — Minh + Nhật → Studio

```jsonc
{
  "campaign_id": "cosrx-1111",
  "language": "vi",

  "product": {
    "name": "COSRX Advanced Snail 96 Mucin Power Essence (100ml)",
    "category": "Skincare / Facial Essence",
    "price": "390.000đ",
    "promotion": "11.11: giảm 25% còn 290.000đ + freeship",
    "key_selling_points": ["96% Snail Secretion Filtrate — phục hồi hàng rào da", "..."],

    // ⚠️ HAY QUÊN — chữ IN TRÊN BAO BÌ. Thiếu là QA báo động giả liên tục
    //    và prompt sẽ để model tự bịa nhãn.
    "label_text": ["COSRX", "ADVANCED SNAIL 96", "MUCIN POWER ESSENCE", "100ml"],

    // ⚠️ SỐNG CÒN — không có ảnh này thì mất sạch L1 + L2. Nam scrape về.
    "photos": ["media/products/cosrx_essence_1.jpg"]
  },

  "brand": {
    "colors": ["#FFFFFF", "#1A1A1A", "#00A19A"],
    "tone": "sạch sẽ, khoa học, đáng tin, tối giản",
    "logo": "media/brands/cosrx_logo.png"
  },

  "audience": {
    "target": "Nữ 18-30, da nhạy cảm / sau mụn, mê skincare Hàn",
    "market": "Vietnam / SEA",
    "platforms": ["tiktok_shop", "shopee", "facebook"]
  },

  "compliance": {
    "required_claims": ["96% snail mucin", "đã kiểm nghiệm lâm sàng"],
    "forbidden_claims": ["trị mụn dứt điểm", "chữa khỏi", "trắng da vĩnh viễn"]
  },

  "routes": [
    {
      "route_id": "A",
      "name": "science_led",
      "hook": "96% snail mucin — con số không nói dối",
      "message_angle": "Bằng chứng khoa học, không cảm tính",
      "visual_direction": "phòng lab sạch, trắng, macro texture",

      // ⚠️ MỌI chuỗi sẽ được VẼ LÊN ẢNH đều phải nằm ở đây.
      //    Studio không tự nghĩ chữ. Bỏ trống = model bịa = hỏng.
      "copy": {
        "headline": "PHỤC HỒI HÀNG RÀO DA",
        "subhead": "Tinh chất ốc sên 96%",
        "badge": "GIẢM 25%",
        "cta": "MUA NGAY",
        "vo_lines": [
          "Da khô căng, xỉn màu?",
          "96% tinh chất ốc sên, phục hồi hàng rào da.",
          "Đã kiểm nghiệm lâm sàng.",
          "Giảm 25% duy nhất 11.11."
        ]
      }
    },
    { "route_id": "B", "name": "testimonial_ugc", "...": "..." }
  ]
}
```

---

## 10. HỢP ĐỒNG ② — Studio → Duy

### Kết quả cuối

```jsonc
{
  "campaign_id": "cosrx-1111",
  "status": "running | done | failed",
  "routes": [{
    "route_id": "A",
    "style_spine": {
      "lens": "85mm macro", "lighting": "khuếch tán lạnh từ trái",
      "surface": "travertine ướt", "grade": "neutral, low contrast, airy",
      "palette": ["#FFFFFF", "#1A1A1A", "#00A19A"]
    },
    "hero": { /* Asset */ },
    "images": [ /* Asset[] */ ],
    "videos": [ /* Video[] */ ]
  }]
}
```

**Asset**
```jsonc
{
  "asset_id": "A.shopee.main",
  "platform": "shopee", "slot": "main_image",
  "ratio": "1:1", "size": [2048, 2048],
  "url": "/media/cosrx-1111/A_shopee_main.jpg",
  "text_rendered": ["PHỤC HỒI HÀNG RÀO DA", "Tinh chất ốc sên 96%"],
  "model": "dola-seedream-5-0-pro-260628",
  "refs": ["product_photo", "hero"],
  "qa": { "verdict": "PASS", "attempts": 1, "checks": { "C1": true, "C2": true, "C3": true } },
  "gen_seconds": 42
}
```

**Video**
```jsonc
{
  "video_id": "A.tiktok.master",
  "platform": "tiktok_shop", "ratio": "9:16", "size": [720, 1280], "duration": 20.2,
  "url": "/media/cosrx-1111/A_tiktok_master.mp4",
  "shots": [{
    "i": 0, "role": "hook", "duration": 5.06,
    "keyframe": "/media/.../A_shot0_key.jpg",
    "clip": "/media/.../A_shot0.mp4",
    "onscreen_text": "PHỤC HỒI HÀNG RÀO DA",
    "vo_text": "Da khô căng, xỉn màu?",
    "fallback_kenburns": false        // true = clip lỗi, đã dùng keyframe thay
  }],
  "cutdowns": [{ "id": "15s", "url": "..." }, { "id": "1x1", "url": "..." }],
  "voiceover": { "url": "/media/.../A_vo.mp3", "duration": 6.3 },
  "subtitle": { "url": "/media/.../A.ass" }
}
```

### Sự kiện tiến trình (SSE) — ⚠️ Duy đọc kỹ

Một route mất **6–12 phút**. **Không thể là request → chờ → nhận kết quả.**
UI phải hiện dần: keyframe xuất hiện trước, clip thay vào chỗ đó sau.

```jsonc
{"event":"stage",    "route":"A", "stage":"direct|anchor|fanout|motion|assemble", "pct":0.2}
{"event":"asset",    "route":"A", "asset_id":"A.hero", "url":"...", "qa":"PASS"}
{"event":"qa_retry", "route":"A", "asset_id":"A.hero", "attempt":2, "reason":"C2 sai dấu"}
{"event":"keyframe", "route":"A", "shot":0, "url":"..."}
{"event":"clip",     "route":"A", "shot":0, "url":"..."}
{"event":"done",     "route":"A"}
{"event":"error",    "route":"A", "where":"motion.shot2", "message":"..."}
```

Đây cũng là chỗ ăn điểm: BGK **nhìn thấy máy đang làm việc** — 15đ *Workflow & Demo Clarity*.

---

## 11. Cấu trúc file

```
backend/app/services/studio/
├── contracts.py   Pydantic: CampaignBrief · StyleSpine · Storyboard · AssetPlan · AssetPack
├── platforms.py   ma trận sàn: tỉ lệ · safe area · luật nền trắng
├── ark.py         client BytePlus: retry · resume task · download · seedream/seedance/tts/vision
├── direct.py      ① style spine + storyboard + asset plan   (không gọi API)
├── render.py      ②③ hero + fan-out ảnh
├── motion.py      ④ keyframe → clip, TTS
├── assemble.py    ⑤ ffmpeg: nối · VO · phụ đề · cutdown · Ken Burns dự phòng
├── qa.py          gate C1-C5: cắt 4 mảnh → vision chép → code phán
└── pipeline.py    điều phối + phát sự kiện SSE
```

---

## 12. Chưa đo — rủi ro còn lại

- Concurrency video >4 (ảnh đã xác nhận 10 song song tốt; video mới thử 4)
- i2v với ảnh sản phẩm brand **thật** (mới thử bằng ảnh Seedream tự sinh — nhưng chữ đã sống sót nên khả năng cao ổn)
- Ken Burns dự phòng ghép vào giữa các clip thật — có lộ không
- Ghép nhạc nền với audio native của Seedance — có cần duck không
