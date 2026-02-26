import uuid

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ReservationForm
from .models import Store

# Create your views here.


def store_list(request):
    stores = Store.objects.all()
    return render(request, "reservations/store_list.html", {"stores": stores})


@login_required  # ログインしていないとこの画面に入れないようにする防御壁！
def create_reservation(request):
    if request.method == "POST":
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)  # まだDBには保存しない
            # 裏側で足りないデータを自動でセットする
            reservation.user = request.user
            reservation.is_paid = True
            reservation.status = "RESERVED"
            reservation.qr_token = uuid.uuid4()  # 重複しないランダムな文字列を自動生成

            reservation.save()  # 全てセットしたらDBに保存！
            return redirect("reservations:store_list")  # 完了したら店舗一覧へ
    else:
        form = ReservationForm()

    return render(request, "reservations/reserve.html", {"form": form})
