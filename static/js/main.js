/**
 * Main JavaScript - SalesManager Pro
 */

document.addEventListener("DOMContentLoaded", function () {

  // ── Sidebar toggle ─────────────────────────────────────────────────────────
  const sidebarToggle = document.getElementById("sidebarToggle");
  const sidebar = document.getElementById("sidebar");
  const mainContent = document.getElementById("mainContent");

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", () => {
      if (window.innerWidth <= 768) {
        sidebar.classList.toggle("show");
      } else {
        const collapsed = sidebar.style.width === "0px";
        if (collapsed) {
          sidebar.style.width = "var(--sidebar-width)";
          mainContent.style.marginLeft = "var(--sidebar-width)";
        } else {
          sidebar.style.width = "0px";
          mainContent.style.marginLeft = "0";
        }
      }
    });
  }

  // ── Animated counter ──────────────────────────────────────────────────────
  const counters = document.querySelectorAll(".counter");
  const formatter = new Intl.NumberFormat("vi-VN");

  const observerOptions = { threshold: 0.2 };
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const target = parseInt(el.getAttribute("data-target")) || 0;
        animateCount(el, target, formatter);
        observer.unobserve(el);
      }
    });
  }, observerOptions);

  counters.forEach(c => observer.observe(c));

  function animateCount(el, target, fmt) {
    let current = 0;
    const duration = 1500;
    const steps = 60;
    const increment = target / steps;
    const interval = duration / steps;

    const timer = setInterval(() => {
      current = Math.min(current + increment, target);
      el.textContent = fmt.format(Math.floor(current));
      if (current >= target) {
        el.textContent = fmt.format(target);
        clearInterval(timer);
      }
    }, interval);
  }

  // ── Auto dismiss alerts ────────────────────────────────────────────────────
  setTimeout(() => {
    document.querySelectorAll(".alert.alert-dismissible").forEach(alert => {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    });
  }, 4000);

  // ── Active nav highlight ───────────────────────────────────────────────────
  const currentPath = window.location.pathname;
  document.querySelectorAll(".nav-item").forEach(item => {
    if (item.getAttribute("href") === currentPath) {
      item.classList.add("active");
    }
  });

  // ── Tooltips ───────────────────────────────────────────────────────────────
  const tooltipEls = document.querySelectorAll("[data-bs-toggle='tooltip']");
  tooltipEls.forEach(el => new bootstrap.Tooltip(el));

});
