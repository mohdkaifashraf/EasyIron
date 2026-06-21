from django.urls import path
from . import views

app_name = "home"

urlpatterns = [
    path("", views.homepage, name="homepage"),
    path("services/search/", views.search_services, name="search_services"),
    path("help/", views.help_center, name="help_center"),
]
