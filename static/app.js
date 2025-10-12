(() => {
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const THEME_KEY = 'parking-theme';
  const root = document.documentElement;
  const themeToggle = document.getElementById('themeToggle');

  const setTheme = (theme) => {
    root.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
    if (themeToggle) {
      const icon = theme === 'dark' ? 'bi-sun' : 'bi-moon-stars';
      themeToggle.innerHTML = `<i class="bi ${icon}"></i>`;
    }
  };

  const savedTheme = localStorage.getItem(THEME_KEY);
  setTheme(savedTheme || (prefersDark ? 'dark' : 'light'));

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const current = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      setTheme(current);
    });
  }

  const header = document.querySelector('.navbar');
  const toggleHeader = () => {
    if (!header) return;
    if (window.scrollY > 24) header.classList.add('is-scrolled');
    else header.classList.remove('is-scrolled');
  };
  toggleHeader();
  window.addEventListener('scroll', toggleHeader, { passive: true });

  const currentPath = window.location.pathname;
  document.querySelectorAll('.navbar .nav-link').forEach((link) => {
    const href = link.getAttribute('href');
    if (!href) return;
    if (href === '/' && currentPath === '/') {
      link.classList.add('active');
    } else if (href !== '/' && currentPath.startsWith(href)) {
      link.classList.add('active');
    }
  });

  window.ParkingApp = window.ParkingApp || {};
  window.ParkingApp.showToast = (message, icon = 'bi-check-circle') => {
    let toast = document.querySelector('.toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.className = 'toast';
      toast.setAttribute('role', 'status');
      document.body.appendChild(toast);
    }
    toast.innerHTML = `<i class="bi ${icon}"></i><span>${message}</span>`;
    requestAnimationFrame(() => toast.classList.add('is-visible'));
    setTimeout(() => toast.classList.remove('is-visible'), 2800);
  };
})();

window.addEventListener('DOMContentLoaded', () => {
  const grid = document.querySelector('[data-slot-grid]');
  if (!grid) return;

  const bookingForm = document.getElementById('bookingForm');
  const hiddenSelect = document.getElementById('id_slot');
  const summarySlot = document.querySelector('[data-summary-slot]');
  const summaryTime = document.querySelector('[data-summary-time]');
  const summaryVehicle = document.querySelector('[data-summary-vehicle]');
  const summaryAmount = document.querySelector('[data-summary-amount]');
  const summaryBase = document.querySelector('[data-summary-base]');
  const amountInput = document.querySelector('[data-amount-input]');
  const paymentMethodInput = document.getElementById('paymentMethodInput');
  const paymentOptions = document.querySelectorAll('.payment-option');
  const locationFilter = document.getElementById('locationFilter');
  const vehicleFilter = document.getElementById('vehicleFilter');
  const vehicleChips = vehicleFilter ? vehicleFilter.querySelectorAll('.chip') : [];
  const slotTiles = Array.from(grid.querySelectorAll('.slot-tile'));

  const PLACEHOLDER = '—';
  const CURRENCY = '\u20B9';

  const defaultRate = bookingForm ? parseFloat(bookingForm.dataset.defaultRate || '0') || 0 : 0;
  let activeRate = defaultRate;
  let selectedVehicle = vehicleFilter ? (vehicleFilter.dataset.selectedVehicle || 'all') : 'all';

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.2 });

  slotTiles.forEach((tile) => {
    tile.dataset.lazy = 'true';
    observer.observe(tile);
  });

  const startField = bookingForm ? bookingForm.querySelector('[name="start_time"]') : null;
  const endField = bookingForm ? bookingForm.querySelector('[name="end_time"]') : null;

  const updateBaseDisplay = (rate) => {
    if (summaryBase) summaryBase.textContent = Math.round(rate).toString();
  };

  const recalcAmount = () => {
    if (!bookingForm) return;
    const start = startField ? startField.value : '';
    const end = endField ? endField.value : '';
    const hasSelection = hiddenSelect && hiddenSelect.value;
    const rate = activeRate || defaultRate;

    updateBaseDisplay(rate);

    if (!start || !end) {
      if (summaryTime) summaryTime.textContent = PLACEHOLDER;
      if (!hasSelection && summaryAmount) summaryAmount.textContent = PLACEHOLDER;
      if (amountInput) amountInput.value = '';
      return;
    }

    if (summaryTime) summaryTime.textContent = `${start} - ${end}`;

    if (!hasSelection) {
      if (summaryAmount) summaryAmount.textContent = PLACEHOLDER;
      if (amountInput) amountInput.value = '';
      return;
    }

    const [sh, sm] = start.split(':').map(Number);
    const [eh, em] = end.split(':').map(Number);
    const startMinutes = sh * 60 + sm;
    const endMinutes = eh * 60 + em;
    if (endMinutes <= startMinutes) {
      if (summaryAmount) summaryAmount.textContent = PLACEHOLDER;
      if (amountInput) amountInput.value = '';
      return;
    }

    const hours = Math.max((endMinutes - startMinutes) / 60, 1);
    const amount = Math.max(hours * rate, rate);
    if (summaryAmount) summaryAmount.textContent = `${CURRENCY} ${amount.toFixed(2)}`;
    if (amountInput) amountInput.value = amount.toFixed(2);
  };

  const highlightTile = (tile) => {
    slotTiles.forEach((item) => {
      const isActive = tile && item === tile;
      item.classList.toggle('is-selected', isActive);
      item.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    });

    if (tile) {
      const rate = parseFloat(tile.dataset.rate || bookingForm.dataset.defaultRate || '0') || defaultRate;
      activeRate = rate;
      if (hiddenSelect) hiddenSelect.value = tile.dataset.slotId;
      if (summarySlot) summarySlot.textContent = tile.dataset.slotLabel;
      if (summaryVehicle) {
        const vehicleLabel = tile.dataset.vehicleLabel || 'Selected slot';
        summaryVehicle.textContent = `${vehicleLabel} \u00B7 ${CURRENCY} ${rate.toFixed(0)}/hr`;
      }
      updateBaseDisplay(rate);
    } else {
      activeRate = defaultRate;
      if (hiddenSelect) hiddenSelect.value = '';
      if (summarySlot) summarySlot.textContent = PLACEHOLDER;
      if (summaryVehicle) summaryVehicle.textContent = 'Select any available slot';
      if (summaryAmount) summaryAmount.textContent = PLACEHOLDER;
      if (summaryTime) summaryTime.textContent = PLACEHOLDER;
      if (amountInput) amountInput.value = '';
      updateBaseDisplay(defaultRate);
    }

    recalcAmount();
  };

  const activateTile = (tile) => {
    if (!tile || tile.dataset.status === 'booked') return;
    const alreadySelected = tile.classList.contains('is-selected');
    highlightTile(tile);
    if (!alreadySelected) {
      window.ParkingApp.showToast(`Slot ${tile.dataset.slotLabel || tile.dataset.slotId} selected`, 'bi-geo-alt');
    }
  };

  grid.addEventListener('click', (event) => {
    const tile = event.target.closest('.slot-tile');
    if (!tile) return;
    activateTile(tile);
  });

  grid.addEventListener('keydown', (event) => {
    if (!['Enter', ' '].includes(event.key)) return;
    const tile = event.target.closest('.slot-tile');
    if (!tile) return;
    event.preventDefault();
    activateTile(tile);
  });

  const applyFilters = () => {
    const locationValue = locationFilter ? locationFilter.value : 'all';
    let currentSelectionVisible = false;

    slotTiles.forEach((tile) => {
      const matchesLocation = locationValue === 'all' || tile.dataset.location === locationValue;
      const matchesVehicle = selectedVehicle === 'all' || tile.dataset.vehicle === selectedVehicle;
      const shouldShow = matchesLocation && matchesVehicle;
      tile.style.display = shouldShow ? '' : 'none';
      if (shouldShow && hiddenSelect && hiddenSelect.value === tile.dataset.slotId) {
        currentSelectionVisible = true;
      }
    });

    if (!currentSelectionVisible && hiddenSelect && hiddenSelect.value) {
      highlightTile(null);
    }
  };

  const setActiveChip = (value) => {
    selectedVehicle = value || 'all';
    vehicleChips.forEach((chip) => {
      const isActive = chip.dataset.vehicle === selectedVehicle;
      chip.classList.toggle('is-active', isActive);
      chip.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    });
    applyFilters();
    recalcAmount();
  };

  if (vehicleChips.length) {
    setActiveChip(selectedVehicle);
    vehicleChips.forEach((chip) => {
      const value = chip.dataset.vehicle || 'all';
      chip.addEventListener('click', () => setActiveChip(value));
      chip.addEventListener('keydown', (event) => {
        if (!['Enter', ' '].includes(event.key)) return;
        event.preventDefault();
        setActiveChip(value);
      });
    });
  }

  if (locationFilter) {
    locationFilter.addEventListener('change', () => {
      applyFilters();
      recalcAmount();
    });
  }

  paymentOptions.forEach((option) => {
    const selectOption = () => {
      paymentOptions.forEach((opt) => {
        opt.classList.remove('is-selected');
        opt.setAttribute('aria-pressed', 'false');
      });
      option.classList.add('is-selected');
      option.setAttribute('aria-pressed', 'true');
      if (paymentMethodInput) paymentMethodInput.value = option.dataset.method;
    };

    option.addEventListener('click', selectOption);
    option.addEventListener('keydown', (event) => {
      if (!['Enter', ' '].includes(event.key)) return;
      event.preventDefault();
      selectOption();
    });
  });

  if (bookingForm) {
    bookingForm.addEventListener('change', recalcAmount);
    bookingForm.addEventListener('input', recalcAmount);
    bookingForm.addEventListener('submit', (event) => {
      const slotSelected = hiddenSelect && hiddenSelect.value;
      if (!slotSelected) {
        event.preventDefault();
        window.ParkingApp.showToast('Please select a slot before continuing', 'bi-info-circle');
      }
    });
  }

  const preselectedTile = hiddenSelect && hiddenSelect.value
    ? slotTiles.find((tile) => tile.dataset.slotId === hiddenSelect.value)
    : null;
  if (preselectedTile) {
    highlightTile(preselectedTile);
  } else {
    highlightTile(null);
  }

  applyFilters();
});
