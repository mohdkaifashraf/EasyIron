document.addEventListener("DOMContentLoaded", () => {
  const sidebar = document.getElementById("agentSidebar");
  document.querySelector(".agent-menu")?.addEventListener("click", () => sidebar.classList.toggle("open"));
  document.addEventListener("click", event => {
    if (window.innerWidth <= 850 && sidebar?.classList.contains("open") &&
        !sidebar.contains(event.target) && !event.target.closest(".agent-menu")) {
      sidebar.classList.remove("open");
    }
  });
});
