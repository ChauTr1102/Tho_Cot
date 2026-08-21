# Base Project Fullstack: Next.js + shadcn/ui & Python FastAPI

Template chuẩn hóa, kiến trúc nhiều tầng (Layered / Clean Architecture) sẵn sàng mở rộng quy mô lớn cho **Backend FastAPI (Python 3.12)** và **Frontend Next.js 15 (App Router, shadcn/ui, Tailwind CSS v4, TypeScript)**.

---

## 📁 Cấu Trúc Dự Án Chuẩn (Clean & Layered Architecture)

```
Tho_Cot/
├── backend/
│   ├── app/
│   │   ├── api/                 # API Controllers & Routing
│   │   │   ├── v1/
│   │   │   │   ├── endpoints/   # Endpoint controllers (health.py, items.py, ...)
│   │   │   │   └── api.py       # Aggregator router v1
│   │   │   └── deps.py          # Centralized Dependency Injections (get_db, pagination, ...)
│   │   ├── core/                # Core Config, Exceptions & Security
│   │   │   ├── config.py        # Pydantic BaseSettings (load .env)
│   │   │   └── exceptions.py    # Custom Exceptions (AppException, NotFoundException) & Handlers
│   │   ├── crud/                # Repository / Database Operations
│   │   │   ├── base.py          # Generic CRUDBase (get, get_multi, create, update, remove)
│   │   │   └── crud_item.py     # Specific CRUD operations for Item
│   │   ├── db/                  # Database Engine, Session & Base Class
│   │   │   ├── base_class.py    # Declarative Base với auto table naming & timestamps
│   │   │   ├── base.py          # Aggregator cho metadata/migrations
│   │   │   ├── session.py       # Engine & SessionLocal
│   │   │   └── init_db.py       # Database table initializers
│   │   ├── models/              # SQLAlchemy Domain ORM Models
│   │   │   └── item.py
│   │   ├── schemas/             # Pydantic v2 DTOs (Request & Response validation)
│   │   │   ├── common.py        # StandardResponse envelope & PaginationParams
│   │   │   ├── health.py
│   │   │   └── item.py
│   │   ├── services/            # Business Logic Layer
│   │   │   └── item_service.py  # Xử lý nghiệp vụ, validation & điều phối CRUD
│   │   └── main.py              # Application Factory, CORS, Lifespan & Middleware
│   ├── tests/                   # Pytest Test Suite
│   │   ├── conftest.py          # In-memory test DB fixture & TestClient
│   │   ├── test_health.py       # Health check tests
│   │   └── test_items.py        # Items CRUD integration tests
│   ├── requirements.txt
│   ├── run.sh                   # Script khởi chạy 1 chạm
│   └── .env
│
└── frontend/
    ├── src/
    │   ├── app/                 # App Router (page.tsx, layout.tsx, globals.css)
    │   ├── components/          # shadcn/ui components, navbar, theme-toggle
    │   │   └── ui/              # button, card, input, badge, dialog, skeleton, sonner
    │   ├── lib/                 # api client (fetch wrapper), utils (cn)
    │   └── types/               # TypeScript interfaces & DTOs
    ├── package.json
    └── .env.local
```

---

## 🚀 Hướng Dẫn Khởi Chạy

### 1. Khởi Động Backend (FastAPI)

Mở 1 terminal tab:
```bash
cd /Users/phanducduy/Desktop/CAIBS/Tho_Cot/backend
./run.sh
```

- **API Base URL**: `http://localhost:8000/api`
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

#### Chạy Test Suite Backend:
```bash
cd /Users/phanducduy/Desktop/CAIBS/Tho_Cot/backend
./venv/bin/pytest -v
```

---

### 2. Khởi Động Frontend (Next.js)

Mở terminal tab thứ 2:
```bash
cd /Users/phanducduy/Desktop/CAIBS/Tho_Cot/frontend
npm run dev
```

- **Giao diện Web**: [http://localhost:3000](http://localhost:3000)

---

## 💎 Điểm Nổi Bật Về Kiến Trúc

1. **Phân tầng rõ ràng (Separation of Concerns)**:
   - `endpoints` chỉ xử lý nhận HTTP request và trả response.
   - `services` chịu trách nhiệm toàn bộ logic nghiệp vụ (business logic).
   - `crud` trừu tượng hóa các câu truy vấn cơ sở dữ liệu qua generic `CRUDBase`.
   - `models` định nghĩa schema dữ liệu trong DB.
   - `schemas` xác thực dữ liệu đầu vào / đầu ra (Pydantic v2).
2. **Unified Response Format**:
   ```json
   {
     "success": true,
     "message": "...",
     "data": { ... },
     "error": null,
     "timestamp": "2026-08-21T04:47:00.000000Z"
   }
   ```
3. **Quản lý lỗi tập trung**: `AppException`, `NotFoundException`, `BadRequestException` tự động được bắt và serialize về format chuẩn.
4. **Pytest Tích Hợp Sẵn**: Fixture `StaticPool` in-memory SQLite giúp kiểm thử độc lập, tốc độ mili-giây.
5. **Frontend Chuẩn Hiện Đại**: Next.js 15 App Router + shadcn/ui + Dark/Light Theme + Optimistic UI.
