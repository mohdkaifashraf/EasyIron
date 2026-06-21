from django.db import models


class Banner(models.Model):
    title = models.CharField(max_length=120)
    subtitle = models.CharField(max_length=180, blank=True)
    image = models.ImageField(upload_to="banners/", blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("sort_order",)

    def __str__(self):
        return self.title


class ServiceCategory(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=180)
    image = models.ImageField(upload_to="services/", blank=True)
    icon = models.CharField(max_length=60, default="bi-basket2")
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("sort_order",)
        verbose_name_plural = "service categories"

    def __str__(self):
        return self.name


class ClothingItem(models.Model):
    category = models.ForeignKey(ServiceCategory, related_name="items", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="items/", blank=True)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=5)
    review_count = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} — ₹{self.price}"


class CustomerReview(models.Model):
    name = models.CharField(max_length=80)
    avatar = models.ImageField(upload_to="reviews/", blank=True)
    rating = models.PositiveSmallIntegerField(default=5)
    review = models.TextField()
    is_featured = models.BooleanField(default=True)

    def __str__(self):
        return self.name
