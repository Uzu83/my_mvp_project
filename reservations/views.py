from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ReservationForm
from .models import Reservation, Store


# (store_list はそのまま)
def store_list(request):
    stores = Store.objects.all()
    return render(request, "reservations/store_list.html", {"stores": stores})


@login_required
def create_reservation(request):
    if request.method == "POST":
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.is_paid = True
            reservation.status = "RESERVED"
            # ✂️ QRトークン生成の行は消したぞ！DBが勝手にやってくれる！
            reservation.save()

            # 完了画面に飛ばす！
            return redirect("reservations:reservation_complete", pk=reservation.pk)
    else:
        form = ReservationForm()
    return render(request, "reservations/reserve.html", {"form": form})


# 完了画面用の処理！
@login_required
def reservation_complete(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk, user=request.user)
    return render(
        request, "reservations/reservation_complete.html", {"reservation": reservation}
    )


@login_required
def my_reservations(request):
    # ログインしているユーザーの予約だけを、新しい順（pkの大きい順）で取得する！
    reservations = Reservation.objects.filter(user=request.user).order_by("-pk")
    return render(
        request, "reservations/my_reservations.html", {"reservations": reservations}
    )
