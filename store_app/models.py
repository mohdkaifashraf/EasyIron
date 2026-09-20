from django.conf import settings
from django.db import models
from django.utils import timezone


class Store(models.Model):
	name = models.CharField(max_length=120)
	code = models.CharField(max_length=20, unique=True)
	address = models.TextField()
	is_active = models.BooleanField(default=True)

	def __str__(self):
		return self.name


class StoreStaff(models.Model):
	class Role(models.TextChoices):
		MANAGER = "manager", "Store Manager"
		STAFF = "staff", "Store Staff"

	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	store = models.ForeignKey(Store, related_name="staff_members", on_delete=models.CASCADE)
	role = models.CharField(max_length=20, choices=Role.choices, default=Role.MANAGER)
	is_active = models.BooleanField(default=True)


class Order(models.Model):
	RECEIVED = "received"
	ACCEPTED = "accepted"
	PICKUP_ASSIGNED = "pickup_assigned"
	PICKED_UP = "picked_up"
	PROCESSING = "processing"
	READY = "ready"
	OUT_FOR_DELIVERY = "out_for_delivery"
	DELIVERED = "delivered"
	STATUS_CHOICES = [
		(RECEIVED, "Order Received"),
		(ACCEPTED, "Accepted by Store"),
		(PICKUP_ASSIGNED, "Pickup Assigned"),
		(PICKED_UP, "Picked Up"),
		(PROCESSING, "Processing"),
		(READY, "Ready for Delivery"),
		(OUT_FOR_DELIVERY, "Out for Delivery"),
		(DELIVERED, "Delivered"),
	]

	store = models.ForeignKey(Store, related_name="orders", on_delete=models.PROTECT)
	order_number = models.CharField(max_length=32, unique=True)
	customer_name = models.CharField(max_length=120)
	customer_phone = models.CharField(max_length=20, blank=True)
	pickup_address = models.TextField()
	pickup_date = models.DateTimeField()
	status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=RECEIVED)
	delivery_agent = models.ForeignKey("agent_app.DeliveryAgent", null=True, blank=True, on_delete=models.SET_NULL)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ("-created_at",)

	def add_tracking(self, status, note="", changed_by=None):
		return self.tracking_events.create(status=status, note=note, changed_by=changed_by)


class OrderItem(models.Model):
	order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
	item_name = models.CharField(max_length=120)
	quantity = models.PositiveIntegerField(default=1)
	price = models.DecimalField(max_digits=9, decimal_places=2)


class Tracking(models.Model):
	order = models.ForeignKey(Order, related_name="tracking_events", on_delete=models.CASCADE)
	status = models.CharField(max_length=30, choices=Order.STATUS_CHOICES)
	note = models.CharField(max_length=250, blank=True)
	changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
	created_at = models.DateTimeField(default=timezone.now)
