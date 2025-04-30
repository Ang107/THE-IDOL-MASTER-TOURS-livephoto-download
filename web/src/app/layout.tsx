import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Footer from "./Footer";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ツアマス ライブフォト Downloader",
  description:
    "「アイドルマスター ツアーズ」の非公式ファンサイト。ライブフォトをまとめてダウンロードできます。",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body
        className={`flex flex-col min-h-screen ${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {/* メインコンテンツ */}
        <main className="flex-1">{children}</main>

        {/* フッター */}
        <Footer />
      </body>
    </html>
  );
}
