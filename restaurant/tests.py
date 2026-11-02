import json

from django.test import TestCase
from django.urls import reverse

from .forms import BookingForm
from .models import Booking, Menu


class ModelTests(TestCase):
    def test_menu_str_returns_name(self):
        item = Menu.objects.create(name="Greek Salad", price=12)
        self.assertEqual(str(item), "Greek Salad")

    def test_booking_str_returns_first_name(self):
        booking = Booking.objects.create(
            first_name="Momo", reservation_date="2026-11-10", reservation_slot=12
        )
        self.assertEqual(str(booking), "Momo")


class BookingFormTests(TestCase):
    def test_valid_form(self):
        form = BookingForm(
            data={"first_name": "Momo", "reservation_date": "2026-11-10", "reservation_slot": 12}
        )
        self.assertTrue(form.is_valid())

    def test_missing_name_is_invalid(self):
        form = BookingForm(data={"reservation_date": "2026-11-10", "reservation_slot": 12})
        self.assertFalse(form.is_valid())
        self.assertIn("first_name", form.errors)


class PageViewTests(TestCase):
    def test_static_pages_return_200(self):
        for name in ("home", "about", "book", "reservations", "menu"):
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_menu_lists_items(self):
        Menu.objects.create(name="Bruschetta", price=8)
        response = self.client.get(reverse("menu"))
        self.assertContains(response, "Bruschetta")

    def test_menu_item_detail_shows_description(self):
        item = Menu.objects.create(name="Pasta", price=15, menu_item_description="Fresh tagliatelle")
        response = self.client.get(reverse("menu_item", kwargs={"pk": item.pk}))
        self.assertContains(response, "Fresh tagliatelle")

    def test_book_form_post_saves_booking(self):
        self.client.post(
            reverse("book"),
            {"first_name": "Momo", "reservation_date": "2026-11-10", "reservation_slot": 14},
        )
        self.assertEqual(Booking.objects.count(), 1)


class BookingsApiTests(TestCase):
    payload = {"first_name": "Momo", "reservation_date": "2026-11-10", "reservation_slot": 12}

    def post(self, data):
        return self.client.post(reverse("bookings"), data=json.dumps(data), content_type="application/json")

    def test_post_creates_booking(self):
        self.post(self.payload)
        self.assertEqual(Booking.objects.count(), 1)

    def test_post_rejects_taken_slot(self):
        self.post(self.payload)
        response = self.post({**self.payload, "first_name": "Other"})
        self.assertEqual(Booking.objects.count(), 1)
        self.assertIn("error", response.content.decode())

    def test_same_slot_on_different_date_is_allowed(self):
        self.post(self.payload)
        self.post({**self.payload, "reservation_date": "2026-11-11"})
        self.assertEqual(Booking.objects.count(), 2)

    def test_get_filters_by_date(self):
        self.post(self.payload)
        self.post({**self.payload, "reservation_date": "2026-11-11", "reservation_slot": 13})
        response = self.client.get(reverse("bookings"), {"date": "2026-11-10"})
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["fields"]["reservation_date"], "2026-11-10")