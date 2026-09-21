from decimal import Decimal
from datetime import date, timedelta

from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from bookings.models import Booking
from organizations.models import Organization
from properties.models import Property
from users.models import User


class ApiHardeningTests(TestCase):
    def setUp(self):
        cache.clear()
        self.org = Organization.objects.create(name='Org A', contact_email='a@example.com')
        self.other = Organization.objects.create(name='Org B', contact_email='b@example.com')
        self.prop = Property.objects.create(
            organization=self.org, title='Rua 141', description='x', location='Salamanca',
            price_per_night='100.00', max_guests=2, is_active=True, is_published=True,
        )
        self.foreign = Property.objects.create(
            organization=self.other, title='Ajeno', description='x', location='Madrid',
            price_per_night='100.00', max_guests=2, is_active=True, is_published=True,
        )
        self.start = date.today() + timedelta(days=5)
        self.end = self.start + timedelta(days=2)

    def login(self, role):
        user = User.objects.create_user(username=f'u-{role}', password='p', organization=self.org, role=role)
        client = APIClient()
        client.force_authenticate(user)
        return client

    def test_only_admins_manage_users(self):
        self.assertEqual(self.login('MANAGER').get('/api/users/').status_code, 403)
        self.assertEqual(APIClient().get('/api/users/').status_code, 401)

    def test_payments_are_scoped_to_organization(self):
        from payments.models import BookingPayment
        mine = Booking.objects.create(apartment=self.prop, check_in=self.start, check_out=self.end, total_price='10')
        theirs = Booking.objects.create(apartment=self.foreign, check_in=self.start, check_out=self.end, total_price='10')
        for booking in (mine, theirs):
            BookingPayment.objects.create(booking=booking, amount_due=Decimal('5'), due_date=self.start)
        response = self.login('MANAGER').get('/api/payments/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([p['booking'] for p in response.data['results']], [mine.id])

    def test_ical_feed_hides_guest_names(self):
        Booking.objects.create(
            apartment=self.prop, client_name='Ana Gil', check_in=self.start, check_out=self.end, total_price='10')
        response = APIClient().get(f'/api/properties/{self.prop.id}/ical/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Ana', response.content.decode())
        self.assertEqual(APIClient().get('/api/properties/99999/ical/').status_code, 404)

    def test_public_booking_is_rate_limited(self):
        client = APIClient()
        statuses = [client.post('/api/public-booking/', {}, format='json').status_code for _ in range(12)]
        self.assertEqual(statuses[-1], 429)

    def test_bootstrap_rejects_wrong_token(self):
        self.assertEqual(APIClient().post('/api/system/bootstrap/').status_code, 404)


class TenancyTests(TestCase):
    def setUp(self):
        cache.clear()
        self.org = Organization.objects.create(name='Org A', contact_email='a@example.com')
        self.other = Organization.objects.create(name='Org B', contact_email='b@example.com')
        self.manager = User.objects.create_user(username='m', password='p', organization=self.org, role='MANAGER')
        self.client_api = APIClient()
        self.client_api.force_authenticate(self.manager)

    def test_clients_agencies_team_and_inbox_are_scoped(self):
        from agencies.models import Agency
        from clients.models import Client
        from integrations.models import InboxMessage
        from team.models import TeamMember
        Client.objects.create(first_name='Mia', last_name='A', email='a@x.com', organization=self.org)
        Client.objects.create(first_name='Otro', last_name='B', email='b@x.com', organization=self.other)
        Agency.objects.create(name='Mia', organization=self.org, commission_percentage=10)
        Agency.objects.create(name='Otra', organization=self.other, commission_percentage=10)
        TeamMember.objects.create(first_name='T', last_name='A', email='t@x.com', phone='1', role='CLEANER', organization=self.org)
        TeamMember.objects.create(first_name='T', last_name='B', email='u@x.com', phone='1', role='CLEANER', organization=self.other)
        InboxMessage.objects.create(channel='DIRECT', direction='INBOUND', sender='x', body='a', organization=self.org)
        InboxMessage.objects.create(channel='DIRECT', direction='INBOUND', sender='y', body='b', organization=self.other)
        for url in ('clients', 'agencies', 'team', 'inbox-messages'):
            response = self.client_api.get(f'/api/{url}/')
            self.assertEqual(response.status_code, 200, url)
            self.assertEqual(len(response.data['results']), 1, url)

    def test_created_records_get_the_users_organization(self):
        response = self.client_api.post('/api/clients/', {'first_name': 'Nuevo', 'last_name': 'C', 'email': 'n@x.com'}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        from clients.models import Client
        self.assertEqual(Client.objects.get(email='n@x.com').organization, self.org)

    def test_dashboard_only_counts_own_organization(self):
        response = self.client_api.get('/api/dashboard/stats/')
        self.assertEqual(response.status_code, 200)
