import calendar as cal
from datetime import date
from decimal import Decimal

from django.db.models import Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounting.models import Transaction
from bookings.models import Booking
from cleaning.models import CleaningTask
from maintenance.models import MaintenanceRequest
from properties.models import Property


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = date.today()
        current_month = today.month
        current_year = today.year
        days_in_month = cal.monthrange(current_year, current_month)[1]
        month_start = date(current_year, current_month, 1)
        month_end = date(current_year, current_month, days_in_month)

        # Revenue from accounting Transactions (INCOME category)
        revenue_month = (
            Transaction.objects
            .filter(category='INCOME', date__year=current_year, date__month=current_month)
            .aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        )
        revenue_year = (
            Transaction.objects
            .filter(category='INCOME', date__year=current_year)
            .aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        )

        # Active bookings: confirmed and not yet checked out
        active_bookings = Booking.objects.filter(
            status='CONFIRMED',
            check_out__gte=today,
        ).count()

        # Today's check-ins / check-outs
        pending_checkins_today = Booking.objects.filter(
            status='CONFIRMED',
            check_in=today,
        ).count()
        pending_checkouts_today = Booking.objects.filter(
            status='CONFIRMED',
            check_out=today,
        ).count()

        # Pending payments: sum of remaining_balance for CONFIRMED bookings
        confirmed_bookings = Booking.objects.filter(status='CONFIRMED').prefetch_related('payments')
        pending_payments = sum(b.remaining_balance for b in confirmed_bookings)

        # Pending cleanings
        pending_cleanings = CleaningTask.objects.filter(
            status__in=['PENDING', 'IN_PROGRESS']
        ).count()

        # Open maintenance
        open_maintenance = MaintenanceRequest.objects.filter(
            status__in=['OPEN', 'IN_PROGRESS']
        ).count()

        # Occupancy rate: booked days this month / (total days this month × active properties)
        total_active = Property.objects.filter(is_active=True).count()
        bookings_this_month = Booking.objects.filter(
            status='CONFIRMED',
            check_in__lte=month_end,
            check_out__gt=month_start,
        )
        total_booked_days = 0
        for booking in bookings_this_month:
            overlap_start = max(booking.check_in, month_start)
            overlap_end = min(booking.check_out, month_end)
            days = (overlap_end - overlap_start).days
            if days > 0:
                total_booked_days += days

        total_possible_days = days_in_month * total_active
        occupancy_rate = (
            round((total_booked_days / total_possible_days) * 100, 1)
            if total_possible_days else 0.0
        )

        return Response({
            'total_revenue_month': revenue_month,
            'total_revenue_year': revenue_year,
            'active_bookings': active_bookings,
            'pending_checkins_today': pending_checkins_today,
            'pending_checkouts_today': pending_checkouts_today,
            'pending_payments': pending_payments,
            'pending_cleanings': pending_cleanings,
            'open_maintenance': open_maintenance,
            'occupancy_rate_percent': occupancy_rate,
        })
