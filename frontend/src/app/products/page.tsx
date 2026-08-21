"use client";

import * as React from "react";
import { ProductsListView } from "@/components/flow/products-list-view";
import { AddProductModal } from "@/components/flow/add-product-modal";
import { ProductData } from "@/types/campaign";
import { useRouter } from "next/navigation";

const INITIAL_PRODUCTS: ProductData[] = [
  {
    id: "prod-sample-1",
    name: "Son Dưỡng Căng Mọng Glow Lip Tint 24h Lumiére",
    brand: "Lumiére Beauty",
    category: "Mỹ phẩm & Làm đẹp",
    price: "189.000",
    originalPrice: "260.000",
    currency: "₫",
    images: [{ id: "img-1", url: "https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=600&q=80", isCover: true }],
    description: "Son tint bóng thuần chay",
    usps: ["Glass Skin"],
    targetAudience: { gender: "female", ageGroup: ["18-24"], painPoints: [], interests: [] },
    toneOfVoice: "Gen Z",
    campaignGoal: "Conversion",
    platform: "tiktok",
  }
];

export default function ProductsPage() {
  const router = useRouter();
  const [products, setProducts] = React.useState<ProductData[]>(INITIAL_PRODUCTS);
  const [isAddModalOpen, setIsAddModalOpen] = React.useState(false);

  return (
    <div className="min-h-screen bg-transparent text-foreground/80 flex flex-col pt-7 pb-6 relative">
      {/* Global Corner Frame Accents */}
      <div className="fixed top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-foreground/20 z-50 pointer-events-none" />
      <div className="fixed top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-foreground/20 z-50 pointer-events-none" />
      <div className="fixed bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-foreground/20 z-50 pointer-events-none" />
      <div className="fixed bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-foreground/20 z-50 pointer-events-none" />

      {/* Top Status Bar */}
      <div className="fixed top-0 left-0 right-0 z-40 border-b border-foreground/10 bg-background/90 backdrop-blur-sm">
        <div className="flex items-center justify-between px-12 py-1.5">
          <div className="flex items-center gap-4 text-[10px] font-mono text-foreground/30 tracking-widest">
            <span>CAIBS.AI.ADS</span>
            <div className="w-1 h-1 bg-foreground/20 rounded-full" />
            <span>EST.2025</span>
          </div>
          <div className="flex items-center gap-4 text-[10px] font-mono text-foreground/25 tracking-widest">
            <span>LAT: 10.7626°</span>
            <div className="w-1 h-1 bg-foreground/15 rounded-full" />
            <span>LONG: 106.6602°</span>
          </div>
        </div>
      </div>

      {/* Bottom Status Bar */}
      <div className="fixed bottom-0 left-0 right-0 z-40 border-t border-foreground/10 bg-background/90 backdrop-blur-sm">
        <div className="flex items-center justify-between px-12 py-1.5">
          <div className="flex items-center gap-4 text-[10px] font-mono text-foreground/25 tracking-widest">
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-[#35ea52] animate-pulse" />
              <span>SYSTEM.ACTIVE</span>
            </div>
            <span>V2.0.0</span>
          </div>
          <div className="flex items-center gap-4 text-[10px] font-mono text-foreground/20 tracking-widest">
            <span>◐ MULTI.AGENT.CORE</span>
            <div className="flex gap-1">
              <div className="w-1 h-1 bg-foreground/40 rounded-full animate-pulse" />
              <div className="w-1 h-1 bg-foreground/25 rounded-full animate-pulse" style={{ animationDelay: "0.2s" }} />
              <div className="w-1 h-1 bg-foreground/10 rounded-full animate-pulse" style={{ animationDelay: "0.4s" }} />
            </div>
            <span>FRAME: ∞</span>
          </div>
        </div>
      </div>

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-8 flex flex-col">
        <ProductsListView
          products={products}
          onOpenAddModal={() => setIsAddModalOpen(true)}
          onSelectProductForAd={() => {
            router.push("/campaigns");
          }}
          onDeleteProduct={() => {}}
        />
      </main>

      <AddProductModal
        open={isAddModalOpen}
        onOpenChange={setIsAddModalOpen}
        onSaveProduct={(p) => setProducts([p, ...products])}
      />
    </div>
  );
}
