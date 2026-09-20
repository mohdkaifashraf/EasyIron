from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "store"

urlpatterns = [
    path("login/", views.store_login, name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
    path("orders/<int:pk>/accept/", views.accept_order, name="accept_order"),
    path("orders/<int:pk>/status/", views.update_status, name="update_status"),
    path("orders/<int:pk>/assign/", views.assign_agent, name="assign_agent"),
]
