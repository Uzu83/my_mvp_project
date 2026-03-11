from django.contrib import admin

from .models import Reservation, Store


class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "capacity")


class ReservationAdmin(admin.ModelAdmin):
    # 管理画面の予約一覧で、誰が・どこを・いつ・どういう状態か、を一目で分かるようにする
    list_display = ("user", "store", "start_time", "status", "is_paid", "otp_failure_count")
    # 予約日時やステータスで絞り込み（フィルター）ができるようにする
    list_filter = ("status", "is_paid", "store")
    # ロックアウト解除のため otp_failure_count を編集可能にする
    fields = (
        "user", "store", "start_time", "end_time", "is_paid", "status",
        "otp_code", "otp_expires_at", "otp_is_used", "otp_failure_count",
    )


admin.site.register(Store, StoreAdmin)
admin.site.register(Reservation, ReservationAdmin)
