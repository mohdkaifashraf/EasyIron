from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ServiceForm
from .models import CustomerNotification, DeliveryAgent, Order, Service, Store, StoreStaff


def _staff_store(request):
    if request.user.is_superuser:
        return Store.objects.filter(is_active=True).first()
    profile = StoreStaff.objects.select_related("store").filter(
        user=request.user, is_active=True, store__is_active=True
    ).first()
    return profile.store if profile else None


def _store_or_forbidden(request):
    store = _staff_store(request)
    if store is None:
        return None, HttpResponseForbidden("Your account is not assigned to an active EasyIron store.")
    return store, None


def _store_order(request, pk):
    store, error = _store_or_forbidden(request)
    if error:
        return None, None, error
    return store, get_object_or_404(Order.objects.prefetch_related("items"), pk=pk, store=store), None


def _notify_status(order):
    CustomerNotification.objects.create(
        order=order,
        customer_phone=order.customer_phone,
        title=f"{order.order_number} updated",
        message=f"Your EasyIron order status is now: {order.get_status_display()}.",
    )


@login_required
def dashboard(request):
    store, error = _store_or_forbidden(request)
    if error:
        return error
    today = timezone.localdate()
    today_orders = store.orders.filter(created_at__date=today)
    completed_today = store.orders.filter(status=Order.Status.DELIVERED, updated_at__date=today)
    stats = {
        "total_today": today_orders.count(),
        "pending": store.orders.filter(status=Order.Status.RECEIVED).count(),
        "processing": store.orders.filter(
            status__in=[
                Order.Status.STORE_RECEIVED,
                Order.Status.PROCESSING,
                Order.Status.IRONING_COMPLETED,
                Order.Status.LAUNDRY_COMPLETED,
                Order.Status.QUALITY_CHECK,
            ]
        ).count(),
        "ready": store.orders.filter(status=Order.Status.READY).count(),
        "completed": completed_today.count(),
        "revenue": sum((order.total_amount for order in completed_today.prefetch_related("items")), 0),
    }
    recent_orders = store.orders.prefetch_related("items").select_related("delivery_agent")[:8]
    return render(request, "store/dashboard.html", {"store": store, "stats": stats, "orders": recent_orders})


@login_required
def incoming_orders(request):
    store, error = _store_or_forbidden(request)
    if error:
        return error
    orders = store.orders.filter(status=Order.Status.RECEIVED, accepted_at__isnull=True).prefetch_related("items")
    return render(request, "store/incoming_orders.html", {"store": store, "orders": orders})


@login_required
def order_detail(request, pk):
    store, order, error = _store_order(request, pk)
    if error:
        return error
    order = (
        store.orders.prefetch_related("items", "tracking_events__changed_by")
        .select_related("delivery_agent")
        .get(pk=order.pk)
    )
    agents = store.delivery_agents.filter(is_active=True, is_available=True)
    return render(
        request,
        "store/order_detail.html",
        {"store": store, "order": order, "status_choices": Order.Status.choices, "agents": agents},
    )


@login_required
@require_POST
@transaction.atomic
def accept_order(request, pk):
    _, order, error = _store_order(request, pk)
    if error:
        return error
    if order.status == Order.Status.RECEIVED and order.accepted_at is None:
        order.accepted_at = timezone.now()
        order.save(update_fields=("accepted_at", "updated_at"))
        order.add_tracking(Order.Status.RECEIVED, "Order accepted by store.", request.user)
        CustomerNotification.objects.create(
            order=order,
            customer_phone=order.customer_phone,
            title="Order accepted",
            message=f"{order.order_number} has been accepted by {order.store.name}.",
        )
        messages.success(request, f"{order.order_number} accepted.")
    return redirect(request.POST.get("next") or "store:incoming_orders")


@login_required
@require_POST
@transaction.atomic
def reject_order(request, pk):
    _, order, error = _store_order(request, pk)
    if error:
        return error
    order.status = Order.Status.REJECTED
    order.rejected_reason = request.POST.get("reason", "").strip() or "Store unable to fulfil order."
    order.save(update_fields=("status", "rejected_reason", "updated_at"))
    order.add_tracking(Order.Status.REJECTED, order.rejected_reason, request.user)
    _notify_status(order)
    messages.warning(request, f"{order.order_number} rejected.")
    return redirect("store:incoming_orders")


@login_required
@require_POST
@transaction.atomic
def update_order_status(request, pk):
    _, order, error = _store_order(request, pk)
    if error:
        return error
    status = request.POST.get("status")
    valid_statuses = dict(Order.Status.choices)
    if status not in valid_statuses:
        messages.error(request, "Invalid order status.")
        return redirect("store:order_detail", pk=order.pk)
    order.status = status
    if status == Order.Status.DELIVERED and not order.delivery_date:
        order.delivery_date = timezone.now()
    order.save(update_fields=("status", "delivery_date", "updated_at"))
    order.add_tracking(status, request.POST.get("note", "").strip(), request.user)
    _notify_status(order)
    messages.success(request, f"Status updated to {valid_statuses[status]}.")
    next_url = request.POST.get("next")
    return redirect(next_url) if next_url else redirect("store:order_detail", pk=order.pk)


@login_required
def inventory(request):
    store, error = _store_or_forbidden(request)
    if error:
        return error
    active_statuses = [value for value, _ in Order.Status.choices if value not in (Order.Status.DELIVERED, Order.Status.REJECTED)]
    orders = store.orders.filter(status__in=active_statuses).prefetch_related("items")
    totals = orders.aggregate(total_pieces=Sum("items__quantity"))
    return render(request, "store/inventory.html", {"store": store, "orders": orders, "totals": totals})


@login_required
def delivery_management(request):
    store, error = _store_or_forbidden(request)
    if error:
        return error
    orders = store.orders.filter(
        status__in=[Order.Status.READY, Order.Status.AGENT_PICKED]
    ).prefetch_related("items").select_related("delivery_agent")
    agents = store.delivery_agents.filter(is_active=True)
    return render(request, "store/deliveries.html", {"store": store, "orders": orders, "agents": agents})


@login_required
@require_POST
@transaction.atomic
def assign_delivery_agent(request, pk):
    store, order, error = _store_order(request, pk)
    if error:
        return error
    agent = get_object_or_404(DeliveryAgent, pk=request.POST.get("agent"), store=store, is_active=True)
    order.delivery_agent = agent
    order.save(update_fields=("delivery_agent", "updated_at"))
    from agent_app.models import AgentNotification, DeliveryAssignment, PickupAssignment

    if order.status == Order.Status.READY:
        DeliveryAssignment.objects.update_or_create(
            order=order,
            defaults={
                "agent": agent,
                "delivery_time": order.delivery_date,
                "status": DeliveryAssignment.Status.READY,
            },
        )
        notification_title = "New delivery assigned"
        notification_message = f"Collect {order.order_number} from {store.name} for customer delivery."
    else:
        PickupAssignment.objects.update_or_create(
            order=order,
            defaults={
                "agent": agent,
                "pickup_time": order.pickup_date,
                "status": PickupAssignment.Status.ASSIGNED,
            },
        )
        notification_title = "New pickup assigned"
        notification_message = f"Pickup {order.order_number} from {order.customer_name}."
    AgentNotification.objects.create(
        agent=agent,
        order=order,
        title=notification_title,
        message=notification_message,
        notification_type="assignment",
    )
    order.add_tracking(order.status, f"Delivery assigned to {agent.name}.", request.user)
    CustomerNotification.objects.create(
        order=order,
        customer_phone=order.customer_phone,
        title="Delivery agent assigned",
        message=f"{agent.name} has been assigned to deliver {order.order_number}.",
    )
    messages.success(request, f"{agent.name} assigned to {order.order_number}.")
    return redirect(request.POST.get("next") or "store:deliveries")


@login_required
def service_list(request):
    store, error = _store_or_forbidden(request)
    if error:
        return error
    services = store.services.all()
    return render(request, "store/service_list.html", {"store": store, "services": services})


@login_required
def service_create(request):
    store, error = _store_or_forbidden(request)
    if error:
        return error
    form = ServiceForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        service = form.save(commit=False)
        service.store = store
        service.save()
        messages.success(request, "Service added.")
        return redirect("store:service_list")
    return render(request, "store/service_form.html", {"store": store, "form": form, "title": "Add Service"})


@login_required
def service_update(request, pk):
    store, error = _store_or_forbidden(request)
    if error:
        return error
    service = get_object_or_404(Service, pk=pk, store=store)
    form = ServiceForm(request.POST or None, request.FILES or None, instance=service)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Service updated.")
        return redirect("store:service_list")
    return render(request, "store/service_form.html", {"store": store, "form": form, "title": "Edit Service"})


@login_required
@require_POST
def service_delete(request, pk):
    store, error = _store_or_forbidden(request)
    if error:
        return error
    service = get_object_or_404(Service, pk=pk, store=store)
    service.delete()
    messages.success(request, "Service deleted.")
    return redirect("store:service_list")


@login_required
def customer_search(request):
    store, error = _store_or_forbidden(request)
    if error:
        return error
    query = request.GET.get("q", "").strip()
    orders = store.orders.none()
    if query:
        orders = store.orders.filter(
            Q(customer_name__icontains=query)
            | Q(customer_phone__icontains=query)
            | Q(order_number__icontains=query)
        ).prefetch_related("items")
    return render(request, "store/customer_search.html", {"store": store, "query": query, "orders": orders})
