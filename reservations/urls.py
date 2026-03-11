from django.urls import path

from . import views

app_name = "reservations"

urlpatterns = [
    path("", views.store_list, name="store_list"),
    path("reserve/", views.create_reservation, name="create_reservation"),
    path("complete/<int:pk>/", views.reservation_complete, name="reservation_complete"),
    path("my/", views.my_reservations, name="my_reservations"),
    path("cancel/<int:pk>/", views.cancel_reservation, name="cancel_reservation"),
    path("qr/<int:pk>/", views.qr_detail, name="qr_detail"),
    path("checkin/<int:pk>/generate-otp/", views.generate_otp, name="generate_otp"),
    path("checkin/<int:pk>/verify/", views.verify_otp, name="verify_otp"),
]
