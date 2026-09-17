from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from store_app.models import DeliveryAgent, Order, OrderItem, Service, Store

from .models import AgentEarnings, DeliveryAssignment, OrderTracking, PickupAssignment


class AgentWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.store = Store.objects.create(
            name="Test Store", code="TEST-01", phone="9999999999", address="Test Address"
        )
        cls.user = get_user_model().objects.create_user(
            username="test_agent", email="agent@example.com", password="Agent@123"
        )
        cls.agent = DeliveryAgent.objects.create(
            user=cls.user,
            store=cls.store,
            name="Test Agent",
            email="agent@example.com",
            phone="9000000000",
        )
        cls.service = Service.objects.create(
            store=cls.store, name="Shirt Ironing", price=Decimal("10.00")
        )

    def make_order(self, number, status):
        order = Order.objects.create(
            store=self.store,
            order_number=number,
            customer_name="Test Customer",
            customer_phone="9111111111",
            pickup_address="Customer Address",
            service_type="Ironing",
            pickup_date=timezone.now() + timedelta(hours=1),
            status=status,
            delivery_agent=self.agent,
        )
        OrderItem.objects.create(
            order=order,
            service=self.service,
            item_name="Shirt Ironing",
            quantity=3,
            price=self.service.price,
        )
        return order

    def login_agent(self):
        response = self.client.post(
            reverse("agent:login"),
            {"identifier": "agent@example.com", "password": "Agent@123"},
        )
        self.assertRedirects(response, reverse("agent:dashboard"))

    def test_agent_pages_render(self):
        self.login_agent()
        for name in (
            "dashboard",
            "pickups",
            "store_deliveries",
            "deliveries",
            "earnings",
            "notifications",
            "profile",
        ):
            self.assertEqual(self.client.get(reverse(f"agent:{name}")).status_code, 200)

    def test_pickup_workflow_updates_order_tracking_and_earnings(self):
        self.login_agent()
        order = self.make_order("TEST-PICKUP", Order.Status.RECEIVED)
        assignment = PickupAssignment.objects.create(
            order=order, agent=self.agent, pickup_time=order.pickup_date
        )
        for status in ("accepted", "reached", "collected", "store_delivered"):
            response = self.client.post(
                reverse("agent:update_pickup", args=(assignment.pk,)), {"status": status}
            )
            self.assertEqual(response.status_code, 302)
        assignment.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(assignment.status, PickupAssignment.Status.STORE_DELIVERED)
        self.assertEqual(order.status, Order.Status.STORE_RECEIVED)
        self.assertEqual(OrderTracking.objects.filter(order=order).count(), 4)
        self.assertEqual(order.notifications.count(), 4)
        self.assertTrue(
            AgentEarnings.objects.filter(
                order=order, task_type=AgentEarnings.TaskType.PICKUP
            ).exists()
        )

    def test_return_delivery_workflow_updates_customer_and_order(self):
        self.login_agent()
        order = self.make_order("TEST-DELIVERY", Order.Status.READY)
        assignment = DeliveryAssignment.objects.create(
            order=order, agent=self.agent, delivery_time=timezone.now()
        )
        for status in ("accepted", "store_picked", "out_for_delivery", "delivered"):
            response = self.client.post(
                reverse("agent:update_delivery", args=(assignment.pk,)), {"status": status}
            )
            self.assertEqual(response.status_code, 302)
        assignment.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(assignment.status, DeliveryAssignment.Status.DELIVERED)
        self.assertEqual(order.status, Order.Status.DELIVERED)
        self.assertIsNotNone(order.delivery_date)
        self.assertEqual(OrderTracking.objects.filter(order=order).count(), 4)
        self.assertEqual(order.notifications.count(), 4)
        self.assertTrue(
            AgentEarnings.objects.filter(
                order=order, task_type=AgentEarnings.TaskType.DELIVERY
            ).exists()
        )
