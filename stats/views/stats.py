from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, F, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.dateparse import parse_date
from datetime import timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter

from order.models import Order, OrderItems, OrderStatusChoices, OrderItemStatusChoices
from accounts.models import UserRoleChoices
from helpers.permissions import IsManagerOrAdmin
from stats.serializers.stats import (
    DashboardSerializer, TopItemSerializer, SeriesPointSerializer, WaiterStatsSerializer,
    ItemSeriesPointSerializer, WaiterServiceFeeSerializer,
)

ACTIVE_STATUSES = [OrderStatusChoices.PREPARING, OrderStatusChoices.DELIVERED]


def _service_fee_amount(order):
    items_subtotal = sum(
        item.subtotal
        for item in order.items.all()
        if item.status != OrderItemStatusChoices.CANCELLED
    )
    amount = items_subtotal * (order.service_fee or 0) / 100
    return amount if amount > 0 else 0


def _service_fee_sum(orders):
    return sum((_service_fee_amount(order) for order in orders), 0)


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
        today_qs = base.filter(status=OrderStatusChoices.CLOSED, closed__date=today)
        yesterday_qs = base.filter(status=OrderStatusChoices.CLOSED, closed__date=yesterday)

        orders_today = today_qs.count()
        revenue_today = today_qs.aggregate(s=Sum('total_amount'))['s'] or 0
        orders_yesterday = yesterday_qs.count()
        revenue_yesterday = yesterday_qs.aggregate(s=Sum('total_amount'))['s'] or 0

        active_waiters = base.filter(created__date=today, status__in=ACTIVE_STATUSES).values('waiter').distinct().count()
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
        try:
            limit = int(request.query_params.get('limit', 10))
        except (TypeError, ValueError):
            limit = 10
        limit = max(1, min(limit, 50))

        qs = OrderItems.objects.filter(
            order__restaurant=restaurant,
            order__status=OrderStatusChoices.CLOSED,
        ).exclude(status=OrderItemStatusChoices.CANCELLED)

        # Davr: date_from/date_to oraliq, range preseti yoki bitta sana (standart: today)
        date_from = parse_date(request.query_params.get('date_from') or '')
        date_to = parse_date(request.query_params.get('date_to') or '')
        range_param = request.query_params.get('range')

        if date_from and date_to and date_from <= date_to:
            qs = qs.filter(order__closed__date__gte=date_from,
                           order__closed__date__lte=date_to)
        elif range_param in ('7d', '30d', '90d'):
            days = {'7d': 7, '30d': 30, '90d': 90}[range_param]
            start = timezone.localdate() - timedelta(days=days - 1)
            qs = qs.filter(order__closed__date__gte=start)
        else:
            date_param = request.query_params.get('date', 'today')
            if date_param == 'today':
                qs = qs.filter(order__closed__date=timezone.localdate())
            elif date_param:
                qs = qs.filter(order__closed__date=date_param)

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
               description="Kunlik tushum va buyurtmalar grafigi. range: 7d | 30d | 90d, "
                           "yoki date_from/date_to (YYYY-MM-DD) bilan ixtiyoriy oraliq.",
               parameters=[
                   OpenApiParameter('range', str, description="7d | 30d | 90d (standart: 30d)"),
                   OpenApiParameter('date_from', str, description="Boshlanish sanasi YYYY-MM-DD"),
                   OpenApiParameter('date_to', str, description="Tugash sanasi YYYY-MM-DD"),
               ],
               responses=SeriesPointSerializer(many=True))
class SeriesView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]

    def get(self, request):
        restaurant = request.user.restaurant

        # date_from/date_to berilgan bo'lsa ixtiyoriy oraliq, aks holda range presetlari
        date_from = parse_date(request.query_params.get('date_from') or '')
        date_to = parse_date(request.query_params.get('date_to') or '')
        if date_from and date_to and date_from <= date_to:
            start, end = date_from, date_to
        else:
            range_param = request.query_params.get('range', '30d')
            days = {'7d': 7, '30d': 30, '90d': 90}.get(range_param, 30)
            end = timezone.localdate()
            start = end - timedelta(days=days - 1)

        total_days = (end - start).days + 1
        # juda katta oraliqni cheklaymiz (1 yil)
        if total_days > 366:
            start = end - timedelta(days=365)
            total_days = 366

        qs = Order.objects.filter(
            restaurant=restaurant,
            status=OrderStatusChoices.CLOSED,
            closed__date__gte=start,
            closed__date__lte=end,
        )

        rows = qs.annotate(day=TruncDate('closed')).values('day').annotate(
            revenue=Sum('total_amount'),
            orders=Count('id'),
        ).order_by('day')

        by_date = {r['day']: r for r in rows}
        data = []
        for i in range(total_days):
            d = start + timedelta(days=i)
            row = by_date.get(d)
            data.append({
                'day': d.strftime('%a'),
                'date': d,
                'revenue': row['revenue'] if row else 0,
                'orders': row['orders'] if row else 0,
            })
        return Response({'status': True, 'message': 'OK', 'data': data})


@extend_schema(tags=['Stats'], summary="Bitta taomning kunlik sotuvi",
               description="Tanlangan taomning kunma-kun sotilgan soni va tushumi. "
                           "range: 7d|30d|90d yoki date_from/date_to (YYYY-MM-DD).",
               parameters=[
                   OpenApiParameter('menu_item', int, description="Taom (menu item) IDsi", required=True),
                   OpenApiParameter('range', str, description="7d | 30d | 90d (standart: 30d)"),
                   OpenApiParameter('date_from', str, description="Boshlanish sanasi YYYY-MM-DD"),
                   OpenApiParameter('date_to', str, description="Tugash sanasi YYYY-MM-DD"),
               ],
               responses=ItemSeriesPointSerializer(many=True))
class ItemSeriesView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]

    def get(self, request):
        restaurant = request.user.restaurant

        try:
            menu_item_id = int(request.query_params.get('menu_item'))
        except (TypeError, ValueError):
            return Response({'status': True, 'message': 'OK', 'data': []})

        date_from = parse_date(request.query_params.get('date_from') or '')
        date_to = parse_date(request.query_params.get('date_to') or '')
        if date_from and date_to and date_from <= date_to:
            start, end = date_from, date_to
        else:
            range_param = request.query_params.get('range', '30d')
            days = {'7d': 7, '30d': 30, '90d': 90}.get(range_param, 30)
            end = timezone.localdate()
            start = end - timedelta(days=days - 1)

        total_days = (end - start).days + 1
        if total_days > 366:
            start = end - timedelta(days=365)
            total_days = 366

        qs = OrderItems.objects.filter(
            order__restaurant=restaurant,
            order__status=OrderStatusChoices.CLOSED,
            menu_item_id=menu_item_id,
            order__closed__date__gte=start,
            order__closed__date__lte=end,
        ).exclude(status=OrderItemStatusChoices.CANCELLED)

        rows = qs.annotate(day=TruncDate('order__closed')).values('day').annotate(
            qty=Sum('quantity'),
            revenue=Sum('subtotal'),
        ).order_by('day')

        by_date = {r['day']: r for r in rows}
        data = []
        for i in range(total_days):
            d = start + timedelta(days=i)
            row = by_date.get(d)
            data.append({
                'date': d,
                'qty': row['qty'] if row else 0,
                'revenue': row['revenue'] if row else 0,
            })
        return Response({'status': True, 'message': 'OK', 'data': data})


@extend_schema(tags=['Stats'], summary="Ofitsiantlar xizmat haqi hisoboti",
               description="Yopilgan buyurtmalar bo'yicha kunlik ofitsiant xizmat haqi summalari. "
                           "range: 7d | 30d | 90d yoki date_from/date_to (YYYY-MM-DD).",
               parameters=[
                   OpenApiParameter('range', str, description="7d | 30d | 90d (standart: 30d)"),
                   OpenApiParameter('date_from', str, description="Boshlanish sanasi YYYY-MM-DD"),
                   OpenApiParameter('date_to', str, description="Tugash sanasi YYYY-MM-DD"),
               ],
               responses=WaiterServiceFeeSerializer(many=True))
class WaiterServiceFeesView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]

    def get(self, request):
        restaurant = request.user.restaurant

        date_from = parse_date(request.query_params.get('date_from') or '')
        date_to = parse_date(request.query_params.get('date_to') or '')
        if date_from and date_to and date_from <= date_to:
            start, end = date_from, date_to
        else:
            range_param = request.query_params.get('range', '30d')
            days = {'7d': 7, '30d': 30, '90d': 90}.get(range_param, 30)
            end = timezone.localdate()
            start = end - timedelta(days=days - 1)

        qs = Order.objects.filter(
            restaurant=restaurant,
            status=OrderStatusChoices.CLOSED,
        ).filter(
            Q(closed__date__gte=start, closed__date__lte=end) |
            Q(closed__isnull=True, created__date__gte=start, created__date__lte=end)
        ).select_related('waiter').prefetch_related('items').order_by('-closed', '-created')

        grouped = {}
        for order in qs:
            day = timezone.localtime(order.closed).date() if order.closed else timezone.localtime(order.created).date()
            key = (day, order.waiter_id)
            if key not in grouped:
                grouped[key] = {
                    'date': day,
                    'waiter_id': order.waiter_id,
                    'waiter_name': order.waiter.full_name or order.waiter.username,
                    'orders': 0,
                    'service_fee': 0,
                }
            grouped[key]['orders'] += 1
            grouped[key]['service_fee'] += _service_fee_amount(order)

        data = sorted(grouped.values(), key=lambda x: (x['date'], x['waiter_name']), reverse=True)
        return Response({'status': True, 'message': 'OK', 'data': data})


@extend_schema(tags=['Stats'], summary="Ofitsiant statistikasi",
               description="Joriy ofitsiantning bugungi va haftalik buyurtma soni, tushumi hamda aktiv buyurtmalari.",
               responses=WaiterStatsSerializer)
class WaiterStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        restaurant = user.restaurant
        today = timezone.localdate()
        week_start = today - timedelta(days=6)

        base = Order.objects.filter(waiter=user, restaurant=restaurant).exclude(status=OrderStatusChoices.CANCELLED)
        today_qs = base.filter(status=OrderStatusChoices.CLOSED, closed__date=today)
        week_qs = base.filter(status=OrderStatusChoices.CLOSED, closed__date__gte=week_start)
        closed_base = base.filter(status=OrderStatusChoices.CLOSED).prefetch_related('items')
        service_fee_today = _service_fee_sum(closed_base.filter(
            Q(closed__date=today) | Q(closed__isnull=True, created__date=today)
        ))
        service_fee_week = _service_fee_sum(closed_base.filter(
            Q(closed__date__gte=week_start) | Q(closed__isnull=True, created__date__gte=week_start)
        ))

        data = {
            'orders_today': today_qs.count(),
            'revenue_today': today_qs.aggregate(s=Sum('total_amount'))['s'] or 0,
            'service_fee_today': service_fee_today,
            'orders_week': week_qs.count(),
            'revenue_week': week_qs.aggregate(s=Sum('total_amount'))['s'] or 0,
            'service_fee_week': service_fee_week,
            'active_orders': Order.objects.filter(waiter=user, restaurant=restaurant, status__in=ACTIVE_STATUSES).count(),
            'total_orders': base.count(),
        }
        return Response({'status': True, 'message': 'OK', 'data': data})
