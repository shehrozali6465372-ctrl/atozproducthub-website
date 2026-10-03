import type { Metadata, Viewport } from "next";
import Script from "next/script";
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
    "Discover curated products, practical guides, collections, and inspiration across thoughtfully organized worlds.",
  metadataBase: new URL(SITE.url),
  applicationName: SITE.name,
  category: "shopping",
  alternates: {
    canonical: "/",
  },
  icons: {
    icon: [{ url: "/brand/logo.png", type: "image/png" }],
    apple: [{ url: "/brand/logo.png", type: "image/png" }],
  },
  openGraph: {
    type: "website",
    siteName: SITE.name,
    title: `${SITE.name} — ${SITE.tagline}`,
    description:
      "Curated products, useful ideas, guides, and collections designed for intentional discovery.",
    url: SITE.url,
    locale: "en_US",
  },
  twitter: {
    card: "summary",
    title: `${SITE.name} — ${SITE.tagline}`,
    description:
      "Curated products, useful ideas, guides, and collections designed for intentional discovery.",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f6f7f4" },
    { media: "(prefers-color-scheme: dark)", color: "#08110f" },
  ],
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
        <Script
          src="https://www.googletagmanager.com/gtag/js?id=G-31917SCQH9"
          strategy="afterInteractive"
        />
        <Script id="google-analytics" strategy="afterInteractive">
          {"window.dataLayer = window.dataLayer || [];\nfunction gtag(){dataLayer.push(arguments);}\ngtag('js', new Date());\ngtag('config', 'G-31917SCQH9');"}
        </Script>
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
