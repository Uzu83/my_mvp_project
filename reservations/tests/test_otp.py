"""
OTP チェックイン機能のテスト

select_for_update() の正確な動作確認には PostgreSQL が必要。

実行方法:
  # ローカル（PostgreSQL が起動済みの場合）
  DATABASE_URL=postgres://postgres:postgres@localhost:5432/test_db \
    uv run python manage.py test reservations.tests.test_otp --settings=config.test_settings

  # CI 環境では DATABASE_URL が自動設定されるため:
  uv run python manage.py test reservations.tests.test_otp --settings=config.test_settings

  # 全テスト一括実行:
  DATABASE_URL=postgres://postgres:postgres@localhost:5432/test_db \
    uv run python manage.py test --settings=config.test_settings
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from reservations.models import Reservation, Store

User = get_user_model()


class OTPTestBase(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="テスト店舗", capacity=10)
        self.user = User.objects.create_user(username="user1", password="pass")
        self.other_user = User.objects.create_user(username="user2", password="pass")
        self.reservation = Reservation.objects.create(
            user=self.user,
            store=self.store,
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=1),
            status="RESERVED",
        )
        self.client.force_login(self.user)

    def _generate_otp_url(self, pk=None):
        return reverse("reservations:generate_otp", args=[pk or self.reservation.pk])

    def _verify_otp_url(self, pk=None):
        return reverse("reservations:verify_otp", args=[pk or self.reservation.pk])

    def _do_generate_otp(self):
        return self.client.post(self._generate_otp_url())

    def _do_verify_otp(self, otp_code):
        return self.client.post(self._verify_otp_url(), {"otp_code": otp_code})

    def _set_valid_otp(self, code="123456"):
        """OTPフィールドを直接セットするヘルパー"""
        self.reservation.otp_code = code
        self.reservation.otp_expires_at = timezone.now() + timezone.timedelta(minutes=2)
        self.reservation.otp_is_used = False
        self.reservation.save()


class OTPLockoutTest(OTPTestBase):
    def test_lockout_after_5_failures(self):
        """5回失敗するとカウンターが5になり、以降のアクセスがブロックされる"""
        self._set_valid_otp("111111")

        # 4回失敗してカウンターが4になることを確認
        for _ in range(4):
            self._do_verify_otp("999999")

        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.otp_failure_count, 4)

        # 5回目の失敗でカウンターが5になる
        self._do_verify_otp("999999")
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.otp_failure_count, 5)

        # 6回目: ロックアウト済みとしてブロックされ、カウンターは増加しない
        self._do_verify_otp("999999")
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.otp_failure_count, 5)


class OTPSuccessTest(OTPTestBase):
    def test_correct_otp_transitions_to_checked_in(self):
        """正しいOTPを入力するとステータスが CHECKED_IN になる"""
        self._set_valid_otp("123456")

        self._do_verify_otp("123456")

        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, "CHECKED_IN")
        self.assertTrue(self.reservation.otp_is_used)
        self.assertEqual(self.reservation.otp_failure_count, 0)


class OTPExpiredTest(OTPTestBase):
    def test_expired_otp_fails(self):
        """期限切れのOTPでは認証に失敗し、カウンターは増加しない"""
        self.reservation.otp_code = "123456"
        self.reservation.otp_expires_at = timezone.now() - timezone.timedelta(seconds=1)
        self.reservation.otp_is_used = False
        self.reservation.save()

        self._do_verify_otp("123456")

        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, "RESERVED")
        # 期限切れは otp_valid チェックで弾かれるためカウンター増加なし
        self.assertEqual(self.reservation.otp_failure_count, 0)


class OTPOtherUserTest(OTPTestBase):
    def test_other_user_generate_otp_returns_404(self):
        """他ユーザーの予約に対する generate_otp は 404 を返す"""
        self.client.force_login(self.other_user)
        response = self.client.post(self._generate_otp_url())
        self.assertEqual(response.status_code, 404)

    def test_other_user_verify_otp_returns_404(self):
        """他ユーザーの予約に対する verify_otp は 404 を返す"""
        self._set_valid_otp("123456")
        self.client.force_login(self.other_user)
        response = self._do_verify_otp("123456")
        self.assertEqual(response.status_code, 404)


class OTPInvalidFormatTest(OTPTestBase):
    def test_invalid_format_does_not_increment_failure_count(self):
        """非6桁入力（abc, 空文字, 12345）はカウンターが増加しない"""
        self._set_valid_otp("123456")

        for invalid_input in ["abc", "", "12345"]:
            self._do_verify_otp(invalid_input)

        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.otp_failure_count, 0)


class OTPGenerateIdempotentTest(OTPTestBase):
    def test_generate_otp_twice_does_not_regenerate_within_expiry(self):
        """有効OTP期限内に generate_otp を2回呼んでも OTP は再生成されない"""
        # 1回目: OTP を生成
        self._do_generate_otp()
        self.reservation.refresh_from_db()
        first_otp = self.reservation.otp_code
        first_expires_at = self.reservation.otp_expires_at
        self.assertIsNotNone(first_otp)

        # 2回目: 期限内なので再生成されない
        self._do_generate_otp()
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.otp_code, first_otp)
        self.assertEqual(self.reservation.otp_expires_at, first_expires_at)


class OTPUsedTest(OTPTestBase):
    def test_used_otp_fails(self):
        """使用済み OTP（otp_is_used=True）では認証に失敗する"""
        self.reservation.otp_code = "123456"
        self.reservation.otp_expires_at = timezone.now() + timezone.timedelta(minutes=2)
        self.reservation.otp_is_used = True
        self.reservation.save()

        self._do_verify_otp("123456")

        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, "RESERVED")
