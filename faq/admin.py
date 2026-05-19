from django.contrib import admin
from django import forms
from .models import FAQCategory, FAQ


class FAQInline(admin.TabularInline):
    model = FAQ
    extra = 1
    formfield_overrides = {
        FAQ._meta.get_field('question').__class__: {
            'widget': forms.TextInput(attrs={'class': 'faq-admin-text'}),
        },
        FAQ._meta.get_field('answer').__class__: {
            'widget': forms.Textarea(attrs={'class': 'faq-admin-textarea'}),
        },
    }

    class Media:
        css = {'all': ('faq/admin.css',)}


@admin.register(FAQCategory)
class FAQCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    inlines = [FAQInline]


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'is_published', 'order')
    list_filter = ('category', 'is_published')
    search_fields = ('question', 'answer')
    formfield_overrides = {
        FAQ._meta.get_field('question').__class__: {
            'widget': forms.TextInput(attrs={'class': 'faq-admin-text'}),
        },
        FAQ._meta.get_field('answer').__class__: {
            'widget': forms.Textarea(attrs={'class': 'faq-admin-textarea'}),
        },
    }

    class Media:
        css = {'all': ('faq/admin.css',)}
