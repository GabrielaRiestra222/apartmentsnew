from rest_framework import serializers
from .models import Amenity, Property, PropertyImage


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = '__all__'


class PropertyImageSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    image = serializers.SerializerMethodField()

    class Meta:
        model = PropertyImage
        fields = ('id', 'property', 'image', 'image_url', 'caption', 'order', 'is_main')
        read_only_fields = ('property', 'image')

    def get_image(self, obj):
        return obj.image


class PropertySerializer(serializers.ModelSerializer):
    bookings_count = serializers.SerializerMethodField(read_only=True)
    images = PropertyImageSerializer(many=True, required=False)
    amenity_details = AmenitySerializer(source='amenities', many=True, read_only=True)

    class Meta:
        model = Property
        fields = '__all__'
        read_only_fields = ('slug', 'created_at', 'organization')

    def get_bookings_count(self, obj):
        return obj.bookings.count()

    def to_internal_value(self, data):
        mutable_data = data.copy()

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
            payload = {
                'image_url': image_data.get('image_url', ''),
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


class PublicPropertySerializer(serializers.ModelSerializer):
    """Lean serializer for public landing page — no sensitive org data."""
    images = PropertyImageSerializer(many=True, read_only=True)
    amenity_details = AmenitySerializer(source='amenities', many=True, read_only=True)
    bookings_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Property
        fields = (
            'id', 'title', 'slug', 'description', 'location', 'address',
            'price_per_night', 'cleaning_fee', 'max_guests', 'rooms', 'bathrooms',
            'check_in_time', 'check_out_time', 'min_nights', 'rules',
            'tourist_registration_number', 'size_m2', 'floor',
            'construction_year', 'renovation_year', 'distribution',
            'beds', 'equipment', 'warnings',
            'amenity_details', 'images', 'bookings_count',
        )

    def get_bookings_count(self, obj):
        return obj.bookings.count()
