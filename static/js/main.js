/* ═══════════════════════════════════════════
   SkyRoute Flight Management System — Main JS
═══════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  // ── Navbar scroll effect ──────────────────
  const navbar = document.getElementById('mainNavbar');
  if (navbar) {
    const handleScroll = () => {
      if (window.scrollY > 60) {
        navbar.classList.add('scrolled');
      } else {
        navbar.classList.remove('scrolled');
      }
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
  }

  // ── Auto-dismiss toasts ───────────────────
  document.querySelectorAll('.toast').forEach(toastEl => {
    const bsToast = new bootstrap.Toast(toastEl, { autohide: true, delay: 4500 });
    bsToast.show();
  });

  // ── Animate elements on scroll ───────────
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('in-view');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.animate-on-scroll').forEach(el => observer.observe(el));

  // ── Swap Origin / Destination ─────────────
  const swapBtn = document.getElementById('swapBtn');
  if (swapBtn) {
    swapBtn.addEventListener('click', () => {
      const originSelect = document.getElementById('id_origin');
      const destSelect   = document.getElementById('id_destination');
      if (originSelect && destSelect) {
        const tmp = originSelect.value;
        originSelect.value = destSelect.value;
        destSelect.value   = tmp;
        // Visual feedback
        swapBtn.style.transform = 'rotate(180deg)';
        setTimeout(() => swapBtn.style.transform = '', 400);
      }
    });
  }

  // ── Set default departure date to today ───
  const dateInput = document.getElementById('id_departure_date');
  if (dateInput && !dateInput.value) {
    const today = new Date().toISOString().split('T')[0];
    dateInput.value = today;
    dateInput.min   = today;
  }

  // ── Flight search form loading state ──────
  const searchForm = document.getElementById('searchForm');
  const searchBtn  = document.getElementById('searchBtn');
  if (searchForm && searchBtn) {
    searchForm.addEventListener('submit', (e) => {
      const origin = document.getElementById('id_origin').value;
      const dest   = document.getElementById('id_destination').value;
      const date   = document.getElementById('id_departure_date').value;
      if (!origin || !dest || !date) return; // let form validation handle

      searchBtn.innerHTML = `
        <span class="spinner-border spinner-border-sm me-2"></span>Searching...
      `;
      searchBtn.disabled = true;
    });
  }

  // ── Results search re-submit loading ──────
  const resultsForm = document.getElementById('resultsSearchForm');
  if (resultsForm) {
    resultsForm.addEventListener('submit', () => {
      const btn = resultsForm.querySelector('[type="submit"]');
      if (btn) {
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
        btn.disabled = true;
      }
    });
  }

  // ── Booking page: live price update ───────
  updateBookingPrice();
  function updateBookingPrice() {
    // If on booking page, update total dynamically when seat class changes
    const seatRadios = document.querySelectorAll('[name="seat_class"]');
    seatRadios.forEach(radio => {
      radio.addEventListener('change', () => {
        // Price update handled server-side on submit; this is for UX feedback
        highlightSelectedClass(radio.value);
      });
    });
  }

  function highlightSelectedClass(cls) {
    document.querySelectorAll('.seat-class-option').forEach(el => {
      el.classList.toggle('active', el.dataset.class === cls);
    });
  }

  // ── Smooth counter animation (for KPI cards) ──
  function animateCounter(el) {
    const target = parseFloat(el.getAttribute('data-target'));
    const isPrice = el.getAttribute('data-prefix') === '₹';
    const duration = 1200;
    const startTime = performance.now();

    const tick = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.floor(eased * target);

      el.textContent = (isPrice ? '₹' : '') + current.toLocaleString('en-IN');

      if (progress < 1) requestAnimationFrame(tick);
      else el.textContent = (isPrice ? '₹' : '') + target.toLocaleString('en-IN');
    };
    requestAnimationFrame(tick);
  }

  // Observe KPI values
  const kpiObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        kpiObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  document.querySelectorAll('[data-counter]').forEach(el => kpiObserver.observe(el));

  // ── Tooltip init ──────────────────────────
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
    new bootstrap.Tooltip(el);
  });

  // ── Form input focus ring (custom) ────────
  document.querySelectorAll('.form-control, .form-select').forEach(input => {
    input.addEventListener('focus', () => input.closest('.mb-4, .col-md-6, .col-12, .col-lg-3')?.classList.add('field-focused'));
    input.addEventListener('blur',  () => input.closest('.mb-4, .col-md-6, .col-12, .col-lg-3')?.classList.remove('field-focused'));
  });

  // ── Print button ─────────────────────────
  document.querySelectorAll('[data-action="print"]').forEach(btn => {
    btn.addEventListener('click', () => window.print());
  });

  // ── Dashboard: animate KPI numbers ───────
  document.querySelectorAll('.kpi-value').forEach(el => {
    const rawText = el.textContent.trim();
    const isRupee = rawText.startsWith('₹');
    const numStr  = rawText.replace(/[₹,]/g, '').trim();
    const target  = parseFloat(numStr);
    if (!isNaN(target) && target > 0) {
      el.setAttribute('data-target', target);
      el.setAttribute('data-prefix', isRupee ? '₹' : '');
      el.setAttribute('data-counter', '');
      kpiObserver.observe(el);
    }
  });

  // ── Flight detail toggle (redundant safety) ──
  window.toggleDetails = window.toggleDetails || function(flightId, btn) {
    const details = document.getElementById('details-' + flightId);
    if (!details) return;
    const isOpen = details.classList.toggle('open');
    btn.innerHTML = isOpen
      ? '<i class="bi bi-chevron-up me-1"></i> Hide Details'
      : '<i class="bi bi-chevron-down me-1"></i> Flight Details';
  };

  // ── Booking history: add `now` for template comparison ──
  // (This isn't needed in JS; view passes `now` to template context)

  // ── Dark mode is default (data-bs-theme="dark") ──
  // No toggle needed; always dark.

  console.log('%c✈ SkyRoute FMS Loaded', 'color: #4361ee; font-size: 16px; font-weight: bold;');
});
