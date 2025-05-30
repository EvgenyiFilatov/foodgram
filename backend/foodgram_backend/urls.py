from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from api.views import RecipesViewSet, redirect_short_link

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path(
        's/<str:short_link>/',
        redirect_short_link,
        name='redirect_short_link'
    ),
    path(
        'recipes/<int:pk>/',
        RecipesViewSet.as_view({'get': 'retrieve'}),
        name='recipes'
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
