from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("agent/", include("agent.urls")),
    path("store/", include("store.urls")),
    path("", include("home.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
