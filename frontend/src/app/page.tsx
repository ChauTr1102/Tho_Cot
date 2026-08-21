"use client";

import { useEffect, useState } from "react";
import { Navbar } from "@/components/navbar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { HealthStatus, Item } from "@/types";
import { toast } from "sonner";
import {
  CheckCircle2,
  Circle,
  Database,
  ExternalLink,
  Flame,
  Layers,
  Plus,
  RefreshCw,
  Server,
  Trash2,
  Zap,
} from "lucide-react";

export default function HomePage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isBackendConnected, setIsBackendConnected] = useState<boolean | null>(null);
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // Form states
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  const checkHealthAndLoadData = async () => {
    setLoading(true);
    try {
      const healthRes = await api.getHealth();
      setHealth(healthRes.data);
      setIsBackendConnected(true);

      const itemsRes = await api.getItems();
      if (itemsRes.data) {
        setItems(itemsRes.data);
      }
    } catch (error) {
      console.error("Health/Data fetch error:", error);
      setIsBackendConnected(false);
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealthAndLoadData();
  }, []);

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      toast.error("Vui lòng nhập tiêu đề cho item");
      return;
    }

    setSubmitting(true);
    try {
      const res = await api.createItem({
        title: title.trim(),
        description: description.trim() || undefined,
      });

      if (res.data) {
        setItems((prev) => [res.data!, ...prev]);
        setTitle("");
        setDescription("");
        toast.success("Đã thêm item mới thành công!");
      }
    } catch (error: any) {
      toast.error(error?.message || "Lỗi khi tạo item. Kiểm tra lại backend!");
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleComplete = async (item: Item) => {
    const newStatus = !item.is_completed;
    try {
      // Optimistic update
      setItems((prev) =>
        prev.map((it) => (it.id === item.id ? { ...it, is_completed: newStatus } : it))
      );

      await api.updateItem(item.id, { is_completed: newStatus });
      toast.success(newStatus ? "Đã đánh dấu hoàn thành!" : "Đã hoàn tác!");
    } catch (error: any) {
      // Revert on error
      setItems((prev) =>
        prev.map((it) => (it.id === item.id ? { ...it, is_completed: !newStatus } : it))
      );
      toast.error(error?.message || "Lỗi khi cập nhật trạng thái");
    }
  };

  const handleDeleteItem = async (id: number) => {
    try {
      await api.deleteItem(id);
      setItems((prev) => prev.filter((it) => it.id !== id));
      toast.success("Đã xóa item thành công");
    } catch (error: any) {
      toast.error(error?.message || "Lỗi khi xóa item");
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col selection:bg-primary selection:text-primary-foreground">
      <Navbar isBackendConnected={isBackendConnected} serverVersion={health?.version} />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-8 sm:px-6 sm:py-12 space-y-10">
        {/* Hero Section */}
        <section className="space-y-4 text-center max-w-3xl mx-auto pt-4">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3.5 py-1.5 text-xs font-medium text-primary">
            <Flame className="h-3.5 w-3.5 text-amber-500" />
            <span>Fast-Track MVP Template</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-bold tracking-tight bg-gradient-to-b from-foreground to-foreground/70 bg-clip-text text-transparent">
            Next.js + shadcn/ui & FastAPI Base
          </h1>

          <p className="text-muted-foreground text-sm sm:text-base leading-relaxed">
            Nền tảng tối giản chuẩn hóa, sẵn sàng phát triển sản phẩm với App Router, Tailwind CSS, 
            SQLite ORM và FastAPI Async Server.
          </p>

          {/* Quick tech stack badges */}
          <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
            <Badge variant="secondary" className="font-mono text-xs">Next.js 15 App Router</Badge>
            <Badge variant="secondary" className="font-mono text-xs">shadcn/ui</Badge>
            <Badge variant="secondary" className="font-mono text-xs">Tailwind CSS v4</Badge>
            <Badge variant="secondary" className="font-mono text-xs">Python FastAPI</Badge>
            <Badge variant="secondary" className="font-mono text-xs">SQLite & SQLAlchemy 2.0</Badge>
          </div>
        </section>

        {/* Live CRUD Demo & Backend Status Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Interactive CRUD Demo (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            <Card className="border-border/60 shadow-sm">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Zap className="h-4 w-4 text-amber-500" />
                      Demo Tương Tác CRUD Trực Tiếp
                    </CardTitle>
                    <CardDescription>
                      Dữ liệu được lưu trữ trực tiếp vào database SQLite thông qua FastAPI.
                    </CardDescription>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={checkHealthAndLoadData}
                    disabled={loading}
                    title="Tải lại dữ liệu"
                    className="h-8 w-8 text-muted-foreground hover:text-foreground"
                  >
                    <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                  </Button>
                </div>
              </CardHeader>

              <CardContent className="space-y-5">
                {/* Form Add Item */}
                <form onSubmit={handleAddItem} className="space-y-3">
                  <div className="space-y-2">
                    <Input
                      placeholder="Nhập tiêu đề công việc / item mới..."
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      disabled={submitting}
                      className="bg-background"
                    />
                    <Input
                      placeholder="Mô tả chi tiết (tùy chọn)..."
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      disabled={submitting}
                      className="bg-background text-xs"
                    />
                  </div>
                  <Button type="submit" disabled={submitting || !title.trim()} className="w-full gap-2">
                    <Plus className="h-4 w-4" />
                    {submitting ? "Đang lưu..." : "Thêm Item Mới"}
                  </Button>
                </form>

                <div className="h-px bg-border" />

                {/* Items List */}
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between text-xs text-muted-foreground font-medium">
                    <span>Danh sách dữ liệu ({items.length})</span>
                    <span>Hành động</span>
                  </div>

                  {loading ? (
                    <div className="space-y-2">
                      <Skeleton className="h-12 w-full rounded-lg" />
                      <Skeleton className="h-12 w-full rounded-lg" />
                    </div>
                  ) : items.length === 0 ? (
                    <div className="rounded-lg border border-dashed p-8 text-center space-y-2">
                      <p className="text-sm font-medium text-muted-foreground">Chưa có item nào trong cơ sở dữ liệu</p>
                      <p className="text-xs text-muted-foreground">Hãy nhập tiêu đề ở trên và nhấn &quot;Thêm Item Mới&quot; để thử nghiệm!</p>
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-[360px] overflow-y-auto pr-1">
                      {items.map((item) => (
                        <div
                          key={item.id}
                          className="flex items-start justify-between gap-3 p-3 rounded-lg border bg-card/50 hover:bg-accent/40 transition-colors group"
                        >
                          <button
                            type="button"
                            onClick={() => handleToggleComplete(item)}
                            className="mt-0.5 text-muted-foreground hover:text-primary transition-colors shrink-0"
                          >
                            {item.is_completed ? (
                              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                            ) : (
                              <Circle className="h-4 w-4" />
                            )}
                          </button>

                          <div className="flex-1 min-w-0">
                            <p
                              className={`text-sm font-medium leading-snug break-words ${
                                item.is_completed
                                  ? "line-through text-muted-foreground"
                                  : "text-foreground"
                              }`}
                            >
                              {item.title}
                            </p>
                            {item.description && (
                              <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                                {item.description}
                              </p>
                            )}
                          </div>

                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDeleteItem(item.id)}
                            className="h-7 w-7 text-muted-foreground opacity-0 group-hover:opacity-100 hover:text-destructive transition-opacity shrink-0"
                            title="Xóa"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column: Server Info & Quick Architecture Cards (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            {/* Backend Health & DB Status Card */}
            <Card className="border-border/60 shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Server className="h-4 w-4 text-primary" />
                  Trạng Thái Backend (FastAPI)
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="flex items-center justify-between py-1.5 border-b text-xs">
                  <span className="text-muted-foreground">API Server URL</span>
                  <span className="font-mono font-medium">http://localhost:8000</span>
                </div>
                <div className="flex items-center justify-between py-1.5 border-b text-xs">
                  <span className="text-muted-foreground">Database Engine</span>
                  <span className="font-mono font-medium flex items-center gap-1">
                    <Database className="h-3.5 w-3.5 text-sky-500" />
                    SQLite ({health?.database || "Offline"})
                  </span>
                </div>
                <div className="flex items-center justify-between py-1.5 border-b text-xs">
                  <span className="text-muted-foreground">API Response Format</span>
                  <span className="font-mono text-emerald-600 dark:text-emerald-400 font-medium">StandardEnvelope (JSON)</span>
                </div>
                <div className="flex items-center justify-between py-1.5 text-xs">
                  <span className="text-muted-foreground">Tài liệu API Tự động</span>
                  <div className="flex gap-2">
                    <a
                      href="http://localhost:8000/docs"
                      target="_blank"
                      rel="noreferrer"
                      className="text-primary hover:underline inline-flex items-center gap-1 font-mono"
                    >
                      Swagger <ExternalLink className="h-3 w-3" />
                    </a>
                    <span className="text-muted-foreground">|</span>
                    <a
                      href="http://localhost:8000/redoc"
                      target="_blank"
                      rel="noreferrer"
                      className="text-primary hover:underline inline-flex items-center gap-1 font-mono"
                    >
                      ReDoc <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Quick Developer Cheat Sheet */}
            <Card className="border-border/60 shadow-sm bg-muted/20">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Layers className="h-4 w-4 text-primary" />
                  Hướng Dẫn Mở Rộng Nhanh
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-xs text-muted-foreground">
                <div className="p-2.5 rounded-md bg-background border space-y-1">
                  <p className="font-semibold text-foreground">1. Thêm API Route mới trong Backend:</p>
                  <p className="font-mono text-[11px] text-muted-foreground">
                    Tạo file trong <span className="text-primary">backend/app/routers/</span> và include vào <span className="text-primary">backend/app/main.py</span>.
                  </p>
                </div>

                <div className="p-2.5 rounded-md bg-background border space-y-1">
                  <p className="font-semibold text-foreground">2. Thêm component UI mới:</p>
                  <p className="font-mono text-[11px] text-muted-foreground">
                    Chạy <span className="text-primary">npx shadcn@latest add [component-name]</span> trong thư mục frontend.
                  </p>
                </div>

                <div className="p-2.5 rounded-md bg-background border space-y-1">
                  <p className="font-semibold text-foreground">3. Gọi API từ Frontend:</p>
                  <p className="font-mono text-[11px] text-muted-foreground">
                    Bổ sung method vào <span className="text-primary">src/lib/api.ts</span> với kiểu dữ liệu trong <span className="text-primary">src/types/index.ts</span>.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t py-6 text-center text-xs text-muted-foreground">
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Khởi tạo bởi Antigravity • Base Template FastAPI + Next.js</span>
          <span className="font-mono">Tho_Cot Workspace</span>
        </div>
      </footer>
    </div>
  );
}
