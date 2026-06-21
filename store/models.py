from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class Store(models.Model):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class StoreStaff(models.Model):
    class Role(models.TextChoices):
        MANAGER = "manager", "Store Manager"
        STAFF = "staff", "Store Staff"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, related_name="staff_members", on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} — {self.get_role_display()}"


class Service(models.Model):
    store = models.ForeignKey(Store, related_name="services", on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=9, decimal_places=2)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="store/services/", blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(fields=("store", "name"), name="unique_service_per_store")
        ]

    def __str__(self):
        return self.name


class DeliveryAgent(models.Model):
    class VehicleType(models.TextChoices):
        BICYCLE = "bicycle", "Bicycle"
        BIKE = "bike", "Motorbike"
        SCOOTER = "scooter", "Scooter"
        VAN = "van", "Delivery Van"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="delivery_agent_profile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    store = models.ForeignKey(Store, related_name="delivery_agents", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20)
    photo = models.ImageField(upload_to="agents/", blank=True)
    vehicle_type = models.CharField(max_length=20, choices=VehicleType.choices, default=VehicleType.BIKE)
    vehicle_number = models.CharField(max_length=30, blank=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=5.0)
    is_available = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "received", "Order Received"
        STORE_RECEIVED = "store_received", "Clothes Received at Store"
        PROCESSING = "processing", "Processing"
        IRONING_COMPLETED = "ironing_completed", "Ironing Completed"
        LAUNDRY_COMPLETED = "laundry_completed", "Laundry Completed"
        QUALITY_CHECK = "quality_check", "Quality Check"
        READY = "ready", "Ready for Delivery"
        AGENT_PICKED = "agent_picked", "Picked by Delivery Agent"
        DELIVERED = "delivered", "Delivered"
        REJECTED = "rejected", "Rejected"

    store = models.ForeignKey(Store, related_name="orders", on_delete=models.PROTECT)
    order_number = models.CharField(max_length=24, unique=True)
    customer_name = models.CharField(max_length=120)
    customer_phone = models.CharField(max_length=20, db_index=True)
    pickup_address = models.TextField()
    service_type = models.CharField(max_length=120)
    pickup_date = models.DateTimeField()
    delivery_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.RECEIVED)
    delivery_agent = models.ForeignKey(
        DeliveryAgent, related_name="orders", null=True, blank=True, on_delete=models.SET_NULL
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    rejected_reason = models.CharField(max_length=250, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.order_number

    @property
    def item_count(self):
        return self.items.aggregate(total=Sum("quantity"))["total"] or 0

    @property
    def total_amount(self):
        return sum((item.total for item in self.items.all()), Decimal("0.00"))

    def add_tracking(self, status, note="", changed_by=None):
        return self.tracking_events.create(status=status, note=note, changed_by=changed_by)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    service = models.ForeignKey(Service, related_name="order_items", null=True, on_delete=models.SET_NULL)
    item_name = models.CharField(max_length=120)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=9, decimal_places=2)

    @property
    def total(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.item_name} × {self.quantity}"


class Tracking(models.Model):
    order = models.ForeignKey(Order, related_name="tracking_events", on_delete=models.CASCADE)
    status = models.CharField(max_length=30, choices=Order.Status.choices)
    note = models.CharField(max_length=250, blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"{self.order.order_number}: {self.get_status_display()}"


class CustomerNotification(models.Model):
    order = models.ForeignKey(Order, related_name="notifications", on_delete=models.CASCADE)
    customer_phone = models.CharField(max_length=20, db_index=True)
    title = models.CharField(max_length=120)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.title
