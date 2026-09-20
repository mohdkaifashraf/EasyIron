from django.conf import settings
from django.db import models


class DeliveryAgent(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	name = models.CharField(max_length=100)
	phone = models.CharField(max_length=20)
	store = models.ForeignKey("store_app.Store", related_name="agents", on_delete=models.CASCADE)
	is_active = models.BooleanField(default=True)


class Assignment(models.Model):
	PICKUP = "pickup"
	DELIVERY = "delivery"
	task_type = models.CharField(max_length=20, choices=[(PICKUP, "Pickup"), (DELIVERY, "Delivery")])
	order = models.ForeignKey("store_app.Order", related_name="assignments", on_delete=models.CASCADE)
	agent = models.ForeignKey(DeliveryAgent, related_name="assignments", on_delete=models.CASCADE)
	completed = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
