from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from store_app.forms import ServiceForm
from store_app.models import DeliveryAgent, Service, Store, StoreStaff

User = get_user_model()


def is_admin_user(user):
    return user.is_superuser or user.is_staff


admin_required = user_passes_test(is_admin_user, login_url="adminpanel:login")


def admin_login(request):
    if request.user.is_authenticated and is_admin_user(request.user):
        return redirect("adminpanel:dashboard")

    next_page = request.GET.get("next") or request.POST.get("next")
    data = None
    if request.method == "POST":
        data = request.POST.copy()
        login_value = data.get("username", "").strip()
        if "@" in login_value:
            user_by_email = User.objects.filter(email__iexact=login_value).first()
            if user_by_email:
                data["username"] = user_by_email.get_username()

    form = AuthenticationForm(request, data=data)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        if is_admin_user(user):
            login(request, user)
            return redirect(next_page or "adminpanel:dashboard")
        form.add_error(None, "You must login with an admin account.")

    return render(request, "adminpanel/login.html", {"form": form, "next": next_page})


@admin_required
def admin_dashboard(request):
    stores = Store.objects.filter(is_active=True)
    success_message = None
    error_message = None
    store_form_data = {}
    agent_form_data = {}

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create_store":
            name = request.POST.get("name", "").strip()
            code = request.POST.get("code", "").strip()
            phone = request.POST.get("phone", "").strip()
            email = request.POST.get("email", "").strip()
            address = request.POST.get("address", "").strip()
            staff_name = request.POST.get("staff_name", "").strip()
            staff_email = request.POST.get("staff_email", "").strip()
            staff_phone = request.POST.get("staff_phone", "").strip()
            staff_password = request.POST.get("staff_password", "")

            store_form_data = {
                "name": name,
                "code": code,
                "phone": phone,
                "email": email,
                "address": address,
                "staff_name": staff_name,
                "staff_email": staff_email,
                "staff_phone": staff_phone,
            }

            if not (name and code and phone and address and staff_email and staff_password):
                error_message = "Please fill all required store and staff fields."
            elif User.objects.filter(email__iexact=staff_email).exists():
                error_message = "A staff user with this email already exists."
            else:
                with transaction.atomic():
                    store, _ = Store.objects.get_or_create(
                        code=code,
                        defaults={
                            "name": name,
                            "phone": phone,
                            "email": email,
                            "address": address,
                            "is_active": True,
                        },
                    )
                    store.name = name
                    store.phone = phone
                    store.email = email
                    store.address = address
                    store.is_active = True
                    store.save()

                    staff_user = User.objects.create_user(
                        username=staff_email,
                        email=staff_email,
                        password=staff_password,
                        first_name=staff_name or "Store Manager",
                    )
                    StoreStaff.objects.create(
                        user=staff_user,
                        store=store,
                        role=StoreStaff.Role.MANAGER,
                        phone=staff_phone,
                        is_active=True,
                    )

                success_message = "Store and manager account created successfully."
                store_form_data = {}
        elif action == "create_agent":
            store_id = request.POST.get("store")
            name = request.POST.get("name", "").strip()
            email = request.POST.get("email", "").strip()
            phone = request.POST.get("phone", "").strip()
            vehicle_type = request.POST.get("vehicle_type", DeliveryAgent.VehicleType.BIKE)
            vehicle_number = request.POST.get("vehicle_number", "").strip()
            agent_password = request.POST.get("password", "")

            agent_form_data = {
                "store": store_id,
                "name": name,
                "email": email,
                "phone": phone,
                "vehicle_type": vehicle_type,
                "vehicle_number": vehicle_number,
            }

            if not (store_id and name and email and phone and agent_password):
                error_message = "Please fill all required delivery agent fields."
            else:
                store = get_object_or_404(Store, pk=store_id)
                if User.objects.filter(email__iexact=email).exists():
                    error_message = "An agent user with this email already exists."
                else:
                    with transaction.atomic():
                        agent_user = User.objects.create_user(
                            username=email,
                            email=email,
                            password=agent_password,
                            first_name=name,
                        )
                        DeliveryAgent.objects.create(
                            user=agent_user,
                            store=store,
                            name=name,
                            email=email,
                            phone=phone,
                            vehicle_type=vehicle_type,
                            vehicle_number=vehicle_number,
                            is_available=True,
                            is_active=True,
                            rating=Decimal("5.0"),
                        )

                    success_message = "Delivery agent account created successfully."
                    agent_form_data = {}
        else:
            error_message = "Invalid form submission."

        stores = Store.objects.filter(is_active=True)

    stats = {
        "services_total": Service.objects.count(),
        "services_active": Service.objects.filter(is_active=True).count(),
        "stores_total": Store.objects.count(),
        "delivery_agents_total": DeliveryAgent.objects.count(),
        "created_today": User.objects.filter(date_joined__date=timezone.localdate()).count(),
    }

    return render(
        request,
        "adminpanel/dashboard.html",
        {
            **stats,
            "stores": stores,
            "vehicle_choices": DeliveryAgent.VehicleType.choices,
            "success_message": success_message,
            "error_message": error_message,
            "store_form_data": store_form_data,
            "agent_form_data": agent_form_data,
        },
    )


@admin_required
def service_list(request):
    services = Service.objects.select_related("store").all().order_by("store__name", "name")
    return render(request, "adminpanel/services/list.html", {"services": services})


@admin_required
def service_create(request):
    if request.method == "POST":
        store_id = request.POST.get("store")
        store = get_object_or_404(Store, pk=store_id)
        form = ServiceForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                service = form.save(commit=False)
                service.store = store
                service.save()
            messages.success(request, "Service created successfully.")
            return redirect("adminpanel:service_list")
    else:
        form = ServiceForm()

    stores = Store.objects.filter(is_active=True)
    return render(
        request,
        "adminpanel/services/form.html",
        {"form": form, "stores": stores, "mode": "add"},
    )


@admin_required
def service_update(request, pk):
    service = get_object_or_404(Service, pk=pk)

    if request.method == "POST":
        form = ServiceForm(request.POST, request.FILES, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Service updated successfully.")
            return redirect("adminpanel:service_list")
    else:
        form = ServiceForm(instance=service)

    stores = Store.objects.filter(is_active=True)
    return render(
        request,
        "adminpanel/services/form.html",
        {"form": form, "stores": stores, "mode": "edit", "service": service},
    )


@admin_required
@require_http_methods(["POST"])
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    service.delete()
    messages.success(request, "Service deleted successfully.")
    return redirect("adminpanel:service_list")


@admin_required
def create_store(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        code = request.POST.get("code", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        address = request.POST.get("address", "").strip()

        staff_name = request.POST.get("staff_name", "").strip()
        staff_email = request.POST.get("staff_email", "").strip()
        staff_phone = request.POST.get("staff_phone", "").strip()
        staff_password = request.POST.get("staff_password", "")

        if not (name and code and phone and address and staff_email and staff_password):
            messages.error(request, "Please fill all required fields.")
            return redirect("adminpanel:create_store")

        with transaction.atomic():
            store, _ = Store.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "phone": phone,
                    "email": email,
                    "address": address,
                    "is_active": True,
                },
            )
            store.name = name
            store.phone = phone
            store.email = email
            store.address = address
            store.is_active = True
            store.save()

            if User.objects.filter(email__iexact=staff_email).exists():
                messages.error(request, "A staff user with this email already exists.")
                return redirect("adminpanel:create_store")

            staff_user = User.objects.create_user(
                username=staff_email,
                email=staff_email,
                password=staff_password,
                first_name=staff_name or "Store Manager",
            )
            StoreStaff.objects.create(
                user=staff_user,
                store=store,
                role=StoreStaff.Role.MANAGER,
                phone=staff_phone,
                is_active=True,
            )

        messages.success(request, "Store + staff account created successfully.")
        return redirect("adminpanel:store_staff_list")

    return render(request, "adminpanel/store/create_store.html")


@admin_required
def store_staff_list(request):
    staffs = StoreStaff.objects.select_related("store", "user").all().order_by("store__name")
    return render(request, "adminpanel/store/staff_list.html", {"staffs": staffs})


@admin_required
def create_delivery_agent(request):
    if request.method == "POST":
        store_id = request.POST.get("store")
        store = get_object_or_404(Store, pk=store_id)

        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        vehicle_type = request.POST.get("vehicle_type", DeliveryAgent.VehicleType.BIKE)
        vehicle_number = request.POST.get("vehicle_number", "").strip()
        agent_password = request.POST.get("password", "")

        if not (name and email and phone and agent_password):
            messages.error(request, "Please fill all required fields.")
            return redirect("adminpanel:create_delivery_agent")

        with transaction.atomic():
            if User.objects.filter(email__iexact=email).exists():
                messages.error(request, "An agent user with this email already exists.")
                return redirect("adminpanel:create_delivery_agent")

            agent_user = User.objects.create_user(
                username=email,
                email=email,
                password=agent_password,
                first_name=name,
            )

            DeliveryAgent.objects.create(
                user=agent_user,
                store=store,
                name=name,
                email=email,
                phone=phone,
                vehicle_type=vehicle_type,
                vehicle_number=vehicle_number,
                is_available=True,
                is_active=True,
                rating=Decimal("5.0"),
            )

        messages.success(request, "Delivery agent account created successfully.")
        return redirect("adminpanel:delivery_agent_list")

    stores = Store.objects.filter(is_active=True)
    return render(request, "adminpanel/agents/create_delivery_agent.html", {"stores": stores})


@admin_required
def delivery_agent_list(request):
    agents = DeliveryAgent.objects.select_related("store", "user").all().order_by("store__name", "name")
    return render(request, "adminpanel/agents/agent_list.html", {"agents": agents})

