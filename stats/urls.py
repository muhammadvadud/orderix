from django.urls import path

from stats.views.stats import (
    DashboardView, TopItemsView, SeriesView, ItemSeriesView, WaiterStatsView,
)

urlpatterns = [
    path('stats/dashboard', DashboardView.as_view(), name='stats-dashboard'),
    path('stats/top-items', TopItemsView.as_view(), name='stats-top-items'),
    path('stats/series', SeriesView.as_view(), name='stats-series'),
    path('stats/item-series', ItemSeriesView.as_view(), name='stats-item-series'),
    path('stats/waiter', WaiterStatsView.as_view(), name='stats-waiter'),
]
