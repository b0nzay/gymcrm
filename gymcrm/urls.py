from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

from gymcrm.views import spa_index
from memberships.views import StatsView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/memberships/', include('memberships.urls')),
    path('api/clients/', include('users.client_urls')),
    path('api/users/', include('users.admin_urls')),
    path('api/stats/', StatsView.as_view()),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    re_path(r'^(?!api/|admin/|media/|static/).*$', spa_index),
]
