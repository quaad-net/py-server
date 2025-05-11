from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include, re_path
from django.views.static import serve

urlpatterns = [
    path('uwm-fs-expend/monthly-totals-with-prev-yr/', views.uwm_fs_expend_monthly_totals_with_prev_yr),
    re_path(r'uwm-fs-expend/range=(?P<range>\d+)/', views.uwm_fs_expend),
]
