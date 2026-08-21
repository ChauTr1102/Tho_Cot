import type { Metadata } from "next";
import { Geist_Mono, Inter, Space_Grotesk } from "next/font/google";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";

/**
 * The event identity's type pairing, from assets/style-guide.md: Space Grotesk
 * for display, Inter for body. Both are loaded through next/font/google, which
 * self-hosts the files at build time — no request to fonts.googleapis.com on
 * the critical path, and no flash of fallback text.
 *
 * The `vietnamese` subset is not optional here. The UI is Vietnamese and
 * latin-ext alone drops the stacked diacritics (ạ, ữ, ồ) the copy is full of.
 */
const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin", "latin-ext", "vietnamese"],
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  variable: "--font-display",
  subsets: ["latin", "latin-ext", "vietnamese"],
  display: "swap",
});

/** Numerals, timings and node ids — anything that must not jitter as it ticks. */
const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Thợ Cốt — AI Campaign Studio",
  description:
    "Dựng bộ ảnh và video sẵn đăng bán cho TikTok Shop và Shopee từ ảnh sản phẩm thật của thương hiệu.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <body
        className={`${inter.variable} ${spaceGrotesk.variable} ${geistMono.variable} bg-background flex min-h-screen flex-col font-sans antialiased`}
      >
        {/* Theme config is left as the template shipped it: the BTC palette is
            defined identically on :root and .dark, so light and dark resolve to
            the same forest identity and no surface can drift off-brand. */}
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
          <Toaster richColors position="top-right" />
        </ThemeProvider>
      </body>
    </html>
  );
}
