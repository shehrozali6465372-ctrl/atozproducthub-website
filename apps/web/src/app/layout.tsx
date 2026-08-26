import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono, Lora } from "next/font/google";
import {
  SiteFooter,
  SiteHeader,
  SkipLink,
  ThemeProvider,
  ThemeScript,
} from "@atoz/design-system";
import { FOOTER_GROUPS, NAV_ITEMS, SITE } from "@/lib/site";
import "@/styles/globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });
const lora = Lora({ subsets: ["latin"], variable: "--font-lora", display: "swap" });
const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: `${SITE.name} — ${SITE.tagline}`,
    template: `%s | ${SITE.name}`,
  },
  description:
    "Premium editorial commerce across 10 curated worlds: articles, products, collections, and visual discovery.",
  metadataBase: new URL(SITE.url),
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#F7F5F0",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${inter.variable} ${lora.variable} ${jetbrainsMono.variable}`}
    >
      <head>
        <ThemeScript />
      </head>
      <body className="min-h-screen bg-surface-0 font-sans text-text-900 antialiased">
        <ThemeProvider>
          <SkipLink />
          <SiteHeader navItems={NAV_ITEMS} />
          <main id="main-content">{children}</main>
          <SiteFooter groups={FOOTER_GROUPS} />
        </ThemeProvider>
      </body>
    </html>
  );
}
