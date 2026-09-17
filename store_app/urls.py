from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "store"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="store/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("orders/incoming/", views.incoming_orders, name="incoming_orders"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
    path("orders/<int:pk>/accept/", views.accept_order, name="accept_order"),
    path("orders/<int:pk>/reject/", views.reject_order, name="reject_order"),
    path("orders/<int:pk>/status/", views.update_order_status, name="update_status"),
    path("inventory/", views.inventory, name="inventory"),
    path("deliveries/", views.delivery_management, name="deliveries"),
    path("orders/<int:pk>/assign-agent/", views.assign_delivery_agent, name="assign_agent"),
    path("services/", views.service_list, name="service_list"),
    path("services/add/", views.service_create, name="service_create"),
    path("services/<int:pk>/edit/", views.service_update, name="service_update"),
    path("services/<int:pk>/delete/", views.service_delete, name="service_delete"),
    path("search/", views.customer_search, name="customer_search"),
]
