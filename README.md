# 省人化店舗運営システム MVP
[![CI](https://github.com/Uzu83/my_mvp_project/actions/workflows/ci.yml/badge.svg)](https://github.com/Uzu83/my_mvp_project/actions/workflows/ci.yml)

🚀 **Live Demo:** https://my-mvp-app-w6x2.onrender.com
> RenderのFreeプランのため、初回アクセス時は起動まで約1分かかる場合があります。

## プロジェクトの目的（Why）

ホテルフロントを含む様々な接客業務の経験から、「定型業務はシステムで自動化し、人間は付加価値の高い接客に集中すべきだ」という仮説を立て、その検証のために開発しています。予約から入退店までの店舗オペレーションをシステム化し、省人化を実現するプラットフォームのMVPです。

## 実装機能

**✅ 実装済み**
- カスタムユーザーモデル（`CustomUser`）による新規登録・ログイン・ログアウト
- `@login_required` によるアクセス制限ガード
- 店舗一覧の表示・予約作成（Create）・予約一覧確認（Read）
- 予約確定時のUUID自動生成による QRトークン発行
- **QRコードチケット表示**（予約完了画面・専用ページでQR画像をインライン表示、ファイル保存なし）
- **キャンセル機能**（確認ダイアログ付き・RESERVED状態のみ許可・キャンセル済み予約へのQRアクセスをブロック）
- **OTPチェックイン認証**（6桁ワンタイムパスワードによる実店舗入店確認・ブルートフォース対策付き）
- Django Admin を用いた管理画面
- Render（PostgreSQL / Gunicorn / WhiteNoise）への本番デプロイ

## 技術的ハイライト

### OTP チェックイン認証の堅牢性

単なる「6桁コードの照合」ではなく、本番運用を意識した多層防御を実装しています。

**暗号・乱数**
- `secrets.randbelow(1_000_000)` による暗号論的に安全な乱数生成。`random` モジュールは使用しない。
- `hmac.compare_digest(stored, user_input)` による定数時間比較。`==` 演算子では発生するタイミングサイドチャネル攻撃を防止。

**ブルートフォース対策**
- `otp_failure_count` カラムで失敗回数を追跡し、**5回でロックアウト**。以降の試行は OTP コードの検証に到達しない。
- フォーマット不正入力（非6桁・英字混入など）は `re.fullmatch(r"\d{6}", ...)` で弾き、カウンターを増加させない。ブルートフォーススクリプトによるカウンター消費を防ぐ。

**IDOR 防止**
- 全ての OTP ビューで `get_object_or_404(Reservation, pk=pk, user=request.user)` を使用。他ユーザーの予約 ID を推測しても 404 を返す。

**レースコンディション対策**
- `transaction.atomic()` + `select_for_update()` をセットで使用し、同一 OTP への並行リクエストによる二重チェックインを防止。本機能の結合テストには SQLite では不十分なため PostgreSQL が必須。

**CI での PostgreSQL 統合テスト**
- GitHub Actions で `postgres:15` サービスコンテナを起動し、`select_for_update()` の排他制御を含む OTP テストをCIで自動検証。ローカルと本番の差異をパイプラインで早期検出。

---

## 技術スタック

| カテゴリ | 技術 |
|---|---|
| Backend | Python 3.12 / Django 6.0 |
| QR生成 | qrcode / Pillow（Base64エンコード・メモリ処理） |
| Database | PostgreSQL（本番） / SQLite3（開発） |
| Infrastructure | Render (Web Service + PostgreSQL) |
| Package Manager | uv |

## ローカル開発環境セットアップ

```bash
git clone https://github.com/Uzu83/my_mvp_project.git
cd my_mvp_project
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

## テスト実行

```bash
# 全テスト（SQLite / 高速）
uv run python manage.py test

# アプリ単位
uv run python manage.py test reservations
uv run python manage.py test accounts

# OTP テスト（select_for_update の排他制御確認には PostgreSQL が必要）
DATABASE_URL=postgres://postgres:postgres@localhost:5432/test_db \
  uv run python manage.py test reservations.tests.test_otp --settings=config.test_settings
```

## ER図

```mermaid
erDiagram
    CustomUser ||--o{ Reservation : "1人のユーザーが複数の予約を持つ"
    Store ||--o{ Reservation : "1店舗に複数の予約が紐づく"

    CustomUser {
        int id PK
        string username
        string email
        string phone_number
    }

    Store {
        int id PK
        string name
        int capacity
    }

    Reservation {
        int id PK
        int user_id FK
        int store_id FK
        datetime start_time
        datetime end_time
        boolean is_paid
        uuid qr_token UK
        string otp_code
        datetime otp_expires_at
        boolean otp_is_used
        int otp_failure_count
        string status
        datetime created_at
    }
```

## 設計の意思決定

**Djangoを選んだ理由**
最短でMVPを構築して仮説検証を行うため。Admin機能により管理画面の実装コストを削減し、コア機能の開発に集中できる。

**OTPカラムをReservationテーブルに持たせた理由**
本MVPでは監査ログの要件がないため、別テーブルに正規化せずReservationに直接カラムを持たせて上書きする設計とした。JOIN不要でクエリをシンプルに保ち、初期の実装コストを下げる意図がある。

