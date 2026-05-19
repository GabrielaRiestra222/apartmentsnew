import uuid
import builtins
from django.db import models
from django.utils.text import slugify


def property_image_path(instance, filename):
    ext = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{ext}"
    if instance.property_id:
        return f'properties/property_{instance.property_id}/{unique_filename}'
    return f'properties/temp/{unique_filename}'


class Amenity(models.Model):
    CATEGORY_CHOICES = [
        ('INTERNET', 'Internet'),
        ('KITCHEN', 'Kitchen'),
        ('BATHROOM', 'Bathroom'),
        ('MULTIMEDIA', 'Multimedia'),
        ('COMFORT', 'Comfort'),
        ('OUTDOOR', 'Outdoor'),
        ('BUILDING', 'Building'),
        ('SERVICES', 'Services'),
        ('SAFETY', 'Safety'),
        ('ACCESSIBILITY', 'Accessibility'),
        ('RULES', 'Rules'),
        ('OTHER', 'Other'),
    ]

    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='OTHER')
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'Amenity'
        verbose_name_plural = 'Amenities'
        ordering = ['name']

    def __str__(self):
        return self.name


class Property(models.Model):
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='properties'
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    location = models.CharField(max_length=255)
    address = models.CharField(max_length=500, blank=True)

    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    cleaning_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    max_guests = models.PositiveIntegerField()
    rooms = models.PositiveIntegerField(default=1)
    bathrooms = models.PositiveIntegerField(default=1)

    check_in_time = models.TimeField(default='15:00')
    check_out_time = models.TimeField(default='11:00')
    min_nights = models.PositiveIntegerField(default=1)
    rules = models.TextField(blank=True)
    tourist_registration_number = models.CharField(max_length=120, blank=True)
    size_m2 = models.PositiveIntegerField(null=True, blank=True)
    floor = models.CharField(max_length=80, blank=True)
    construction_year = models.PositiveIntegerField(null=True, blank=True)
    renovation_year = models.PositiveIntegerField(null=True, blank=True)
    distribution = models.JSONField(default=dict, blank=True)
    beds = models.JSONField(default=list, blank=True)
    equipment = models.JSONField(default=dict, blank=True)
    warnings = models.JSONField(default=list, blank=True)

    amenities = models.ManyToManyField(Amenity, blank=True)

    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Property'
        verbose_name_plural = 'Properties'
        ordering = ['title']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class PropertyImage(models.Model):
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='images',
    )
    image_url = models.CharField(max_length=1000, blank=True)
    image_file = models.ImageField(upload_to=property_image_path, blank=True, null=True)
    caption = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_main = models.BooleanField(default=False)

    @builtins.property
    def image(self):
        if self.image_file:
            return self.image_file.url
        return self.image_url or ''

    class Meta:
        verbose_name = 'Property Image'
        verbose_name_plural = 'Property Images'
        ordering = ['order']

    def __str__(self):
        return f"Image for {self.property.title} (order={self.order})"
