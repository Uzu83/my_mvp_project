# 省人化店舗運営システム MVP

## プロジェクトの目的（Why）
「人が行う接客」を付加価値（プレミアム）として再定義するため、予約から入退店までの店舗オペレーションをシステム化し、省人化を実現するプラットフォームのMVP（最小限のプロダクト）です。
自身の接客アルバイト経験から、「基本業務はシステムで自動化し、人間は本当に必要な接客のみを行うべきだ」という仮説を立て、その検証のために開発しています。

## 現在のステータス
**✅ Implemented（実装済み）**
- データベース設計とモデル構築（`CustomUser`, `Store`, `Reservation`）
- Django Adminを用いた管理画面の構築
- 店舗一覧ページの表示（MTVアーキテクチャの連携）

**🚧 Planned / WIP（実装予定・進行中）**
- 一般ユーザー向けの予約作成機能（擬似決済フラグ）
- QRコード発行（UUID自動生成）
- OTP（ワンタイムパスワード）を用いたチェックイン認証ロジックの実装
- Renderへのデプロイ（PostgreSQL環境）

## 技術スタック
- **Backend:** Python / Django 6.0.x
- **Database:** SQLite（開発環境） / PostgreSQL（本番想定）
- **Infrastructure:** Render（デプロイ予定）
- **Package Manager:** uv

## 開発環境セットアップ
```bash
# パッケージの同期
uv sync

# マイグレーションの適用
uv run python manage.py migrate

# 開発サーバーの起動
uv run python manage.py runserver

```

## ER図

```mermaid
erDiagram
    CustomUser ||--o{ Reservation : "1人のユーザーが複数の予約を持つ"
    Store ||--o{ Reservation : "1店舗に複数の予約が紐づく"

    CustomUser {
        int id PK "主キー（自動生成）"
        string username "ユーザー名"
        string email "メールアドレス"
        string first_name "名"
        string last_name "姓"
        string phone_number "電話番号（SMS認証用）"
    }

    Store {
        int id PK "主キー（自動生成）"
        string name "店舗名"
        int capacity "最大収容人数"
    }

    Reservation {
        int id PK "主キー（自動生成）"
        int user_id FK "CustomUser.id"
        int store_id FK "Store.id"
        datetime start_time "予約開始日時"
        datetime end_time "予約終了日時"
        boolean is_paid "擬似決済フラグ"
        uuid qr_token UK "QRコード用トークン（一意）"
        string otp_code "OTP（6桁）"
        datetime otp_expires_at "OTP有効期限"
        boolean otp_is_used "OTP使用済み"
        string status "RESERVED/CHECKED_IN/CHECKED_OUT/CANCELLED"
        datetime created_at "作成日時"
    }

```

## 設計の意思決定
<<<<<<< HEAD

* **Djangoの選定理由:**
長期間かけて開発するのではなく、最短で動くMVPを構築して仮説検証を行うため。標準搭載の強力なAdmin機能により、管理側画面の実装コストを大幅に削減できる点も採用理由です。
* **OTP（ワンタイムパスワード）のテーブル設計:**
本MVPでは監査ログの要件がないため、別テーブルに正規化せず、`Reservation`テーブルに直接カラム（`otp_code`, `otp_expires_at`等）を持たせて上書きする設計としました。これにより、JOIN不要でクエリをシンプルに保ち、初期の実装コストを下げる意図があります。

```

=======
- OTPモック実装にした理由：...
- UUIDをqr_tokenに使った理由：...

現在Phase 2進行中：店舗一覧のMTVアーキテクチャ実装完了
>>>>>>> 6dd91a446ab1b51d26eec5bff97b7753e16648f1
