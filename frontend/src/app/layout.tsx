import type { Metadata } from "next";
import { IBM_Plex_Mono, Instrument_Sans, Newsreader } from "next/font/google";

import { Providers } from "@/components/providers";

import "./globals.css";

const display = Newsreader({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["400", "600", "700"],
});

const sans = Instrument_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
  weight: ["400", "500", "600", "700"],
});

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: {
    default: "ExtractAI — Intelligent Web Scraping & Structured Data",
    template: "%s · ExtractAI",
  },
  description:
    "ExtractAI profiles any website, chooses the best scraping strategy, and returns copy-paste-ready JSON entities. Cloud jobs, scheduling, proxies, and API access.",
  keywords: [
    "web scraping",
    "data extraction",
    "structured JSON",
    "browser agent",
    "ExtractAI",
  ],
  openGraph: {
    title: "ExtractAI — Intelligent Web Scraping",
    description:
      "Paste a URL. Get ready-made entity JSON with live pipeline visibility.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="light" suppressHydrationWarning>
      <body
        className={`${display.variable} ${sans.variable} ${mono.variable} font-sans bg-void text-slate-900 dark:bg-slate-950 dark:text-slate-100`}
      >
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
