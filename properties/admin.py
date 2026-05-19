from django.contrib import admin
from .models import Amenity, Property, PropertyImage


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name',)


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'price_per_night', 'is_active', 'is_published')
    list_filter = ('is_active', 'is_published', 'organization')
    search_fields = ('title', 'location')
    filter_horizontal = ('amenities',)
    inlines = [PropertyImageInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == 'ADMIN':
            return qs
        return qs.filter(organization=request.user.organization)

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        if request.user.role != 'ADMIN' and 'organization' in fields:
            fields.remove('organization')
        return fields

    def save_model(self, request, obj, form, change):
        # Si no tiene organization asignada, usar la del usuario
        if not obj.organization_id:
            obj.organization = request.user.organization
        super().save_model(request, obj, form, change)


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'order', 'is_main', 'caption')
    list_filter = ('is_main',)