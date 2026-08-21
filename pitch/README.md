# 🎤 Pitch Deck — Team Thợ Cốt

Bộ slide pitch template theo đúng **brand kit** cuộc thi (xem `../assets/style-guide.md`).
2 bản dùng song song — sửa bản nào tuỳ bối cảnh.

## 📦 File trong thư mục
| File | Là gì |
|---|---|
| `index.html` | **Bản HTML** trình chiếu (mở trình duyệt là chạy) |
| `tho-cot-pitch-template.pptx` | **Bản PowerPoint** (sửa trong PowerPoint / Google Slides / Keynote) |
| `build_pptx.py` | Script gen lại file .pptx |
| `brand/` | `logo-event.png` (logo sự kiện) + `bg.png` (nền grid/glow cho PPTX) |
| `preview/` | Ảnh xem trước các slide (HTML + PPTX cover) |

> 🏷️ **Nhận diện:** cover dùng **logo sự kiện** + dải nhà tài trợ (ngữ cảnh người dự thi); các slide nội dung có logo sự kiện nhỏ ở góc phải, **THỢ CỐT** là nhận diện team ở góc trái. Không mạo danh BTC. Có logo riêng của Thợ Cốt thì thay chữ "THỢ CỐT." ở góc trái.
> 🎨 **Nền** (xanh rừng + lưới mờ + glow) giống nhau ở cả HTML và PPTX. Font **Space Grotesk** + **Inter**. Không dùng ảnh/hoạ tiết rối — thuần typographic.

## 🖥️ Bản HTML — dùng thế nào
- Mở: **double-click `index.html`** (hoặc kéo vào trình duyệt). Không cần mạng nội bộ; chỉ cần internet để tải font.
- Điều khiển khi trình chiếu:
  - **← →** hoặc **Space**: chuyển slide · **Home/End**: đầu/cuối
  - **F**: toàn màn hình · **P**: in ra **PDF** (mỗi slide 1 trang — bản backup an toàn khi máy hội trường không mở được HTML)
  - Bấm **chấm tròn** dưới để nhảy slide · vuốt trái/phải trên điện thoại
- Sửa nội dung: mở `index.html` bằng editor, thay các chỗ **`[...]`**. Cấu trúc rõ ràng, mỗi slide 1 khối `<section class="slide">`.

## 📊 Bản PowerPoint — dùng thế nào
- Mở `tho-cot-pitch-template.pptx` bằng PowerPoint / Google Slides / Keynote, thay các chỗ **`[...]`**.
- **Để đẹp nhất:** cài 2 font **Space Grotesk** + **Inter** (miễn phí trên Google Fonts) trước khi mở — nếu không, phần mềm sẽ tự thay font gần giống.
- Gen lại file (khi sửa `build_pptx.py`): 
  ```bash
  pip install python-pptx   # nếu chưa có
  python3 build_pptx.py
  ```

## 🧱 Khung 8 slide (editorial, kicker đánh số 01–07)
1. **Cover** — nhà tài trợ phân hạng ở trên · logo cuộc thi · **tên sản phẩm cỡ lớn** + tagline · mô tả · **cột thông số bên phải** (thời gian / địa điểm / hạng mục / đội / powered by).
2. **01 · Vấn đề** — headline tuyên bố + hero stat lớn (trái) · các dòng số liệu có kẻ ngang (phải).
3. **02 · Giải pháp** — 3 tính năng đánh số 01/02/03, kẻ dọc phân cột (không dùng card).
4. **03 · Demo** — khung chèn ảnh/video/link demo.
5. **04 · Công nghệ** — flow Input → Lõi AI (Claude · [+ BytePlus]) → Output + chip công nghệ.
6. **05 · Tác động** — hero stat (TAM) + các dòng chỉ số (phải).
7. **06 · Lộ trình** — timeline Hackathon → POC → **DNES Incubation** (gold) → Thị trường.
8. **07 · Đội ngũ + Cảm ơn** — thành viên + CTA/liên hệ.

> 🔗 Bản HTML deep-link được: mở `index.html#3` để tới thẳng slide 3 (tiện khi trình bày/chụp).

> 💡 Chấm điểm có **15đ cho Demo & Trình bày** + **+5đ sponsor** → slide 4 (demo chạy được) và slide 5 (ghép BytePlus) là chỗ ăn điểm. Chi tiết ở `../docs/thong-tin-cuoc-thi.md`.
