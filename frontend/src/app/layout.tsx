import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "GrowthGuide",
  description:
    "A grounded product and growth knowledge assistant.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}