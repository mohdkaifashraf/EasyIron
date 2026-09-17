from django.shortcuts import render


def role_login_gate(request):
    # next can be forwarded to the chosen login screen (customer/store/agent)
    next_url = request.GET.get("next") or ""
    return render(request, "home/role_login_gate.html", {"next": next_url})

