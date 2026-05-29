import type { Metadata } from "next";
import { Analytics } from "@vercel/analytics/next";
import { SpeedInsights } from "@vercel/speed-insights/next";
import { NavigationProgressProvider } from "@/components/ui/navigation-bar";
import { BrandToaster } from "@/components/ui/brand-toaster";
import "./globals.css";

export const metadata: Metadata = {
  title: "Agent OZE",
  description:
    "Centrum dowodzenia handlowca OZE — przegląd lejka, plan dnia i klienci.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pl" className="h-full antialiased">
      <body className="flex min-h-full flex-col">
        <NavigationProgressProvider>
          {children}
          <BrandToaster />
        </NavigationProgressProvider>
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  );
}
