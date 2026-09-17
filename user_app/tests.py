from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Cart, CartItem


class CartAccessTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester",
            email="tester@example.com",
            password="secret123",
        )

    def test_guest_cannot_add_item_to_cart(self):
        response = self.client.post(
            reverse("home:add_to_cart"),
            {"item_name": "Shirt", "price": "10", "quantity": "2"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)
        self.assertFalse(Cart.objects.exists())

    def test_logged_in_user_can_add_item_to_cart(self):
        self.client.login(username="tester", password="secret123")

        response = self.client.post(
            reverse("home:add_to_cart"),
            {"item_name": "Shirt", "price": "10", "quantity": "2"},
        )

        self.assertEqual(response.status_code, 302)
        cart = Cart.objects.get(user=self.user, active=True)
        item = CartItem.objects.get(cart=cart, item_name="Shirt")
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.price, 10)

    def test_cart_badge_shows_total_quantity(self):
        self.client.login(username="tester", password="secret123")
        cart = Cart.objects.create(user=self.user, active=True)
        CartItem.objects.create(cart=cart, item_name="Shirt", price=10, quantity=2)
        CartItem.objects.create(cart=cart, item_name="Pant", price=15, quantity=3)

        response = self.client.get(reverse("home:homepage"))

        self.assertContains(response, '<span id="cartCount">5</span>', html=True)

    def test_cart_badge_decreases_after_quantity_update(self):
        self.client.login(username="tester", password="secret123")
        cart = Cart.objects.create(user=self.user, active=True)
        item = CartItem.objects.create(cart=cart, item_name="Shirt", price=10, quantity=4)

        response = self.client.post(
            reverse("home:account_cart"),
            {"item_id": item.id, "quantity": "1", "update_item": "1"},
            follow=True,
        )

        self.assertContains(response, '<span id="cartCount">1</span>', html=True)

    def test_ajax_add_to_cart_returns_json_without_redirect(self):
        self.client.login(username="tester", password="secret123")

        response = self.client.post(
            reverse("home:add_to_cart"),
            {"item_name": "Shirt", "price": "10", "quantity": "2", "next": "/#clothes"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(CartItem.objects.get(item_name="Shirt").quantity, 2)

    def test_home_cart_remove_item_endpoint_removes_selected_item(self):
        self.client.login(username="tester", password="secret123")
        cart = Cart.objects.create(user=self.user, active=True)
        item = CartItem.objects.create(cart=cart, item_name="Shirt", price=10, quantity=2)

        response = self.client.post(
            reverse("home:remove_cart_item"),
            {"item_id": item.id},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["subtotal"], 0)
        self.assertFalse(CartItem.objects.filter(pk=item.id).exists())

