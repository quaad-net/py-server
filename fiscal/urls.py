from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include, re_path
from django.views.static import serve

urlpatterns = [
    path('uwm-fs-expend/purchase-freq/', views.get_purchase_freq),
    path('uwm-fs-expend/purchase-historical-records/', views.get_purchase_historical_records),
    path('uwm-fs-expend/monthlyTtls/', views.monthly_totals),
    re_path(r'get-dataset/(?P<table>\w+)', views.get_dataset),
    re_path(r'uwm-fs-expend/range=(?P<range>\d+)/', views.expend),
    re_path(r'uwm-fs-expend/month=(?P<month>\d+)&year=(?P<year>\d+)/', views.expend_month),
    re_path(r'uwm-fs-expend/monthlyTtlsPerctMod=(?P<perct_mod>\d+(\.\d+)?)-(?P<sign>\w+)/', views.monthly_totals_mod),
    re_path(r'uwm-fs-expend/perct-mod-month=(?P<month>\d+)&year=(?P<year>\d+)&perctMod=(?P<perct_mod>\d+(\.\d+)?)-(?P<sign>\w+)/', views.expend_month_mod), 
    re_path(r'uwm-fs-expend/purchase-hist=(?P<item_code>[\w-]+)/', views.get_purchase_hist), 
]