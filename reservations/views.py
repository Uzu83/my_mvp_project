import base64
import io

import qrcode
from django.contrib import messages
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


@login_required
def qr_detail(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk, user=request.user)
    if reservation.status == "CANCELLED":
        messages.warning(request, "キャンセル済みの予約です")
        return redirect("reservations:my_reservations")
    img = qrcode.make(str(reservation.qr_token))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_b64 = base64.b64encode(buffer.getvalue()).decode()
    return render(request, "reservations/qr_code_detail.html", {
        "reservation": reservation,
        "qr_b64": qr_b64,
    })


@login_required
def cancel_reservation(request, pk):
    if request.method != "POST":
        return redirect("reservations:my_reservations")

    reservation = get_object_or_404(Reservation, pk=pk, user=request.user)

    if reservation.status == "RESERVED":
        reservation.status = "CANCELLED"
        reservation.save()
        messages.success(request, "キャンセルしました")

    return redirect("reservations:my_reservations")
