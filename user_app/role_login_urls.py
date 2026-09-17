from django.urls import path

from . import role_login_views

app_name = "role_login"

urlpatterns = [
    path("/", role_login_views.role_login_gate, name="role_login_gate"),
]

