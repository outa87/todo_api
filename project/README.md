# Todo API

Python と FastAPI を使用して開発した、ユーザー認証機能付きの Todo 管理 API です。

Todo の作成・取得・更新・削除に加え、ユーザーごとのデータ管理、期限・優先度の設定、絞り込み、並び替え、ページネーションを実装しています。

## 主な機能

- **ユーザー認証**
  - ユーザー登録・ログイン
  - パスワードのハッシュ化
  - JWT による認証
  - 認証トークンの有効期限チェック

- **Todo 管理**
  - Todo の作成・取得・更新・削除
  - タスクの期限と優先度の設定
  - 完了状態による絞り込み
  - 優先度による絞り込み
  - 作成日時・期限による並び替え
  - ページネーション

- **データ管理**
  - SQLAlchemy によるデータベース操作
  - SQLite によるデータ保存
  - ユーザーごとの Todo のアクセス制御

- **品質・エラー対応**
  - Pydantic による入力値の検証
  - ログ出力
  - pytest による自動テスト
  - 他のユーザーの Todo にアクセスできないことを確認するテスト

## 使用技術

| 技術 | 用途 |
|---|---|
| Python | アプリケーションの実装 |
| FastAPI | API の構築 |
| SQLAlchemy | データベース操作 |
| SQLite | データの保存 |
| Pydantic | リクエストデータの検証 |
| JWT（python-jose） | 認証トークンの生成・検証 |
| Passlib / bcrypt | パスワードのハッシュ化 |
| pytest | 自動テスト |
| HTTPX | API テスト用の HTTP クライアント |
| Uvicorn | アプリケーションの起動 |

## 動作環境

- Python
- Windows / PowerShell を想定した起動手順

## セットアップ

以下のコマンドは、`project` フォルダがあるプロジェクトのルートディレクトリで実行します。

### 1. 仮想環境を作成する

```powershell
python -m venv .venv
```

### 2. 仮想環境を有効にする

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. 必要なライブラリをインストールする

```powershell
python -m pip install -r requirements.txt
```

### 4. 環境変数を設定する

`project` フォルダ内に `.env` ファイルを作成し、JWT の署名に使用する秘密鍵を設定します。

```env
SECRET_KEY=自分で生成した十分に長いランダムな秘密鍵
```

秘密鍵は公開リポジトリに登録しないでください。

## 起動方法

プロジェクトのルートディレクトリで以下を実行します。

```powershell
uvicorn project.main:app --reload
```

起動後、以下の URL からアクセスできます。

- API ドキュメント: http://127.0.0.1:8000/docs
- フロントエンド: http://127.0.0.1:8000/frontend/index.html

## API 一覧

| メソッド | エンドポイント | 説明 | 認証 |
|---|---|---|---|
| POST | `/register` | ユーザー登録 | 不要 |
| POST | `/login` | ログイン・トークン取得 | 不要 |
| POST | `/todos` | Todo 作成 | 必要 |
| GET | `/todos` | Todo 一覧取得 | 必要 |
| PATCH | `/todos/{todo_id}` | Todo の完了状態を更新 | 必要 |
| DELETE | `/todos/{todo_id}` | Todo 削除 | 必要 |

### Todo 一覧取得のクエリパラメータ

| パラメータ | 説明 |
|---|---|
| `done` | 完了状態による絞り込み |
| `priority` | 優先度による絞り込み（1〜3） |
| `sort_by` | `created` または `due` による並び替え |
| `skip` | 取得を開始する位置 |
| `limit` | 取得件数（1〜100） |

例：

```text
GET /todos?done=false&priority=2&sort_by=due&skip=0&limit=10
```

この例では、未完了かつ優先度 2 の Todo を期限順に並べ、先頭から 10 件取得します。

## テスト

プロジェクトのルートディレクトリで実行します。

```powershell
python -m pytest
```

テストでは、ユーザー登録・ログイン・認証・Todo の CRUD・入力値の検証・絞り込み・並び替え・ページネーション・ユーザー間のアクセス制御などを確認します。

## セキュリティ上の注意

- パスワードはハッシュ化して保存します。
- 認証が必要な API では JWT を検証します。
- Todo の取得・更新・削除では、操作対象がログインユーザーの所有物であることを確認します。
- `.env`、データベースファイル、仮想環境は GitHub に公開しないようにします。

## 今後の改善候補

- PostgreSQL への移行
- Docker による開発・実行環境の整備
- 本番環境へのデプロイ
- CI による自動テストの実行
