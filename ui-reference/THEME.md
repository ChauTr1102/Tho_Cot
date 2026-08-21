# THEME — đồng bộ nhận diện BTC (AI Cross-Border Hackathon 2026)

Nguồn màu bóc từ site sự kiện `aiglobal.dev` (chi tiết: [`style-guide.md`](./style-guide.md)).

## Nguyên tắc vàng: UI **xanh lá**, xanh dương chỉ ở **hero**

BTC dùng 2 lớp — đừng trộn lẫn:

| Lớp | Dùng ở | Màu |
|---|---|---|
| **UI** (mặc định) | nền trang, card, text, nút, dashboard | **nền xanh rừng `#001708`** + accent **lime `#35ea52`/`#7ef962`** |
| **Hero / key-visual** | banner, ảnh bìa, section tiêu đề lớn | gradient **xanh dương → tím → xanh lá neon** |

- **Nút hành động chính (CTA) = CAM `#fe6e00`** (glow đỏ), KHÔNG dùng xanh cho CTA.
- **Gold `#fcbb00`** cho sponsor / huy hiệu / premium.
- **Xanh dương không được làm màu chủ đạo của UI** — chỉ xuất hiện ở hero gradient + vài mảng glow.

## Bảng màu nhanh

| Vai trò | Hex |
|---|---|
| Nền | `#001708` |
| Chữ | `#f4faf5` · phụ `#a1c1a7` |
| Card | `#00220e` · surface `#012a14` |
| Primary (green) | `#35ea52` · glow `#90fd77` |
| Accent (lime) | `#7ef962` |
| Gold | `#fcbb00` |
| CTA (cam) | `#fe6e00` → `#ff9a3d` |
| Danger | `#fd393f` |

**Font:** tiêu đề **Space Grotesk**, body **Inter** · **Radius** `.75rem`.

## Cách dùng

### 1. Trong app Next (đã cấu hình sẵn)
`frontend/src/app/globals.css` đã nhuộm token shadcn sang palette BTC → **mọi component shadcn tự đồng bộ**. Cứ dùng class Tailwind bình thường:
```tsx
<button className="bg-primary text-primary-foreground rounded-lg">Chạy</button>
<div className="bg-card border rounded-xl p-6 glow">…</div>
<span className="text-gold">Nhà tài trợ</span>
<button className="btn-cta px-5 py-2">Đăng ký ngay</button>   {/* CTA cam kiểu BTC */}
<section className="bg-hero">…</section>                        {/* hero: chỗ dùng xanh dương */}
```
Class tiện có sẵn: `.btn-cta` `.bg-hero` `.text-gradient` `.glow` `.glow-accent` `.cta-glow` `.grid-faint`.

### 2. Ngoài app (slide / landing HTML)
`@import` hoặc copy [`theme.css`](./theme.css) → dùng biến `var(--bg)`, `var(--primary)`, class `.btn-cta`, `.bg-hero`…

## Logo sponsor
Đã crawl về **`frontend/public/sponsors/`** (bản `-white` nền trong suốt, hợp nền tối). Dùng trong app:
```tsx
<img src="/sponsors/byteplus.png" alt="BytePlus" />
```
Danh sách + hạng (title/gold/bronze/partner…) xem `frontend/public/sponsors/SOURCES.md`.
Logo/screenshot sự kiện gốc: `ui-reference/brand/` + `ui-reference/reference/`.

> Đây là tham chiếu để **đồng bộ với sự kiện**. Sản phẩm Thợ Cốt vẫn nên có điểm nhấn riêng, không mạo danh BTC.
