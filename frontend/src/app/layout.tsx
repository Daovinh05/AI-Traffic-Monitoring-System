import type { Metadata } from "next";
import "./globals.css";
import "../components/LegacyFrame.css";

export const metadata: Metadata = {
  title: "AI Traffic Monitoring",
  description: "AI Traffic Monitoring System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <head>
        <link
          rel="stylesheet"
          href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
