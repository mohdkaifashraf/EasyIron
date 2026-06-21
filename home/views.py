from django.db.models import Q
from django.shortcuts import render

from .models import Banner, ClothingItem, CustomerReview, ServiceCategory


DEFAULT_ITEM_GROUPS = [
    {
        "name": "Ironing",
        "slug": "ironing",
        "items": [
            {"name": "Shirt Ironing", "price": 10, "reviews": 120, "rating": 5, "icon": "bi-person-standing-dress"},
            {"name": "Pant Ironing", "price": 15, "reviews": 95, "rating": 5, "icon": "bi-person"},
            {"name": "Kurti Ironing", "price": 18, "reviews": 82, "rating": 5, "icon": "bi-person-standing-dress"},
            {"name": "T-Shirt Ironing", "price": 10, "reviews": 108, "rating": 5, "icon": "bi-person-arms-up"},
        ],
    },
    {
        "name": "Laundry",
        "slug": "laundry",
        "items": [
            {"name": "Shirt Wash", "price": 35, "reviews": 89, "rating": 5, "icon": "bi-person-standing"},
            {"name": "Pant Wash", "price": 45, "reviews": 76, "rating": 5, "icon": "bi-person"},
            {"name": "Kurti Wash", "price": 50, "reviews": 64, "rating": 5, "icon": "bi-person-standing-dress"},
            {"name": "Bedsheet Wash", "price": 80, "reviews": 112, "rating": 5, "icon": "bi-grid"},
        ],
    },
    {
        "name": "Dry Cleaning",
        "slug": "dry-cleaning",
        "items": [
            {"name": "Suit", "price": 299, "reviews": 71, "rating": 5, "icon": "bi-person-badge"},
            {"name": "Blazer", "price": 199, "reviews": 86, "rating": 5, "icon": "bi-person-vcard"},
            {"name": "Jacket", "price": 179, "reviews": 58, "rating": 5, "icon": "bi-snow"},
            {"name": "Saree", "price": 249, "reviews": 103, "rating": 5, "icon": "bi-person-standing-dress"},
        ],
    },
    {
        "name": "Premium Garment Care",
        "slug": "premium",
        "items": [
            {"name": "Silk Saree Care", "price": 349, "reviews": 78, "rating": 5, "icon": "bi-person-standing-dress"},
            {"name": "Designer Lehenga Care", "price": 499, "reviews": 54, "rating": 5, "icon": "bi-gem"},
            {"name": "Sherwani Care", "price": 449, "reviews": 61, "rating": 5, "icon": "bi-person-badge"},
            {"name": "Wedding Gown Care", "price": 599, "reviews": 42, "rating": 5, "icon": "bi-stars"},
        ],
    },
    {
        "name": "Shoe Cleaning",
        "slug": "shoes",
        "items": [
            {"name": "Sports Shoe Cleaning", "price": 199, "reviews": 94, "rating": 5, "icon": "bi-lightning"},
            {"name": "Leather Shoe Cleaning", "price": 249, "reviews": 72, "rating": 5, "icon": "bi-briefcase"},
            {"name": "Sneaker Cleaning", "price": 229, "reviews": 118, "rating": 5, "icon": "bi-stars"},
            {"name": "Boot Cleaning", "price": 299, "reviews": 49, "rating": 5, "icon": "bi-shield-check"},
        ],
    },
    {
        "name": "Blanket Cleaning",
        "slug": "blankets",
        "items": [
            {"name": "Single Blanket", "price": 199, "reviews": 87, "rating": 5, "icon": "bi-layers"},
            {"name": "Double Blanket", "price": 299, "reviews": 105, "rating": 5, "icon": "bi-layers-fill"},
            {"name": "Comforter Cleaning", "price": 349, "reviews": 69, "rating": 5, "icon": "bi-grid"},
            {"name": "Quilt Cleaning", "price": 399, "reviews": 57, "rating": 5, "icon": "bi-bounding-box"},
        ],
    },
]


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
        {"categories": categories, "banners": banners, "reviews": reviews, "item_groups": DEFAULT_ITEM_GROUPS},
    )


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
    return render(request, "home/help_center.html", {"faqs": faqs})
