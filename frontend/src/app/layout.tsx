import type { Metadata } from "next";
import { Inter, Space_Grotesk } from "next/font/google";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";
import { SidebarNav } from "@/components/sidebar-nav";

const fontSans = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const fontDisplay = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CAIBS - Multi-Agent Campaign Platform",
  description: "AI-driven product campaign generation",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark h-full" suppressHydrationWarning>
      <body
        className={`${fontSans.variable} ${fontDisplay.variable} min-h-screen bg-background text-foreground/80 font-sans antialiased flex flex-col relative`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          forcedTheme="dark"
          disableTransitionOnChange
        >
          {/* Global Corner Frame Accents */}
          <div className="fixed top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-foreground/20 z-50 pointer-events-none" />
          <div className="fixed top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-foreground/20 z-50 pointer-events-none" />
          <div className="fixed bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-foreground/20 z-50 pointer-events-none" />
          <div className="fixed bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-foreground/20 z-50 pointer-events-none" />

          <div className="bg-fx">
            <div className="glow g1"></div>
            <div className="glow g2"></div>
            <div className="glow g3"></div>
          </div>

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
                  <span>HỆ THỐNG.HOẠT ĐỘNG</span>
                </div>
                <span>V2.0.0</span>
              </div>
              <div className="flex items-center gap-4 text-[10px] font-mono text-foreground/20 tracking-widest">
                <span>◐ LÕI.ĐA.TÁC.TỬ</span>
                <div className="flex gap-1">
                  <div className="w-1 h-1 bg-foreground/40 rounded-full animate-pulse" />
                  <div className="w-1 h-1 bg-foreground/25 rounded-full animate-pulse" style={{ animationDelay: "0.2s" }} />
                  <div className="w-1 h-1 bg-foreground/10 rounded-full animate-pulse" style={{ animationDelay: "0.4s" }} />
                </div>
                <span>KHUNG: ∞</span>
              </div>
            </div>
          </div>

          <SidebarNav />

          {children}

          <Toaster richColors position="top-right" />
        </ThemeProvider>
      </body>
    </html>
  );
}
