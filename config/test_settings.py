"""
テスト用設定ファイル（select_for_update() のために PostgreSQL を使用）

実行方法:
  # ローカル（PostgreSQL が起動済みの場合）
  DATABASE_URL=postgres://postgres:postgres@localhost:5432/test_db \
    uv run python manage.py test --settings=config.test_settings

  # CI 環境では DATABASE_URL が自動設定されるため:
  uv run python manage.py test --settings=config.test_settings
"""
from config.settings import *  # noqa: F401, F403

import dj_database_url

# SQLite では select_for_update() がテーブルロックに降格されるため、
# OTP の同時実行制御テストには PostgreSQL が必須。
DATABASES = {
    "default": dj_database_url.config(
        default="postgres://postgres:postgres@localhost:5432/test_db",
        conn_max_age=0,
    )
}
