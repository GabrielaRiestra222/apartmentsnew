from django.apps import AppConfig


class BookingsConfig(AppConfig):
    name = 'bookings'
    verbose_name = 'Bookings'

    def ready(self):
        import bookings.signals  # noqa: F401
