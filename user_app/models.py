from django.conf import settings
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


class CustomerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    mobile = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True)
    allow_marketing = models.BooleanField(default=True)
    share_data = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "home_customerprofile"

    def __str__(self):
        return self.user.get_full_name() or self.user.email


class UserProfile(CustomerProfile):
    class Meta:
        proxy = True


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="addresses", on_delete=models.CASCADE)
    label = models.CharField(max_length=80, default="Home")
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=80)
    state = models.CharField(max_length=80)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=80, default="India")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.label} — {self.line1}, {self.city}"


class Order(models.Model):
    STATUS_PLACED = "placed"
    STATUS_PICKUP = "pickup_assigned"
    STATUS_PICKED = "picked_up"
    STATUS_PROCESSING = "processing"
    STATUS_IRONING = "ironing_completed"
    STATUS_DELIVERING = "out_for_delivery"
    STATUS_DELIVERED = "delivered"

    PAYMENT_PENDING = "pending"
    PAYMENT_PAID = "paid"
    PAYMENT_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PLACED, "Order Placed"),
        (STATUS_PICKUP, "Pickup Assigned"),
        (STATUS_PICKED, "Clothes Picked Up"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_IRONING, "Ironing Completed"),
        (STATUS_DELIVERING, "Out for Delivery"),
        (STATUS_DELIVERED, "Delivered"),
    ]
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_PENDING, "Pending"),
        (PAYMENT_PAID, "Paid"),
        (PAYMENT_FAILED, "Failed"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="orders", on_delete=models.CASCADE)
    store = models.ForeignKey(
        "store_app.Store", related_name="customer_orders", null=True, blank=True, on_delete=models.PROTECT
    )
    order_id = models.CharField(max_length=32, unique=True)
    pickup_address_record = models.ForeignKey(
        Address, related_name="orders", null=True, blank=True, on_delete=models.SET_NULL
    )
    pickup_address = models.TextField(blank=True)
    pickup_date = models.DateField(null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PLACED)
    payment_status = models.CharField(max_length=24, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_PENDING)
    razorpay_order_id = models.CharField(max_length=64, blank=True)
    razorpay_payment_id = models.CharField(max_length=64, blank=True)
    total_amount = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.order_id

    def status_index(self):
        order = [self.STATUS_PLACED, self.STATUS_PICKUP, self.STATUS_PICKED, self.STATUS_PROCESSING, self.STATUS_IRONING, self.STATUS_DELIVERING, self.STATUS_DELIVERED]
        return order.index(self.status) if self.status in order else 0

    def progress_steps(self):
        return [
            {"label": "Order Placed", "done": self.status_index() >= 0},
            {"label": "Pickup Assigned", "done": self.status_index() >= 1},
            {"label": "Clothes Picked Up", "done": self.status_index() >= 2},
            {"label": "Processing", "done": self.status_index() >= 3},
            {"label": "Ironing Completed", "done": self.status_index() >= 4},
            {"label": "Out for Delivery", "done": self.status_index() >= 5},
            {"label": "Delivered", "done": self.status_index() >= 6},
        ]


class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="carts", on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart for {self.user.email}"

    def total_amount(self):
        return sum(item.total_price for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    item_name = models.CharField(max_length=120)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.item_name} x{self.quantity}"

    @property
    def total_price(self):
        return self.quantity * self.price
