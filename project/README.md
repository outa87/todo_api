# Todo API（FastAPI）

## 概要
FastAPIを使ったTodo管理APIです。  
JWT認証とユーザーごとの権限制御を実装しています。

---

## URL
※デプロイ後に追記

---

## 機能

- ユーザー登録 / ログイン（JWT認証）
- Todo作成 / 取得 / 更新 / 削除
- ユーザーごとのデータ管理（他人のデータにアクセス不可）
- フィルタ（done, priority）
- 並び替え（created_at, due_date）
- ページネーション（skip, limit）

---

## 使用技術

- Python
- FastAPI
- SQLAlchemy
- SQLite
- JWT（python-jose）
- passlib（bcrypt）
- pytest

---

## API例

### ログイン

POST /login

### Todo取得

GET /todos?skip=0&limit=10

---

## 工夫した点

- JWT認証によるセキュリティ設計
- ユーザーごとのデータ分離（認可）
- フィルタ・並び替え・ページネーション対応
- ログ出力によるデバッグ性向上
- テストによる動作保証

---

## 今後の改善

- フロントエンド追加
- Docker対応
- PostgreSQL移行