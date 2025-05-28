from django.contrib import admin
from django.urls import path
from django.urls import include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.test, name = 'test'),
    path('admin/', admin.site.urls),
    path('fiscal/', include('fiscal.urls')),
    # path('', RedirectView.as_view(url='path/')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)