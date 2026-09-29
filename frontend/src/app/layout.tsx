import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ 
  subsets: ["latin"], 
  variable: "--font-sans",
  display: 'swap',
});

export const metadata: Metadata = {
  title: "ArogyaGrid — Federated AI for PHC Supply Chain Intelligence",
  description:
    "Multi-agent AI platform for national PHC resource intelligence and patient medicine literacy.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable}`}>
      <body className="font-[family-name:var(--font-sans)] gradient-bg text-[var(--color-ink)] bg-[var(--color-canvas)] min-h-screen">
        {children}
      </body>
    </html>
  );
}
