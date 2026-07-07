// ── Sidebar Toggle (mobile) ──────────────────────
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar = document.getElementById('sidebar');

if (sidebarToggle && sidebar) {
  sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
  });

  // Close sidebar when clicking outside on mobile
  document.addEventListener('click', (e) => {
    if (window.innerWidth <= 768 &&
        !sidebar.contains(e.target) &&
        !sidebarToggle.contains(e.target)) {
      sidebar.classList.remove('open');
    }
  });
}

// ── Auto-dismiss flash alerts after 5s ──────────
document.querySelectorAll('.alert.fade.show').forEach(alert => {
  setTimeout(() => {
    const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
    if (bsAlert) bsAlert.close();
  }, 5000);
});

// ── Confirm delete dialogs ───────────────────────
document.querySelectorAll('[data-confirm]').forEach(btn => {
  btn.addEventListener('click', (e) => {
    const msg = btn.getAttribute('data-confirm') || 'Are you sure?';
    if (!confirm(msg)) e.preventDefault();
  });
});

// ── Donor search typeahead for donation form ─────
const donorSearchInput = document.getElementById('donorSearch');
const donorIdField     = document.getElementById('donor_id');
const donorResults     = document.getElementById('donorResults');

if (donorSearchInput && donorIdField && donorResults) {
  let searchTimer;

  donorSearchInput.addEventListener('input', () => {
    clearTimeout(searchTimer);
    const val = donorSearchInput.value.trim();
    if (val.length < 2) { donorResults.innerHTML = ''; return; }

    searchTimer = setTimeout(async () => {
      try {
        const bg = document.getElementById('blood_group')?.value || '';
        const res = await fetch(`/donors/api/search?blood_group=${encodeURIComponent(bg)}`);
        const donors = await res.json();

        const filtered = donors.filter(d =>
          d.full_name.toLowerCase().includes(val.toLowerCase()) ||
          (d.phone && d.phone.includes(val))
        );

        donorResults.innerHTML = filtered.length
          ? filtered.map(d => `
              <div class="donor-result-item" data-id="${d.id}" data-name="${d.full_name}" data-bg="${d.blood_group}">
                <strong>${d.full_name}</strong>
                <span class="bg-badge ms-2">${d.blood_group}</span>
                <small class="text-muted ms-2">${d.phone || ''}</small>
              </div>`).join('')
          : '<div class="donor-result-item text-muted">No donors found</div>';

        donorResults.querySelectorAll('.donor-result-item[data-id]').forEach(item => {
          item.addEventListener('click', () => {
            donorIdField.value = item.dataset.id;
            donorSearchInput.value = item.dataset.name;
            // Auto-set blood group
            const bgSelect = document.getElementById('blood_group');
            if (bgSelect && item.dataset.bg) bgSelect.value = item.dataset.bg;
            donorResults.innerHTML = '';
          });
        });
      } catch (err) {
        console.error('Donor search error:', err);
      }
    }, 300);
  });

  document.addEventListener('click', (e) => {
    if (!donorSearchInput.contains(e.target) && !donorResults.contains(e.target)) {
      donorResults.innerHTML = '';
    }
  });
}

// ── Inventory progress bars animation ───────────
document.querySelectorAll('.inv-bar-fill[data-width]').forEach(bar => {
  setTimeout(() => {
    bar.style.width = bar.dataset.width + '%';
  }, 100);
});

// ── Animate stat counters ────────────────────────
function animateCounter(el) {
  const target = parseInt(el.dataset.target, 10);
  if (isNaN(target)) return;
  const duration = 1000;
  const start = performance.now();
  const update = (now) => {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(target * ease).toLocaleString();
    if (progress < 1) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}

document.querySelectorAll('.stat-value[data-target]').forEach(el => {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCounter(el);
        observer.unobserve(el);
      }
    });
  });
  observer.observe(el);
});
