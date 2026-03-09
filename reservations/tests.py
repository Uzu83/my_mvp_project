from django.test import TestCase

from .models import Store


class StoreModelTest(TestCase):
    def test_store_creation(self):
        """店舗（Store）が正しくデータベースに作成されるかをテストする"""
        store = Store.objects.create(name="テストホテル博多", capacity=100)
        self.assertEqual(store.name, "テストホテル博多")
        self.assertEqual(store.capacity, 100)
