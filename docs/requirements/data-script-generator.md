# データ駆動型Instagram Reelsスクリプトジェネレーター

## 概要
Instagram Reelsから高エンゲージメントコンテンツを収集し、データに基づいた日本語の台本を生成するシステム。

## 主要機能
1. **Instagram Reelsスクレイピング**
   - Playwrightステルスモードによるハッシュタグ検索
   - エンゲージメント率に基づくコンテンツフィルタリング
   - コメント収集と視聴者分析

2. **視聴者分析**
   - コメントからの年齢層・性別・興味関心の抽出
   - k-means クラスタリングによるセグメンテーション
   - Zero-Shot分類によるラベリング

3. **音声文字起こし**
   - Whisper APIによる日本語トランスクリプト生成
   - 音声のみm3u8ファイルの抽出とffmpegによる処理
   - 必要に応じたMP4動画のダウンロード

4. **台本生成**
   - 高エンゲージメントコンテンツに基づく台本構造
   - クライアント設定に基づくトーン調整
   - 複数スタイルの台本オプション提供

5. **UI機能**
   - テーマ入力とターゲット設定
   - 台本オプション選択
   - セクション単位の編集と保存

## 技術スタック
- **フロントエンド**: Next.js, TypeScript, shadcn-ui
- **バックエンド**: FastAPI, SQLite, Playwright, Whisper
- **データ処理**: k-means, Zero-Shot分類, ffmpeg
- **テスト**: Playwright E2E, GitHub Actions

## データベーススキーマ
```sql
CREATE TABLE IF NOT EXISTS reels(
  reel_id TEXT PRIMARY KEY,
  permalink TEXT, like_count INT, comment_count INT,
  audio_url TEXT, local_video TEXT, transcript TEXT,
  audience_json TEXT, scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS client_settings(
  client_id TEXT PRIMARY KEY,
  default_target TEXT,   -- {"age":"18-24","interest":"productivity"}
  tone_rules TEXT,       -- NG ワード等
  length_limit INT
);

CREATE TABLE IF NOT EXISTS scripts(
  id TEXT PRIMARY KEY,
  client_id TEXT, original_reel_id TEXT, option INT, 
  sections TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (original_reel_id) REFERENCES reels(reel_id),
  FOREIGN KEY (client_id) REFERENCES client_settings(client_id)
);
```

## APIエンドポイント
### POST /script/auto
```json
{
  "client_id": "c123",
  "theme": "AIで英語学習",
  "target": {"age":"18-24","interest":"study"},
  "need_video": false
}
```
- `target`は省略可能。省略時は`client_settings.default_target`を使用
- キーワード抽出→スクレイプ→フィルタ→台本×2(JSON sections)を返却

### POST /script/save
```json
{
  "client_id": "c123",
  "script_id": "script_uuid",
  "option": 1,
  "sections": [
    {"type": "intro", "content": "こんにちは！", "duration": 5},
    {"type": "main", "content": "今日は...", "duration": 20},
    {"type": "cta", "content": "チャンネル登録お願いします", "duration": 5}
  ]
}
```
- 選択・編集した台本をscriptsテーブルに保存

## スクレイパー使用方法
```bash
python backend/ig_scraper.py "キーワード" --top 10 --min_engage 2.0
```
- `--top`: 取得するReels数の上限
- `--min_engage`: 最小エンゲージメント率（%）
- `--need_video`: 動画もダウンロードする場合に指定

## テスト
```bash
make scraper-test  # keyword "productivity" で reels ≥3 & audience_json, transcript 非NULL
```

## 制約事項
- Instagram Graph APIは使用せず、Playwrightステルススクレイピングのみ
- メディア/書き起こしはSQLite内部保存。フロントへは要約のみ
- UI・台本とも完全日本語
