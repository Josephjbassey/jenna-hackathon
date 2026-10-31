import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OmniStore AI — Physical-to-Digital Micro-Commerce Engine",
  description:
    "Instant physical storefront and inventory digitization with Meta SAM 3.1, Muse Spark 1.3, and Muse Code. Built for the Meta Global AI Developer Hackathon.",
  keywords: [
    "OmniStore AI",
    "SAM 3.1",
    "Muse Spark",
    "Muse Code",
    "Micro-Commerce",
    "Meta Global AI Hackathon",
    "Build for Your World",
  ],
  authors: [{ name: "Joseph John Bassey" }],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-[#090b0e] text-slate-100 antialiased selection:bg-emerald-500 selection:text-black">
        {children}
      </body>
    </html>
  );
}
