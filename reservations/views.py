import base64
import hmac
import io
import re
import secrets
from datetime import timedelta

import qrcode
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ReservationForm
from .models import Reservation, Store


def generate_qr_base64(qr_token):
    img = qrcode.make(str(qr_token))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


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
    qr_b64 = generate_qr_base64(reservation.qr_token)
    return render(
        request, "reservations/reservation_complete.html", {"reservation": reservation, "qr_b64": qr_b64}
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
    qr_b64 = generate_qr_base64(reservation.qr_token)
    return render(request, "reservations/qr_code_detail.html", {
        "reservation": reservation,
        "qr_b64": qr_b64,
    })


@login_required
@require_POST
def generate_otp(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk, user=request.user)
    if reservation.status != "RESERVED":
        messages.warning(request, "この予約はチェックイン操作できません")
        return redirect("reservations:my_reservations")

    with transaction.atomic():
        try:
            reservation = Reservation.objects.select_for_update().get(pk=pk, user=request.user)
        except Reservation.DoesNotExist:
            from django.http import Http404
            raise Http404

        if reservation.status != "RESERVED":
            messages.warning(request, "この予約はチェックイン操作できません")
            return redirect("reservations:my_reservations")

        if reservation.otp_failure_count >= 5:
            messages.error(request, "OTP認証の失敗回数が上限に達しています。管理者にお問い合わせください。")
            return redirect("reservations:my_reservations")

        now = timezone.now()
        if (
            reservation.otp_code is not None
            and reservation.otp_expires_at is not None
            and reservation.otp_expires_at > now
        ):
            return redirect("reservations:verify_otp", pk=pk)

        reservation.otp_code = f"{secrets.randbelow(1_000_000):06d}"
        reservation.otp_expires_at = now + timedelta(minutes=2)
        reservation.otp_is_used = False
        reservation.save()

    return redirect("reservations:verify_otp", pk=pk)


@login_required
def verify_otp(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk, user=request.user)
    if reservation.status != "RESERVED":
        messages.warning(request, "この予約はチェックイン操作できません")
        return redirect("reservations:my_reservations")

    if request.method != "POST":
        return render(request, "reservations/verify_otp.html", {"reservation": reservation})

    user_input = request.POST.get("otp_code", "").strip()

    if not re.fullmatch(r"\d{6}", user_input):
        messages.error(request, "OTPは6桁の数字で入力してください")
        return redirect("reservations:verify_otp", pk=pk)

    with transaction.atomic():
        try:
            reservation = Reservation.objects.select_for_update().get(pk=pk, user=request.user)
        except Reservation.DoesNotExist:
            from django.http import Http404
            raise Http404

        if reservation.status != "RESERVED":
            messages.warning(request, "この予約はチェックイン操作できません")
            return redirect("reservations:my_reservations")

        now = timezone.now()
        otp_valid = (
            reservation.otp_expires_at is not None
            and reservation.otp_code is not None
            and reservation.otp_expires_at > now
        )

        if not otp_valid:
            messages.error(request, "OTPが無効または期限切れです。再度発行してください。")
            return redirect("reservations:my_reservations")

        if reservation.otp_is_used:
            messages.error(request, "このOTPはすでに使用済みです。")
            return redirect("reservations:my_reservations")

        if reservation.otp_failure_count >= 5:
            messages.error(request, "OTP認証の失敗回数が上限に達しています。管理者にお問い合わせください。")
            return redirect("reservations:my_reservations")

        if not hmac.compare_digest(str(reservation.otp_code), str(user_input)):
            reservation.otp_failure_count += 1
            reservation.save()
            messages.error(request, f"OTPが一致しません。（失敗回数: {reservation.otp_failure_count}/5）")
            return redirect("reservations:verify_otp", pk=pk)

        reservation.status = "CHECKED_IN"
        reservation.otp_is_used = True
        reservation.otp_failure_count = 0
        reservation.save()

    messages.success(request, "チェックインが完了しました。")
    return redirect("reservations:my_reservations")


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
