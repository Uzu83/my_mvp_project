from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from reservations.models import Reservation, Store

User = get_user_model()


class StoreModelTest(TestCase):
    def test_store_creation(self):
        """店舗（Store）が正しくデータベースに作成されるかをテストする"""
        store = Store.objects.create(name="テストホテル博多", capacity=100)
        self.assertEqual(store.name, "テストホテル博多")
        self.assertEqual(store.capacity, 100)


class CancelReservationTest(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="テスト店舗", capacity=10)
        self.user = User.objects.create_user(username="user1", password="pass")
        self.other_user = User.objects.create_user(username="user2", password="pass")
        self.start = timezone.now()
        self.end = self.start + timezone.timedelta(hours=1)

    def _make_reservation(self, user, status="RESERVED"):
        return Reservation.objects.create(
            user=user,
            store=self.store,
            start_time=self.start,
            end_time=self.end,
            status=status,
        )

    def _cancel_url(self, pk):
        return reverse("reservations:cancel_reservation", args=[pk])

    def test_cancel_reserved_reservation(self):
        """正常系: 自分のRESERVED予約をPOSTするとCANCELLEDになる"""
        reservation = self._make_reservation(self.user, "RESERVED")
        self.client.force_login(self.user)
        self.client.post(self._cancel_url(reservation.pk))
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, "CANCELLED")

    def test_cancel_checked_in_reservation_does_not_change_status(self):
        """異常系: CHECKED_IN予約はキャンセルしてもstatusが変わらない"""
        reservation = self._make_reservation(self.user, "CHECKED_IN")
        self.client.force_login(self.user)
        self.client.post(self._cancel_url(reservation.pk))
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, "CHECKED_IN")

    def test_cancel_other_users_reservation_returns_404(self):
        """異常系: 他ユーザーの予約をキャンセルしようとすると404が返る"""
        reservation = self._make_reservation(self.other_user, "RESERVED")
        self.client.force_login(self.user)
        response = self.client.post(self._cancel_url(reservation.pk))
        self.assertEqual(response.status_code, 404)
