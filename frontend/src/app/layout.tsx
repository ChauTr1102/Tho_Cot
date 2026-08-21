import type { Metadata } from "next";
import { Inter, Space_Grotesk } from "next/font/google";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";
import { SidebarNav } from "@/components/sidebar-nav";

const fontSans = Inter({
  variable: "--font-inter",
  subsets: ["latin", "latin-ext", "vietnamese"],
});

const fontDisplay = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin", "latin-ext", "vietnamese"],
});

export const metadata: Metadata = {
  title: "Thợ cốt",
  description: "Hệ thống đa tác tử khởi tạo chiến dịch thương mại điện tử thông minh",
  icons: {
    icon: [
      { url: "/brand/logo-header.png" },
      { url: "/icon.png" },
    ],
    shortcut: "/brand/logo-header.png",
    apple: "/brand/logo-header.png",
  },
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
          <div className="bg-fx">
            <div className="glow g1"></div>
            <div className="glow g2"></div>
            <div className="glow g3"></div>
          </div>

          <SidebarNav />

          {children}

          <Toaster richColors position="top-right" />
        </ThemeProvider>
      </body>
    </html>
  );
}
