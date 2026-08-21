"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { ArrowRight, Sparkles, Bot, Layers, ShieldCheck, Zap } from "lucide-react";

interface Ripple {
  id: number;
  x: number;
  y: number;
}

interface DigitalSerenityProps {
  topTagline?: string;
  topSubtag?: string;
  mainHeadingWord1?: string;
  mainHeadingWord2?: string;
  mainHeadingWord3?: string;
  subHeading?: string;
  bottomTagline?: string;
  ctaText?: string;
  ctaHref?: string;
  secondaryCtaText?: string;
  secondaryCtaHref?: string;
}

export const DigitalSerenity: React.FC<DigitalSerenityProps> = ({
  topTagline = "CAIBS.AI.ADS",
  topSubtag = "HỆ THỐNG ĐA TÁC TỬ QUẢNG CÁO THÔNG MINH",
  mainHeadingWord1 = "Từ Dữ Liệu",
  mainHeadingWord2 = "Đến Chiến Dịch",
  mainHeadingWord3 = "Bùng Nổ Doanh Số.",
  subHeading = "Tự động trích xuất thông tin sản phẩm, phân tích thị trường, định vị góc nhìn và tạo nội dung đa nền tảng trong vài giây.",
  bottomTagline = "Nghiên cứu thị trường · Định vị góc nhìn · Tối ưu chuyển đổi · Kiểm soát rủi ro",
  ctaText = "BẮT ĐẦU CHIẾN DỊCH AI",
  ctaHref = "/campaigns",
  secondaryCtaText = "XEM HỒ SƠ NGHIÊN CỨU",
  secondaryCtaHref = "/research",
}) => {
  const [mouseGradientStyle, setMouseGradientStyle] = useState({
    left: "0px",
    top: "0px",
    opacity: 0,
  });
  const [ripples, setRipples] = useState<Ripple[]>([]);
  const [scrolled, setScrolled] = useState(false);
  const floatingElementsRef = useRef<HTMLElement[]>([]);

  useEffect(() => {
    const animateWords = () => {
      const wordElements = document.querySelectorAll<HTMLElement>(".word-animate");
      wordElements.forEach((word) => {
        const delay = parseInt(word.getAttribute("data-delay") || "0", 10) || 0;
        setTimeout(() => {
          if (word) word.style.animation = "word-appear 0.8s ease-out forwards";
        }, delay);
      });
    };
    const timeoutId = setTimeout(animateWords, 300);
    return () => clearTimeout(timeoutId);
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMouseGradientStyle({
        left: `${e.clientX}px`,
        top: `${e.clientY}px`,
        opacity: 1,
      });
    };
    const handleMouseLeave = () => {
      setMouseGradientStyle((prev) => ({ ...prev, opacity: 0 }));
    };
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseleave", handleMouseLeave);
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseleave", handleMouseLeave);
    };
  }, []);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      const newRipple = { id: Date.now(), x: e.clientX, y: e.clientY };
      setRipples((prev) => [...prev, newRipple]);
      setTimeout(() => setRipples((prev) => prev.filter((r) => r.id !== newRipple.id)), 1000);
    };
    document.addEventListener("click", handleClick);
    return () => document.removeEventListener("click", handleClick);
  }, []);

  useEffect(() => {
    const wordElements = document.querySelectorAll<HTMLElement>(".word-animate");
    const handleMouseEnter = (e: Event) => {
      const target = e.target as HTMLElement;
      if (target) target.style.textShadow = "0 0 25px rgba(53, 234, 82, 0.7)";
    };
    const handleMouseLeave = (e: Event) => {
      const target = e.target as HTMLElement;
      if (target) target.style.textShadow = "none";
    };
    wordElements.forEach((word) => {
      word.addEventListener("mouseenter", handleMouseEnter);
      word.addEventListener("mouseleave", handleMouseLeave);
    });
    return () => {
      wordElements.forEach((word) => {
        if (word) {
          word.removeEventListener("mouseenter", handleMouseEnter);
          word.removeEventListener("mouseleave", handleMouseLeave);
        }
      });
    };
  }, []);

  useEffect(() => {
    const elements = document.querySelectorAll<HTMLElement>(".floating-element-animate");
    floatingElementsRef.current = Array.from(elements);
    const handleScroll = () => {
      if (!scrolled) {
        setScrolled(true);
        floatingElementsRef.current.forEach((el, index) => {
          setTimeout(() => {
            if (el) {
              el.style.animationPlayState = "running";
              el.style.opacity = "";
            }
          }, parseFloat(el.style.animationDelay || "0") * 1000 + index * 100);
        });
      }
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, [scrolled]);

  const pageStyles = `
    #mouse-gradient-react {
      position: fixed;
      pointer-events: none;
      border-radius: 9999px;
      background-image: radial-gradient(circle, rgba(53, 234, 82, 0.12), rgba(16, 185, 129, 0.06), transparent 70%);
      transform: translate(-50%, -50%);
      will-change: left, top, opacity;
      transition: left 70ms linear, top 70ms linear, opacity 300ms ease-out;
      z-index: 1;
    }
    @keyframes word-appear {
      0% { opacity: 0; transform: translateY(30px) scale(0.85); filter: blur(8px); }
      50% { opacity: 0.8; transform: translateY(8px) scale(0.98); filter: blur(2px); }
      100% { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
    }
    @keyframes grid-draw {
      0% { stroke-dashoffset: 1000; opacity: 0; }
      50% { opacity: 0.35; }
      100% { stroke-dashoffset: 0; opacity: 0.2; }
    }
    @keyframes pulse-glow {
      0%, 100% { opacity: 0.15; transform: scale(1); }
      50% { opacity: 0.45; transform: scale(1.15); }
    }
    .word-animate {
      display: inline-block;
      opacity: 0;
      margin: 0 0.12em;
      transition: color 0.3s ease, transform 0.3s ease;
    }
    .word-animate:hover {
      color: #35ea52;
      transform: translateY(-2px);
    }
    .grid-line {
      stroke: #35ea52;
      stroke-width: 0.5;
      opacity: 0;
      stroke-dasharray: 6 6;
      stroke-dashoffset: 1000;
      animation: grid-draw 2s ease-out forwards;
    }
    .detail-dot {
      fill: #35ea52;
      opacity: 0;
      animation: pulse-glow 3s ease-in-out infinite;
    }
    .corner-element-animate {
      position: absolute;
      width: 44px;
      height: 44px;
      border: 1px solid rgba(53, 234, 82, 0.25);
      opacity: 0;
      animation: word-appear 1s ease-out forwards;
    }
    .text-decoration-animate {
      position: relative;
    }
    .text-decoration-animate::after {
      content: '';
      position: absolute;
      bottom: -8px;
      left: 0;
      width: 0;
      height: 1px;
      background: linear-gradient(90deg, transparent, #35ea52, transparent);
      animation: underline-grow 2s ease-out forwards;
      animation-delay: 1.8s;
    }
    @keyframes underline-grow {
      to { width: 100%; }
    }
    .floating-element-animate {
      position: absolute;
      width: 3px;
      height: 3px;
      background: #35ea52;
      border-radius: 50%;
      opacity: 0;
      animation: float 4s ease-in-out infinite;
      animation-play-state: paused;
    }
    @keyframes float {
      0%, 100% { transform: translateY(0) translateX(0); opacity: 0.2; }
      25% { transform: translateY(-12px) translateX(6px); opacity: 0.7; }
      50% { transform: translateY(-6px) translateX(-4px); opacity: 0.4; }
      75% { transform: translateY(-18px) translateX(8px); opacity: 0.9; }
    }
    .ripple-effect {
      position: fixed;
      width: 6px;
      height: 6px;
      background: rgba(53, 234, 82, 0.7);
      border-radius: 50%;
      transform: translate(-50%, -50%);
      pointer-events: none;
      animation: pulse-glow 1s ease-out forwards;
      z-index: 9999;
    }
  `;

  const headingWords1 = mainHeadingWord1.split(" ");
  const headingWords2 = mainHeadingWord2.split(" ");
  const headingWords3 = mainHeadingWord3.split(" ");

  return (
    <>
      <style>{pageStyles}</style>
      <div className="min-h-screen bg-gradient-to-br from-black via-[#061009] to-black text-slate-100 font-mono overflow-hidden relative selection:bg-[#35ea52] selection:text-black">
        {/* Cyberpunk Grid Background */}
        <svg
          className="absolute inset-0 w-full h-full pointer-events-none opacity-60"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          <defs>
            <pattern id="gridDarkMatrix" width="60" height="60" patternUnits="userSpaceOnUse">
              <path d="M 60 0 L 0 0 0 60" fill="none" stroke="rgba(53, 234, 82, 0.08)" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#gridDarkMatrix)" />
          <line x1="0" y1="20%" x2="100%" y2="20%" className="grid-line" style={{ animationDelay: "0.5s" }} />
          <line x1="0" y1="80%" x2="100%" y2="80%" className="grid-line" style={{ animationDelay: "1s" }} />
          <line x1="20%" y1="0" x2="20%" y2="100%" className="grid-line" style={{ animationDelay: "1.5s" }} />
          <line x1="80%" y1="0" x2="80%" y2="100%" className="grid-line" style={{ animationDelay: "2s" }} />
          <line x1="50%" y1="0" x2="50%" y2="100%" className="grid-line" style={{ animationDelay: "2.5s", opacity: "0.05" }} />
          <line x1="0" y1="50%" x2="100%" y2="50%" className="grid-line" style={{ animationDelay: "3s", opacity: "0.05" }} />
          <circle cx="20%" cy="20%" r="2.5" className="detail-dot" style={{ animationDelay: "3s" }} />
          <circle cx="80%" cy="20%" r="2.5" className="detail-dot" style={{ animationDelay: "3.2s" }} />
          <circle cx="20%" cy="80%" r="2.5" className="detail-dot" style={{ animationDelay: "3.4s" }} />
          <circle cx="80%" cy="80%" r="2.5" className="detail-dot" style={{ animationDelay: "3.6s" }} />
          <circle cx="50%" cy="50%" r="2" className="detail-dot" style={{ animationDelay: "4s" }} />
        </svg>

        {/* Responsive Corner Elements */}
        <div className="corner-element-animate top-4 left-4 sm:top-6 sm:left-6 md:top-8 md:left-8" style={{ animationDelay: "1s" }}>
          <div className="absolute top-0 left-0 w-2 h-2 bg-[#35ea52] opacity-60 rounded-full"></div>
        </div>
        <div className="corner-element-animate top-4 right-4 sm:top-6 sm:right-6 md:top-8 md:right-8" style={{ animationDelay: "1.2s" }}>
          <div className="absolute top-0 right-0 w-2 h-2 bg-[#35ea52] opacity-60 rounded-full"></div>
        </div>
        <div className="corner-element-animate bottom-4 left-4 sm:bottom-6 sm:left-6 md:bottom-8 md:left-8" style={{ animationDelay: "1.4s" }}>
          <div className="absolute bottom-0 left-0 w-2 h-2 bg-[#35ea52] opacity-60 rounded-full"></div>
        </div>
        <div className="corner-element-animate bottom-4 right-4 sm:bottom-6 sm:right-6 md:bottom-8 md:right-8" style={{ animationDelay: "1.6s" }}>
          <div className="absolute bottom-0 right-0 w-2 h-2 bg-[#35ea52] opacity-60 rounded-full"></div>
        </div>

        {/* Floating particles */}
        <div className="floating-element-animate" style={{ top: "25%", left: "15%", animationDelay: "0.5s" }}></div>
        <div className="floating-element-animate" style={{ top: "60%", left: "85%", animationDelay: "1s" }}></div>
        <div className="floating-element-animate" style={{ top: "40%", left: "10%", animationDelay: "1.5s" }}></div>
        <div className="floating-element-animate" style={{ top: "75%", left: "90%", animationDelay: "2s" }}></div>

        {/* Responsive Main Content */}
        <div className="relative z-10 min-h-screen flex flex-col justify-between items-center px-6 py-10 sm:px-8 sm:py-12 md:px-16 md:py-16">
          {/* Top Header Badge */}
          <div className="text-center space-y-2">
            <div className="inline-flex items-center gap-2 border border-[#35ea52]/30 bg-[#35ea52]/[0.08] px-3.5 py-1 text-[11px] font-mono tracking-widest text-[#35ea52] uppercase">
              <span className="w-1.5 h-1.5 rounded-full bg-[#35ea52] animate-ping" />
              <span>{topTagline}</span>
              <span className="opacity-40">/</span>
              <span className="text-foreground/80">{topSubtag}</span>
            </div>
            <div className="mt-3 w-16 sm:w-24 h-px bg-gradient-to-r from-transparent via-[#35ea52] to-transparent opacity-40 mx-auto"></div>
          </div>

          {/* Center Hero Heading & Slogan */}
          <div className="text-center max-w-5xl mx-auto relative my-auto py-6">
            <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold leading-tight tracking-tight text-slate-100 text-decoration-animate">
              {/* Line 1 */}
              <div className="mb-2 md:mb-3">
                {headingWords1.map((w, i) => (
                  <span key={i} className="word-animate" data-delay={400 + i * 120}>
                    {w}
                  </span>
                ))}
              </div>

              {/* Line 2 */}
              <div className="mb-4 md:mb-5 text-[#35ea52]">
                {headingWords2.map((w, i) => (
                  <span key={i} className="word-animate font-extrabold" data-delay={700 + i * 120}>
                    {w}
                  </span>
                ))}
              </div>

              {/* Line 3: Slogan Subtitle */}
              <div className="text-base sm:text-lg md:text-xl font-normal text-slate-400 leading-relaxed tracking-normal max-w-3xl mx-auto mt-4 font-sans">
                <span className="word-animate" data-delay="1200">
                  {subHeading}
                </span>
              </div>
            </h1>

            {/* Feature Pills / Capabilities */}
            <div className="flex flex-wrap justify-center gap-3 mt-8 opacity-0" style={{ animation: "word-appear 0.8s ease-out forwards", animationDelay: "1.6s" }}>
              <div className="flex items-center gap-1.5 px-3 py-1 border border-foreground/15 bg-foreground/[0.02] text-xs text-foreground/70">
                <Sparkles className="h-3.5 w-3.5 text-[#35ea52]" />
                <span>Playwright Crawler</span>
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1 border border-foreground/15 bg-foreground/[0.02] text-xs text-foreground/70">
                <Bot className="h-3.5 w-3.5 text-[#35ea52]" />
                <span>Gemini 3.6 Flash Multi-Agent</span>
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1 border border-foreground/15 bg-foreground/[0.02] text-xs text-foreground/70">
                <Layers className="h-3.5 w-3.5 text-[#35ea52]" />
                <span>8-Stage Campaign Pipeline</span>
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1 border border-foreground/15 bg-foreground/[0.02] text-xs text-foreground/70">
                <ShieldCheck className="h-3.5 w-3.5 text-[#35ea52]" />
                <span>QA & Policy Gate</span>
              </div>
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3.5 mt-8 opacity-0" style={{ animation: "word-appear 0.8s ease-out forwards", animationDelay: "1.9s" }}>
              <Link
                href={ctaHref}
                className="w-full sm:w-auto px-7 py-3.5 bg-[#35ea52] text-black font-bold text-xs font-mono tracking-wider hover:bg-[#35ea52]/90 transition-all flex items-center justify-center gap-2 shadow-[0_0_25px_rgba(53,234,82,0.35)] hover:scale-105"
              >
                <span>{ctaText}</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href={secondaryCtaHref}
                className="w-full sm:w-auto px-6 py-3.5 border border-foreground/25 bg-foreground/[0.02] text-foreground/80 hover:text-foreground hover:border-[#35ea52] text-xs font-mono tracking-wider transition-all flex items-center justify-center gap-2"
              >
                <Zap className="h-3.5 w-3.5 text-[#35ea52]" />
                <span>{secondaryCtaText}</span>
              </Link>
            </div>

            {/* Responsive Detail Lines */}
            <div
              className="absolute -left-6 sm:-left-8 top-1/2 transform -translate-y-1/2 w-4 sm:w-6 h-px bg-[#35ea52] opacity-0"
              style={{ animation: "word-appear 1s ease-out forwards", animationDelay: "2s" }}
            ></div>
            <div
              className="absolute -right-6 sm:-right-8 top-1/2 transform -translate-y-1/2 w-4 sm:w-6 h-px bg-[#35ea52] opacity-0"
              style={{ animation: "word-appear 1s ease-out forwards", animationDelay: "2.2s" }}
            ></div>
          </div>

          {/* Bottom Footer Section */}
          <div className="text-center space-y-2">
            <div className="mb-3 w-16 sm:w-24 h-px bg-gradient-to-r from-transparent via-[#35ea52] to-transparent opacity-40 mx-auto"></div>
            <p className="text-xs sm:text-sm font-mono font-light text-slate-300 uppercase tracking-[0.15em] opacity-80">
              <span className="word-animate" data-delay="2400">
                {bottomTagline}
              </span>
            </p>
            <div
              className="mt-4 flex justify-center space-x-3 opacity-0"
              style={{ animation: "word-appear 1s ease-out forwards", animationDelay: "2.7s" }}
            >
              <div className="w-1.5 h-1.5 bg-[#35ea52] rounded-full opacity-40"></div>
              <div className="w-1.5 h-1.5 bg-[#35ea52] rounded-full opacity-80"></div>
              <div className="w-1.5 h-1.5 bg-[#35ea52] rounded-full opacity-40"></div>
            </div>
          </div>
        </div>

        {/* Responsive Mouse Gradient */}
        <div
          id="mouse-gradient-react"
          className="w-64 h-64 blur-xl sm:w-80 sm:h-80 sm:blur-2xl md:w-[420px] md:h-[420px] md:blur-3xl"
          style={{
            left: mouseGradientStyle.left,
            top: mouseGradientStyle.top,
            opacity: mouseGradientStyle.opacity,
          }}
        ></div>

        {/* Click Ripples */}
        {ripples.map((ripple) => (
          <div key={ripple.id} className="ripple-effect" style={{ left: `${ripple.x}px`, top: `${ripple.y}px` }}></div>
        ))}
      </div>
    </>
  );
};

export default DigitalSerenity;
