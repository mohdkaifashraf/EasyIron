from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from store_app.models import Order

from .models import Assignment, DeliveryAgent


def current_agent(request):
	return DeliveryAgent.objects.filter(user=request.user, is_active=True).first()


def agent_login(request):
	if request.user.is_authenticated and current_agent(request):
		next_url = request.GET.get("next")
		if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
			return redirect(next_url)
		return redirect("agent:dashboard")

	error = ""
	if request.method == "POST":
		user_id = request.POST.get("username", "").strip()
		password = request.POST.get("password", "")
		user = authenticate(request, username=user_id, password=password)
		if user and DeliveryAgent.objects.filter(user=user, is_active=True).exists():
			login(request, user)
			next_url = request.POST.get("next") or request.GET.get("next")
			if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
				return redirect(next_url)
			return redirect("agent:dashboard")
		error = "Invalid agent user ID or password."

	return render(request, "agent/login.html", {"error": error, "next": request.GET.get("next", "")})


@login_required(login_url="agent:login")
def dashboard(request):
	agent = current_agent(request)
	if not agent:
		return render(request, "agent/login.html", {"error": "This account is not an active delivery agent."}, status=403)
	assignments = agent.assignments.select_related("order").filter(completed=False)
	return render(request, "agent/dashboard.html", {"agent": agent, "assignments": assignments})


@login_required(login_url="agent:login")
@require_POST
@transaction.atomic
def complete_assignment(request, pk):
	agent = current_agent(request)
	assignment = get_object_or_404(Assignment.objects.select_for_update().select_related("order"), pk=pk, agent=agent, completed=False)
	order = assignment.order
	if assignment.task_type == Assignment.PICKUP:
		order.status = Order.PICKED_UP
	elif assignment.task_type == Assignment.DELIVERY:
		order.status = Order.DELIVERED
	order.save(update_fields=("status", "updated_at"))
	order.add_tracking(order.status, f"{agent.name} completed {assignment.task_type}.", request.user)
	assignment.completed = True
	assignment.save(update_fields=("completed",))
	from store_app.views import sync_customer
	sync_customer(order)
	messages.success(request, "Assignment completed and customer status updated.")
	return redirect("agent:dashboard")

# Create your views here.
