import json
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import (
    AccountSettingsForm,
    AddressForm,
    CustomerSignUpForm,
    ProfileUpdateForm,
)
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
)


DEFAULT_ITEM_GROUPS = [
    {
        "name": "Ironing",
        "slug": "ironing",
        "image": "images/cloth-ironing.svg",
        "items": [
            {"name": "Shirt Ironing", "price": 10, "reviews": 120, "rating": 5, "icon": "bi-person-standing-dress", "image": "images/shirt_image.jpg"},
            {"name": "Pant Ironing", "price": 15, "reviews": 95, "rating": 5, "icon": "bi-person", "image": "images/pant_image.jpg"},
            {"name": "Kurti Ironing", "price": 18, "reviews": 82, "rating": 5, "icon": "bi-person-standing-dress", "image": "images/kurti_image.jpg"},
            {"name": "T-Shirt Ironing", "price": 10, "reviews": 108, "rating": 5, "icon": "bi-person-arms-up", "image": "images/t-shirt_image.jpg"},
        ],
    },
    {
        "name": "Laundry",
        "slug": "laundry",
        "image": "images/cloth-laundry.svg",
        "items": [
            {"name": "Shirt Wash", "price": 35, "reviews": 89, "rating": 5, "icon": "bi-person-standing", "image": "images/shirt_image.jpg"},
            {"name": "Pant Wash", "price": 45, "reviews": 76, "rating": 5, "icon": "bi-person", "image": "images/pant_image.jpg"},
            {"name": "Kurti Wash", "price": 50, "reviews": 64, "rating": 5, "icon": "bi-person-standing-dress", "image": "images/kurti_image.jpg"},
            {"name": "Bedsheet Wash", "price": 80, "reviews": 112, "rating": 5, "icon": "bi-grid", "image": "images/bedsheet_image.jpg"},
        ],
    },
    {
        "name": "Dry Cleaning",
        "slug": "dry-cleaning",
        "image": "images/cloth-dry-cleaning.svg",
        "items": [
            {"name": "Suit", "price": 299, "reviews": 71, "rating": 5, "icon": "bi-person-badge", "image": "images/suit_image.jpg"},
            {"name": "Blazer", "price": 199, "reviews": 86, "rating": 5, "icon": "bi-person-vcard", "image": "images/blazer_image.jpg"},
            {"name": "Jacket", "price": 179, "reviews": 58, "rating": 5, "icon": "bi-snow", "image": "images/jacket_image.jpg"},
            {"name": "Saree", "price": 249, "reviews": 103, "rating": 5, "icon": "bi-person-standing-dress", "image": "images/saree_image.jpg"},
        ],
    },
    {
        "name": "Premium Garment Care",
        "slug": "premium",
        "image": "images/cloth-premium.svg",
        "items": [
            {"name": "Silk Saree Care", "price": 349, "reviews": 78, "rating": 5, "icon": "bi-person-standing-dress", "image": "images/silk_saree_image.jpg"},
            {"name": "Designer Lehenga Care", "price": 499, "reviews": 54, "rating": 5, "icon": "bi-gem", "image": "images/lehanga_image.jpg"},
            {"name": "Sherwani Care", "price": 449, "reviews": 61, "rating": 5, "icon": "bi-person-badge", "image": "images/serwanee_image.jpg"},
            {"name": "Wedding Gown Care", "price": 599, "reviews": 42, "rating": 5, "icon": "bi-stars", "image": "images/wedding_gown_image.jpg"},
        ],    
    },
    {
        "name": "Shoe Cleaning",
        "slug": "shoes",
        "image": "images/cloth-shoes.svg",
        "items": [
            {"name": "Sports Shoe Cleaning", "price": 199, "reviews": 94, "rating": 5, "icon": "bi-lightning", "image": "images/sport_shoe_image.jpg"},
            {"name": "Leather Shoe Cleaning", "price": 249, "reviews": 72, "rating": 5, "icon": "bi-briefcase", "image": "images/leather_shoe_image.jpg"},
            {"name": "Sneaker Cleaning", "price": 229, "reviews": 118, "rating": 5, "icon": "bi-stars", "image": "images/sneaker_shoe_image.jpg"},
            {"name": "Boot Cleaning", "price": 299, "reviews": 49, "rating": 5, "icon": "bi-shield-check", "image": "images/boot_shoe_image.jpg"},
        ],
    },
    {
        "name": "Blanket Cleaning",
        "slug": "blankets",
        "image": "images/cloth-blankets.svg",
        "items": [
            {"name": "Single Blanket", "price": 199, "reviews": 87, "rating": 5, "icon": "bi-layers", "image": "images/single_blanket_image.jpg"},
            {"name": "Double Blanket", "price": 299, "reviews": 105, "rating": 5, "icon": "bi-layers-fill", "image": "images/doule_blanket_image.jpg"},
            {"name": "Comforter Cleaning", "price": 349, "reviews": 69, "rating": 5, "icon": "bi-grid", "image": "images/comforter_image.jpg"},
            {"name": "Quilt Cleaning", "price": 399, "reviews": 57, "rating": 5, "icon": "bi-bounding-box", "image": "images/quilt_image.jpg"},
        ],
    },
]


def get_profile(user):
    profile, _ = CustomerProfile.objects.get_or_create(user=user)
    return profile


def get_active_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user, active=True)
    return cart


def homepage(request):
    categories = list(ServiceCategory.objects.prefetch_related("items").all())
    banners = list(Banner.objects.filter(is_active=True))
    reviews = list(CustomerReview.objects.filter(is_featured=True))

    if not categories:
        categories = [
            {"name": "Ironing Service", "slug": "ironing", "icon": "bi-steam", "description": "Crisp, wrinkle-free finishing for everyday wear."},
            {"name": "Laundry Service", "slug": "laundry", "icon": "bi-droplet", "description": "Fresh, hygienic washing with fabric-safe care."},
            {"name": "Dry Cleaning", "slug": "dry-cleaning", "icon": "bi-stars", "description": "Specialist cleaning for delicate and formal wear."},
            {"name": "Premium Garment Care", "slug": "premium", "icon": "bi-gem", "description": "Signature care for luxury and designer garments."},
            {"name": "Shoe Cleaning", "slug": "shoes", "icon": "bi-brush", "description": "Deep cleaning that brings your footwear back to life."},
            {"name": "Blanket Cleaning", "slug": "blankets", "icon": "bi-layers", "description": "Deep, gentle cleaning for blankets and comforters."},
        ]

    if not banners:
        banners = [
            {"title": "50% OFF on First Order", "subtitle": "Use code EASY50"},
            {"title": "Free Pickup & Delivery", "subtitle": "Right from your doorstep"},
            {"title": "Same Day Service", "subtitle": "Fresh clothes, faster"},
            {"title": "Premium Garment Care", "subtitle": "Special care for special clothes"},
            {"title": "Monthly Laundry Subscription", "subtitle": "Save more every month"},
        ]

    if not reviews:
        reviews = [
            {"name": "Aarav Mehta", "rating": 5, "review": "Super convenient and the shirts came back perfectly pressed. Pickup was exactly on time."},
            {"name": "Neha Sharma", "rating": 5, "review": "EasyIron handled my silk saree beautifully. The packaging and finish felt truly premium."},
            {"name": "Rohan Kapoor", "rating": 5, "review": "The monthly plan is excellent value. Reliable service and very responsive support."},
        ]

    return render(
        request,
        "home/home.html",
        {
            "categories": categories,
            "banners": banners,
            "reviews": reviews,
            "item_groups": DEFAULT_ITEM_GROUPS,
        },
    )


def signup(request):
    if request.user.is_authenticated:
        return redirect("home:account")

    if request.method == "POST":
        form = CustomerSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your account has been created successfully. Please log in.")
            return redirect("home:login")
    else:
        form = CustomerSignUpForm()

    return render(request, "home/signup.html", {"form": form})


def role_login_gate(request):
    next_url = request.GET.get("next") or ""
    return render(request, "home/role_login_gate.html", {"next": next_url})


def customer_login(request):

    if request.user.is_authenticated:
        return redirect("home:account")

    next_page = request.GET.get("next") or request.POST.get("next")
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, "Welcome back!")
            # After login, always land on the home page.
            return redirect(reverse("home:homepage"))
    else:
        form = AuthenticationForm(request)

    form.fields["username"].label = "Email address"
    form.fields["username"].widget.attrs.update(
        {"class": "form-control", "placeholder": "you@example.com", "autofocus": True}
    )
    form.fields["password"].widget.attrs.update(
        {"class": "form-control", "placeholder": "Enter your password"}
    )

    return render(request, "home/login.html", {"form": form, "next": next_page})


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("home:login")


@login_required
def account_dashboard(request):
    profile = get_profile(request.user)
    orders = request.user.orders.all()[:4]
    addresses = request.user.addresses.all()[:3]
    cart = get_active_cart(request.user)
    notifications = [
        {"title": "Pickup confirmed", "message": "Your pickup for order #EI2048 has been scheduled.", "time": "2h ago"},
        {"title": "Order processed", "message": "Clothes from order #EI2041 are now being processed.", "time": "1d ago"},
        {"title": "Delivery scheduled", "message": "Your order #EI2039 is out for delivery tomorrow.", "time": "3d ago"},
    ]

    return render(
        request,
        "home/account/dashboard.html",
        {
            "profile": profile,
            "orders": orders,
            "addresses": addresses,
            "cart": cart,
            "notifications": notifications,
        },
    )


@login_required
def account_profile(request):
    profile = get_profile(request.user)
    if request.method == "POST":
        if "profile_submit" in request.POST:
            profile_form = ProfileUpdateForm(request.POST, user=request.user)
            password_form = PasswordChangeForm(request.user)
            if profile_form.is_valiwd():
                profile_form.save()
                messages.success(request, "Your profile was updated successfully.")
                return redirect("home:account_profile")
        elif "password_submit" in request.POST:
            profile_form = ProfileUpdateForm(user=request.user, initial={
                "name": request.user.first_name,
                "email": request.user.email,
                "mobile": profile.mobile,
                "address": profile.address,
            })
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Your password has been updated.")
                return redirect("home:account_profile")
        else:
            profile_form = ProfileUpdateForm(
                user=request.user,
                initial={
                    "name": request.user.first_name,
                    "email": request.user.email,
                    "mobile": profile.mobile,
                    "address": profile.address,
                },
            )
            password_form = PasswordChangeForm(request.user)
    else:
        profile_form = ProfileUpdateForm(
            user=request.user,
            initial={
                "name": request.user.first_name,
                "email": request.user.email,
                "mobile": profile.mobile,
                "address": profile.address,
            },
        )
        password_form = PasswordChangeForm(request.user)

    return render(
        request,
        "home/account/profile.html",
        {
            "profile": profile,
            "profile_form": profile_form,
            "password_form": password_form,
        },
    )


@login_required
def account_orders(request):
    orders = request.user.orders.all()
    return render(request, "home/account/orders.html", {"orders": orders})


@login_required
def account_addresses(request):
    profile = get_profile(request.user)
    edit_id = request.GET.get("edit")
    address = None
    if edit_id:
        address = get_object_or_404(Address, pk=edit_id, user=request.user)

    if request.method == "POST":
        if "save_address" in request.POST:
            if address:
                form = AddressForm(request.POST, instance=address)
            else:
                form = AddressForm(request.POST)
            if form.is_valid():
                address_instance = form.save(commit=False)
                address_instance.user = request.user
                if address_instance.is_default:
                    Address.objects.filter(user=request.user).update(is_default=False)
                address_instance.save()
                messages.success(request, "Address saved successfully.")
                return redirect("home:account_addresses")
        elif "delete_address" in request.POST:
            address_id = request.POST.get("address_id")
            if address_id:
                Address.objects.filter(pk=address_id, user=request.user).delete()
                messages.success(request, "Address removed.")
            return redirect("home:account_addresses")
        elif "set_default" in request.POST:
            address_id = request.POST.get("address_id")
            if address_id:
                Address.objects.filter(user=request.user).update(is_default=False)
                Address.objects.filter(pk=address_id, user=request.user).update(is_default=True)
                messages.success(request, "Default address updated.")
            return redirect("home:account_addresses")
    else:
        form = AddressForm(instance=address)

    return render(
        request,
        "home/account/addresses.html",
        {
            "profile": profile,
            "addresses": request.user.addresses.all(),
            "form": form,
            "edit_address": address,
        },
    )


@require_POST
def add_to_cart(request):
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to add items to your cart.")
        return redirect("home:login")

    item_name = request.POST.get("item_name", "").strip()

    if not item_name:
        messages.error(request, "Please select an item to add to your cart.")
        return redirect("home:homepage")

    try:
        price = Decimal(str(request.POST.get("price", "0")))
    except (InvalidOperation, ValueError):
        price = Decimal("0")

    quantity = int(request.POST.get("quantity", 1) or 1)

    if quantity < 1:
        quantity = 1

    cart = get_active_cart(request.user)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        item_name=item_name,
        defaults={
            "price": price,
            "quantity": quantity
        },
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.price = price
        cart_item.save(update_fields=["quantity", "price"])

    messages.success(request, f"{item_name} added to your cart.")

    cart_count = sum(item.quantity for item in cart.items.all())
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "message": f"{item_name} added to your cart.",
            "cart_count": cart_count,
        })

    next_url = request.POST.get("next")
    if next_url and next_url.startswith("/"):
        return redirect(next_url)

    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)

    return redirect("home:homepage")


@login_required 
def account_cart(request):
    cart = get_active_cart(request.user)
    if request.method == "POST":
        if "update_item" in request.POST:
            item_id = request.POST.get("item_id")
            quantity = int(request.POST.get("quantity", 1))
            item = get_object_or_404(CartItem, pk=item_id, cart=cart)
            if quantity < 1:
                item.delete()
            else:
                item.quantity = quantity
                item.save()
            messages.success(request, "Cart updated.")
            return redirect("home:account_cart")
        if "remove_item" in request.POST:
            item_id = request.POST.get("item_id")
            CartItem.objects.filter(pk=item_id, cart=cart).delete()
            messages.success(request, "Item removed from cart.")
            return redirect("home:account_cart")
        if "clear_cart" in request.POST:
            cart.items.all().delete()
            messages.success(request, "Cart cleared.")
            return redirect("home:account_cart")
    items = cart.items.all()
    subtotal = cart.total_amount()
    return render(request, "home/account/cart.html", {"cart": cart, "items": items, "subtotal": subtotal})


@login_required
def remove_cart_item(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Only POST requests are allowed."}, status=405)

    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        payload = {}

    item_id = payload.get("item_id") or request.POST.get("item_id")
    if not item_id:
        return JsonResponse({"success": False, "message": "Missing item_id."}, status=400)

    cart = get_active_cart(request.user)
    cart_item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    removed_total = float(cart_item.total_price)
    cart_item.delete()

    remaining_count = sum(item.quantity for item in cart.items.all())
    remaining_subtotal = float(cart.total_amount())
    return JsonResponse({
        "success": True,
        "message": "Item removed from cart.",
        "cart_count": remaining_count,
        "subtotal": remaining_subtotal,
        "removed_total": removed_total,
    })


@login_required
def account_settings(request):
    profile = get_profile(request.user)
    if request.method == "POST":
        if "settings_submit" in request.POST:
            form = AccountSettingsForm(request.POST, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(request, "Account settings updated.")
                return redirect("home:account_settings")
        elif "delete_account" in request.POST:
            request.user.delete()
            messages.success(request, "Your account has been deleted.")
            return redirect("home:homepage")
    else:
        form = AccountSettingsForm(instance=profile)

    return render(request, "home/account/settings.html", {"profile": profile, "settings_form": form})


def search_services(request):
    query = request.GET.get("q", "").strip()
    results = []

    if query:
        database_items = ClothingItem.objects.filter(is_available=True).filter(
            Q(name__icontains=query)
            | Q(category__name__icontains=query)
            | Q(category__slug__icontains=query)
            | Q(category__description__icontains=query)
        ).select_related("category")

        for item in database_items:
            results.append(
                {
                    "name": item.name,
                    "price": item.price,
                    "reviews": item.review_count,
                    "rating": item.rating,
                    "icon": item.category.icon,
                    "category": item.category.name,
                }
            )

        if not results:
            search_term = query.casefold()
            aliases = {
                "iron": "ironing",
                "press": "ironing",
                "wash": "laundry",
                "washing": "laundry",
                "dry clean": "dry cleaning",
            }
            expanded_term = next(
                (value for key, value in aliases.items() if key in search_term),
                search_term,
            )
            for group in DEFAULT_ITEM_GROUPS:
                group_matches = (
                    search_term in group["name"].casefold()
                    or expanded_term in group["name"].casefold()
                )
                for item in group["items"]:
                    if group_matches or search_term in item["name"].casefold():
                        results.append({**item, "category": group["name"]})

    return render(
        request,
        "home/search_results.html",
        {"query": query, "results": results},
    )


def help_center(request):
    faqs = [
        {
            "question": "How do I book a pickup?",
            "answer": "Choose your required services, add the clothing items to your laundry bag, and select Schedule Pickup.",
        },
        {
            "question": "Is pickup and delivery free?",
            "answer": "Pickup and delivery are free for eligible orders above ₹199.",
        },
        {
            "question": "How long does an order take?",
            "answer": "Standard orders are usually completed within 48 hours. Same-day service is available for selected items and locations.",
        },
        {
            "question": "How can I track my order?",
            "answer": "Use Track Order from the navigation bar and enter your EasyIron order number.",
        },
        {
            "question": "What happens if a garment needs special care?",
            "answer": "Our garment-care team checks every item and contacts you before applying any treatment that requires approval.",
        },
        {
            "question": "How can I change or cancel a booking?",
            "answer": "Contact our support team before the pickup begins, and we will update or cancel the booking for you.",
        },
    ]
    return render(
        request,
        "home/help_center.html",
        {"faqs": faqs},
    )
