from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from store_app.models import DeliveryAgent, Order, OrderItem, Service, Store, StoreStaff
from agent_app.models import AgentNotification, DeliveryAssignment, PickupAssignment


class Command(BaseCommand):
    help = "Create development data for the EasyIron store dashboard."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="storemanager")
        parser.add_argument("--password", default="EasyIron@123")

    def handle(self, *args, **options):
        store, _ = Store.objects.get_or_create(
            code="EI-DEL-01",
            defaults={
                "name": "EasyIron Central Store",
                "phone": "+91 98765 43210",
                "email": "central@easyiron.in",
                "address": "Sector 18, Noida, Uttar Pradesh",
            },
        )
        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=options["username"],
            defaults={"first_name": "Aarav", "last_name": "Manager", "is_staff": True},
        )
        if created:
            user.set_password(options["password"])
            user.save()
        StoreStaff.objects.update_or_create(
            user=user,
            defaults={"store": store, "role": StoreStaff.Role.MANAGER, "phone": "+91 90000 10001"},
        )

        service_specs = [
            ("Shirt Ironing", "10.00", "Crisp steam ironing for shirts."),
            ("Pant Ironing", "15.00", "Professional crease and finish."),
            ("Kurti Ironing", "18.00", "Gentle ironing for kurtis."),
            ("Laundry", "45.00", "Fabric-safe wash and fold."),
            ("Dry Cleaning", "199.00", "Specialist care for formal and delicate garments."),
        ]
        services = {}
        for name, price, description in service_specs:
            service, _ = Service.objects.update_or_create(
                store=store,
                name=name,
                defaults={"price": Decimal(price), "description": description, "is_active": True},
            )
            services[name] = service

        agents = {}
        for name, phone, email, vehicle in [
            ("Ravi Kumar", "+91 90000 20001", "ravi@easyiron.in", "DL 01 EI 2048"),
            ("Imran Khan", "+91 90000 20002", "imran@easyiron.in", "DL 01 EI 3052"),
        ]:
            username = email.split("@")[0] + "_agent"
            agent_user, agent_user_created = user_model.objects.get_or_create(
                username=username,
                defaults={"first_name": name.split()[0], "last_name": name.split()[-1], "email": email},
            )
            if agent_user_created:
                agent_user.set_password("Agent@123")
                agent_user.save()
            agent, _ = DeliveryAgent.objects.update_or_create(
                store=store,
                phone=phone,
                defaults={
                    "user": agent_user,
                    "name": name,
                    "email": email,
                    "vehicle_type": DeliveryAgent.VehicleType.BIKE,
                    "vehicle_number": vehicle,
                    "is_available": True,
                    "is_active": True,
                },
            )
            agents[name] = agent

        now = timezone.now()
        order_specs = [
            ("EI1001", "Neha Sharma", "+91 98111 22334", "Ironing", Order.Status.RECEIVED, [("Shirt Ironing", 5), ("Pant Ironing", 3), ("Kurti Ironing", 2)]),
            ("EI1002", "Rohan Kapoor", "+91 98222 33445", "Laundry", Order.Status.PROCESSING, [("Laundry", 6), ("Shirt Ironing", 2)]),
            ("EI1003", "Meera Joshi", "+91 98333 44556", "Dry Cleaning", Order.Status.READY, [("Dry Cleaning", 2), ("Pant Ironing", 2)]),
            ("EI1004", "Kabir Mehta", "+91 98444 55667", "Ironing", Order.Status.DELIVERED, [("Shirt Ironing", 4), ("Pant Ironing", 4)]),
        ]
        for index, (number, customer, phone, service_type, status, items) in enumerate(order_specs):
            order, order_created = Order.objects.get_or_create(
                order_number=number,
                defaults={
                    "store": store,
                    "customer_name": customer,
                    "customer_phone": phone,
                    "pickup_address": f"{42 + index}, Green Park, New Delhi",
                    "service_type": service_type,
                    "pickup_date": now + timedelta(hours=index + 1),
                    "delivery_date": now + timedelta(days=2) if status == Order.Status.DELIVERED else None,
                    "status": status,
                    "accepted_at": now if status != Order.Status.RECEIVED else None,
                },
            )
            if order_created:
                for service_name, quantity in items:
                    service = services[service_name]
                    OrderItem.objects.create(
                        order=order,
                        service=service,
                        item_name=service_name,
                        quantity=quantity,
                        price=service.price,
                    )
                order.add_tracking(Order.Status.RECEIVED, "Order placed by customer.", user)
                if status != Order.Status.RECEIVED:
                    order.add_tracking(status, f"Order moved to {order.get_status_display()}.", user)

        pickup_order = Order.objects.get(order_number="EI1001")
        pickup, pickup_created = PickupAssignment.objects.get_or_create(
            order=pickup_order,
            defaults={
                "agent": agents["Ravi Kumar"],
                "pickup_time": pickup_order.pickup_date,
            },
        )
        pickup_order.delivery_agent = agents["Ravi Kumar"]
        pickup_order.save(update_fields=("delivery_agent",))
        if pickup_created:
            AgentNotification.objects.create(
                agent=agents["Ravi Kumar"],
                order=pickup_order,
                title="New pickup assigned",
                message=f"Pickup {pickup_order.order_number} from {pickup_order.customer_name}.",
                notification_type="assignment",
            )

        delivery_order = Order.objects.get(order_number="EI1003")
        delivery, delivery_created = DeliveryAssignment.objects.get_or_create(
            order=delivery_order,
            defaults={
                "agent": agents["Ravi Kumar"],
                "delivery_time": now + timedelta(hours=3),
            },
        )
        delivery_order.delivery_agent = agents["Ravi Kumar"]
        delivery_order.save(update_fields=("delivery_agent",))
        if delivery_created:
            AgentNotification.objects.create(
                agent=agents["Ravi Kumar"],
                order=delivery_order,
                title="Store ready for delivery",
                message=f"{delivery_order.order_number} is ready to collect from {store.name}.",
                notification_type="assignment",
            )

        self.stdout.write(self.style.SUCCESS("EasyIron store demo data is ready."))
        if created:
            self.stdout.write(f"Login: {options['username']} / {options['password']}")
        else:
            self.stdout.write(f"Existing login retained for: {options['username']}")
        self.stdout.write("Agent login: ravi@easyiron.in / Agent@123")
