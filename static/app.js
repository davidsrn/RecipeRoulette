// app.js — RecipeRoulette client-side logic

// ── State ─────────────────────────────────────────────────────────────────────

const filters = { category: 'All', mood: 'All' };
let currentRecipe = null;
let editingId = null;

// ── Helpers ───────────────────────────────────────────────────────────────────

const sleep = ms => new Promise(r => setTimeout(r, ms));

// ── Filter chips ──────────────────────────────────────────────────────────────

function toggleFilter(type, value, el) {
  filters[type] = value;
  const group = document.getElementById(type === 'category' ? 'category-chips' : 'mood-chips');
  group.querySelectorAll('.chip').forEach(c => c.classList.remove('chip-active'));
  el.classList.add('chip-active');
  hideReveal();
}

// ── Slot machine ──────────────────────────────────────────────────────────────

const FOOD_EMOJIS = ['🍕','🍜','🥗','🌮','🍣','🥩','🍝','🫕','🥘','🍛','🍱','🥟','🧆','🥙','🍲','🫔'];

function showSlotMachine() {
  const card     = document.getElementById('reveal-card');
  const thumb    = document.getElementById('reveal-thumb');
  const fallback = document.getElementById('thumb-fallback');
  const titleEl  = document.getElementById('reveal-title');
  const catEl    = document.getElementById('reveal-category');
  const moodEl   = document.getElementById('reveal-mood');

  // Reveal card in "loading" state
  card.classList.remove('hidden', 'card-pop', 'fade-up');
  thumb.style.display = 'none';
  fallback.style.display = 'flex';
  titleEl.style.display = 'none';
  catEl.textContent  = '· · ·';
  moodEl.textContent = '· · ·';

  // Cycle emojis
  let idx = Math.floor(Math.random() * FOOD_EMOJIS.length);
  let alive = true;

  (function cycle() {
    if (!alive) return;
    fallback.textContent = FOOD_EMOJIS[idx++ % FOOD_EMOJIS.length];
    setTimeout(cycle, 105);
  })();

  return function stop() { alive = false; };
}

// ── Confetti ──────────────────────────────────────────────────────────────────

function spawnConfetti(anchor) {
  const rect   = anchor.getBoundingClientRect();
  const cx     = rect.left + rect.width  / 2;
  const cy     = rect.top  + rect.height * 0.3;
  const colors = ['#F97316','#FBBF24','#FB923C','#FCD34D','#FDE68A','#EC4899','#34D399','#60A5FA'];

  for (let i = 0; i < 18; i++) {
    const dot   = document.createElement('div');
    dot.className = 'confetti-dot';
    const angle = (i / 18) * 360 + (Math.random() * 20 - 10);
    const dist  = 50 + Math.random() * 100;
    const tx    = (Math.cos(angle * Math.PI / 180) * dist).toFixed(1) + 'px';
    const ty    = (Math.sin(angle * Math.PI / 180) * dist - 50).toFixed(1) + 'px';
    const rot   = (Math.random() * 720 - 360).toFixed(0) + 'deg';
    // Alternate between circles and squares
    const radius = i % 3 === 0 ? '2px' : '50%';

    dot.style.cssText = [
      `left:${(cx - 4.5).toFixed(0)}px`,
      `top:${(cy - 4.5).toFixed(0)}px`,
      `background:${colors[i % colors.length]}`,
      `border-radius:${radius}`,
      `--tx:${tx}`,
      `--ty:${ty}`,
      `--rot:${rot}`,
      `animation-delay:${(Math.random() * 80).toFixed(0)}ms`,
    ].join(';');

    document.body.appendChild(dot);
    setTimeout(() => dot.remove(), 1000);
  }
}

// ── Spin ──────────────────────────────────────────────────────────────────────

async function spin() {
  const btn       = document.getElementById('spin-btn');
  const noResults = document.getElementById('no-results');

  btn.classList.add('is-spinning');
  btn.disabled = true;
  noResults.classList.add('hidden');

  const stopSlot   = showSlotMachine();
  const minWait    = sleep(900); // always spin at least 900 ms for drama

  const params = new URLSearchParams();
  if (filters.category !== 'All') params.set('category', filters.category);
  if (filters.mood     !== 'All') params.set('mood',     filters.mood);

  try {
    const [res] = await Promise.all([
      fetch(`/api/spin?${params.toString()}`),
      minWait,
    ]);

    stopSlot();

    if (res.status === 404) {
      hideReveal();
      noResults.classList.remove('hidden');
      return;
    }
    if (!res.ok) throw new Error(`Server error ${res.status}`);

    currentRecipe = await res.json();
    await sleep(60); // tiny beat so the slot machine has a moment to stop
    showReveal(currentRecipe);

  } catch (err) {
    stopSlot();
    hideReveal();
    showToast('Something went wrong. Try again.', 'error');
  } finally {
    btn.classList.remove('is-spinning');
    btn.disabled = false;
  }
}

function showReveal(recipe) {
  const card     = document.getElementById('reveal-card');
  const titleEl  = document.getElementById('reveal-title');
  const catEl    = document.getElementById('reveal-category');
  const moodEl   = document.getElementById('reveal-mood');
  const thumb    = document.getElementById('reveal-thumb');
  const fallback = document.getElementById('thumb-fallback');

  // Title
  titleEl.textContent   = recipe.title || '';
  titleEl.style.display = recipe.title ? '' : 'none';

  // Badges
  catEl.textContent  = recipe.category;
  moodEl.textContent = recipe.mood === 'None' ? 'No mood set' : recipe.mood;

  // Thumbnail
  if (recipe.has_thumbnail) {
    fallback.style.display = 'none';
    thumb.classList.remove('thumb-reveal');
    // Set src in rAF to re-trigger blur-reveal animation.
    // Do NOT blank thumb.src first — setting src='' fires onerror which hides the element.
    requestAnimationFrame(() => {
      thumb.style.display = '';
      thumb.src = `/api/thumbnail/${recipe.id}`;
      thumb.classList.add('thumb-reveal');
    });
  } else {
    thumb.style.display   = 'none';
    fallback.style.display = 'flex';
    fallback.textContent  = '🍽️';
  }

  // Recipe details + analyze button
  showRecipeDetails(recipe);
  const analyzeBtn = document.getElementById('analyze-btn');
  const hasExtracted = recipe.ingredients || recipe.instructions;
  if (recipe.description && !hasExtracted) {
    analyzeBtn.classList.remove('hidden');
    document.getElementById('analyze-icon').textContent = '✨';
    document.getElementById('analyze-label').textContent = 'Extract recipe';
    analyzeBtn.disabled = false;
  } else {
    analyzeBtn.classList.add('hidden');
  }

  // Spring-pop the card (force reflow to re-trigger animation even if card was visible)
  card.classList.remove('hidden', 'card-pop', 'fade-up');
  void card.offsetWidth;
  card.classList.add('card-pop');

  // Confetti burst
  requestAnimationFrame(() => spawnConfetti(card));

  // Scroll into view
  setTimeout(() => card.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 100);
}

function hideReveal() {
  const card = document.getElementById('reveal-card');
  card.classList.add('hidden');
  card.classList.remove('card-pop', 'fade-up');
  currentRecipe = null;
  document.getElementById('recipe-details').classList.add('hidden');
  document.getElementById('analyze-btn').classList.add('hidden');
}

// ── Deep link ─────────────────────────────────────────────────────────────────

function openRecipe() {
  if (!currentRecipe) return;
  const { url, shortcode } = currentRecipe;
  const deepLink = `instagram://media?id=${shortcode}`;
  window.location.href = deepLink;
  setTimeout(() => { window.open(url, '_blank', 'noopener'); }, 500);
}

// ── Manage page: list filter ──────────────────────────────────────────────────

function filterList(query) {
  const q = query.toLowerCase();
  document.querySelectorAll('#recipe-list li[id^="row-"]').forEach(row => {
    const text = [
      row.dataset.title,
      row.dataset.shortcode,
      row.dataset.category,
      row.dataset.mood,
    ].join(' ').toLowerCase();
    row.style.display = text.includes(q) ? '' : 'none';
  });
}

// ── Manage page: edit modal ───────────────────────────────────────────────────

function openEdit(id, category, mood, title) {
  editingId = id;
  const row = document.getElementById(`row-${id}`);
  document.getElementById('edit-shortcode').textContent = row?.dataset.shortcode ?? '';
  document.getElementById('edit-title').value           = title || '';
  document.getElementById('edit-category').value        = category;
  document.getElementById('edit-mood').value            = mood;
  document.getElementById('edit-modal').classList.remove('hidden');
}

function closeEdit() {
  editingId = null;
  document.getElementById('edit-modal').classList.add('hidden');
}

async function saveEdit() {
  if (!editingId) return;

  const title    = document.getElementById('edit-title').value.trim();
  const category = document.getElementById('edit-category').value;
  const mood     = document.getElementById('edit-mood').value;

  try {
    const res = await fetch(`/api/recipe/${editingId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, category, mood }),
    });

    if (!res.ok) throw new Error(`Server error ${res.status}`);

    const updated = await res.json();

    const row = document.getElementById(`row-${editingId}`);
    if (row) {
      row.dataset.title    = updated.title || '';
      row.dataset.category = updated.category;
      row.dataset.mood     = updated.mood;

      const titleEl = row.querySelector('[data-role="title"]');
      if (titleEl) {
        titleEl.textContent   = updated.title || '';
        titleEl.style.display = updated.title ? '' : 'none';
      }

      const badges = row.querySelectorAll('span[class*="rounded-full"]');
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

// ── Recipe details ────────────────────────────────────────────────────────────

function escHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function showRecipeDetails(recipe) {
  const detailsEl    = document.getElementById('recipe-details');
  const ingrSection  = document.getElementById('ingr-section');
  const instrSection = document.getElementById('instr-section');
  const ingrList     = document.getElementById('ingr-list');
  const instrList    = document.getElementById('instr-list');

  if (recipe.ingredients) {
    const lines = recipe.ingredients.split('\n').map(l => l.trim()).filter(Boolean);
    ingrList.innerHTML = lines
      .map(l => `<li class="flex gap-2 items-start"><span class="text-primary mt-0.5 shrink-0">•</span><span>${escHtml(l)}</span></li>`)
      .join('');
    ingrSection.classList.remove('hidden');
  } else {
    ingrSection.classList.add('hidden');
  }

  if (recipe.instructions) {
    const lines = recipe.instructions.split('\n').map(l => l.trim()).filter(Boolean);
    instrList.innerHTML = lines
      .map((l, i) => {
        const text = l.replace(/^\d+[\.\)]\s*/, '');
        return `<li class="flex gap-2 items-start"><span class="text-primary font-bold min-w-[1.25rem] shrink-0">${i + 1}.</span><span>${escHtml(text)}</span></li>`;
      })
      .join('');
    instrSection.classList.remove('hidden');
  } else {
    instrSection.classList.add('hidden');
  }

  if (recipe.ingredients || recipe.instructions) {
    detailsEl.classList.remove('hidden');
    detailsEl.classList.remove('details-fade');
    void detailsEl.offsetWidth;
    detailsEl.classList.add('details-fade');
  } else {
    detailsEl.classList.add('hidden');
  }
}

async function analyzeRecipe() {
  if (!currentRecipe) return;
  const btn   = document.getElementById('analyze-btn');
  const icon  = document.getElementById('analyze-icon');
  const label = document.getElementById('analyze-label');

  btn.disabled      = true;
  icon.textContent  = '⏳';
  label.textContent = 'Extracting…';

  try {
    const res = await fetch(`/api/recipe/${currentRecipe.id}/analyze`, { method: 'POST' });
    if (!res.ok) throw new Error(`${res.status}`);
    const updated = await res.json();
    currentRecipe = updated;
    showRecipeDetails(updated);
    btn.classList.add('hidden');
    // Refresh mood badge if it changed
    const moodEl = document.getElementById('reveal-mood');
    if (moodEl) moodEl.textContent = updated.mood === 'None' ? 'No mood set' : updated.mood;
    showToast('Recipe extracted! ✨', 'success');
  } catch (err) {
    icon.textContent  = '✨';
    label.textContent = 'Extract recipe';
    btn.disabled      = false;
    showToast('Extraction failed. Try again.', 'error');
  }
}

// ── Keyboard shortcuts ────────────────────────────────────────────────────────

document.addEventListener('keydown', e => {
  if ((e.code === 'Space' || e.code === 'Enter') && document.getElementById('spin-btn')) {
    if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'BUTTON') {
      e.preventDefault();
      spin();
    }
  }
  if (e.code === 'Escape') closeEdit();
});
