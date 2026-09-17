from django.urls import path

from . import views

app_name = "adminpanel"

urlpatterns = [
    path("login/", views.admin_login, name="login"),
    path("", views.admin_dashboard, name="dashboard"),
    path("services/", views.service_list, name="service_list"),
    path("services/add/", views.service_create, name="service_create"),
    path("services/<int:pk>/edit/", views.service_update, name="service_update"),
    path("services/<int:pk>/delete/", views.service_delete, name="service_delete"),
    path("agents/store/create/", views.create_store, name="create_store"),
    path(
        "agents/delivery/create/",
        views.create_delivery_agent,
        name="create_delivery_agent",
    ),
    path("agents/store/list/", views.store_staff_list, name="store_staff_list"),
    path(
        "agents/delivery/list/",
        views.delivery_agent_list,
        name="delivery_agent_list",
    ),
]


