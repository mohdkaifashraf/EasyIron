document.addEventListener("DOMContentLoaded", () => {
  window.addEventListener("scroll", () => {
    document.querySelector(".navbar")?.classList.toggle("scrolled", window.scrollY > 20);
  });

  const navCollapse = document.getElementById("mainNav");
  const navInstance = navCollapse ? bootstrap.Collapse.getOrCreateInstance(navCollapse, { toggle: false }) : null;
  const navLinks = Array.from(navCollapse?.querySelectorAll(".nav-link") || []).filter((link) => {
    const href = link.getAttribute("href") || "";
    return href.includes("#");
  });

  navCollapse?.querySelectorAll(".nav-link, .nav-actions a").forEach((link) => {
    link.addEventListener("click", () => {
      if (window.innerWidth < 992 && navCollapse.classList.contains("show")) {
        navInstance?.hide();
      }
    });
  });

  const setActiveNavLink = () => {
    const scrollPos = window.scrollY + 120;
    let activeId = "home";

    navLinks.forEach((link) => {
      const href = link.getAttribute("href") || "";
      const targetId = href.split("#").pop();
      const section = targetId ? document.getElementById(targetId) : null;
      if (section && scrollPos >= section.offsetTop && scrollPos < section.offsetTop + section.offsetHeight) {
        activeId = targetId;
      }
    });

    navLinks.forEach((link) => {
      const href = link.getAttribute("href") || "";
      const targetId = href.split("#").pop();
      link.classList.toggle("active", targetId === activeId);
    });
  };

  navLinks.forEach((link) => {
    link.addEventListener("click", () => {
      navLinks.forEach((item) => item.classList.remove("active"));
      link.classList.add("active");
    });
  });

  setActiveNavLink();
  window.addEventListener("scroll", () => {
    window.requestAnimationFrame(setActiveNavLink);
  }, { passive: true });

  document.querySelectorAll(".quantity").forEach((selector) => {
    const value = selector.querySelector("span");
    const hidden = selector.closest("form")?.querySelector('input[name="quantity"]');

    selector.querySelector(".qty-plus").addEventListener("click", () => {
      const nextValue = Number(value.textContent) + 1;
      value.textContent = nextValue;
      if (hidden) hidden.value = nextValue;
    });
    selector.querySelector(".qty-minus").addEventListener("click", () => {
      const nextValue = Math.max(1, Number(value.textContent) - 1);
      value.textContent = nextValue;
      if (hidden) hidden.value = nextValue;
    });
  });

  document.querySelectorAll(".remove-cart-item").forEach((button) => {
    button.addEventListener("click", async () => {
      const itemId = button.dataset.itemId;
      if (!itemId) return;

      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || document.cookie
        .split('; ')
        .find((row) => row.startsWith('csrftoken='))
        ?.split('=')[1];

      const response = await fetch("/cart/remove/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken || "",
          "Accept": "application/json",
        },
        body: JSON.stringify({ item_id: Number(itemId) }),
      });

      const result = await response.json();
      if (!response.ok || !result.success) {
        alert(result.message || "Unable to remove item from cart.");
        return;
      }

      const cartRow = button.closest(".cart-row");
      cartRow?.remove();

      const cartCountEl = document.getElementById("cartCount");
      if (cartCountEl) {
        cartCountEl.textContent = result.cart_count;
      }

      const cartTotalEl = document.getElementById("cartTotal");
      if (cartTotalEl) {
        const subtotal = Number(result.subtotal || 0);
        cartTotalEl.textContent = `₹${subtotal.toFixed(2)}`;
      }

      if (!document.querySelector(".cart-row")) {
        const emptyState = `
          <div class="empty-cart text-center py-5">
            <i class="bi bi-basket3"></i><p class="mt-3">Your laundry bag is empty.</p>
          </div>
        `;
        const cartItems = document.getElementById("cartItems");
        if (cartItems) cartItems.innerHTML = emptyState;
      }
    });
  });
    document.querySelectorAll("[data-cart-form]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();

      const formData = new FormData(form);
      const button = form.querySelector(".add-cart");

      if (button) {
        button.disabled = true;
        button.textContent = "Added";
      }

      try {
        const response = await fetch(form.action, {
          method: "POST",
          body: formData,
          headers: {
            "X-Requested-With": "XMLHttpRequest"
          }
        });

        const data = await response.json();

        if (data.success) {
          const cartCount = document.getElementById("cartCount");
          if (cartCount) {
            cartCount.textContent = data.cart_count;
          }

          if (button) {
            button.textContent = "Added ✓";
          }

          setTimeout(() => {
            window.location.reload();
          }, 250);
        } else {
          if (button) {
            button.disabled = false;
            button.textContent = "Add";
          }
        }
      } catch (error) {
        console.error("Add to cart failed:", error);
        if (button) {
          button.disabled = false;
          button.textContent = "Add";
        }
      }
    });
  });

  const trackingCard = document.getElementById("orderTracking");
  if (trackingCard?.dataset.orderId) {
    const statusLabels = {
      placed: "Order placed",
      pickup_assigned: "Pickup assigned",
      picked_up: "Picked up",
      processing: "Processing",
      ironing_completed: "Ready for delivery",
      out_for_delivery: "Out for delivery",
      delivered: "Delivered",
    };
    const progressByStatus = {
      placed: 0,
      pickup_assigned: 16,
      picked_up: 33,
      processing: 50,
      ironing_completed: 67,
      out_for_delivery: 84,
      delivered: 100,
    };

    const updateTracking = async () => {
      try {
        const response = await fetch(trackingCard.dataset.statusUrl, {
          headers: { "Accept": "application/json" },
          credentials: "same-origin",
        });
        if (!response.ok) return;
        const data = await response.json();
        if (!data.order) return;

        const status = data.order.status;
        const progress = progressByStatus[status] ?? 0;
        trackingCard.dataset.orderId = data.order.id;
        trackingCard.querySelector("[data-tracking-order]").textContent = data.order.id;
        trackingCard.querySelector("[data-tracking-status]").textContent = statusLabels[status] || data.order.status_label;
        trackingCard.querySelector("[data-tracking-progress]").style.width = `${progress}%`;
        trackingCard.classList.toggle("is-delivering", status === "out_for_delivery");
        trackingCard.querySelectorAll("[data-step]").forEach((step) => {
          step.classList.toggle("is-current", step.dataset.step === status);
        });
      } catch (error) {
        console.debug("Order tracking update unavailable", error);
      }
    };

    updateTracking();
    window.setInterval(updateTracking, 10000);
  }

});
