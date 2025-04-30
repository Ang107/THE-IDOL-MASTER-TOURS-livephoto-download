// components/Footer.tsx
import React from 'react'

export default function Footer() {
  return (
    <footer className="bg-gray-100 text-gray-700 py-6">
      <div className="max-w-screen-md mx-auto px-4 space-y-4 text-sm text-center">
        {/* サイト説明 */}
        <p>
          本サイトは「アイドルマスター ツアーズ」の非公式ファンサイトです。  
        </p>

        {/* 著作権・権利表記 */}
        <p>
          &copy; 2025 BANDAI NAMCO Entertainment Inc.  
          All rights reserved.
        </p>

        {/* リンク群 */}
        <div className="flex flex-col sm:flex-row justify-center sm:space-x-6 space-y-2 sm:space-y-0">
          <a
            href="https://github.com/Ang107/THE-IDOL-MASTER-TOURS-livephoto-downloader"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:underline"
          >
            GitHub リポジトリ
          </a>
          <a
            href="https://docs.google.com/forms/d/e/1FAIpQLSdGQvtMP5rm2zvMeDqo-oWNk8phUElR6ck71IdzeytENW-SxA/viewform?usp=header"
            className="hover:underline"
          >
            バグ報告・お問い合わせ
          </a>
          <a
            href="https://twitter.com/Ang_kyopro"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:underline"
          >
            制作者（@Ang_kyopro） 
          </a>
        </div>

        {/* 小さな注釈 */}
        <p className="text-gray-500">
          ※当サイトで提供するコンテンツの著作権はすべて公式権利者に帰属します。
        </p>
      </div>
    </footer>
  )
}
