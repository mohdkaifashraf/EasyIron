from django.contrib import admin

from .models import Order, OrderItem, Store, StoreStaff, Tracking


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
	list_display = ("name", "code", "address", "is_active")
	list_filter = ("is_active",)
	search_fields = ("name", "code", "address")


@admin.register(StoreStaff)
class StoreStaffAdmin(admin.ModelAdmin):
	list_display = ("user", "store", "role", "is_active")
	list_filter = ("role", "is_active", "store")
	search_fields = ("user__username", "user__email", "user__first_name", "store__name")


class OrderItemInline(admin.TabularInline):
	model = OrderItem
	extra = 0


class TrackingInline(admin.TabularInline):
	model = Tracking
	extra = 0
	readonly_fields = ("created_at",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ("order_number", "store", "customer_name", "status", "delivery_agent", "pickup_date", "created_at")
	list_filter = ("status", "store", "delivery_agent")
	search_fields = ("order_number", "customer_name", "customer_phone", "store__name")
	readonly_fields = ("created_at", "updated_at")
	inlines = [OrderItemInline, TrackingInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
	list_display = ("order", "item_name", "quantity", "price")
	search_fields = ("order__order_number", "item_name")


@admin.register(Tracking)
class TrackingAdmin(admin.ModelAdmin):
	list_display = ("order", "status", "changed_by", "created_at")
	list_filter = ("status",)
	search_fields = ("order__order_number", "note", "changed_by__username")
	readonly_fields = ("created_at",)
