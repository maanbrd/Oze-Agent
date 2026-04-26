import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Agent-OZE",
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
      <body className="flex min-h-full flex-col">{children}</body>
    </html>
  );
}
