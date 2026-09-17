from django.contrib import admin

from .models import (
    CustomerNotification,
    DeliveryAgent,
    Order,
    OrderItem,
    Service,
    Store,
    StoreStaff,
    Tracking,
)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


class TrackingInline(admin.TabularInline):
    model = Tracking
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "customer_name", "service_type", "status", "created_at")
    list_filter = ("store", "status")
    search_fields = ("order_number", "customer_name", "customer_phone")
    inlines = (OrderItemInline, TrackingInline)


admin.site.register(Store)
admin.site.register(StoreStaff)
admin.site.register(Service)
admin.site.register(DeliveryAgent)
admin.site.register(CustomerNotification)
