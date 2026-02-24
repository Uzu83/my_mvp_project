# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    # Django標準の機能に、電話番号だけを追加！
    phone_number = models.CharField(max_length=15, blank=True, verbose_name="電話番号")

    def __str__(self):
        return self.username
