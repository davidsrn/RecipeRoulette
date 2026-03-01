// app.js — RecipeRoulette client-side logic

// ── State ─────────────────────────────────────────────────────────────────────

const filters = { category: 'All', mood: 'All' };
let currentRecipe = null;
let editingId = null;

// ── Filter chips ──────────────────────────────────────────────────────────────

function toggleFilter(type, value, el) {
  filters[type] = value;

  // Update active chip styling within the same group
  const group = document.getElementById(type === 'category' ? 'category-chips' : 'mood-chips');
  group.querySelectorAll('.chip').forEach(c => c.classList.remove('chip-active'));
  el.classList.add('chip-active');

  // Hide the reveal card when filters change
  hideReveal();
}

// ── Spin ──────────────────────────────────────────────────────────────────────

async function spin() {
  const btn = document.getElementById('spin-btn');
  const icon = document.getElementById('spin-icon');
  const noResults = document.getElementById('no-results');

  // Animate
  btn.classList.add('spinning');
  icon.textContent = '⏳';
  btn.disabled = true;
  hideReveal();
  noResults.classList.add('hidden');

  // Build query
  const params = new URLSearchParams();
  if (filters.category && filters.category !== 'All') params.set('category', filters.category);
  if (filters.mood && filters.mood !== 'All') params.set('mood', filters.mood);

  try {
    const res = await fetch(`/api/spin?${params.toString()}`);

    if (res.status === 404) {
      noResults.classList.remove('hidden');
      return;
    }
    if (!res.ok) throw new Error(`Server error ${res.status}`);

    currentRecipe = await res.json();
    showReveal(currentRecipe);
  } catch (err) {
    showToast('Something went wrong. Try again.', 'error');
  } finally {
    setTimeout(() => {
      btn.classList.remove('spinning');
      icon.textContent = '🎲';
      btn.disabled = false;
    }, 600);
  }
}

function showReveal(recipe) {
  const card = document.getElementById('reveal-card');
  document.getElementById('reveal-category').textContent = recipe.category;
  document.getElementById('reveal-mood').textContent =
    recipe.mood === 'None' ? 'No mood set' : recipe.mood;

  card.classList.remove('hidden');
  card.classList.add('fade-up');

  // Scroll card into view smoothly
  setTimeout(() => card.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 50);
}

function hideReveal() {
  const card = document.getElementById('reveal-card');
  card.classList.add('hidden');
  card.classList.remove('fade-up');
  currentRecipe = null;
}

// ── Deep link ─────────────────────────────────────────────────────────────────

function openRecipe() {
  if (!currentRecipe) return;

  const { url, shortcode } = currentRecipe;

  // Try Instagram app deep link first; fall back to HTTPS after 500ms
  const deepLink = `instagram://media?id=${shortcode}`;
  window.location.href = deepLink;
  setTimeout(() => { window.open(url, '_blank', 'noopener'); }, 500);
}

// ── Manage page: list filter ──────────────────────────────────────────────────

function filterList(query) {
  const q = query.toLowerCase();
  document.querySelectorAll('#recipe-list li[id^="row-"]').forEach(row => {
    const text = [
      row.dataset.shortcode,
      row.dataset.category,
      row.dataset.mood,
    ].join(' ').toLowerCase();
    row.style.display = text.includes(q) ? '' : 'none';
  });
}

// ── Manage page: edit modal ───────────────────────────────────────────────────

function openEdit(id, category, mood) {
  editingId = id;

  // Find shortcode from the row
  const row = document.getElementById(`row-${id}`);
  document.getElementById('edit-shortcode').textContent = row?.dataset.shortcode ?? '';

  // Pre-select current values
  document.getElementById('edit-category').value = category;
  document.getElementById('edit-mood').value = mood;

  document.getElementById('edit-modal').classList.remove('hidden');
}

function closeEdit() {
  editingId = null;
  document.getElementById('edit-modal').classList.add('hidden');
}

async function saveEdit() {
  if (!editingId) return;

  const category = document.getElementById('edit-category').value;
  const mood = document.getElementById('edit-mood').value;

  try {
    const res = await fetch(`/api/recipe/${editingId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, mood }),
    });

    if (!res.ok) throw new Error(`Server error ${res.status}`);

    const updated = await res.json();

    // Update the row in-place without a page reload
    const row = document.getElementById(`row-${editingId}`);
    if (row) {
      row.dataset.category = updated.category;
      row.dataset.mood = updated.mood;

      const badges = row.querySelectorAll('span');
      if (badges[0]) badges[0].textContent = updated.category;
      if (badges[1]) badges[1].textContent = updated.mood;
    }

    closeEdit();
    showToast('Saved!', 'success');
  } catch (err) {
    showToast('Save failed. Try again.', 'error');
  }
}

// ── Toast ─────────────────────────────────────────────────────────────────────

let toastTimer = null;

function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  if (!toast) return;

  toast.textContent = message;
  toast.className = `fixed bottom-6 left-1/2 -translate-x-1/2 z-50 px-5 py-3 rounded-xl
    shadow-xl text-white text-sm font-semibold transition-all toast-${type}`;

  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.add('hidden'), 2500);
}

// ── Keyboard shortcuts ────────────────────────────────────────────────────────

document.addEventListener('keydown', e => {
  // Space / Enter → spin (on roulette page)
  if ((e.code === 'Space' || e.code === 'Enter') && document.getElementById('spin-btn')) {
    if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'BUTTON') {
      e.preventDefault();
      spin();
    }
  }
  // Escape → close edit modal
  if (e.code === 'Escape') closeEdit();
});
