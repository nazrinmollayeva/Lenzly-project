# project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('auth_system.urls')),
    path('api/', include('profiles_system.urls')),
    path('api/', include('follow_system.urls')),
    path('api/', include('post_app.urls')),
    path('api/', include('story_app.urls')),
    path('api/', include('chat_system.urls'))
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

