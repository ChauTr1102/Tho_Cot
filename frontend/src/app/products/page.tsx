"use client";

import * as React from "react";
import { ProductsListView } from "@/components/flow/products-list-view";
import { AddProductModal } from "@/components/flow/add-product-modal";
import { ProductData } from "@/types/campaign";

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
  const [products, setProducts] = React.useState<ProductData[]>(INITIAL_PRODUCTS);
  const [isAddModalOpen, setIsAddModalOpen] = React.useState(false);

  return (
    <div className="min-h-screen bg-transparent text-foreground/80 flex flex-col py-6 relative">
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-8 flex flex-col">
        <ProductsListView
          products={products}
          onOpenAddModal={() => setIsAddModalOpen(true)}
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
