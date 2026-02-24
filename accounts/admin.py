from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    # ユーザー追加時の画面に phone_number を出す
    add_fieldsets = UserAdmin.add_fieldsets + ((None, {"fields": ("phone_number",)}),)
    # ユーザー編集時の画面に phone_number を出す
    fieldsets = UserAdmin.fieldsets + (("追加情報", {"fields": ("phone_number",)}),)
    # 一覧画面に phone_number を表示する
    list_display = ("username", "email", "phone_number", "is_staff")


admin.site.register(CustomUser, CustomUserAdmin)
