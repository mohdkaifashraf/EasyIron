from django.urls import path
from . import views

app_name = "home"

urlpatterns = [
    path("", views.homepage, name="homepage"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.customer_login, name="login"),
    path("login/choose/", views.role_login_gate, name="role_login_gate"),
    path("logout/", views.logout_view, name="logout"),

    path("account/", views.account_dashboard, name="account"),
    path("account/profile/", views.account_profile, name="account_profile"),
    path("account/orders/", views.account_orders, name="orders"),
    path("account/addresses/", views.account_addresses, name="account_addresses"),
    path("cart/add/", views.add_to_cart, name="add_to_cart"),
    path("account/cart/", views.account_cart, name="account_cart"),
    path("checkout/create/", views.create_checkout_order, name="create_checkout_order"),
    path("checkout/verify/", views.verify_checkout_payment, name="verify_checkout_payment"),
    path("cart/remove/", views.remove_cart_item, name="remove_cart_item"),
    path("account/settings/", views.account_settings, name="account_settings"),
    path("services/search/", views.search_services, name="search_services"),
    path("help/", views.help_center, name="help_center"),
]
