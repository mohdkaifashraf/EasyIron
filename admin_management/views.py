from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction
from django.shortcuts import redirect, render

from agent_app.models import DeliveryAgent
from store_app.models import Store, StoreStaff

User = get_user_model()


def is_admin(user):
	return user.is_authenticated and user.is_staff


admin_required = user_passes_test(is_admin, login_url="adminpanel:login")


def admin_login(request):
	if request.user.is_authenticated and is_admin(request.user):
		return redirect("adminpanel:dashboard")
	form = AuthenticationForm(request, data=request.POST or None)
	if request.method == "POST" and form.is_valid():
		user = form.get_user()
		if user.is_staff:
			login(request, user)
			return redirect("adminpanel:dashboard")
		form.add_error(None, "Only an administrator can access this panel.")
	return render(request, "adminpanel/login.html", {"form": form})


@admin_required
def dashboard(request):
	error = None
	if request.method == "POST":
		action = request.POST.get("action")
		user_id = request.POST.get("user_id", "").strip()
		email = request.POST.get("email", "").strip().lower()
		password = request.POST.get("password", "")
		name = request.POST.get("name", "").strip()
		phone = request.POST.get("phone", "").strip()
		store = Store.objects.filter(pk=request.POST.get("store"), is_active=True).first()

		if not user_id or not password or not name or not phone or not store:
			error = "Complete all required fields and choose an active store."
		elif User.objects.filter(username__iexact=user_id).exists():
			error = "An account already exists with this user ID."
		elif email and User.objects.filter(email__iexact=email).exists():
			error = "An account already exists with this email."
		else:
			with transaction.atomic():
				user = User.objects.create_user(
					username=user_id,
					email=email,
					password=password,
					first_name=name,
				)
				if action == "create_store_staff":
					StoreStaff.objects.create(user=user, store=store, role=StoreStaff.Role.MANAGER)
				elif action == "create_agent":
					DeliveryAgent.objects.create(user=user, store=store, name=name, phone=phone)
				else:
					error = "Invalid account type."
					user.delete()
			if error is None:
				messages.success(request, f"{name}'s login account was created for {store.name}.")

	return render(
		request,
		"adminpanel/dashboard.html",
		{
			"stores": Store.objects.filter(is_active=True).order_by("name"),
			"staff_count": StoreStaff.objects.filter(is_active=True).count(),
			"agent_count": DeliveryAgent.objects.filter(is_active=True).count(),
			"error": error,
		},
	)
from django.shortcuts import render

# Create your views here.
