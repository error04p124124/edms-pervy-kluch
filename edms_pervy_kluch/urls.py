"""
URL Configuration for edms_pervy_kluch project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

# Игнорировать запросы Chrome DevTools
def chrome_devtools(request):
    return HttpResponse(status=204)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', include('documents.urls')),
    # Игнорировать запросы браузера
    re_path(r'^\.well-known/', chrome_devtools),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = 'ООО "Первый ключ" - Система ЭДО'
admin.site.site_title = 'Админ-панель ЭДО'
admin.site.index_title = 'Управление системой'
