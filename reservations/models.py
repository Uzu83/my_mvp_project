import uuid

from django.conf import settings
from django.db import models


class Store(models.Model):
    name = models.CharField(max_length=100, verbose_name="店舗名")
    capacity = models.PositiveIntegerField(verbose_name="最大収容人数")

    def __str__(self):
        return self.name


class Reservation(models.Model):
    # 状態（ステータス）の選択肢を定義
    STATUS_CHOICES = [
        ("RESERVED", "予約済み"),
        ("CHECKED_IN", "チェックイン済み"),
        ("CHECKED_OUT", "チェックアウト済み"),
        ("CANCELLED", "キャンセル"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="ユーザー"
    )
    store = models.ForeignKey(Store, on_delete=models.PROTECT, verbose_name="店舗")
    start_time = models.DateTimeField(verbose_name="予約開始日時")
    end_time = models.DateTimeField(verbose_name="予約終了日時")

    is_paid = models.BooleanField(default=False, verbose_name="決済完了フラグ")
    # QRコードの元になるUUID（自動生成、変更不可）
    qr_token = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False, verbose_name="QRトークン"
    )

    otp_code = models.CharField(
        max_length=6, blank=True, null=True, verbose_name="OTPコード"
    )
    otp_expires_at = models.DateTimeField(
        blank=True, null=True, verbose_name="OTP有効期限"
    )
    otp_is_used = models.BooleanField(default=False, verbose_name="OTP使用済みフラグ")

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="RESERVED",
        verbose_name="ステータス",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "予約"
        verbose_name_plural = "予約一覧"

    def __str__(self):
        return f"{self.user.username} - {self.store.name} ({self.start_time.strftime('%Y-%m-%d %H:%M')})"
