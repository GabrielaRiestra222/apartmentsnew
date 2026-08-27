from rest_framework import serializers
from .models import Amenity, Property, PropertyImage


CRM_EQUIPMENT_FIELDS = (
    'unit_number',
    'city',
    'postal_code',
    'province',
    'country',
    'price_15_days',
    'price_1_month',
    'price_2_months',
    'price_3_5_months',
    'price_6_months',
    'long_stay_discount_percent',
    'last_minute_discount_percent',
    'cup_number',
    'property_registry_number',
    'cadastral_reference',
    'owner_name',
    'rental_type',
    'orientation',
    'viewpoint',
    'windows',
    'housing_type',
    'public_url',
    'video_url',
    'virtual_tour_url',
    'virtual_tour_2_url',
    'other_resources',
    'chat_url',
)

CRM_BOOLEAN_FIELDS = (
    'long_stay_discount_enabled',
    'last_minute_discount_enabled',
)

FORM_ONLY_FIELDS = (
    'bed_main',
    'bed_sofa',
    'equipment_kitchen',
    'equipment_bathroom',
    'equipment_multimedia',
    'equipment_other',
    'equipment_outdoor',
    'services_annex',
    'warnings_text',
    'resources',
)


def first_equipment_value(equipment, key, default=''):
    value = (equipment or {}).get(key, default)
    if isinstance(value, list):
        return value[0] if value else default
    return value


def normalize_equipment_value(value):
    if isinstance(value, list):
        return value
    if value is None or value == '':
        return []
    return [value]


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = '__all__'


class PropertyImageSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    property = serializers.PrimaryKeyRelatedField(queryset=Property.objects.all(), required=False)
    image = serializers.SerializerMethodField()

    class Meta:
        model = PropertyImage
        fields = ('id', 'property', 'image', 'image_url', 'caption', 'order', 'is_main')
        read_only_fields = ('image',)

    def get_image(self, obj):
        return obj.image


class PropertySerializer(serializers.ModelSerializer):
    bookings_count = serializers.SerializerMethodField(read_only=True)
    images = PropertyImageSerializer(many=True, required=False)
    amenity_details = AmenitySerializer(source='amenities', many=True, read_only=True)
    unit_number = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    postal_code = serializers.SerializerMethodField()
    province = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()
    price_15_days = serializers.SerializerMethodField()
    price_1_month = serializers.SerializerMethodField()
    price_2_months = serializers.SerializerMethodField()
    price_3_5_months = serializers.SerializerMethodField()
    price_6_months = serializers.SerializerMethodField()
    long_stay_discount_enabled = serializers.SerializerMethodField()
    long_stay_discount_percent = serializers.SerializerMethodField()
    last_minute_discount_enabled = serializers.SerializerMethodField()
    last_minute_discount_percent = serializers.SerializerMethodField()
    cup_number = serializers.SerializerMethodField()
    property_registry_number = serializers.SerializerMethodField()
    cadastral_reference = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    rental_type = serializers.SerializerMethodField()
    orientation = serializers.SerializerMethodField()
    viewpoint = serializers.SerializerMethodField()
    windows = serializers.SerializerMethodField()
    housing_type = serializers.SerializerMethodField()
    public_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    virtual_tour_url = serializers.SerializerMethodField()
    virtual_tour_2_url = serializers.SerializerMethodField()
    other_resources = serializers.SerializerMethodField()
    chat_url = serializers.SerializerMethodField()
    resources = serializers.SerializerMethodField()
    owner_account_name = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = '__all__'
        read_only_fields = ('slug', 'created_at', 'organization')

    def get_owner_account_name(self, obj):
        if not obj.owner_id:
            return None
        full_name = f"{obj.owner.first_name} {obj.owner.last_name}".strip()
        return full_name or obj.owner.username

    def get_bookings_count(self, obj):
        return obj.bookings.count()

    def get_unit_number(self, obj):
        return first_equipment_value(obj.equipment, 'unit_number')

    def get_city(self, obj):
        return first_equipment_value(obj.equipment, 'city')

    def get_postal_code(self, obj):
        return first_equipment_value(obj.equipment, 'postal_code')

    def get_province(self, obj):
        return first_equipment_value(obj.equipment, 'province')

    def get_country(self, obj):
        return first_equipment_value(obj.equipment, 'country', 'España')

    def get_price_15_days(self, obj):
        return first_equipment_value(obj.equipment, 'price_15_days')

    def get_price_1_month(self, obj):
        return first_equipment_value(obj.equipment, 'price_1_month')

    def get_price_2_months(self, obj):
        return first_equipment_value(obj.equipment, 'price_2_months')

    def get_price_3_5_months(self, obj):
        return first_equipment_value(obj.equipment, 'price_3_5_months')

    def get_price_6_months(self, obj):
        return first_equipment_value(obj.equipment, 'price_6_months')

    def get_long_stay_discount_enabled(self, obj):
        return bool(first_equipment_value(obj.equipment, 'long_stay_discount_enabled', False))

    def get_long_stay_discount_percent(self, obj):
        return first_equipment_value(obj.equipment, 'long_stay_discount_percent')

    def get_last_minute_discount_enabled(self, obj):
        return bool(first_equipment_value(obj.equipment, 'last_minute_discount_enabled', False))

    def get_last_minute_discount_percent(self, obj):
        return first_equipment_value(obj.equipment, 'last_minute_discount_percent')

    def get_cup_number(self, obj):
        return first_equipment_value(obj.equipment, 'cup_number')

    def get_property_registry_number(self, obj):
        return first_equipment_value(obj.equipment, 'property_registry_number')

    def get_cadastral_reference(self, obj):
        return first_equipment_value(obj.equipment, 'cadastral_reference')

    def get_owner_name(self, obj):
        return first_equipment_value(obj.equipment, 'owner_name')

    def get_rental_type(self, obj):
        return first_equipment_value(obj.equipment, 'rental_type', 'TEMPORADA')

    def get_orientation(self, obj):
        return first_equipment_value(obj.equipment, 'orientation', 'EXTERIOR')

    def get_viewpoint(self, obj):
        return first_equipment_value(obj.equipment, 'viewpoint')

    def get_windows(self, obj):
        return first_equipment_value(obj.equipment, 'windows')

    def get_housing_type(self, obj):
        return first_equipment_value(obj.equipment, 'housing_type', 'PISO')

    def get_public_url(self, obj):
        return first_equipment_value(obj.equipment, 'public_url')

    def get_video_url(self, obj):
        return first_equipment_value(obj.equipment, 'video_url') or first_equipment_value(obj.equipment, 'video')

    def get_virtual_tour_url(self, obj):
        return first_equipment_value(obj.equipment, 'virtual_tour_url') or first_equipment_value(obj.equipment, 'virtual_tour')

    def get_virtual_tour_2_url(self, obj):
        return first_equipment_value(obj.equipment, 'virtual_tour_2_url') or first_equipment_value(obj.equipment, 'virtual_tour_2')

    def get_other_resources(self, obj):
        value = (obj.equipment or {}).get('other_resources', [])
        return '\n'.join(value) if isinstance(value, list) else value

    def get_chat_url(self, obj):
        return first_equipment_value(obj.equipment, 'chat_url') or first_equipment_value(obj.equipment, 'chat')

    def get_resources(self, obj):
        resources = (obj.equipment or {}).get('resources')
        if isinstance(resources, list):
            return resources
        return [
            {'id': index + 1, 'name': url.split('/')[-1], 'url': url, 'type': 'OTROS'}
            for index, url in enumerate((obj.equipment or {}).get('resource_files', []))
        ]

    def to_internal_value(self, data):
        mutable_data = data.copy()
        equipment_was_provided = 'equipment' in mutable_data
        equipment = dict(mutable_data.get('equipment') or {})

        for field in CRM_EQUIPMENT_FIELDS:
            if field in mutable_data:
                equipment_was_provided = True
                equipment[field] = normalize_equipment_value(mutable_data.pop(field))

        for field in CRM_BOOLEAN_FIELDS:
            if field in mutable_data:
                equipment_was_provided = True
                equipment[field] = mutable_data.pop(field)

        resources = mutable_data.pop('resources', None)
        if resources is not None:
            equipment_was_provided = True
            equipment['resources'] = resources
            equipment['resource_files'] = [
                item.get('url') for item in resources
                if isinstance(item, dict) and item.get('url')
            ]

        for field in FORM_ONLY_FIELDS:
            mutable_data.pop(field, None)

        if equipment_was_provided:
            mutable_data['equipment'] = equipment

        amenities = mutable_data.get('amenities')
        if isinstance(amenities, list):
            mutable_data['amenities'] = [
                amenity.get('id') if isinstance(amenity, dict) else amenity
                for amenity in amenities
            ]

        return super().to_internal_value(mutable_data)

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        property_obj = super().create(validated_data)
        self._sync_images(property_obj, images_data)
        return property_obj

    def update(self, instance, validated_data):
        images_data = validated_data.pop('images', None)
        property_obj = super().update(instance, validated_data)

        if images_data is not None:
            self._sync_images(property_obj, images_data)

        return property_obj

    def _sync_images(self, property_obj, images_data):
        kept_ids = []

        for index, image_data in enumerate(images_data):
            image_id = image_data.get('id')
            image_url = image_data.get('image_url') or image_data.get('image') or ''
            payload = {
                'image_url': image_url,
                'caption': image_data.get('caption', ''),
                'order': image_data.get('order', index),
                'is_main': image_data.get('is_main', False),
            }

            if image_id:
                image_obj = PropertyImage.objects.filter(id=image_id, property=property_obj).first()
                if image_obj:
                    for key, value in payload.items():
                        setattr(image_obj, key, value)
                    image_obj.save()
                    kept_ids.append(image_obj.id)
                    continue

            image_obj = PropertyImage.objects.create(property=property_obj, **payload)
            kept_ids.append(image_obj.id)

        property_obj.images.exclude(id__in=kept_ids).delete()


class PublicPropertySerializer(PropertySerializer):
    """Lean serializer for public landing page — no sensitive org data."""

    class Meta:
        model = Property
        fields = (
            'id', 'title', 'slug', 'description', 'location', 'address',
            'unit_number', 'city', 'postal_code', 'province', 'country',
            'price_per_night', 'cleaning_fee', 'max_guests', 'rooms', 'bathrooms',
            'price_15_days', 'price_1_month', 'price_2_months',
            'price_3_5_months', 'price_6_months',
            'long_stay_discount_enabled', 'long_stay_discount_percent',
            'last_minute_discount_enabled', 'last_minute_discount_percent',
            'check_in_time', 'check_out_time', 'min_nights', 'rules',
            'tourist_registration_number', 'cup_number',
            'property_registry_number', 'cadastral_reference', 'owner_name',
            'rental_type', 'orientation', 'viewpoint', 'windows',
            'housing_type', 'public_url', 'size_m2', 'floor',
            'construction_year', 'renovation_year', 'distribution',
            'beds', 'equipment', 'warnings',
            'video_url', 'virtual_tour_url', 'virtual_tour_2_url',
            'other_resources', 'chat_url', 'resources',
            'amenity_details', 'images', 'bookings_count',
            'is_active', 'is_published',
        )
