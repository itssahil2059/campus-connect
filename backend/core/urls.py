from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/', include('profiles.urls')),
    path('api/', include('connections.urls')),
    path('api/', include('chat.urls')),
]