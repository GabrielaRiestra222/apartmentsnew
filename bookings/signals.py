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
        organization=instance.apartment.organization,
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

    # Una reserva cancelada libera fechas y deja de contar como ingreso.
    if instance.status == 'CANCELLED':
        CalendarBlock.objects.filter(booking=instance).delete()
        CleaningTask.objects.filter(booking=instance, status='PENDING').delete()
        Transaction.objects.filter(booking=instance).update(is_void=True)
        return

    # Bloqueo de calendario: se crea o se actualiza con cada cambio de la reserva.
    CalendarBlock.objects.update_or_create(
        booking=instance,
        defaults={
            'property': instance.apartment,
            'start_date': instance.check_in,
            'end_date': instance.check_out,
            'reason': 'BOOKING',
        },
    )

    # Limpieza: solo al confirmar (get_or_create evita duplicados).
    if instance.status == 'CONFIRMED':
        CleaningTask.objects.get_or_create(
            booking=instance,
            defaults={
                'property': instance.apartment,
                'scheduled_date': instance.check_out,
                'status': 'PENDING',
            },
        )

    # Ingreso y comisión de agencia: al crear. Si se reactiva una reserva cancelada,
    # se recuperan los movimientos anulados en lugar de duplicarlos.
    reactivated = Transaction.objects.filter(booking=instance, is_void=True).update(is_void=False)
    if created or (not reactivated and not Transaction.objects.filter(booking=instance).exists()):
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
