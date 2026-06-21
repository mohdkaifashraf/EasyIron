document.addEventListener("DOMContentLoaded", () => {
  let savedCart = [];
  try {
    savedCart = JSON.parse(localStorage.getItem("easyironCart") || "[]");
  } catch {
    localStorage.removeItem("easyironCart");
  }

  const cart = new Map(savedCart.map(item => [item.name, item]));
  const cartCount = document.getElementById("cartCount");
  const cartItems = document.getElementById("cartItems");
  const cartTotal = document.getElementById("cartTotal");

  window.addEventListener("scroll", () => {
    document.querySelector(".navbar")?.classList.toggle("scrolled", window.scrollY > 20);
  });

  document.querySelectorAll(".quantity").forEach((selector) => {
    const value = selector.querySelector("span");
    selector.querySelector(".qty-plus").addEventListener("click", () => {
      value.textContent = Number(value.textContent) + 1;
    });
    selector.querySelector(".qty-minus").addEventListener("click", () => {
      value.textContent = Math.max(1, Number(value.textContent) - 1);
    });
  });

  document.querySelectorAll(".add-cart").forEach((button) => {
    button.addEventListener("click", () => {
      const card = button.closest(".item-card");
      const name = card.dataset.name;
      const price = Number(card.dataset.price);
      const quantity = Number(card.querySelector(".quantity span").textContent);
      const current = cart.get(name) || { name, price, quantity: 0 };
      current.quantity += quantity;
      cart.set(name, current);
      renderCart();
      button.innerHTML = '<i class="bi bi-check-lg"></i> Added';
      setTimeout(() => {
        button.innerHTML = '<i class="bi bi-plus-lg"></i> Add';
      }, 1000);
    });
  });

  function renderCart() {
    const items = [...cart.values()];
    const count = items.reduce((sum, item) => sum + item.quantity, 0);
    const total = items.reduce((sum, item) => sum + item.quantity * item.price, 0);

    localStorage.setItem("easyironCart", JSON.stringify(items));
    cartCount.textContent = count;
    cartTotal.textContent = `₹${total}`;

    if (!items.length) {
      cartItems.innerHTML = '<div class="empty-cart text-center py-5"><i class="bi bi-basket3"></i><p class="mt-3">Your laundry bag is empty.</p></div>';
      return;
    }

    cartItems.innerHTML = items.map(item => `
      <div class="cart-row">
        <div class="cart-row-icon"><i class="bi bi-bag-check"></i></div>
        <div><h6>${item.name}</h6><small>${item.quantity} × ₹${item.price}</small></div>
        <strong>₹${item.quantity * item.price}</strong>
        <button data-remove="${item.name}" aria-label="Remove item"><i class="bi bi-x-lg"></i></button>
      </div>`).join("");

    cartItems.querySelectorAll("[data-remove]").forEach((button) => {
      button.addEventListener("click", () => {
        cart.delete(button.dataset.remove);
        renderCart();
      });
    });
  }

  renderCart();
});
