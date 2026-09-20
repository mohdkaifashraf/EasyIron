from django.contrib import admin

from .models import (
    Address,
    Banner,
    Cart,
    CartItem,
    ClothingItem,
    CustomerProfile,
    CustomerReview,
    Order,
    ServiceCategory,
    UserProfile,
)


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "sort_order", "is_active")
    list_editable = ("sort_order", "is_active")


class ClothingItemInline(admin.TabularInline):
    model = ClothingItem
    extra = 0


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sort_order")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ClothingItemInline]


@admin.register(ClothingItem)
class ClothingItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "rating", "review_count", "is_available")
    list_filter = ("category", "is_available")
    search_fields = ("name", "category__name")


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "mobile", "address", "allow_marketing", "share_data", "created_at")
    list_filter = ("allow_marketing", "share_data")
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name", "mobile")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "mobile", "address", "allow_marketing", "share_data")
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name", "mobile")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "label", "city", "state", "postal_code", "is_default", "created_at")
    list_filter = ("country", "state", "is_default")
    search_fields = ("user__username", "user__email", "line1", "city", "postal_code")


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "active", "updated_at", "created_at")
    list_filter = ("active",)
    search_fields = ("user__username", "user__email")
    inlines = [CartItemInline]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_id", "user", "store", "status", "payment_status", "total_amount", "pickup_date")
    list_filter = ("status", "payment_status", "store")
    search_fields = ("order_id", "user__username", "user__email", "razorpay_order_id", "razorpay_payment_id")
    readonly_fields = ("created_at",)


admin.site.register(CustomerReview)
