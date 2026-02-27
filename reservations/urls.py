from django.urls import path

from . import views

app_name = "reservations"

urlpatterns = [
    path("", views.store_list, name="store_list"),
    path("reserve/", views.create_reservation, name="create_reservation"),
    path("complete/<int:pk>/", views.reservation_complete, name="reservation_complete"),
    path("my/", views.my_reservations, name="my_reservations"),
]
