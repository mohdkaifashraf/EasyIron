from django.db import models
from django.utils import timezone

from store_app.models import DeliveryAgent, Order


class PickupAssignment(models.Model):
    class Status(models.TextChoices):
        ASSIGNED = "assigned", "Assigned"
        ACCEPTED = "accepted", "Accepted"
        REACHED = "reached", "Reached Customer"
        COLLECTED = "collected", "Clothes Collected"
        STORE_DELIVERED = "store_delivered", "Delivered to Store"
        CANCELLED = "cancelled", "Cancelled"

    order = models.OneToOneField(Order, related_name="pickup_assignment", on_delete=models.CASCADE)
    agent = models.ForeignKey(DeliveryAgent, related_name="pickup_assignments", on_delete=models.CASCADE)
    pickup_time = models.DateTimeField()
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.ASSIGNED)
    accepted_at = models.DateTimeField(null=True, blank=True)
    reached_at = models.DateTimeField(null=True, blank=True)
    collected_at = models.DateTimeField(null=True, blank=True)
    delivered_to_store_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("pickup_time",)

    def __str__(self):
        return f"Pickup {self.order.order_number} — {self.get_status_display()}"

    @property
    def next_status(self):
        return {
            self.Status.ASSIGNED: self.Status.ACCEPTED,
            self.Status.ACCEPTED: self.Status.REACHED,
            self.Status.REACHED: self.Status.COLLECTED,
            self.Status.COLLECTED: self.Status.STORE_DELIVERED,
        }.get(self.status)

    @property
    def next_action_label(self):
        return {
            self.Status.ASSIGNED: "Accept Pickup",
            self.Status.ACCEPTED: "Mark Reached",
            self.Status.REACHED: "Mark Picked Up",
            self.Status.COLLECTED: "Mark Delivered to Store",
        }.get(self.status, "Completed")


class DeliveryAssignment(models.Model):
    class Status(models.TextChoices):
        READY = "ready", "Ready for Delivery"
        ACCEPTED = "accepted", "Accepted"
        STORE_PICKED = "store_picked", "Picked From Store"
        OUT_FOR_DELIVERY = "out_for_delivery", "Out For Delivery"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    order = models.OneToOneField(Order, related_name="return_assignment", on_delete=models.CASCADE)
    agent = models.ForeignKey(DeliveryAgent, related_name="delivery_assignments", on_delete=models.CASCADE)
    delivery_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.READY)
    accepted_at = models.DateTimeField(null=True, blank=True)
    picked_from_store_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("delivery_time", "created_at")

    def __str__(self):
        return f"Delivery {self.order.order_number} — {self.get_status_display()}"

    @property
    def next_status(self):
        return {
            self.Status.READY: self.Status.ACCEPTED,
            self.Status.ACCEPTED: self.Status.STORE_PICKED,
            self.Status.STORE_PICKED: self.Status.OUT_FOR_DELIVERY,
            self.Status.OUT_FOR_DELIVERY: self.Status.DELIVERED,
        }.get(self.status)

    @property
    def next_action_label(self):
        return {
            self.Status.READY: "Accept Delivery",
            self.Status.ACCEPTED: "Pick From Store",
            self.Status.STORE_PICKED: "Start Delivery",
            self.Status.OUT_FOR_DELIVERY: "Mark Delivered",
        }.get(self.status, "Completed")


class OrderTracking(models.Model):
    order = models.ForeignKey(Order, related_name="agent_tracking_events", on_delete=models.CASCADE)
    agent = models.ForeignKey(DeliveryAgent, related_name="tracking_events", on_delete=models.CASCADE)
    status = models.CharField(max_length=50)
    label = models.CharField(max_length=100)
    note = models.CharField(max_length=250, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"{self.order.order_number}: {self.label}"


class AgentEarnings(models.Model):
    class TaskType(models.TextChoices):
        PICKUP = "pickup", "Customer Pickup"
        DELIVERY = "delivery", "Customer Delivery"

    agent = models.ForeignKey(DeliveryAgent, related_name="earnings", on_delete=models.CASCADE)
    order = models.ForeignKey(Order, related_name="agent_earnings", on_delete=models.CASCADE)
    task_type = models.CharField(max_length=20, choices=TaskType.choices)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    earned_on = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-earned_on",)
        constraints = [
            models.UniqueConstraint(
                fields=("agent", "order", "task_type"), name="unique_agent_order_task_earning"
            )
        ]

    def __str__(self):
        return f"{self.agent.name} — ₹{self.amount}"


class AgentNotification(models.Model):
    agent = models.ForeignKey(DeliveryAgent, related_name="agent_notifications", on_delete=models.CASCADE)
    order = models.ForeignKey(Order, related_name="agent_notifications", null=True, blank=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=120)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, default="info")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.title
