from django.contrib import admin
from .models import Banner, ClothingItem, CustomerReview, ServiceCategory


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


admin.site.register(CustomerReview)
