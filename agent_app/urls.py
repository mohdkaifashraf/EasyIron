from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "agent"

urlpatterns = [
    path("login/", views.agent_login, name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("assignments/<int:pk>/complete/", views.complete_assignment, name="complete_assignment"),
]
