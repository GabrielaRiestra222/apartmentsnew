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
