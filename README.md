# 省人化店舗運営システム MVP

## 課題仮説
「人が行う接客」を付加価値（贅沢品）として再定義するため、
予約から入退店までの店舗オペレーションを完全にシステム化・省人化するプラットフォームを構築する。

## デモ
[Renderデプロイ後にURLを記載] or スクリーンショット

## 技術スタック
- Backend: Python 3.12 / Django 6.0
- DB: PostgreSQL（本番）/ SQLite（開発）
- Infra: GCP Cloud Run / Render
- その他: UUID, OTP（モック実装）

## 主な機能
- ユーザー登録・ログイン（AbstractUser拡張）
- 店舗一覧・予約作成（擬似決済フラグ）
- QRコード発行（UUID自動生成）
- OTP疑似認証によるチェックイン（代理入店防止）
- チェックアウト（誤操作防止の確認ダイアログ付き）

## ER図

```mermaid
***
title: "省人化店舗運営システム MVP"
***
erDiagram
    CustomUser ||--o{ Reservation : "1人のユーザーが複数の予約を持つ"
    Store ||--o{ Reservation : "1店舗に複数の予約が紐づく"

    CustomUser {
        int id PK "主キー（自動生成）"
        string username "ユーザー名"
        string email "メールアドレス"
        string password "パスワード（ハッシュ）"
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
        boolean is_paid "擬似決済フラグ（default: False）"
        uuid qr_token UK "QRコード用トークン（自動生成・一意）"
        string otp_code "ワンタイムパスワード（6桁・チェックイン時生成）"
        datetime otp_expires_at "OTP有効期限（発行から2分後）"
        boolean otp_is_used "OTP使用済みフラグ（default: False）"
        string status "RESERVED / CHECKED_IN / CHECKED_OUT / CANCELLED"
        datetime created_at "予約作成日時（自動記録）"
    }
```


## セットアップ
（手順を記載）

## 設計の意思決定
- OTPモック実装にした理由：...
- UUIDをqr_tokenに使った理由：...
