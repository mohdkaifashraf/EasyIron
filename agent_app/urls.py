from django.urls import path

from . import views

app_name = "agent"

urlpatterns = [
    path("login/", views.agent_login, name="login"),
    path("logout/", views.agent_logout, name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("pickups/", views.pickup_list, name="pickups"),
    path("store-deliveries/", views.store_delivery_list, name="store_deliveries"),
    path("deliveries/", views.return_delivery_list, name="deliveries"),
    path("orders/<int:order_id>/", views.order_detail, name="order_detail"),
    path("pickups/<int:pk>/status/", views.update_pickup_status, name="update_pickup"),
    path("deliveries/<int:pk>/status/", views.update_delivery_status, name="update_delivery"),
    path("earnings/", views.earnings, name="earnings"),
    path("notifications/", views.notifications, name="notifications"),
    path("profile/", views.profile, name="profile"),
]
