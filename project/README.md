# FastAPI Todo API（JWT認証付き）

JWT認証付きのTodo管理APIです。  
ユーザー登録・ログイン・Todo CRUD・フィルタリング・ページネーション機能を実装しています。

---

# 使用技術

- Python 3.x
- FastAPI
- SQLAlchemy
- SQLite
- JWT（python-jose）
- passlib / bcrypt
- Pydantic v2
- pytest
- httpx

---

# 主な機能

## 認証機能
- ユーザー登録
- ログイン
- JWTトークン認証

## Todo機能
- Todo作成
- Todo一覧取得
- Todo更新
- Todo削除

## 追加機能
- 完了状態フィルタ
- 優先度フィルタ
- 作成日 / 期限ソート
- ページネーション

---

# API一覧

| メソッド | エンドポイント | 内容 |
|---|---|---|
| POST | /register | ユーザー登録 |
| POST | /login | ログイン |
| POST | /todos | Todo作成 |
| GET | /todos | Todo一覧取得 |
| PATCH | /todos/{todo_id} | Todo更新 |
| DELETE | /todos/{todo_id} | Todo削除 |

---

# セットアップ方法

## 1. リポジトリをクローン

```bash
git clone GitHubのURL
```

---

## 2. 仮想環境作成

```bash
python -m venv venv
```

---

## 3. 仮想環境起動

### Windows

```bash
venv\Scripts\activate
```

---

## 4. ライブラリインストール

```bash
pip install -r requirements.txt
```

---

## 5. .env作成

projectフォルダ内に `.env` を作成

```env
SECRET_KEY=your_secret_key
```

---

# 起動方法

```bash
uvicorn project.main:app --reload
```

---

# APIドキュメント

FastAPI標準のSwagger UI：

```text
http://127.0.0.1:8000/docs
```

---

# テスト実行

```bash
pytest
```

---

# ディレクトリ構成

```text
project/
│
├── auth.py
├── crud.py
├── database.py
├── main.py
├── models.py
├── test_main.py
├── __init__.py
├── .env
└── todo.db
```

---

# 設計で意識したこと

- JWT認証によるユーザー管理
- CRUD処理をcrud.pyへ分離
- 認証処理をauth.pyへ分離
- SQLAlchemy ORMによるDB操作
- ログ出力によるデバッグ性向上
- pytestによるAPIテスト

---

# 今後の改善予定

- PostgreSQL対応
- Docker対応
- フロントエンド追加
- 入力バリデーション強化
- リフレッシュトークン対応
