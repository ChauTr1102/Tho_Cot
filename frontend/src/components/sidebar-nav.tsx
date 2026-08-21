"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Package,
  Rocket,
  Search,
  Sparkles,
  Menu,
  X,
} from "lucide-react";

interface NavItem {
  id: string;
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  { id: "campaigns", label: "CHIẾN DỊCH", href: "/campaigns", icon: Sparkles },
  { id: "products", label: "SẢN PHẨM", href: "/products", icon: Package },
  { id: "research", label: "NGHIÊN CỨU", href: "/research", icon: Search },
  { id: "deployments", label: "TRIỂN KHAI", href: "/deployments", icon: Rocket },
  { id: "analytics", label: "PHÂN TÍCH", href: "/analytics", icon: BarChart3 },
];

const RADIUS = 112; // Radius of fan spread in px
const START_ANGLE = 60; // Top angle in deg (+60°)
const END_ANGLE = -60; // Bottom angle in deg (-60°)

export const SidebarNav: React.FC = () => {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = React.useState(false);
  const [hoveredItem, setHoveredItem] = React.useState<string | null>(null);
  const menuRef = React.useRef<HTMLDivElement>(null);

  // Close menu when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  // Close menu on route change
  React.useEffect(() => {
    setIsOpen(false);
  }, [pathname]);

  // Do not render on landing page
  if (pathname === "/") {
    return null;
  }

  const count = NAV_ITEMS.length;

  return (
    <div className="fixed left-5 top-1/2 -translate-y-1/2 z-[100]" ref={menuRef}>
      {/* Background backdrop blur when open */}
      <div
        className={`fixed inset-0 -z-10 bg-black/15 backdrop-blur-[1px] transition-opacity duration-300 ${
          isOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        }`}
        onClick={() => setIsOpen(false)}
        aria-hidden="true"
      />

      {/* Decorative Symmetrical Fan Guide Arc */}
      <svg
        className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 pointer-events-none transition-all duration-500 origin-center -z-10 ${
          isOpen ? "opacity-100 scale-100" : "opacity-0 scale-50"
        }`}
        viewBox="-130 -130 260 260"
        aria-hidden="true"
      >
        {/* Outer dotted fan arc */}
        <path
          d={`M ${Math.round(RADIUS * Math.cos((START_ANGLE * Math.PI) / 180))},${Math.round(-RADIUS * Math.sin((START_ANGLE * Math.PI) / 180))} A ${RADIUS} ${RADIUS} 0 0,1 ${Math.round(RADIUS * Math.cos((END_ANGLE * Math.PI) / 180))},${Math.round(-RADIUS * Math.sin((END_ANGLE * Math.PI) / 180))}`}
          fill="none"
          stroke="rgba(40, 200, 64, 0.4)"
          strokeWidth="1.2"
          strokeDasharray="3 3"
        />
        {/* Inner dotted accent arc */}
        <path
          d={`M ${Math.round(RADIUS * 0.6 * Math.cos((START_ANGLE * Math.PI) / 180))},${Math.round(-RADIUS * 0.6 * Math.sin((START_ANGLE * Math.PI) / 180))} A ${RADIUS * 0.6} ${RADIUS * 0.6} 0 0,1 ${Math.round(RADIUS * 0.6 * Math.cos((END_ANGLE * Math.PI) / 180))},${Math.round(-RADIUS * 0.6 * Math.sin((END_ANGLE * Math.PI) / 180))}`}
          fill="none"
          stroke="rgba(40, 200, 64, 0.25)"
          strokeWidth="0.8"
          strokeDasharray="2 4"
        />
      </svg>

      {/* Fan-out Radial Action Items */}
      <div className="relative flex items-center justify-center">
        {NAV_ITEMS.map((item, index) => {
          const Icon = item.icon;
          const isActive = pathname.startsWith(item.href);

          // Symmetrical angle spreading from +60° (top) down to -60° (bottom) facing right
          const angleDeg = START_ANGLE - index * ((START_ANGLE - END_ANGLE) / (count - 1));
          const angleRad = (angleDeg * Math.PI) / 180;
          const targetX = Math.round(RADIUS * Math.cos(angleRad));
          const targetY = Math.round(-RADIUS * Math.sin(angleRad));

          return (
            <div
              key={item.id}
              className="absolute transition-all"
              style={{
                transform: isOpen
                  ? `translate3d(${targetX}px, ${targetY}px, 0px) scale(1)`
                  : "translate3d(0px, 0px, 0px) scale(0.3)",
                opacity: isOpen ? 1 : 0,
                pointerEvents: isOpen ? "auto" : "none",
                transitionDuration: isOpen ? "320ms" : "200ms",
                transitionTimingFunction: isOpen
                  ? "cubic-bezier(0.34, 1.56, 0.64, 1)" // spring overshoot
                  : "cubic-bezier(0.4, 0, 0.2, 1)",
                transitionDelay: isOpen
                  ? `${index * 35}ms`
                  : `${(count - 1 - index) * 20}ms`,
              }}
            >
              <div className="relative group">
                <Link
                  href={item.href}
                  onClick={() => setIsOpen(false)}
                  onMouseEnter={() => setHoveredItem(item.id)}
                  onMouseLeave={() => setHoveredItem(null)}
                  className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-200 border relative select-none shadow-md ${
                    isActive
                      ? "bg-[#28C840] text-white border-[#28C840] shadow-[0_0_18px_rgba(40,200,64,0.4)] scale-105"
                      : "bg-[#FFFFFF]/95 text-[#0D1117] border-[rgba(13,17,23,0.15)] hover:border-[#28C840] hover:text-[#28C840] hover:bg-[#FAF8F5] hover:shadow-[0_0_12px_rgba(40,200,64,0.3)] hover:scale-110"
                  }`}
                  aria-label={item.label}
                >
                  {/* Subtle inner ring */}
                  <div
                    className={`absolute inset-0.5 rounded-full border pointer-events-none ${
                      isActive ? "border-white/20" : "border-black/5"
                    }`}
                  />
                  <Icon className="h-4 w-4" />
                </Link>

                {/* Tooltip / Label chip on the right */}
                <div
                  className={`absolute whitespace-nowrap pointer-events-none transition-all duration-200 z-20 left-12 top-1/2 -translate-y-1/2 ${
                    hoveredItem === item.id || isActive
                      ? "opacity-100 translate-x-0 scale-100"
                      : "opacity-0 -translate-x-1 scale-90"
                  }`}
                >
                  <div
                    className={`px-2.5 py-1 text-[10px] font-mono tracking-wider font-bold rounded border shadow-md flex items-center gap-1.5 ${
                      isActive
                        ? "bg-[#28C840] text-white border-[#28C840] shadow-[0_0_10px_rgba(40,200,64,0.25)]"
                        : "bg-[#FFFFFF] text-[#0D1117] border-[rgba(13,17,23,0.15)] shadow-sm"
                    }`}
                  >
                    <span>{item.label}</span>
                    {isActive && <span className="text-[8px] opacity-80">●</span>}
                  </div>
                </div>
              </div>
            </div>
          );
        })}

        {/* Central Floating Trigger Button */}
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          aria-label={isOpen ? "Đóng menu điều hướng" : "Mở menu điều hướng dạng quạt"}
          className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 shadow-md relative border select-none group active:scale-90 ${
            isOpen
              ? "bg-[#28C840] text-white border-[#28C840] shadow-[0_0_20px_rgba(40,200,64,0.5)] rotate-90"
              : "bg-[#FFFFFF]/95 text-[#0D1117] border-[rgba(13,17,23,0.15)] hover:border-[#28C840] hover:text-[#28C840] hover:shadow-[0_0_15px_rgba(40,200,64,0.25)] hover:scale-105"
          }`}
        >
          {/* Subtle pulse ring when closed */}
          {!isOpen && (
            <div className="absolute inset-0 rounded-full border border-[#28C840]/30 animate-ping opacity-30 pointer-events-none" />
          )}

          {/* Double inner aesthetic rings */}
          <div
            className={`absolute inset-0.5 rounded-full border pointer-events-none transition-colors ${
              isOpen ? "border-white/20" : "border-black/5"
            }`}
          />
          <div
            className={`absolute inset-1.5 rounded-full border pointer-events-none opacity-60 transition-colors ${
              isOpen ? "border-white/10" : "border-black/5"
            }`}
          />

          {/* Icon with smooth rotation */}
          <div className="relative z-10 transition-transform duration-300">
            {isOpen ? (
              <X className="h-4.5 w-4.5 stroke-[2.5]" />
            ) : (
              <Menu className="h-4.5 w-4.5 stroke-[2.2]" />
            )}
          </div>
        </button>
      </div>
    </div>
  );
};
