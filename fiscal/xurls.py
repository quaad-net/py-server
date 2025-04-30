from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include, re_path
from django.views.static import serve

# handler500 = 'fiscalapp.views.handler500'

# Patterns match with 'root/fiscal/...'
urlpatterns = [
    path('', views.fiscal, name = 'fiscal'),
    re_path(r'imports-n-exports/q-(?P<startDate>\d+)/' + r'(?P<endDate>\d+)', views.ImportsExports),
    re_path(r'interest-rates/q-(?P<startDate>\d+)/' + r'(?P<endDate>\d+)', views.InterestRates),
    re_path(r'population/q-(?P<startDate>\d+)/' + r'(?P<endDate>\d+)', views.Population),
    path('posts', views.fiscal_posts, name = 'posts'),
    re_path(r'^posts/charts-(?P<scriptID>\d+)/', views.get_assoc_chts, name = 'get_assoc_chts'),
    path('posts/getcontainers', views.get_containers, name='getcontainers'),
    path('posts/getposts', views.get_posts, name= 'getposts'), 
    re_path(r'price-indices/q-(?P<startDate>\d+)/' + r'(?P<endDate>\d+)', views.PriceIndices),
    re_path(r'production-n-consumption/q-(?P<startDate>\d+)/' + r'(?P<endDate>\d+)', views.ProductionConsumption),
    re_path(r'^q-expd-(?P<startDate>\d+)/' + r'(?P<endDate>\d+)', views.gov_expend_plus, name= 'govexpend'),
    re_path(r'^q-(?P<startDate>\d+)/' + r'(?P<endDate>\d+)', views.fiscalquery, name='fiscalquery'),
    re_path(r'^q-outlays-(?P<year>\d+)', views.update_outlays, name= 'outlays'),
    re_path(r'^q-outlays-drilldown-(?P<classID>\d+)', views.gov_outlays_tbl_drilldown),
    path('test/', views.test, name= 'test'),
    #re_path(r'^.*/$', views.handler500),
]
