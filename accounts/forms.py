from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # パスワード欄は自動で追加されるので、それ以外の入力項目を指定する
        fields = ("username", "email", "phone_number")
