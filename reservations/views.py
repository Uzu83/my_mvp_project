from django.shortcuts import render

from .models import Store  # 追記: Storeモデルをインポート

# Create your views here.


def store_list(request):
    stores = Store.objects.all()
    return render(request, "reservations/store_list.html", {"stores": stores})
