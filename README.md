# SNS AI Agent

SNS AI Agent は、AIを活用してプロフィール、スクリプト、動画処理を生成することで、ユーザーがソーシャルメディアコンテンツを作成するのを支援するWebアプリケーションです。

## 機能

- ターゲット属性、運用目的、プラットフォームの選択（複数選択可）
- ファイルアップロード（動画、テキスト、PDF）
- AIによるアカウント名とプロフィールテキストの生成
- AIによるスクリプト生成（無制限生成可能）
- YouTube動画の字幕分析
- 詳細な成功事例データベース
- 著作権フリーの音声ライブラリ
- アスペクト比調整機能付き動画処理

## インストール方法

1. リポジトリをクローン:
```bash
git clone https://github.com/pdytokyo/sns-ai-agent.git
cd sns-ai-agent
```

2. Python仮想環境を作成して有効化:
```bash
python -m venv venv
source venv/bin/activate  # Linuxの場合
# または
venv\Scripts\activate  # Windowsの場合
```

3. 依存関係をインストール:
```bash
pip install -r requirements.txt
```

4. `.env` ファイルを作成してOpenAI APIキーを設定:
```
OPENAI_API_KEY=<YOUR_API_KEY>
```

## GitHub Container Registry (GHCR) の設定

GitHub Actionsを使用してDockerイメージをビルドし、GitHub Container Registry (GHCR) にプッシュするには、以下の手順が必要です：

1. GitHub Personal Access Token (PAT) を作成:
   - GitHubの設定 > Developer settings > Personal access tokens > Tokens (classic) に移動
   - 「Generate new token」をクリック
   - 以下のスコープを選択: `read:packages`, `write:packages`, `delete:packages`
   - トークンを生成し、安全な場所に保存

2. リポジトリのシークレットを設定:
   - リポジトリの設定 > Secrets and variables > Actions に移動
   - 以下のシークレットを追加:
     - `GHCR_USERNAME`: GitHubのユーザー名
     - `GHCR_PAT`: 生成したPersonal Access Token

これらの設定により、GitHub Actionsワークフローは自動的にDockerイメージをビルドし、GHCRにプッシュします。

## アプリケーションの実行

アプリケーションをローカルで実行するには:

```bash
uvicorn app.main_final_integration:app --reload
```

アプリケーションは http://localhost:8000 で利用可能になります。

## API エンドポイント

### クライアント管理
- `POST /api/clients` - 新しいクライアントを作成
- `POST /api/selections` - クライアントの選択を保存
- `POST /api/uploads/{client_id}` - ファイルをアップロード

### プロフィール生成
- `GET /api/generate-profiles/{client_id}` - AIプロフィールを生成
- `PUT /api/profiles/{profile_id}` - プロフィールを更新
- `PUT /api/profiles/{profile_id}/select` - プロフィールを選択

### スクリプト生成
- `GET /api/generate-scripts/{client_id}` - AIスクリプトを生成
- `PUT /api/scripts/{script_id}` - スクリプトを更新
- `PUT /api/scripts/{script_id}/select` - スクリプトを選択

### 拡張API
- `POST /generate-profile/` - クライアントのプロフィールを生成
- `POST /generate-script/` - クライアントのスクリプトを生成
- `GET /profiles/{client_id}` - クライアントのすべてのプロフィールを取得
- `GET /scripts/{client_id}` - クライアントのすべてのスクリプトを取得
- `POST /profiles/{profile_id}/select` - プロフィールを選択
- `POST /scripts/{script_id}/select` - スクリプトを選択

### 音声ライブラリ
- `GET /api/audio-library` - 著作権フリーの音声トラックを取得
- `GET /api/audio/{audio_id}` - 音声ファイルをストリーミング
- `GET /api/audio-genres` - 利用可能な音声ジャンルを取得
- `GET /api/audio-moods` - 利用可能な音声ムードを取得

### 動画処理
- `POST /api/video-processing/{client_id}` - 動画を処理
- `GET /api/video/{result_id}` - 処理済み動画をストリーミング
- `POST /process-video/` - 拡張動画処理エンドポイント

## データベーススキーマ

アプリケーションは以下のテーブルを持つSQLiteを使用しています:

- `clients` - クライアント情報
- `selections` - ターゲット属性、目的、プラットフォームのクライアント選択
- `uploads` - アップロードされたファイル
- `profiles` - AI生成プロフィール
- `scripts` - AI生成スクリプト
- `detailed_success_cases` - 成功したソーシャルメディアコンテンツのデータベース
- `client_video_transcripts` - YouTube動画の字幕
- `transcript_analysis` - 字幕分析
- `copyright_free_audio` - 音声ライブラリ
- `video_processing_results` - 動画処理結果

## アプリケーションのテスト

1. アプリケーションを起動:
```bash
uvicorn app.main_final_integration:app --reload
```

2. ブラウザを開いて以下のURLにアクセス:
```
http://localhost:8000
```

3. curlを使用してAPIエンドポイントをテスト:
```bash
curl -X GET http://localhost:8000/health
```

## トラブルシューティング

- ファイルアップロードに問題がある場合は、`app/uploads` ディレクトリが存在することを確認してください
- OpenAI APIエラーの場合は、`.env` ファイル内のAPIキーを確認してください
- アプリケーションが起動しない場合は、コンソールでエラーメッセージを確認してください
- 依存関係のインストールに問題がある場合は、Pythonのバージョンが3.8以上であることを確認してください
