import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from organizations.models import Organization
from users.models import User
from .models import Property


class PublicPropertyTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name='Riestra Salamanca',
            contact_email='hello@example.com',
        )

    def make_property(self, title, is_published):
        return Property.objects.create(
            organization=self.organization,
            title=title,
            description='Apartamento premium en Salamanca.',
            location='Salamanca',
            price_per_night='120.00',
            max_guests=2,
            is_active=True,
            is_published=is_published,
        )

    def test_public_catalog_only_returns_published_properties(self):
        published = self.make_property('Rua 141', True)
        self.make_property('Borrador interno', False)

        response = APIClient().get('/api/public/properties/')

        self.assertEqual(response.status_code, 200)
        titles = [item['title'] for item in response.data['results']]
        self.assertEqual(titles, [published.title])

    def test_public_metadata_accepts_legacy_lists_and_scalar_values(self):
        property_obj = self.make_property('Metadatos compatibles', True)
        property_obj.equipment = {
            'city': ['Salamanca'],
            'unit_number': '3A',
            'price_1_month': ['1800.00'],
            'province': [],
            'postal_code': None,
        }
        property_obj.save()

        response = APIClient().get(f'/api/public/properties/{property_obj.pk}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['city'], 'Salamanca')
        self.assertEqual(response.data['unit_number'], '3A')
        self.assertEqual(response.data['price_1_month'], '1800.00')
        self.assertEqual(response.data['province'], '')
        self.assertIsNone(response.data['postal_code'])
        self.assertEqual(response.data['country'], 'España')
        self.assertEqual(response.data['rental_type'], 'TEMPORADA')
        self.assertEqual(response.data['orientation'], 'EXTERIOR')
        self.assertEqual(response.data['housing_type'], 'PISO')


class PropertyImageUploadTests(TestCase):
    def setUp(self):
        self.temp_media_root = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.temp_media_root)
        self.override.enable()
        self.organization = Organization.objects.create(
            name='Riestra Salamanca',
            contact_email='hello@example.com',
        )
        self.user = User.objects.create_user(
            username='manager',
            password='test-pass-123',
            role='MANAGER',
            organization=self.organization,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.temp_media_root, ignore_errors=True)

    def test_upload_image_stores_file_and_returns_media_url(self):
        image = SimpleUploadedFile(
            'apartment.jpg',
            b'\xff\xd8\xff\xe0' + b'test-image',
            content_type='image/jpeg',
        )

        response = self.client.post(
            '/api/properties/upload-image/',
            {'image': image},
            format='multipart',
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['url'].startswith('/media/properties/temp/'))
        self.assertTrue(response.data['path'].startswith('properties/temp/'))

    def test_property_image_can_be_attached_to_existing_property(self):
        property_obj = Property.objects.create(
            organization=self.organization,
            title='Rua 141',
            description='Apartamento premium.',
            location='Salamanca',
            price_per_night='120.00',
            max_guests=2,
        )

        response = self.client.post(
            '/api/property-images/',
            {
                'property': property_obj.id,
                'image_url': '/media/properties/property_1/example.jpg',
                'caption': 'Principal',
                'order': 0,
                'is_main': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['property'], property_obj.id)
        self.assertEqual(property_obj.images.count(), 1)


class CRMPropertyPayloadTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name='Riestra Salamanca',
            contact_email='hello@example.com',
        )
        self.user = User.objects.create_user(
            username='crm-manager',
            password='test-pass-123',
            role='MANAGER',
            organization=self.organization,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_create_property_accepts_crm_extra_fields(self):
        response = self.client.post(
            '/api/properties/',
            {
                'title': 'Apartamento CRM completo',
                'description': 'Ficha creada desde el CRM con metadatos comerciales.',
                'location': 'Salamanca Centro',
                'address': 'Rúa Mayor',
                'unit_number': '3A',
                'city': 'Salamanca',
                'province': 'Salamanca',
                'country': 'España',
                'price_per_night': '120.00',
                'price_1_month': '1800.00',
                'cleaning_fee': '60.00',
                'max_guests': 2,
                'rooms': 1,
                'bathrooms': 1,
                'min_nights': 3,
                'check_in_time': '15:00',
                'check_out_time': '11:00',
                'rules': '',
                'tourist_registration_number': '',
                'size_m2': None,
                'floor': '',
                'construction_year': None,
                'renovation_year': None,
                'distribution': {'bedrooms': 1, 'kitchen': 1},
                'beds': [{'label': 'Cama matrimonio'}],
                'equipment': {'kitchen': ['Microondas']},
                'warnings': [],
                'warnings_text': '',
                'video_url': 'https://example.com/video',
                'resources': [{'id': 1, 'name': 'Tour', 'url': 'https://example.com/tour', 'type': 'TOUR_VIRTUAL'}],
                'images': [
                    {'image_url': '/media/properties/temp/example.jpg', 'caption': 'Principal', 'order': 0, 'is_main': True},
                ],
                'amenities': [],
                'is_active': True,
                'is_published': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['unit_number'], '3A')
        self.assertEqual(response.data['city'], 'Salamanca')
        self.assertEqual(response.data['price_1_month'], '1800.00')
        self.assertEqual(response.data['video_url'], 'https://example.com/video')
        self.assertEqual(response.data['resources'][0]['url'], 'https://example.com/tour')
        self.assertEqual(response.data['images'][0]['image_url'], '/media/properties/temp/example.jpg')

    def test_update_property_persists_title_slug_and_rules(self):
        property_obj = Property.objects.create(
            organization=self.organization,
            title='Apartamento antiguo',
            description='Ficha inicial.',
            location='Salamanca',
            price_per_night='120.00',
            max_guests=2,
            rules='Normas antiguas',
        )

        response = self.client.patch(
            f'/api/properties/{property_obj.id}/',
            {
                'title': 'Apartamento nuevo',
                'rules': 'No fumar\nNo fiestas',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200, response.data)
        property_obj.refresh_from_db()
        self.assertEqual(property_obj.title, 'Apartamento nuevo')
        self.assertEqual(property_obj.slug, 'apartamento-nuevo')
        self.assertEqual(property_obj.rules, 'No fumar\nNo fiestas')

    def test_partial_publish_update_preserves_equipment_metadata(self):
        property_obj = Property.objects.create(
            organization=self.organization,
            title='Apartamento con extras',
            description='Ficha inicial.',
            location='Salamanca',
            price_per_night='120.00',
            max_guests=2,
            equipment={
                'kitchen': ['Microondas'],
                'price_1_month': ['1800.00'],
                'owner_name': ['Riestra'],
            },
        )

        response = self.client.patch(
            f'/api/properties/{property_obj.id}/',
            {'is_published': True},
            format='json',
        )

        self.assertEqual(response.status_code, 200, response.data)
        property_obj.refresh_from_db()
        self.assertTrue(property_obj.is_published)
        self.assertEqual(property_obj.equipment['kitchen'], ['Microondas'])
        self.assertEqual(property_obj.equipment['price_1_month'], ['1800.00'])
        self.assertEqual(property_obj.equipment['owner_name'], ['Riestra'])

    def test_admin_without_organization_can_edit_property(self):
        property_obj = Property.objects.create(
            organization=self.organization,
            title='Apartamento administrado',
            description='Ficha inicial.',
            location='Salamanca',
            price_per_night='120.00',
            max_guests=2,
        )
        admin = User.objects.create_user(username='admin-no-org', role='ADMIN')
        self.client.force_authenticate(admin)

        response = self.client.patch(
            f'/api/properties/{property_obj.pk}/',
            {'title': 'Apartamento actualizado'},
            format='json',
        )

        self.assertEqual(response.status_code, 200, response.data)
        property_obj.refresh_from_db()
        self.assertEqual(property_obj.organization_id, self.organization.pk)
        self.assertEqual(property_obj.title, 'Apartamento actualizado')


class SecurityRegressionTests(TestCase):
    """Cierra los fallos de acceso, precio, propiedad y cancelación."""

    def setUp(self):
        from datetime import date, timedelta
        from django.core.cache import cache
        cache.clear()  # los límites de peticiones se guardan en caché
        self.today = date.today()
        self.org = Organization.objects.create(name='Org A', contact_email='a@example.com')
        self.other_org = Organization.objects.create(name='Org B', contact_email='b@example.com')
        self.prop = Property.objects.create(
            organization=self.org, title='Rua 141', description='x', location='Salamanca',
            price_per_night='100.00', cleaning_fee='20.00', max_guests=2,
            is_active=True, is_published=True,
            equipment={'cup_number': ['X1'], 'owner_name': ['Juan'], 'kitchen': ['Horno']},
        )
        self.foreign = Property.objects.create(
            organization=self.other_org, title='Ajeno', description='x', location='Madrid',
            price_per_night='100.00', max_guests=2, is_active=True, is_published=True,
        )
        self.user = User.objects.create_user(username='u', password='p', organization=self.org)
        self.check_in = self.today + timedelta(days=10)
        self.check_out = self.today + timedelta(days=12)

    def public_payload(self, **extra):
        data = {
            'property_id': self.prop.id, 'guest_name': 'Ana Gil', 'guest_email': 'ana@example.com',
            'check_in': str(self.check_in), 'check_out': str(self.check_out), 'guests': 2,
            'total': '1.00',
        }
        data.update(extra)
        return data

    def test_internal_catalog_requires_login(self):
        self.assertEqual(APIClient().get('/api/properties/').status_code, 401)

    def test_public_api_hides_internal_metadata(self):
        data = APIClient().get(f'/api/public/properties/{self.prop.id}/').data
        for key in ('cup_number', 'cadastral_reference', 'owner_name', 'bookings_count'):
            self.assertNotIn(key, data)
        self.assertNotIn('cup_number', data['equipment'])
        self.assertNotIn('owner_name', data['equipment'])

    def test_public_booking_ignores_client_price(self):
        response = APIClient().post('/api/public-booking/', self.public_payload(), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(str(response.data['total_price']), '220.00')

    def test_public_booking_rejects_too_many_guests(self):
        response = APIClient().post('/api/public-booking/', self.public_payload(guests=9), format='json')
        self.assertEqual(response.status_code, 400)

    def test_cannot_book_foreign_apartment(self):
        client = APIClient()
        client.force_authenticate(self.user)
        response = client.post('/api/bookings/', {
            'apartment': self.foreign.id, 'check_in': str(self.check_in),
            'check_out': str(self.check_out), 'total_price': '200.00', 'num_guests': 1,
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_cancelling_releases_dates_and_income(self):
        from accounting.models import Transaction
        from bookings.models import Booking
        from property_calendar.models import CalendarBlock
        booking = Booking.objects.create(
            apartment=self.prop, check_in=self.check_in, check_out=self.check_out,
            total_price='200.00', status='CONFIRMED',
        )
        self.assertTrue(CalendarBlock.objects.filter(booking=booking).exists())
        booking.status = 'CANCELLED'
        booking.save()
        self.assertFalse(CalendarBlock.objects.filter(booking=booking).exists())
        self.assertFalse(Transaction.objects.filter(booking=booking, is_void=False).exists())
        self.assertTrue(Transaction.objects.filter(booking=booking, is_void=True).exists())

        booking.status = 'CONFIRMED'
        booking.save()
        self.assertEqual(Transaction.objects.filter(booking=booking, is_void=False).count(), 1)
        self.assertFalse(Transaction.objects.filter(booking=booking, is_void=True).exists())

    def test_contact_form_creates_inbox_message(self):
        from integrations.models import InboxMessage
        response = APIClient().post('/api/contact/', {
            'name': 'Ana Gil', 'email': 'ana@example.com', 'guests': 2,
            'check_in': str(self.check_in), 'check_out': str(self.check_out),
            'message': 'Hola',
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        msg = InboxMessage.objects.get()
        self.assertEqual(msg.direction, 'INBOUND')
        self.assertIn('ana@example.com', msg.sender)

    def test_organization_isolation_and_roles(self):
        from bookings.models import Booking
        manager = User.objects.create_user(username='m', password='p', organization=self.org, role='MANAGER')
        owner = User.objects.create_user(username='o', password='p', organization=self.org, role='OWNER')
        client = APIClient()
        client.force_authenticate(manager)
        titles = [p['title'] for p in client.get('/api/properties/').data['results']]
        self.assertEqual(titles, ['Rua 141'])
        self.assertEqual(client.get(f'/api/properties/{self.foreign.id}/').status_code, 404)
        foreign_booking = Booking.objects.create(
            apartment=self.foreign, check_in=self.check_in, check_out=self.check_out, total_price='10')
        self.assertEqual(client.get(f'/api/bookings/{foreign_booking.id}/').status_code, 404)
        response = client.post('/api/channel-connections/', {
            'property': self.foreign.id, 'channel': 'AIRBNB', 'external_listing_id': 'x'}, format='json')
        self.assertEqual(response.status_code, 403, response.data)
        client.force_authenticate(owner)
        self.assertEqual(client.get('/api/inbox-messages/').status_code, 403)
        self.assertEqual(client.post('/api/amenities/', {'name': 'Piscina'}, format='json').status_code, 403)

    def test_n8n_webhook_requires_secret(self):
        from django.test import override_settings
        client = APIClient()
        self.assertEqual(client.post('/api/integrations/n8n/inbound/', {}, format='json').status_code, 403)
        with override_settings(N8N_INBOUND_SECRET='s3cret'):
            self.assertEqual(client.post('/api/integrations/n8n/inbound/', {}, format='json').status_code, 403)
            ok = client.post('/api/integrations/n8n/inbound/', {}, format='json', HTTP_X_APARTMENTS_SECRET='s3cret')
            self.assertEqual(ok.status_code, 200)
