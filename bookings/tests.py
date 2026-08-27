from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from clients.models import Client
from organizations.models import Organization
from properties.models import Property
from users.models import User
from .models import Booking


class BookingFilterTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name='Riestra Salamanca',
            contact_email='hello@example.com',
        )
        self.user = User.objects.create_user(
            username='booking-manager',
            password='test-pass-123',
            role='MANAGER',
            organization=self.organization,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.guest = Client.objects.create(
            first_name='Gabriela',
            last_name='Lucas',
            email='gabriela@example.com',
        )
        self.apartment_1 = self.make_property('Apartamento nº 1')
        self.apartment_2 = self.make_property('Apartamento nº 2')

    def make_property(self, title):
        return Property.objects.create(
            organization=self.organization,
            title=title,
            description='Apartamento premium.',
            location='Salamanca',
            price_per_night='120.00',
            max_guests=2,
        )

    def make_booking(self, apartment, check_in):
        return Booking.objects.create(
            apartment=apartment,
            client=self.guest,
            check_in=check_in,
            check_out=date(check_in.year, check_in.month, check_in.day + 2),
            total_price='240.00',
            status='CONFIRMED',
            num_guests=1,
        )

    def test_booking_list_accepts_property_filter_for_calendar(self):
        expected = self.make_booking(self.apartment_1, date(2026, 8, 7))
        self.make_booking(self.apartment_2, date(2026, 8, 12))

        response = self.client.get('/api/bookings/', {'property': self.apartment_1.id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data['results']], [expected.id])

    def test_booking_list_accepts_apartment_filter_alias(self):
        expected = self.make_booking(self.apartment_2, date(2026, 8, 12))
        self.make_booking(self.apartment_1, date(2026, 8, 7))

        response = self.client.get('/api/bookings/', {'apartment': self.apartment_2.id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data['results']], [expected.id])
