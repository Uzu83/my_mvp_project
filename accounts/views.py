from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import CustomUserCreationForm


def signup(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # 登録成功したらそのまま自動ログイン
            return redirect("reservations:store_list")
    else:
        form = CustomUserCreationForm()

    return render(request, "accounts/signup.html", {"form": form})
