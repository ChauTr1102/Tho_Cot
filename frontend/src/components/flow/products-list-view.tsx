"use client";

import * as React from "react";
import { ProductData } from "@/types/campaign";
import { Input } from "@/components/ui/input";
import {
  Package,
  Plus,
  Search,
  Star,
  Trash2,
  Wand2,
} from "lucide-react";

interface ProductsListViewProps {
  products: ProductData[];
  onOpenAddModal: () => void;
  onSelectProductForAd: (product: ProductData) => void;
  onDeleteProduct: (id: string) => void;
}

export const ProductsListView: React.FC<ProductsListViewProps> = ({
  products,
  onOpenAddModal,
  onSelectProductForAd,
  onDeleteProduct,
}) => {
  const [searchTerm, setSearchTerm] = React.useState("");

  const filteredProducts = React.useMemo(() => {
    if (!searchTerm.trim()) return products;
    const lower = searchTerm.toLowerCase();
    return products.filter(
      (p) =>
        p.name.toLowerCase().includes(lower) ||
        (p.brand && p.brand.toLowerCase().includes(lower)) ||
        p.category.toLowerCase().includes(lower)
    );
  }, [products, searchTerm]);

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header — brutalist */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div className="space-y-2">
          <div className="flex items-center gap-2 opacity-40">
            <div className="w-6 h-px bg-foreground" />
            <span className="text-[11px] font-mono tracking-widest">∞</span>
            <div className="flex-1 h-px bg-foreground" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-wider text-foreground font-mono uppercase">
            PRODUCTS
          </h1>
          <p className="text-sm text-foreground/35 font-mono tracking-wider">
            Manage imported ecommerce products and assets.
          </p>
        </div>

        <button
          type="button"
          onClick={onOpenAddModal}
          className="flex items-center gap-2 px-4 py-2.5 border border-foreground text-foreground font-mono text-sm tracking-wider hover:bg-foreground hover:text-black transition-all"
        >
          <Plus className="h-3.5 w-3.5" />
          <span>ADD.PRODUCT</span>
        </button>
      </div>

      {/* Search bar */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="h-3.5 w-3.5 absolute left-3 top-3 text-foreground/30" />
          <Input
            placeholder="Search by title, brand..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9 h-9 text-sm font-mono bg-transparent border-foreground/15 text-foreground/70 placeholder:text-foreground/20 focus:border-foreground/40"
          />
        </div>
        <span className="text-xs text-foreground/30 font-mono tracking-wider">
          [{filteredProducts.length}]
        </span>
      </div>

      {/* Product Grid */}
      {filteredProducts.length === 0 ? (
        <div className="p-12 text-center border border-dashed border-foreground/15 space-y-3 dot-grid">
          <div className="h-10 w-10 border border-foreground/20 flex items-center justify-center mx-auto">
            <Package className="h-5 w-5 text-foreground/30" />
          </div>
          <p className="text-sm font-mono text-foreground/50 tracking-wider">NO_PRODUCTS_FOUND</p>
          <p className="text-xs font-mono text-foreground/25 max-w-md mx-auto">
            {searchTerm
              ? "No products match your search filter."
              : "Import a product URL (TikTok, Shopee, Amazon) or enter details manually."}
          </p>
          <button
            type="button"
            onClick={onOpenAddModal}
            className="text-xs font-mono border border-foreground/30 px-4 py-2 text-foreground/60 hover:bg-foreground hover:text-black transition-all tracking-wider mt-2"
          >
            + ADD.FIRST.PRODUCT
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {filteredProducts.map((product) => {
            const coverImg = product.images.find((img) => img.isCover)?.url || product.images[0]?.url;

            return (
              <div
                key={product.id}
                className="group border border-foreground/10 bg-background overflow-hidden hover:border-foreground/30 transition-all flex flex-col justify-between relative"
              >
                {/* Corner accents */}
                <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-foreground/20 z-10" />
                <div className="absolute top-0 right-0 w-2 h-2 border-t border-r border-foreground/20 z-10" />

                <div>
                  {/* Thumbnail */}
                  <div className="aspect-square bg-foreground/[0.02] relative overflow-hidden">
                    {coverImg ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={coverImg}
                        alt={product.name}
                        className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Package className="h-8 w-8 text-foreground/15" />
                      </div>
                    )}

                    {product.platform && (
                      <span className="absolute top-2 left-2 text-[11px] font-mono font-bold uppercase px-1.5 py-0.5 border border-foreground/30 bg-background/70 text-foreground/70 tracking-wider">
                        {product.platform}
                      </span>
                    )}

                    <button
                      type="button"
                      onClick={() => product.id && onDeleteProduct(product.id)}
                      className="absolute top-2 right-2 h-6 w-6 border border-foreground/30 bg-background/70 text-foreground/50 hover:text-red-400 hover:border-red-400/50 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100"
                      title="Delete"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>

                  {/* Body */}
                  <div className="p-3 space-y-2 border-t border-foreground/8">
                    <div className="flex items-center justify-between text-[11px] text-foreground/30 font-mono">
                      <span className="text-foreground/50 truncate max-w-[100px] tracking-wider uppercase">
                        {product.brand || product.category}
                      </span>
                      {product.rating && (
                        <span className="flex items-center gap-1 text-amber-400/70">
                          <Star className="h-2.5 w-2.5 fill-amber-400/70" /> {product.rating}
                        </span>
                      )}
                    </div>

                    <h3 className="text-sm font-mono font-bold text-foreground/70 leading-snug line-clamp-2 min-h-[28px]">
                      {product.name}
                    </h3>

                    <div className="flex items-baseline gap-2">
                      <span className="text-[15px] font-mono font-bold text-foreground">
                        {product.price} {product.currency || "₫"}
                      </span>
                      {product.originalPrice && (
                        <span className="text-xs text-foreground/25 font-mono line-through">
                          {product.originalPrice}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Footer Action */}
                <div className="p-3 pt-0 border-t border-foreground/8">
                  <button
                    type="button"
                    onClick={() => onSelectProductForAd(product)}
                    className="w-full flex items-center justify-center gap-2 py-2 border border-foreground/20 text-xs font-mono text-foreground/50 hover:bg-foreground hover:text-black transition-all tracking-wider"
                  >
                    <Wand2 className="h-3 w-3" />
                    <span>GENERATE.AD</span>
                  </button>
                </div>

                <div className="absolute bottom-0 left-0 w-2 h-2 border-b border-l border-foreground/20" />
                <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-foreground/20" />
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
