"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";

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
      if (target) target.style.textShadow = "0 0 20px rgba(40, 200, 64, 0.45)";
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
      background-image: radial-gradient(circle, rgba(40, 200, 64, 0.10), rgba(40, 200, 64, 0.06), rgba(200, 195, 180, 0.04), transparent 70%);
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
      50% { opacity: 0.6; }
      100% { stroke-dashoffset: 0; opacity: 0.4; }
    }
    @keyframes pulse-glow {
      0%, 100% { opacity: 0.15; transform: scale(1); }
      50% { opacity: 0.4; transform: scale(1.15); }
    }
    @keyframes flyer-sway {
      0%, 100% { transform: rotate(-2.5deg); }
      30% { transform: rotate(-1deg); }
      60% { transform: rotate(-3.5deg); }
      80% { transform: rotate(-1.8deg); }
    }
    @keyframes led-border-flicker {
      0%, 100% {
        box-shadow: 3px 5px 14px rgba(0,0,0,0.4), 0 0 8px rgba(40,200,64,0.3), inset 0 0 6px rgba(40,200,64,0.08);
        border-color: rgba(40,200,64,0.4);
      }
      15% {
        box-shadow: 3px 5px 14px rgba(0,0,0,0.4), 0 0 18px rgba(40,200,64,0.7), 0 0 40px rgba(40,200,64,0.2), inset 0 0 12px rgba(40,200,64,0.15);
        border-color: rgba(40,200,64,0.9);
      }
      18% {
        box-shadow: 3px 5px 14px rgba(0,0,0,0.4), 0 0 4px rgba(40,200,64,0.15);
        border-color: rgba(40,200,64,0.2);
      }
      22% {
        box-shadow: 3px 5px 14px rgba(0,0,0,0.4), 0 0 20px rgba(40,200,64,0.75), 0 0 50px rgba(40,200,64,0.25), inset 0 0 14px rgba(40,200,64,0.18);
        border-color: rgba(40,200,64,1);
      }
      55% {
        box-shadow: 3px 5px 14px rgba(0,0,0,0.4), 0 0 12px rgba(40,200,64,0.45), inset 0 0 8px rgba(40,200,64,0.1);
        border-color: rgba(40,200,64,0.55);
      }
      70% {
        box-shadow: 3px 5px 14px rgba(0,0,0,0.4), 0 0 6px rgba(40,200,64,0.2);
        border-color: rgba(40,200,64,0.3);
      }
      73% {
        box-shadow: 3px 5px 14px rgba(0,0,0,0.4), 0 0 22px rgba(40,200,64,0.8), 0 0 45px rgba(40,200,64,0.22), inset 0 0 12px rgba(40,200,64,0.15);
        border-color: rgba(40,200,64,0.95);
      }
    }
    .word-animate {
      display: inline-block;
      opacity: 0;
      margin: 0 0.12em;
      transition: color 0.3s ease, transform 0.3s ease;
    }
    .word-animate:hover {
      color: #28C840;
      transform: translateY(-2px);
    }
    .grid-line {
      stroke: rgba(30, 80, 55, 0.3);
      stroke-width: 0.8;
      opacity: 0;
      stroke-dasharray: 6 6;
      stroke-dashoffset: 1000;
      animation: grid-draw 2s ease-out forwards;
    }
    .detail-dot {
      fill: #28C840;
      opacity: 0;
      animation: pulse-glow 3s ease-in-out infinite;
    }
    .corner-element-animate {
      position: absolute;
      width: 44px;
      height: 44px;
      border: 1px solid rgba(30, 80, 55, 0.12);
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
      height: 2px;
      background: linear-gradient(90deg, transparent, #28C840, #5BD66A, #8DE69A, transparent);
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
      background: #28C840;
      border-radius: 50%;
      opacity: 0;
      animation: float 4s ease-in-out infinite;
      animation-play-state: paused;
    }
    @keyframes float {
      0%, 100% { transform: translateY(0) translateX(0); opacity: 0.15; }
      25% { transform: translateY(-12px) translateX(6px); opacity: 0.5; }
      50% { transform: translateY(-6px) translateX(-4px); opacity: 0.3; }
      75% { transform: translateY(-18px) translateX(8px); opacity: 0.6; }
    }
    @keyframes marquee-scroll {
      0% { transform: translateX(0%); }
      100% { transform: translateX(-50%); }
    }
    .animate-marquee-infinite {
      display: flex;
      width: max-content;
      animation: marquee-scroll 38s linear infinite;
    }
    .animate-marquee-infinite:hover {
      animation-play-state: paused;
    }
    .ripple-effect {
      position: fixed;
      width: 6px;
      height: 6px;
      background: rgba(40, 200, 64, 0.5);
      border-radius: 50%;
      transform: translate(-50%, -50%);
      pointer-events: none;
      animation: pulse-glow 1s ease-out forwards;
      z-index: 9999;
    }
  `;

  return (
    <>
      <style>{pageStyles}</style>
      <div className="min-h-screen bg-gradient-to-br from-[#C8DCD9] via-[#C2D3D4] to-[#C6D7D6] text-[#0D1117] font-mono overflow-hidden relative selection:bg-[#28C840] selection:text-white">
        {/* Cyberpunk Grid Background */}
        <svg
          className="absolute inset-0 w-full h-full pointer-events-none opacity-80"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          <defs>
            <pattern id="gridDarkMatrix" width="60" height="60" patternUnits="userSpaceOnUse">
              <path d="M 60 0 L 0 0 0 60" fill="none" stroke="rgba(30, 80, 55, 0.18)" strokeWidth="0.8" />
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
          <div className="absolute top-0 left-0 w-2 h-2 bg-[#28C840] opacity-50 rounded-full"></div>
        </div>
        <div className="corner-element-animate top-4 right-4 sm:top-6 sm:right-6 md:top-8 md:right-8" style={{ animationDelay: "1.2s" }}>
          <div className="absolute top-0 right-0 w-2 h-2 bg-[#28C840] opacity-50 rounded-full"></div>
        </div>
        <div className="corner-element-animate bottom-4 left-4 sm:bottom-6 sm:left-6 md:bottom-8 md:left-8" style={{ animationDelay: "1.4s" }}>
          <div className="absolute bottom-0 left-0 w-2 h-2 bg-[#28C840] opacity-50 rounded-full"></div>
        </div>
        <div className="corner-element-animate bottom-4 right-4 sm:bottom-6 sm:right-6 md:bottom-8 md:right-8" style={{ animationDelay: "1.6s" }}>
          <div className="absolute bottom-0 right-0 w-2 h-2 bg-[#28C840] opacity-50 rounded-full"></div>
        </div>

        {/* Floating particles */}
        <div className="floating-element-animate" style={{ top: "25%", left: "15%", animationDelay: "0.5s" }}></div>
        <div className="floating-element-animate" style={{ top: "60%", left: "85%", animationDelay: "1s" }}></div>
        <div className="floating-element-animate" style={{ top: "40%", left: "10%", animationDelay: "1.5s" }}></div>
        <div className="floating-element-animate" style={{ top: "75%", left: "90%", animationDelay: "2s" }}></div>

        {/* Responsive Main Content */}
        <div className="relative z-10 min-h-screen flex flex-col justify-between items-center px-6 py-8 sm:px-8 sm:py-10 md:px-16 md:py-12">
          {/* Top Header — Logo only */}
          <div className="text-center flex flex-col items-center pt-2">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/brand/logo-header.png"
              alt="CAIBS Brand Logo"
              className="h-12 sm:h-16 w-auto object-contain drop-shadow-[0_2px_8px_rgba(0,0,0,0.25)] hover:scale-105 transition-transform"
            />
          </div>

          {/* Center Hero Heading & Slogan */}
          <div className="flex-1 flex flex-col items-center justify-center text-center max-w-5xl mx-auto w-full py-4 sm:py-8 my-auto">
            <h1 className="text-3xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold leading-[1.15] tracking-tight text-decoration-animate flex flex-wrap items-center justify-center gap-x-3 sm:gap-x-4 gap-y-1.5 max-w-4xl mx-auto">
              <span className="text-[#0D1117] flex items-center gap-2">
                <span className="word-animate" data-delay="300">Từ</span>
                <span className="word-animate" data-delay="420">Dữ</span>
                <span className="word-animate" data-delay="540">Liệu</span>
              </span>
              <span className="text-[#0D1117] flex items-center gap-2">
                <span className="word-animate" data-delay="660">Đến</span>
              </span>
              <span className="text-[#28C840] drop-shadow-[0_0_18px_rgba(40,200,64,0.25)] flex items-center gap-2">
                <span className="word-animate font-black" data-delay="780">Chiến</span>
                <span className="word-animate font-black" data-delay="900">Dịch</span>
              </span>
              <span className="text-[#28C840] drop-shadow-[0_0_18px_rgba(40,200,64,0.25)] flex items-center gap-2">
                <span className="word-animate font-black" data-delay="1020">Bùng</span>
                <span className="word-animate font-black" data-delay="1140">Nổ</span>
              </span>
            </h1>


            {/* SPONSORS & PARTNERS RUNNING DIRECTLY ON BACKGROUND */}
            <div
              className="w-full my-6 sm:my-8 overflow-hidden opacity-0"
              style={{ animation: "word-appear 0.8s ease-out forwards", animationDelay: "1.5s" }}
            >
              <div className="relative w-full overflow-hidden [mask-image:linear-gradient(to_right,transparent,black_6%,black_94%,transparent)] py-3 select-none">
                <div className="flex w-max animate-marquee-infinite items-center gap-12 select-none">
                  {/* Set 1 */}
                  <div className="flex items-center gap-12 shrink-0">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src="/brand/logo-horizontal.png"
                      alt="CAIBS"
                      className="h-7 sm:h-8 w-auto object-contain mr-2"
                    />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/dnes.png" alt="DNES" className="h-7 sm:h-8 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/ecomdy.png" alt="Ecomdy" className="h-6 sm:h-7 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/byteplus.png" alt="BytePlus" className="h-5 sm:h-6 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/printway.png" alt="Printway" className="h-5 sm:h-6 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/burgerprints.png" alt="BurgerPrints" className="h-5 sm:h-6 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/kalodata.png" alt="Kalodata" className="h-6 sm:h-7 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/wealify.png" alt="Wealify" className="h-5 sm:h-6 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/gke-logistics.png" alt="GKE Logistics" className="h-5 sm:h-6 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/pgprints.png" alt="PG Prints" className="h-5 sm:h-6 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/fristify.png" alt="Fristify" className="h-5 sm:h-6 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/innovark.png" alt="Innovark" className="h-5 sm:h-6 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/lianlian.png" alt="LianLian Global" className="h-5 sm:h-6 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/partner-swissep.png" alt="Swiss EP" className="h-5 sm:h-6 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/partner-genaifund.png" alt="GenAI Fund" className="h-5 sm:h-6 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/partner-dsa.png" alt="DSA" className="h-5 sm:h-6 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                  </div>

                  {/* Set 2 (Seamless loop copy) */}
                  <div className="flex items-center gap-12 shrink-0" aria-hidden="true">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src="/brand/logo-horizontal.png"
                      alt="CAIBS"
                      className="h-7 sm:h-8 w-auto object-contain mr-2"
                    />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/dnes.png" alt="DNES" className="h-7 sm:h-8 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/ecomdy.png" alt="Ecomdy" className="h-6 sm:h-7 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/byteplus.png" alt="BytePlus" className="h-5 sm:h-6 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/printway.png" alt="Printway" className="h-5 sm:h-6 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/burgerprints.png" alt="BurgerPrints" className="h-5 sm:h-6 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/kalodata.png" alt="Kalodata" className="h-6 sm:h-7 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/wealify.png" alt="Wealify" className="h-5 sm:h-6 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/gke-logistics.png" alt="GKE Logistics" className="h-5 sm:h-6 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/pgprints.png" alt="PG Prints" className="h-5 sm:h-6 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/fristify.png" alt="Fristify" className="h-5 sm:h-6 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/innovark.png" alt="Innovark" className="h-5 sm:h-6 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/lianlian.png" alt="LianLian Global" className="h-5 sm:h-6 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/partner-swissep.png" alt="Swiss EP" className="h-5 sm:h-6 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/partner-genaifund.png" alt="GenAI Fund" className="h-5 sm:h-6 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/sponsors/partner-dsa.png" alt="DSA" className="h-5 sm:h-6 w-auto object-contain opacity-90 hover:opacity-100 transition-all hover:scale-110 drop-shadow-[0_1px_3px_rgba(0,0,0,0.15)]" />
                  </div>
                </div>
              </div>
            </div>

            {/* CTA Button */}
            <div className="flex items-center justify-center mt-4 sm:mt-6 opacity-0" style={{ animation: "word-appear 0.8s ease-out forwards", animationDelay: "1.8s" }}>
              <Link
                href={ctaHref}
                className="px-8 sm:px-10 py-3.5 sm:py-4 bg-[#28C840] text-white font-bold text-xs sm:text-sm font-mono tracking-wider hover:bg-[#22B038] transition-all flex items-center justify-center gap-2.5 shadow-[0_0_20px_rgba(40,200,64,0.25)] hover:scale-105 rounded-sm"
              >
                <span>{ctaText}</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
            {/* Responsive Detail Lines */}
            <div
              className="absolute -left-6 sm:-left-8 top-1/2 transform -translate-y-1/2 w-4 sm:w-6 h-px bg-[#28C840] opacity-0"
              style={{ animation: "word-appear 1s ease-out forwards", animationDelay: "2s" }}
            ></div>
            <div
              className="absolute -right-6 sm:-right-8 top-1/2 transform -translate-y-1/2 w-4 sm:w-6 h-px bg-[#28C840] opacity-0"
              style={{ animation: "word-appear 1s ease-out forwards", animationDelay: "2.2s" }}
            ></div>
          </div>

          {/* Bottom Footer Section */}
          <div className="text-center space-y-2">
            <div className="mb-3 w-20 sm:w-32 h-[2px] bg-gradient-to-r from-transparent via-[#28C840] to-transparent mx-auto"></div>
            <p className="text-xs sm:text-sm font-mono font-bold text-[#0D1117]/65 uppercase tracking-[0.18em]">
              <span className="word-animate" data-delay="2400">
                {bottomTagline}
              </span>
            </p>
            <div
              className="mt-4 flex justify-center space-x-3 opacity-0"
              style={{ animation: "word-appear 1s ease-out forwards", animationDelay: "2.7s" }}
            >
              <div className="w-1.5 h-1.5 bg-[#28C840] rounded-full opacity-50"></div>
              <div className="w-1.5 h-1.5 bg-[#28C840] rounded-full opacity-80"></div>
              <div className="w-1.5 h-1.5 bg-[#28C840] rounded-full opacity-50"></div>
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
