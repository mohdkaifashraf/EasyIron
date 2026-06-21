document.addEventListener("DOMContentLoaded", () => {
  const sidebar = document.getElementById("storeSidebar");
  document.querySelector(".sidebar-toggle")?.addEventListener("click", () => {
    sidebar.classList.toggle("open");
  });

  document.addEventListener("click", (event) => {
    if (window.innerWidth <= 850 && sidebar?.classList.contains("open") &&
        !sidebar.contains(event.target) && !event.target.closest(".sidebar-toggle")) {
      sidebar.classList.remove("open");
    }
  });

  const rejectModal = document.getElementById("rejectModal");
  rejectModal?.addEventListener("show.bs.modal", (event) => {
    const button = event.relatedTarget;
    document.getElementById("rejectOrderNumber").textContent = button.dataset.number;
    document.getElementById("rejectForm").action = `/store/orders/${button.dataset.order}/reject/`;
  });

  const deleteModal = document.getElementById("deleteServiceModal");
  deleteModal?.addEventListener("show.bs.modal", (event) => {
    const button = event.relatedTarget;
    document.getElementById("deleteServiceName").textContent = button.dataset.name;
    document.getElementById("deleteServiceForm").action = button.dataset.url;
  });
});
