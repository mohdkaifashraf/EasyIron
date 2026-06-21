from datetime import timedelta
from decimal import Decimal
from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from store.models import CustomerNotification, DeliveryAgent, Order

from .models import (
    AgentEarnings,
    AgentNotification,
    DeliveryAssignment,
    OrderTracking,
    PickupAssignment,
)


PICKUP_TRANSITIONS = {
    PickupAssignment.Status.ASSIGNED: PickupAssignment.Status.ACCEPTED,
    PickupAssignment.Status.ACCEPTED: PickupAssignment.Status.REACHED,
    PickupAssignment.Status.REACHED: PickupAssignment.Status.COLLECTED,
    PickupAssignment.Status.COLLECTED: PickupAssignment.Status.STORE_DELIVERED,
}
DELIVERY_TRANSITIONS = {
    DeliveryAssignment.Status.READY: DeliveryAssignment.Status.ACCEPTED,
    DeliveryAssignment.Status.ACCEPTED: DeliveryAssignment.Status.STORE_PICKED,
    DeliveryAssignment.Status.STORE_PICKED: DeliveryAssignment.Status.OUT_FOR_DELIVERY,
    DeliveryAssignment.Status.OUT_FOR_DELIVERY: DeliveryAssignment.Status.DELIVERED,
}


def agent_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{redirect('agent:login').url}?next={request.path}")
        agent = DeliveryAgent.objects.select_related("store", "user").filter(
            user=request.user, is_active=True
        ).first()
        if not agent:
            return HttpResponseForbidden("This account is not an active EasyIron delivery agent.")
        request.delivery_agent = agent
        return view_func(request, *args, **kwargs)

    return wrapped


def _base_context(request):
    agent = request.delivery_agent
    return {
        "agent": agent,
        "unread_notifications": agent.agent_notifications.filter(is_read=False).count(),
    }


def _notify_customer(order, title, message):
    CustomerNotification.objects.create(
        order=order,
        customer_phone=order.customer_phone,
        title=title,
        message=message,
    )


def _track(order, agent, status, label, note=""):
    OrderTracking.objects.create(
        order=order, agent=agent, status=status, label=label, note=note
    )
    _notify_customer(order, f"{order.order_number}: {label}", note or label)


def agent_login(request):
    if request.user.is_authenticated and hasattr(request.user, "delivery_agent_profile"):
        return redirect("agent:dashboard")
    if request.method == "POST":
        identifier = request.POST.get("identifier", "").strip()
        password = request.POST.get("password", "")
        agent = DeliveryAgent.objects.select_related("user").filter(
            Q(email__iexact=identifier) | Q(phone=identifier), is_active=True, user__isnull=False
        ).first()
        user = authenticate(
            request,
            username=agent.user.username if agent and agent.user else identifier,
            password=password,
        )
        if user and agent and user.pk == agent.user_id:
            login(request, user)
            return redirect(request.GET.get("next") or "agent:dashboard")
        messages.error(request, "Invalid credentials or inactive delivery-agent account.")
    return render(request, "agent/login.html")


@require_POST
def agent_logout(request):
    logout(request)
    return redirect("agent:login")


@agent_required
def dashboard(request):
    agent = request.delivery_agent
    today = timezone.localdate()
    pickups = agent.pickup_assignments.select_related("order").filter(
        status__in=PICKUP_TRANSITIONS.keys()
    )
    deliveries = agent.delivery_assignments.select_related("order").filter(
        status__in=DELIVERY_TRANSITIONS.keys()
    )
    completed_pickups = agent.pickup_assignments.filter(
        status=PickupAssignment.Status.STORE_DELIVERED,
        delivered_to_store_at__date=today,
    ).count()
    completed_deliveries = agent.delivery_assignments.filter(
        status=DeliveryAssignment.Status.DELIVERED,
        delivered_at__date=today,
    ).count()
    context = {
        **_base_context(request),
        "pickups": pickups[:4],
        "deliveries": deliveries[:4],
        "stats": {
            "pickups_today": completed_pickups,
            "deliveries_today": completed_deliveries,
            "pending": pickups.count() + deliveries.count(),
            "completed": completed_pickups + completed_deliveries,
            "earnings": agent.earnings.filter(earned_on__date=today).aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0.00"),
        },
    }
    return render(request, "agent/dashboard.html", context)


@agent_required
def pickup_list(request):
    assignments = request.delivery_agent.pickup_assignments.select_related("order").prefetch_related(
        "order__items"
    )
    status_filter = request.GET.get("status", "")
    query = request.GET.get("q", "").strip()
    if status_filter:
        assignments = assignments.filter(status=status_filter)
    if query:
        assignments = assignments.filter(
            Q(order__order_number__icontains=query)
            | Q(order__customer_name__icontains=query)
            | Q(order__customer_phone__icontains=query)
        )
    return render(
        request,
        "agent/pickups.html",
        {
            **_base_context(request),
            "assignments": assignments,
            "status_choices": PickupAssignment.Status.choices,
            "status_filter": status_filter,
            "query": query,
        },
    )


@agent_required
def store_delivery_list(request):
    assignments = request.delivery_agent.pickup_assignments.select_related(
        "order", "order__store"
    ).filter(status=PickupAssignment.Status.COLLECTED)
    return render(
        request,
        "agent/store_deliveries.html",
        {**_base_context(request), "assignments": assignments},
    )


@agent_required
def return_delivery_list(request):
    assignments = request.delivery_agent.delivery_assignments.select_related("order").prefetch_related(
        "order__items"
    )
    status_filter = request.GET.get("status", "")
    query = request.GET.get("q", "").strip()
    if status_filter:
        assignments = assignments.filter(status=status_filter)
    if query:
        assignments = assignments.filter(
            Q(order__order_number__icontains=query)
            | Q(order__customer_name__icontains=query)
            | Q(order__customer_phone__icontains=query)
        )
    return render(
        request,
        "agent/deliveries.html",
        {
            **_base_context(request),
            "assignments": assignments,
            "status_choices": DeliveryAssignment.Status.choices,
            "status_filter": status_filter,
            "query": query,
        },
    )


@agent_required
def order_detail(request, order_id):
    agent = request.delivery_agent
    order = get_object_or_404(
        Order.objects.prefetch_related("items", "agent_tracking_events").select_related("store"),
        Q(pickup_assignment__agent=agent) | Q(return_assignment__agent=agent),
        pk=order_id,
    )
    pickup = PickupAssignment.objects.filter(order=order, agent=agent).first()
    delivery = DeliveryAssignment.objects.filter(order=order, agent=agent).first()
    return render(
        request,
        "agent/order_detail.html",
        {**_base_context(request), "order": order, "pickup": pickup, "delivery": delivery},
    )


@agent_required
@require_POST
@transaction.atomic
def update_pickup_status(request, pk):
    agent = request.delivery_agent
    assignment = get_object_or_404(
        PickupAssignment.objects.select_for_update().select_related("order", "order__store"),
        pk=pk,
        agent=agent,
    )
    requested_status = request.POST.get("status")
    expected_status = PICKUP_TRANSITIONS.get(assignment.status)
    if requested_status != expected_status:
        messages.error(request, "That pickup action is not available at this stage.")
        return redirect(request.POST.get("next") or "agent:pickups")

    now = timezone.now()
    assignment.status = requested_status
    timestamp_fields = {
        PickupAssignment.Status.ACCEPTED: "accepted_at",
        PickupAssignment.Status.REACHED: "reached_at",
        PickupAssignment.Status.COLLECTED: "collected_at",
        PickupAssignment.Status.STORE_DELIVERED: "delivered_to_store_at",
    }
    setattr(assignment, timestamp_fields[requested_status], now)
    assignment.save()

    labels = {
        PickupAssignment.Status.ACCEPTED: ("pickup_accepted", "Pickup Accepted", "Your pickup has been accepted by the delivery agent."),
        PickupAssignment.Status.REACHED: ("reached_customer", "Reached Customer", "Your EasyIron agent has reached the pickup address."),
        PickupAssignment.Status.COLLECTED: ("picked_up", "Clothes Collected", "Your clothes have been collected and are heading to the store."),
        PickupAssignment.Status.STORE_DELIVERED: ("delivered_to_store", "Delivered to Store", f"Your clothes have reached {assignment.order.store.name}."),
    }
    status, label, note = labels[requested_status]
    _track(assignment.order, agent, status, label, note)

    if requested_status == PickupAssignment.Status.STORE_DELIVERED:
        assignment.order.status = Order.Status.STORE_RECEIVED
        assignment.order.save(update_fields=("status", "updated_at"))
        assignment.order.add_tracking(
            Order.Status.STORE_RECEIVED, "Clothes delivered to store by delivery agent.", request.user
        )
        AgentEarnings.objects.get_or_create(
            agent=agent,
            order=assignment.order,
            task_type=AgentEarnings.TaskType.PICKUP,
            defaults={"amount": Decimal("30.00")},
        )
    messages.success(request, f"{assignment.order.order_number}: {label}.")
    return redirect(request.POST.get("next") or "agent:pickups")


@agent_required
@require_POST
@transaction.atomic
def update_delivery_status(request, pk):
    agent = request.delivery_agent
    assignment = get_object_or_404(
        DeliveryAssignment.objects.select_for_update().select_related("order"),
        pk=pk,
        agent=agent,
    )
    requested_status = request.POST.get("status")
    expected_status = DELIVERY_TRANSITIONS.get(assignment.status)
    if requested_status != expected_status:
        messages.error(request, "That delivery action is not available at this stage.")
        return redirect(request.POST.get("next") or "agent:deliveries")

    now = timezone.now()
    assignment.status = requested_status
    timestamp_fields = {
        DeliveryAssignment.Status.ACCEPTED: "accepted_at",
        DeliveryAssignment.Status.STORE_PICKED: "picked_from_store_at",
        DeliveryAssignment.Status.OUT_FOR_DELIVERY: "started_at",
        DeliveryAssignment.Status.DELIVERED: "delivered_at",
    }
    setattr(assignment, timestamp_fields[requested_status], now)
    assignment.save()

    labels = {
        DeliveryAssignment.Status.ACCEPTED: ("delivery_accepted", "Delivery Accepted", "Your return delivery has been accepted by the agent."),
        DeliveryAssignment.Status.STORE_PICKED: ("picked_from_store", "Picked From Store", "Your processed clothes have been picked up from the store."),
        DeliveryAssignment.Status.OUT_FOR_DELIVERY: ("out_for_delivery", "Out For Delivery", "Your EasyIron order is on its way to you."),
        DeliveryAssignment.Status.DELIVERED: ("delivered", "Delivered", "Your EasyIron order has been delivered successfully."),
    }
    status, label, note = labels[requested_status]
    _track(assignment.order, agent, status, label, note)

    if requested_status == DeliveryAssignment.Status.STORE_PICKED:
        assignment.order.status = Order.Status.AGENT_PICKED
    elif requested_status == DeliveryAssignment.Status.DELIVERED:
        assignment.order.status = Order.Status.DELIVERED
        assignment.order.delivery_date = now
        AgentEarnings.objects.get_or_create(
            agent=agent,
            order=assignment.order,
            task_type=AgentEarnings.TaskType.DELIVERY,
            defaults={"amount": Decimal("40.00")},
        )
    assignment.order.save(update_fields=("status", "delivery_date", "updated_at"))
    assignment.order.add_tracking(
        assignment.order.status, note, request.user
    )
    messages.success(request, f"{assignment.order.order_number}: {label}.")
    return redirect(request.POST.get("next") or "agent:deliveries")


@agent_required
def earnings(request):
    agent = request.delivery_agent
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    entries = agent.earnings.select_related("order")
    context = {
        **_base_context(request),
        "entries": entries[:30],
        "today_total": entries.filter(earned_on__date=today).aggregate(total=Sum("amount"))["total"] or 0,
        "week_total": entries.filter(earned_on__date__gte=week_start).aggregate(total=Sum("amount"))["total"] or 0,
        "month_total": entries.filter(earned_on__date__gte=month_start).aggregate(total=Sum("amount"))["total"] or 0,
        "completed_orders": entries.values("order").distinct().count(),
    }
    return render(request, "agent/earnings.html", context)


@agent_required
def notifications(request):
    agent = request.delivery_agent
    items = agent.agent_notifications.select_related("order")
    items.filter(is_read=False).update(is_read=True)
    return render(
        request,
        "agent/notifications.html",
        {**_base_context(request), "notification_items": items},
    )


@agent_required
def profile(request):
    agent = request.delivery_agent
    completed = agent.delivery_assignments.filter(
        status=DeliveryAssignment.Status.DELIVERED
    ).count()
    return render(
        request,
        "agent/profile.html",
        {**_base_context(request), "total_deliveries": completed},
    )
