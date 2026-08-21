# 🎨 Brand & Style Guide — Cross-Border AI Innovation Summit 2026

> Bóc trực tiếp từ CSS & key visual của **aiglobal.dev** (15/08/2026). Dùng khi tự làm slide / landing / poster để **đồng bộ nhận diện với BTC** (phòng khi không có template sẵn).
> File gốc: `assets/reference/site.css`, hình: `assets/brand/`.

## 🧬 Có 2 lớp nhận diện
1. **UI Website (dark theme)** — nền **xanh rừng đậm** + accent **xanh lime** + điểm nhấn **vàng gold**. Dùng cho: web/app sản phẩm, slide nền tối, dashboard.
2. **Key Visual / Hero (marketing)** — gradient **xanh dương → tím → xanh lá neon**, mascot + motif văn hoá Việt. Dùng cho: banner, poster, ảnh bìa, trang tiêu đề slide.

---

## 🎨 Bảng màu (UI — chính xác từ CSS variables)

### Nền & chữ
| Vai trò | Hex | Ghi chú |
|---|---|---|
| Background | `#001708` | Nền trang, xanh rừng gần đen |
| Foreground (text) | `#f4faf5` | Chữ chính, trắng ngả xanh |
| Card | `#00220e` | Nền thẻ |
| Muted (surface) | `#012a14` | Bề mặt phụ |
| Muted text | `#a1c1a7` | Chữ phụ, xanh sage |
| Border | `#6bef75` @ ~18% | Viền xanh mờ |
| theme-color (meta) | `#0a1f12` | Màu thanh trình duyệt |

### Nhấn (accent) — chữ ký thương hiệu
| Vai trò | Hex |
|---|---|
| **Primary** (green) | `#35ea52` |
| Primary glow | `#90fd77` |
| Primary foreground | `#001205` |
| **Accent** (lime) | `#7ef962` |
| Accent glow | `#34f47a` |
| Secondary | `#003219` |
| Ring / focus | `#35ea52` |
| Destructive (đỏ) | `#fd393f` |

### Màu phụ trợ (scale)
- **Emerald:** `#5ee9b5` · `#00d294` · `#00bb7f`
- **Gold / Amber** (dùng cho sponsor/premium, huy hiệu): `#ffd236` · `#fcbb00` · `#f99c00` · `#f5c451` · `#fde68a` · `#f59e0b` · `#b75000`
- **Orange:** `#fe6e00` · `#ffb96d`

---

## 🔤 Typography
- **Display / tiêu đề:** **Space Grotesk** — weights 500, 600, 700 (kỹ thuật, hình học, hơi "geek").
- **Body / nội dung:** **Inter** — weights 400, 500, 600.
- **Mono:** ui-monospace, SFMono, Menlo, Monaco…
- Google Fonts: `https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&display=swap`

## 📐 Bo góc & hiệu ứng
- **Radius:** base `0.75rem` (12px) · lớn `1rem` · rất lớn `1.5rem`.
- **Gradient CTA:** `linear-gradient(135deg, #35ea52, #90fd77)`.
- **Grid nền mờ:** `linear-gradient(#ffffff0a 1px, transparent 1px)` (lưới kỹ thuật rất nhạt).
- **Glow (ánh sáng phát quang):**
  - `--shadow-glow: 0 0 40px #35ea5280`
  - `--shadow-glow-accent: 0 0 60px #7ef96273`
  - `--shadow-cta-glow: 0 0 40px #ee35338c`
  - `--shadow-elegant: 0 10px 40px -10px rgba(0,5,1,.7)`

---

## 🖼️ Key Visual / Hero (motif nhận diện)
Xem `assets/brand/hero-banner.jpg`. Đặc trưng:
- **Gradient nền:** xanh dương đậm → tím → xanh lá neon (khác với UI xanh rừng — đây là bản "lễ hội").
- **Mascot:** nhân vật 3D (mascot Ecomdy) **đội nón lá + cờ đỏ sao vàng**, bay theo vệt sáng neon → chất Việt Nam + cross-border.
- **Kiến trúc:** bóng **Văn Miếu / Khuê Văn Các** hai bên (di sản Hà Nội).
- **Vệt sáng neon** cyan→green chạy ngang dưới chân.
- **Vòng orbit / swoosh** quấn quanh chữ tiêu đề; **ngôi sao 4 cánh** (sparkle) rải rác.
- Chữ tiêu đề: trắng + xanh lá, chữ **AI** to nổi.

## 🧩 Element / component hay dùng trên web
- Nút CTA lớn phát sáng ("Join Hackathon" / "Register").
- **Countdown timer** (Days/Hours/Min/Sec).
- **Stat counters** (số đăng ký, thí sinh, team, giải pháp).
- Layout **card** cho tracks / sponsors / partners.
- Section tối, phân tách rõ, tiêu đề lớn Space Grotesk.
- Logo dạng vuông (header) + ngang (footer).

## 🏷️ Logo
- `assets/brand/logo-header.png` — logo "AI SUMMIT 26" xanh lime, chữ AI khối góc cạnh + sparkle (nền trong suốt).
- `assets/brand/logo-horizontal.png` — bản ngang.
- `assets/brand/logo-footer.png` — bản footer.
> ⚠️ Đây là logo của BTC/sự kiện — dùng để tham chiếu & trong ngữ cảnh sự kiện. Team **tự làm logo/nhận diện riêng của Thợ Cốt** cho sản phẩm; không mạo danh BTC.

---

## ✅ Xác nhận từ bản live (aiglobal.dev)
Chụp 12 section ở `assets/reference/screenshots/`. Quan sát thêm:
- **Nút CTA chính "Tham gia Hackathon" màu CAM–CORAL** (gradient cam→đỏ) — đây là lý do có `--shadow-cta-glow` đỏ trong CSS. Nút phụ = viền trắng trong suốt ("Xem chương trình"). → CTA nổi bật bằng cam trên nền xanh, không phải xanh.
- **Countdown** khối lớn số Space Grotesk xanh lime + nhãn nhỏ chữ hoa giãn cách (NGÀY/GIỜ/PHÚT/GIÂY).
- **Card thử thách/đối tượng:** icon vuông bo góc nền lime, tiêu đề trắng, bullet chấm tròn xanh.
- **Thang điểm** hiển thị bằng **progress bar xanh** (Kỹ thuật 20đ, Sáng tạo 15đ…).
- **Card nhà tài trợ có viền phát sáng theo hạng:** BytePlus/đồng hành = **glow xanh lá**; Nhà tài trợ Vàng (Kalodata) = **glow vàng gold**; Đồng (Wealify) = **glow cam/đồng**. Nền card có texture lưới mờ.
- **Giải thưởng:** icon 🏆 cúp vàng + 🥈🥉 huy chương; nhãn QUÁN QUÂN / Á QUÂN / HẠNG BA.
- **FAQ:** accordion (câu hỏi + mũi tên chevron ▾).
- **Hero card** bo góc lớn, viền + **glow xanh lá** bao quanh; nền trang có vệt sáng xanh mờ ở section.
- **Header:** logo trái, menu giữa, toggle **EN/VI** + nút CTA cam phải. (Web có sẵn bản tiếng Việt.)

## 📋 Token sẵn dùng (dán vào CSS khi build slide/web)
```css
:root {
  /* base */
  --bg:        #001708;
  --fg:        #f4faf5;
  --card:      #00220e;
  --muted:     #012a14;
  --muted-fg:  #a1c1a7;
  --border:    rgba(107,239,117,.18);
  /* accent */
  --primary:   #35ea52;
  --primary-glow: #90fd77;
  --accent:    #7ef962;
  --accent-glow:  #34f47a;
  --gold:      #fcbb00;
  --cta:       #fe6e00;   /* nút CTA cam-coral (glow đỏ #ee3533) */
  --danger:    #fd393f;
  /* type & shape */
  --font-display: "Space Grotesk", ui-sans-serif, system-ui, sans-serif;
  --font-body:    "Inter", ui-sans-serif, system-ui, sans-serif;
  --radius:    .75rem;
  --glow:      0 0 40px rgba(53,234,82,.5);
}
```
