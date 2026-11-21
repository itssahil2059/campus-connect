from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/', include('profiles.urls')),
    path('api/', include('connections.urls')),
    path('api/', include('chat.urls')),
]
# Local dev only: Django serves uploaded photos. In production Nginx serves
# /media/ straight from disk (deploy/nginx-app.conf); static() returns no
# URLs when DEBUG is off.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
