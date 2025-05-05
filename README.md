# ツアマス ライブフォト Downloader  
## 概要
このプロジェクトは、[アイドルマスター ツアーズ (通称ツアマス)](https://bandainamco-am.co.jp/am/vg/idolmaster-tours/)のライブフォト (ゲーム内の画像データ) のダウンロードを自動化・効率化するツールです。  
ツアマスのゲーム内で表示されたQRコードの写真をアップロードすることで、QRコードを解析し、該当するライブフォトをまとめてZIP形式で取得できます。
## 公開URL
以下のURLからサービスを実際に利用できます:  
https://the-idol-master-tours-livephoto.onrender.com/  

アクセス直後に以下のような待機画面が表示される場合は、1分ほど待つとアクセス可能になります。
![image](https://github.com/user-attachments/assets/d96b8a7d-026c-4071-a375-be6ba7993446)

## 特徴
- 最大10枚のQRコード付き画像を同時にアップロード可能
- QRコードの検出とURLの有効性を検証
- 幅広い画像形式に対応: JPEG, PNG, HEIC, HEIF
- 取得した画像をキャッシュすることで外部サーバーへの負荷を軽減
- ダウンロードはZIP形式で提供
- UIはNext.js + Tailwind CSS、APIはFastAPIで構築
## インストールと起動
### 必要条件
- Docker / Docker Compose
### 起動手順
```bash
git clone https://github.com/Ang107/THE-IDOL-MASTER-TOURS-livephoto-downloader.git
cd idolmaster-tours-livephoto-downloader
docker compose up --build
```
- API: http://localhost:8000
- フロントエンド: http://localhost:3000
## 使い方
1. QRコードが写った画像を最大10枚までアップロード
2. 「検証する」をクリック
3. 有効な画像があれば「ダウンロード」ボタンが有効化される
4. ZIPファイルをダウンロード
## APIエンドポイント
### `POST /validate`  
QRコード付き画像を検証し、ライブフォトのURLの有効性をチェックします。
有効なQRコードが1枚以上あった場合は、ZIPファイルのチケットを返します。
### `Get /download/{ticket}`  
ライブフォトをZIP形式で返します。
## ライセンス
MIT LIcense

## 製作者
Ang

