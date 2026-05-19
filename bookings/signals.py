from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps


@receiver(post_save, sender='bookings.Booking')
def booking_autocreate_client(sender, instance, created, **kwargs):
    if instance.client_id is not None or not instance.client_email:
        return

    Client = apps.get_model('clients', 'Client')
    client, _ = Client.objects.get_or_create(
        email=instance.client_email,
        defaults={
            'first_name': instance.client_name.split()[0] if instance.client_name else '',
            'last_name': ' '.join(instance.client_name.split()[1:]) if instance.client_name else '',
            'phone': instance.client_phone,
        },
    )
    # Use update() to avoid re-triggering the signal
    sender.objects.filter(pk=instance.pk).update(client=client)


@receiver(post_save, sender='bookings.Booking')
def booking_post_save(sender, instance, created, **kwargs):
    CalendarBlock = apps.get_model('property_calendar', 'CalendarBlock')
    CleaningTask = apps.get_model('cleaning', 'CleaningTask')
    Transaction = apps.get_model('accounting', 'Transaction')

    # 1. Sync CalendarBlock — create or update whenever the booking changes.
    CalendarBlock.objects.update_or_create(
        booking=instance,
        defaults={
            'property': instance.apartment,
            'start_date': instance.check_in,
            'end_date': instance.check_out,
            'reason': 'BOOKING',
        },
    )

    # 2. Create CleaningTask when booking is CONFIRMED (idempotent via get_or_create).
    if instance.status == 'CONFIRMED':
        CleaningTask.objects.get_or_create(
            booking=instance,
            defaults={
                'property': instance.apartment,
                'scheduled_date': instance.check_out,
                'status': 'PENDING',
            },
        )

    # 3 & 4. Income + optional agency commission — only on first creation.
    if created:
        Transaction.objects.create(
            property=instance.apartment,
            booking=instance,
            category='INCOME',
            subcategory='Booking payment',
            amount=instance.total_price,
            date=instance.check_in,
        )

        if instance.agency_id:
            commission = (
                instance.total_price
                * Decimal(str(instance.agency.commission_percentage))
                / Decimal('100')
            )
            Transaction.objects.create(
                property=instance.apartment,
                booking=instance,
                category='EXPENSE',
                subcategory='Agency commission',
                amount=commission,
                date=instance.check_in,
            )
