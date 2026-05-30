from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter

from order.models import Order, OrderItems, OrderStatusChoices
from accounts.models import UserRoleChoices
from helpers.permissions import IsManagerOrAdmin
from stats.serializers.stats import (
    DashboardSerializer, TopItemSerializer, SeriesPointSerializer, WaiterStatsSerializer,
)

ACTIVE_STATUSES = [OrderStatusChoices.PREPARING, OrderStatusChoices.DELIVERED]
# tushumga kiradigan statuslar (bekor qilingani hisobga olinmaydi)
REVENUE_STATUSES = [OrderStatusChoices.PREPARING, OrderStatusChoices.DELIVERED, OrderStatusChoices.CLOSED]


def _percent_change(current, previous):
    current = float(current or 0)
    previous = float(previous or 0)
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round((current - previous) / previous * 100, 1)


@extend_schema(tags=['Stats'], summary="Dashboard statistikasi",
               description="Bugungi buyurtma soni, tushum, faol ofitsiantlar, ochiq buyurtmalar, "
                           "kechagi kunga nisbatan trend va oxirgi buyurtmalarni qaytaradi.",
               responses=DashboardSerializer)
class DashboardView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]

    def get(self, request):
        restaurant = request.user.restaurant
        today = timezone.localdate()
        yesterday = today - timedelta(days=1)

        base = Order.objects.filter(restaurant=restaurant)
        today_qs = base.filter(created__date=today)
        yesterday_qs = base.filter(created__date=yesterday)

        orders_today = today_qs.exclude(status=OrderStatusChoices.CANCELLED).count()
        revenue_today = today_qs.filter(status__in=REVENUE_STATUSES).aggregate(
            s=Sum('total_amount'))['s'] or 0
        orders_yesterday = yesterday_qs.exclude(status=OrderStatusChoices.CANCELLED).count()
        revenue_yesterday = yesterday_qs.filter(status__in=REVENUE_STATUSES).aggregate(
            s=Sum('total_amount'))['s'] or 0

        active_waiters = today_qs.filter(status__in=ACTIVE_STATUSES).values('waiter').distinct().count()
        open_orders = base.filter(status__in=ACTIVE_STATUSES).count()

        recent = base.select_related('waiter', 'location').order_by('-created')[:10]
        recent_orders = [{
            'id': o.id,
            'waiter_name': o.waiter.full_name or o.waiter.username,
            'location_name': o.location.name,
            'status': o.status,
            'total_amount': o.total_amount,
            'created': o.created,
        } for o in recent]

        data = {
            'orders_today': orders_today,
            'revenue_today': revenue_today,
            'active_waiters': active_waiters,
            'open_orders': open_orders,
            'trends': {
                'orders': _percent_change(orders_today, orders_yesterday),
                'revenue': _percent_change(revenue_today, revenue_yesterday),
            },
            'recent_orders': recent_orders,
        }
        return Response({'status': True, 'message': 'OK', 'data': data})


@extend_schema(tags=['Stats'], summary="Eng ko'p sotilgan taomlar",
               description="Berilgan davr uchun eng ko'p sotilgan taomlar (soni va tushumi bo'yicha).",
               parameters=[
                   OpenApiParameter('date', str, description="today | YYYY-MM-DD (standart: today)"),
                   OpenApiParameter('limit', int, description="Nechta taom qaytarilsin (standart: 10)"),
               ],
               responses=TopItemSerializer(many=True))
class TopItemsView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]

    def get(self, request):
        restaurant = request.user.restaurant
        limit = int(request.query_params.get('limit', 10))
        date_param = request.query_params.get('date', 'today')

        qs = OrderItems.objects.filter(order__restaurant=restaurant).exclude(
            order__status=OrderStatusChoices.CANCELLED)

        if date_param == 'today':
            qs = qs.filter(order__created__date=timezone.localdate())
        elif date_param:
            qs = qs.filter(order__created__date=date_param)

        rows = qs.values('menu_item').annotate(
            name=F('menu_item__name'),
            qty=Sum('quantity'),
            revenue=Sum('subtotal'),
        ).order_by('-qty')[:limit]

        data = [{
            'menu_id': r['menu_item'],
            'name': r['name'],
            'qty': r['qty'],
            'revenue': r['revenue'],
        } for r in rows]
        return Response({'status': True, 'message': 'OK', 'data': data})


@extend_schema(tags=['Stats'], summary="Tushum/buyurtma grafigi",
               description="Kunlik tushum va buyurtmalar grafigi uchun ma'lumot. range: 7d | 30d | 90d.",
               parameters=[OpenApiParameter('range', str, description="7d | 30d | 90d (standart: 30d)")],
               responses=SeriesPointSerializer(many=True))
class SeriesView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]

    def get(self, request):
        restaurant = request.user.restaurant
        range_param = request.query_params.get('range', '30d')
        days = {'7d': 7, '30d': 30, '90d': 90}.get(range_param, 30)

        start = timezone.localdate() - timedelta(days=days - 1)
        qs = Order.objects.filter(
            restaurant=restaurant,
            created__date__gte=start,
        ).exclude(status=OrderStatusChoices.CANCELLED)

        rows = qs.annotate(day=TruncDate('created')).values('day').annotate(
            revenue=Sum('total_amount'),
            orders=Count('id'),
        ).order_by('day')

        by_date = {r['day']: r for r in rows}
        data = []
        for i in range(days):
            d = start + timedelta(days=i)
            row = by_date.get(d)
            data.append({
                'day': d.strftime('%a'),
                'date': d,
                'revenue': row['revenue'] if row else 0,
                'orders': row['orders'] if row else 0,
            })
        return Response({'status': True, 'message': 'OK', 'data': data})


@extend_schema(tags=['Stats'], summary="Ofitsiant statistikasi",
               description="Joriy ofitsiantning bugungi va haftalik buyurtma soni, tushumi hamda aktiv buyurtmalari.",
               responses=WaiterStatsSerializer)
class WaiterStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.localdate()
        week_start = today - timedelta(days=6)

        base = Order.objects.filter(waiter=user).exclude(status=OrderStatusChoices.CANCELLED)
        today_qs = base.filter(created__date=today)
        week_qs = base.filter(created__date__gte=week_start)

        data = {
            'orders_today': today_qs.count(),
            'revenue_today': today_qs.aggregate(s=Sum('total_amount'))['s'] or 0,
            'orders_week': week_qs.count(),
            'revenue_week': week_qs.aggregate(s=Sum('total_amount'))['s'] or 0,
            'active_orders': Order.objects.filter(waiter=user, status__in=ACTIVE_STATUSES).count(),
            'total_orders': base.count(),
        }
        return Response({'status': True, 'message': 'OK', 'data': data})
