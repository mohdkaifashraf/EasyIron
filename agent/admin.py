from django.contrib import admin

from .models import AgentEarnings, AgentNotification, DeliveryAssignment, OrderTracking, PickupAssignment

admin.site.register(PickupAssignment)
admin.site.register(DeliveryAssignment)
admin.site.register(OrderTracking)
admin.site.register(AgentEarnings)
admin.site.register(AgentNotification)
