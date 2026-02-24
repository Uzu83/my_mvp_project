from django.urls import path

from . import views

app_name = "reservations"

urlpatterns = [
    path("", views.store_list, name="store_list"),
]
