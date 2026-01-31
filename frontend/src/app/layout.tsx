import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Compute Oracle",
  description: "Self-improving agent that predicts compute cost fluctuations",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
