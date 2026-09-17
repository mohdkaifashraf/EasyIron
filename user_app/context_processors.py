def cart_summary(request):
    if not request.user.is_authenticated:
        return {
            "cart_count": 0,
            "cart_items": [],
            "cart_subtotal": 0,
        }

    from .models import Cart

    cart = (
        Cart.objects.filter(user=request.user, active=True)
        .prefetch_related("items")
        .first()
    )
    if not cart:
        return {
            "cart_count": 0,
            "cart_items": [],
            "cart_subtotal": 0,
        }

    items = list(cart.items.all())
    return {
        "cart_count": sum(item.quantity for item in items),
        "cart_items": items,
        "cart_subtotal": sum(item.total_price for item in items),
    }
