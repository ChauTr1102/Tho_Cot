'use client';

import { useEffect } from 'react';

export default function HeroAsciiOne() {
  useEffect(() => {
    const embedScript = document.createElement('script');
    embedScript.type = 'text/javascript';
    embedScript.textContent = `
      !function(){
        if(!window.UnicornStudio){
          window.UnicornStudio={isInitialized:!1};
          var i=document.createElement("script");
          i.src="https://cdn.jsdelivr.net/gh/hiunicornstudio/unicornstudio.js@v1.4.33/dist/unicornStudio.umd.js";
          i.onload=function(){
            window.UnicornStudio.isInitialized||(UnicornStudio.init(),window.UnicornStudio.isInitialized=!0)
          };
          (document.head || document.body).appendChild(i)
        }
      }();
    `;
    document.head.appendChild(embedScript);

    const style = document.createElement('style');
    style.textContent = `
      [data-us-project] {
        position: relative !important;
        overflow: hidden !important;
      }
      [data-us-project] canvas {
        clip-path: inset(0 0 10% 0) !important;
      }
      [data-us-project] * {
        pointer-events: none !important;
      }
      [data-us-project] a[href*="unicorn"],
      [data-us-project] button[title*="unicorn"],
      [data-us-project] div[title*="Made with"],
      [data-us-project] .unicorn-brand,
      [data-us-project] [class*="brand"],
      [data-us-project] [class*="credit"],
      [data-us-project] [class*="watermark"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        position: absolute !important;
        left: -9999px !important;
        top: -9999px !important;
      }
    `;
    document.head.appendChild(style);

    const hideBranding = () => {
      const selectors = [
        '[data-us-project]',
        '[data-us-project="OMzqyUv6M3kSnv0JeAtC"]',
        '.unicorn-studio-container',
        'canvas[aria-label*="Unicorn"]'
      ];
      selectors.forEach(selector => {
        const containers = document.querySelectorAll(selector);
        containers.forEach(container => {
          const allElements = container.querySelectorAll('*');
          allElements.forEach(el => {
            const htmlEl = el as HTMLElement;
            const text = (htmlEl.textContent || '').toLowerCase();
            const title = (htmlEl.getAttribute('title') || '').toLowerCase();
            const href = (htmlEl.getAttribute('href') || '').toLowerCase();
            if (
              text.includes('made with') ||
              text.includes('unicorn') ||
              title.includes('made with') ||
              title.includes('unicorn') ||
              href.includes('unicorn.studio')
            ) {
              htmlEl.style.display = 'none';
              htmlEl.style.visibility = 'hidden';
              htmlEl.style.opacity = '0';
              htmlEl.style.pointerEvents = 'none';
              htmlEl.style.position = 'absolute';
              htmlEl.style.left = '-9999px';
              htmlEl.style.top = '-9999px';
              try { htmlEl.remove(); } catch { /* noop */ }
            }
          });
        });
      });
    };

    hideBranding();
    const interval = setInterval(hideBranding, 50);
    setTimeout(hideBranding, 500);
    setTimeout(hideBranding, 1000);
    setTimeout(hideBranding, 2000);
    setTimeout(hideBranding, 5000);
    setTimeout(hideBranding, 10000);

    return () => {
      clearInterval(interval);
      document.head.removeChild(embedScript);
      document.head.removeChild(style);
    };
  }, []);

  return (
    <main className="relative min-h-screen overflow-hidden bg-background">
      {/* Background Animation */}
      <div className="absolute inset-0 w-full h-full hidden lg:block">
        <div
          data-us-project="OMzqyUv6M3kSnv0JeAtC"
          style={{ width: '100%', height: '100%', minHeight: '100vh' }}
        />
      </div>

      {/* Mobile stars background */}
      <div className="absolute inset-0 w-full h-full lg:hidden stars-bg"></div>

      {/* Top Header */}
      <div className="absolute top-0 left-0 right-0 z-20 border-b border-foreground/20">
        <div className="container mx-auto px-4 lg:px-8 py-3 lg:py-4 flex items-center justify-between">
          <div className="flex items-center gap-2 lg:gap-4">
            <div className="font-mono text-foreground text-xl lg:text-2xl font-bold tracking-widest italic transform -skew-x-12">
              UIMIX
            </div>
            <div className="h-3 lg:h-4 w-px bg-foreground/40"></div>
            <span className="text-foreground/60 text-[10px] lg:text-xs font-mono">EST. 2025</span>
          </div>

          <div className="hidden lg:flex items-center gap-3 text-xs font-mono text-foreground/60">
            <span>LAT: 37.7749°</span>
            <div className="w-1 h-1 bg-foreground/40 rounded-full"></div>
            <span>LONG: 122.4194°</span>
          </div>
        </div>
      </div>

      {/* Corner Frame Accents */}
      <div className="absolute top-0 left-0 w-8 h-8 lg:w-12 lg:h-12 border-t-2 border-l-2 border-foreground/30 z-20"></div>
      <div className="absolute top-0 right-0 w-8 h-8 lg:w-12 lg:h-12 border-t-2 border-r-2 border-foreground/30 z-20"></div>
      <div className="absolute left-0 w-8 h-8 lg:w-12 lg:h-12 border-b-2 border-l-2 border-foreground/30 z-20" style={{ bottom: '5vh' }}></div>
      <div className="absolute right-0 w-8 h-8 lg:w-12 lg:h-12 border-b-2 border-r-2 border-foreground/30 z-20" style={{ bottom: '5vh' }}></div>

      {/* CTA Content */}
      <div className="relative z-10 flex min-h-screen items-center justify-end pt-16 lg:pt-0" style={{ marginTop: '5vh' }}>
        <div className="w-full lg:w-1/2 px-6 lg:px-16 lg:pr-[10%]">
          <div className="max-w-lg relative lg:ml-auto">
            {/* Top decorative line */}
            <div className="flex items-center gap-2 mb-3 opacity-60">
              <div className="w-8 h-px bg-foreground"></div>
              <span className="text-foreground text-xs font-mono tracking-wider">∞</span>
              <div className="flex-1 h-px bg-foreground"></div>
            </div>

            {/* Title with dithered accent */}
            <div className="relative">
              <div className="hidden lg:block absolute -right-3 top-0 bottom-0 w-1 dither-pattern opacity-40"></div>
              <h1 className="text-2xl lg:text-5xl font-bold text-foreground mb-3 lg:mb-4 leading-tight font-mono tracking-wider whitespace-nowrap lg:-ml-[5%]" style={{ letterSpacing: '0.1em' }}>
                ENDLESS PURSUIT
              </h1>
            </div>

            {/* Decorative dots pattern - desktop only */}
            <div className="hidden lg:flex gap-1 mb-3 opacity-40">
              {Array.from({ length: 40 }).map((_, i) => (
                <div key={i} className="w-0.5 h-0.5 bg-foreground rounded-full"></div>
              ))}
            </div>

            {/* Description */}
            <div className="relative">
              <p className="text-xs lg:text-base text-gray-300 mb-5 lg:mb-6 leading-relaxed font-mono opacity-80">
                Like Sisyphus, we push forward — not despite the struggle, but because of it. Every iteration, every pixel, every line of code is our boulder.
              </p>
              <div className="hidden lg:block absolute -left-4 top-1/2 w-3 h-3 border border-foreground opacity-30" style={{ transform: 'translateY(-50%)' }}>
                <div className="absolute top-1/2 left-1/2 w-1 h-1 bg-foreground" style={{ transform: 'translate(-50%, -50%)' }}></div>
              </div>
            </div>

            {/* Buttons */}
            <div className="flex flex-col lg:flex-row gap-3 lg:gap-4">
              <button className="relative px-5 lg:px-6 py-2 lg:py-2.5 bg-transparent text-foreground font-mono text-xs lg:text-sm border border-foreground hover:bg-foreground hover:text-black transition-all duration-200 group">
                <span className="hidden lg:block absolute -top-1 -left-1 w-2 h-2 border-t border-l border-foreground opacity-0 group-hover:opacity-100 transition-opacity"></span>
                <span className="hidden lg:block absolute -bottom-1 -right-1 w-2 h-2 border-b border-r border-foreground opacity-0 group-hover:opacity-100 transition-opacity"></span>
                BEGIN THE CLIMB
              </button>
              <button className="relative px-5 lg:px-6 py-2 lg:py-2.5 bg-transparent border border-foreground text-foreground font-mono text-xs lg:text-sm hover:bg-foreground hover:text-black transition-all duration-200">
                EMBRACE THE JOURNEY
              </button>
            </div>

            {/* Bottom technical notation */}
            <div className="hidden lg:flex items-center gap-2 mt-6 opacity-40">
              <span className="text-foreground text-[11px] font-mono">∞</span>
              <div className="flex-1 h-px bg-foreground"></div>
              <span className="text-foreground text-[11px] font-mono">SISYPHUS.PROTOCOL</span>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Footer */}
      <div className="absolute left-0 right-0 z-20 border-t border-foreground/20 bg-background/40 backdrop-blur-sm" style={{ bottom: '5vh' }}>
        <div className="container mx-auto px-4 lg:px-8 py-2 lg:py-3 flex items-center justify-between">
          <div className="flex items-center gap-3 lg:gap-6 text-[10px] lg:text-[11px] font-mono text-foreground/50">
            <span className="hidden lg:inline">SYSTEM.ACTIVE</span>
            <span className="lg:hidden">SYS.ACT</span>
            <span>V1.0.0</span>
          </div>
          <div className="flex items-center gap-2 lg:gap-4 text-[10px] lg:text-[11px] font-mono text-foreground/50">
            <span className="hidden lg:inline">◐ RENDERING</span>
            <div className="flex gap-1">
              <div className="w-1 h-1 bg-foreground/60 rounded-full animate-pulse"></div>
              <div className="w-1 h-1 bg-foreground/40 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
              <div className="w-1 h-1 bg-foreground/20 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
            </div>
            <span className="hidden lg:inline">FRAME: ∞</span>
          </div>
        </div>
      </div>
    </main>
  );
}
