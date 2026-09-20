from django.urls import path

from . import views

app_name = "adminpanel"

urlpatterns = [
    path("login/", views.admin_login, name="login"),
    path("", views.dashboard, name="dashboard"),
]
