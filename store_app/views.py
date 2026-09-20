from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.views.decorators.http import require_POST

from agent_app.models import Assignment, DeliveryAgent
from user_app.models import Order as CustomerOrder

from .models import Order, Store, StoreStaff


CUSTOMER_STATUS = {
	Order.RECEIVED: CustomerOrder.STATUS_PLACED,
	Order.ACCEPTED: CustomerOrder.STATUS_PICKUP,
	Order.PICKUP_ASSIGNED: CustomerOrder.STATUS_PICKUP,
	Order.PICKED_UP: CustomerOrder.STATUS_PICKED,
	Order.PROCESSING: CustomerOrder.STATUS_PROCESSING,
	Order.READY: CustomerOrder.STATUS_IRONING,
	Order.OUT_FOR_DELIVERY: CustomerOrder.STATUS_DELIVERING,
	Order.DELIVERED: CustomerOrder.STATUS_DELIVERED,
}


def staff_store(request):
	staff = StoreStaff.objects.select_related("store").filter(user=request.user, is_active=True, store__is_active=True).first()
	return staff.store if staff else None


def store_required(request):
	store = staff_store(request)
	if not store:
		return None, HttpResponseForbidden("This account is not assigned to an active store.")
	return store, None


def store_login(request):
	if request.user.is_authenticated and staff_store(request):
		next_url = request.GET.get("next")
		if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
			return redirect(next_url)
		return redirect("store:dashboard")

	error = ""
	if request.method == "POST":
		user_id = request.POST.get("username", "").strip()
		password = request.POST.get("password", "")
		user = authenticate(request, username=user_id, password=password)
		if user and StoreStaff.objects.filter(user=user, is_active=True, store__is_active=True).exists():
			login(request, user)
			next_url = request.POST.get("next") or request.GET.get("next")
			if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
				return redirect(next_url)
			return redirect("store:dashboard")
		error = "Invalid store user ID or password."

	return render(request, "store/login.html", {"error": error, "next": request.GET.get("next", "")})


def sync_customer(order):
	values = {"status": CUSTOMER_STATUS[order.status]}
	if order.status == Order.DELIVERED:
		values["delivery_date"] = timezone.localdate()
	CustomerOrder.objects.filter(order_id=order.order_number).update(**values)


@login_required(login_url="store:login")
def dashboard(request):
	store, error = store_required(request)
	if error:
		return error
	orders = store.orders.prefetch_related("items", "assignments__agent")
	return render(request, "store/dashboard.html", {"store": store, "orders": orders})


@login_required(login_url="store:login")
def order_detail(request, pk):
	store, error = store_required(request)
	if error:
		return error
	order = get_object_or_404(store.orders.prefetch_related("items", "tracking_events", "assignments__agent"), pk=pk)
	agents = DeliveryAgent.objects.filter(store=store, is_active=True)
	return render(request, "store/order_detail.html", {"store": store, "order": order, "agents": agents})


@login_required(login_url="store:login")
@require_POST
@transaction.atomic
def accept_order(request, pk):
	store, error = store_required(request)
	if error:
		return error
	order = get_object_or_404(store.orders, pk=pk)
	if order.status == Order.RECEIVED:
		order.status = Order.ACCEPTED
		order.save(update_fields=("status", "updated_at"))
		order.add_tracking(order.status, "Order accepted by the store.", request.user)
		sync_customer(order)
		messages.success(request, "Order accepted. Assign a pickup agent.")
	return redirect("store:order_detail", pk=order.pk)


@login_required(login_url="store:login")
@require_POST
@transaction.atomic
def assign_agent(request, pk):
	store, error = store_required(request)
	if error:
		return error
	order = get_object_or_404(store.orders, pk=pk)
	agent = get_object_or_404(DeliveryAgent, pk=request.POST.get("agent"), store=store, is_active=True)
	task_type = Assignment.DELIVERY if order.status == Order.READY else Assignment.PICKUP
	Assignment.objects.update_or_create(order=order, task_type=task_type, defaults={"agent": agent, "completed": False})
	if task_type == Assignment.PICKUP:
		order.status = Order.PICKUP_ASSIGNED
		order.save(update_fields=("status", "updated_at"))
		sync_customer(order)
	order.add_tracking(order.status, f"{agent.name} assigned for {task_type}.", request.user)
	messages.success(request, f"{agent.name} assigned.")
	return redirect("store:order_detail", pk=order.pk)


@login_required(login_url="store:login")
@require_POST
@transaction.atomic
def update_status(request, pk):
	store, error = store_required(request)
	if error:
		return error
	order = get_object_or_404(store.orders, pk=pk)
	next_status = request.POST.get("status")
	allowed = {
		Order.PICKED_UP: {Order.PROCESSING},
		Order.PROCESSING: {Order.READY},
		Order.READY: {Order.OUT_FOR_DELIVERY},
	}
	if next_status not in allowed.get(order.status, set()):
		messages.error(request, "Choose the next valid order status.")
		return redirect("store:order_detail", pk=order.pk)
	order.status = next_status
	order.save(update_fields=("status", "updated_at"))
	order.add_tracking(order.status, request.POST.get("note", ""), request.user)
	sync_customer(order)
	messages.success(request, "Customer order status updated.")
	return redirect("store:order_detail", pk=order.pk)

# Create your views here.
