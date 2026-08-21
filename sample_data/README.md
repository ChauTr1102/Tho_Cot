# Sample Input Data — BP-01 Commerce Campaign Launch Copilot

Bộ **input mẫu** để demo BP-01. Brand **thật**, cross-border, bán mạnh trên TikTok Shop / Shopee / livestream — phủ đủ các kịch bản của đề. Mỗi brand/chiến dịch một **folder riêng** = 1 bộ `data_input` hoàn chỉnh.

> **Điểm cố ý quan trọng:** mỗi folder để đầu vào ở **một định dạng file khác nhau** (PDF, Word, Excel, Markdown, .txt, ảnh-only, link URL). Vì **end-user thật quăng vào bất cứ file gì** — không ai điền JSON. Bộ data này để chứng minh lớp **Universal Intake** nuốt được mọi loại file, tự soi thiếu gì, rồi mới quyết định lấp thêm.

## Cấu trúc

```
sample_data/
├── 01_cosrx_snail_essence/     # K-beauty skincare
│   ├── brief.pdf               # brief dạng PDF (one-pager)
│   ├── past_campaign.xlsx      # data chiến dịch cũ (Excel) → Performance Learning
│   └── assets/                 # logo + 2 ảnh SP (+ SOURCES.md)
├── 02_oatside_barista/         # F&B / oat milk (SEA)
│   ├── brief.docx              # brief dạng Word
│   └── assets/
├── 03_anker_powerbank/         # Điện tử / sạc dự phòng
│   └── assets/                 # CHỈ ẢNH — không brief (vision phải tự suy)
├── 04_cocoon_ca_phe_dak_lak/   # Mỹ phẩm thuần chay Việt → cross-border SEA
│   ├── product_link.txt        # CHỈ 1 LINK — hệ thống tự crawl trang SP
│   └── assets/
├── 05_trung_nguyen_g7/         # Cà phê hoà tan Việt → cross-border (TQ/US)
│   ├── brief.txt               # text tự do, bừa bộn, thiếu field
│   └── assets/
└── 06_marou_chocolate/         # Socola bean-to-bar Việt → cross-border cao cấp
    ├── brief.md                # ghi chú Markdown
    └── assets/
```

## Bảng tổng: format & độ đầy đủ

| Folder | Brand | Ngành | Định dạng input | Độ đầy đủ | Kịch bản BP-01 |
|---|---|---|---|---|---|
| `01_cosrx` | COSRX 🇰🇷 | Skincare | **PDF** + **XLSX** | Full + data cũ | #2 Skincare · #4 Performance |
| `02_oatside` | Oatside 🇸🇬 | Oat milk | **DOCX** | Full core | #1 New Launch |
| `03_anker` | Anker 🌐 | Sạc dự phòng | **Ảnh-only** | Sparse (chỉ ảnh) | #3 Sale 11.11 |
| `04_cocoon` | Cocoon 🇻🇳 | Mỹ phẩm thuần chay | **Link URL** | Sparse (chỉ link) | #1 Cross-border (Việt→SEA) |
| `05_trung_nguyen_g7` | Trung Nguyên 🇻🇳 | Cà phê hoà tan | **TXT** tự do | Partial | #1 Cross-border (Việt→TQ/US) |
| `06_marou_chocolate` | Marou 🇻🇳 | Socola cao cấp | **Markdown** | Partial | #1 Cross-border premium |

*Partial/Sparse = cố tình thiếu field* (03 không có brief; 04 chỉ có link; 05/06 thiếu `existing visuals`, `consumer pain point`, `search keyword`) → để demo bước intake tự phát hiện & lấp.

## Universal Intake nuốt file thế nào

| File quăng vào | Cách parse |
|---|---|
| Ảnh (jpg/png/webp/svg) | Vision — đọc bao bì, logo, màu, chữ claim trên pack (OCR) |
| PDF / DOCX / PPTX / XLSX / CSV | `markitdown` (MCP có sẵn) → text + bảng |
| .txt / .md / paste text | đọc thẳng |
| Link sản phẩm | crawl trang (đã dùng để lấy ảnh trong `assets/`) |

→ đổ về schema nội bộ → bảng "có / thiếu / không chắc" → **tự bổ sung** (màu từ logo, trend/keyword/competitor từ web...) **hoặc hỏi lại** những field KHÔNG được bịa (`required/forbidden claims`, `price`).

## Cách dùng để demo

1. **Nạp input** (bất kỳ file nào ở trên) → Copilot: positioning → ≥2 creative routes → ≥1 video → ≥4 ảnh → copy → A/B plan.
2. **Brand Lock:** ảnh trong `assets/` làm reference cho Seedream 5.0 Pro (image-to-image) & Seedance 2.5 (image-to-video) → giữ đúng bao bì/sản phẩm.
3. **Performance Learning:** `01_.../past_campaign.xlsx` → hệ thống nên rút ra route **testimonial_ugc / before_after** ăn hơn hẳn **science_led** → *giữ* UGC, *đổi* hook nặng khoa học, *test* thêm góc UGC.
4. **Compliance:** mỗi brief có `required_claims` + `forbidden_claims` → demo bám claim bắt buộc & tránh claim cấm.

## Lưu ý (cho phần Q&A với giám khảo)

- **Ảnh trong `assets/`** là tài sản thương hiệu bên thứ ba, dùng **chỉ cho mục đích demo hackathon** (phi thương mại, fair-use làm brand-kit reference) — không dùng thương mại. Xuất phẩm do model sinh là của đội. Nguồn từng ảnh ghi trong `assets/SOURCES.md`.
- **Giá & khuyến mãi** là mức minh hoạ hợp lý cho demo.
- **`brand_colors`** là áng chừng — verify trên Brandfetch (`brandfetch.com/<brand>.com`).
- **`past_campaign.xlsx`** là số liệu **synthetic** — chỉ để demo module học từ hiệu quả.
