from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("user_app.urls")),
    path("store/", include("store_app.urls")),
    path("agent/", include("agent_app.urls")),
    path("admin-panel/", include("admin_management.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

