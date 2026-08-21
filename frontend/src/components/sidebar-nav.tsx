"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "@/components/theme-toggle";
import {
  BarChart3,
  LogOut,
  Package,
  Rocket,
  Search,
  Sparkles,
  Menu,
  X
} from "lucide-react";

const NAV_ITEMS = [
  { id: "campaigns", label: "CHIẾN DỊCH", icon: Sparkles },
  { id: "products", label: "SẢN PHẨM", icon: Package },
  { id: "research", label: "NGHIÊN CỨU", icon: Search },
  { id: "deployments", label: "TRIỂN KHAI", icon: Rocket },
  { id: "analytics", label: "PHÂN TÍCH", icon: BarChart3 },
];

export const SidebarNav: React.FC = () => {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = React.useState(false);
  const menuRef = React.useRef<HTMLDivElement>(null);
  const activeCampaignCount = 0; // Mock data

  // Close menu when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  // Close menu when route changes
  React.useEffect(() => {
    setTimeout(() => setIsOpen(false), 0);
  }, [pathname]);

  // Do not render the floating nav on the landing page
  if (pathname === "/") {
    return null;
  }

  return (
    <div className="fixed bottom-10 left-10 z-[100]" ref={menuRef}>
      
      {/* Floating Menu Popover */}
      {isOpen && (
        <div className="absolute bottom-20 left-0 w-64 border border-foreground/20 bg-background/95 backdrop-blur-xl animate-in fade-in zoom-in-95 slide-in-from-bottom-5 duration-200 origin-bottom-left shadow-2xl flex flex-col justify-between select-none">
          {/* Corner frame accents */}
          <div className="absolute top-0 left-0 w-3 h-3 border-t border-l border-[#35ea52]" />
          <div className="absolute top-0 right-0 w-3 h-3 border-t border-r border-foreground/20" />
          <div className="absolute bottom-0 left-0 w-3 h-3 border-b border-l border-foreground/20" />
          <div className="absolute bottom-0 right-0 w-3 h-3 border-b border-r border-[#35ea52]" />

          {/* Top Brand Area */}
          <div className="p-4 border-b border-foreground/10 bg-foreground/[0.02]">
            <div className="flex items-center gap-2.5">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/brand/logo-header.png"
                alt="CAIBS Logo"
                className="h-6 w-auto object-contain drop-shadow-[0_0_10px_rgba(53,234,82,0.3)]"
              />
              <div className="h-4 w-px bg-foreground/20" />
              <span className="text-foreground/40 text-[10px] font-mono tracking-widest">
                MULTI.AGENT
              </span>
            </div>
            <div className="flex items-center gap-1.5 mt-2.5">
              <div className="w-1 h-1 rounded-full bg-[#35ea52] animate-pulse" />
              <span className="text-[10px] font-mono text-foreground/40 tracking-wider">HỆ THỐNG.TRỰC TUYẾN V2.0</span>
            </div>
          </div>

          {/* Navigation Items */}
          <div className="p-2 space-y-0.5 flex-1 overflow-y-auto">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = pathname.startsWith(`/${item.id}`);
              return (
                <Link
                  key={item.id}
                  href={`/${item.id}`}
                  className={`w-full flex items-center justify-between px-3 py-3 text-sm font-mono tracking-wider transition-all relative ${
                    isActive
                      ? "text-black bg-[#35ea52]"
                      : "text-foreground/60 hover:text-foreground hover:bg-foreground/[0.05]"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className="h-4 w-4" />
                    <span className={isActive ? "font-bold" : ""}>{item.label}</span>
                  </div>
                  {item.id === "campaigns" && activeCampaignCount > 0 && (
                    <span className={`text-[11px] font-mono ${isActive ? 'text-black/60' : 'text-foreground/30'}`}>[{activeCampaignCount}]</span>
                  )}
                  {isActive && <span className="text-black text-[15px] opacity-70">›</span>}
                </Link>
              );
            })}
          </div>

          {/* Bottom Settings */}
          <div className="p-3 border-t border-foreground/10 bg-foreground/[0.01] space-y-3">
            <div className="px-2 py-2 border border-foreground/10 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="h-6 w-6 border border-foreground/20 bg-foreground/5 text-foreground/60 font-mono flex items-center justify-center text-xs">A</div>
                <span className="text-xs font-mono text-foreground/50">TÀI KHOẢN</span>
              </div>
              <ThemeToggle />
            </div>

            <button type="button" className="w-full flex items-center gap-2 px-2 py-1 text-xs font-mono text-foreground/30 hover:text-red-400 transition-colors tracking-wider">
              <LogOut className="h-3 w-3" /> LOGOUT
            </button>
          </div>
        </div>
      )}

      {/* Primary Floating Button (Assistive Touch Style) */}
      <button 
        onClick={() => setIsOpen(!isOpen)} 
        className={`w-14 h-14 rounded-full flex items-center justify-center transition-all duration-300 shadow-2xl relative border border-foreground/20 hover:scale-110 active:scale-95 ${
          isOpen ? 'bg-[#35ea52] text-black shadow-[0_0_20px_rgba(0,255,136,0.2)]' : 'bg-background text-foreground hover:bg-foreground/10'
        }`}
      >
        {/* iOS Assistive Touch inner rings aesthetic */}
        <div className={`absolute inset-1 rounded-full border ${isOpen ? 'border-black/20' : 'border-foreground/10'}`} />
        <div className={`absolute inset-2 rounded-full border opacity-50 ${isOpen ? 'border-black/10' : 'border-foreground/5'}`} />
        
        {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
      </button>

    </div>
  );
};
