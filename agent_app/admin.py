from django.contrib import admin

from .models import Assignment, DeliveryAgent


@admin.register(DeliveryAgent)
class DeliveryAgentAdmin(admin.ModelAdmin):
	list_display = ("name", "user", "phone", "store", "is_active")
	list_filter = ("is_active", "store")
	search_fields = ("name", "phone", "user__username", "user__email", "store__name")


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
	list_display = ("order", "agent", "task_type", "completed", "created_at")
	list_filter = ("task_type", "completed", "agent__store")
	search_fields = ("order__order_number", "agent__name", "agent__user__username")
	readonly_fields = ("created_at",)
