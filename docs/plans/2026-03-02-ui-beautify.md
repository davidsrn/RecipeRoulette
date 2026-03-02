# UI Beautify Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the orange-on-cream UI with a warm artisanal cream & burgundy aesthetic, add Playfair Display typography, collapse filters into a drawer, and redesign the spin button and recipe card to feel like a premium food magazine.

**Architecture:** Pure frontend changes — Tailwind config tokens in `base.html`, CSS animation colors in `style.css`, template restructuring in `index.html` and `manage.html`, and a small JS addition in `app.js` for the filter drawer toggle. Zero backend changes.

**Tech Stack:** Jinja2 templates, Tailwind CSS (CDN config), vanilla JS, Google Fonts (Playfair Display + Inter)

---

### Task 1: Update Color Tokens and Font in base.html

**Files:**
- Modify: `templates/base.html`

**Context:** `base.html` defines the Tailwind theme extension and Google Fonts import. All color tokens are defined here and used throughout all templates. Changing them here cascades everywhere.

**Step 1: Read the file**

Open `templates/base.html` and locate:
- The `tailwind.config` `<script>` block (lines ~12-29)
- The Google Fonts `<link>` tag (line ~34)

**Step 2: Replace the Google Fonts link**

Old:
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
```

New:
```html
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,400&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
```

**Step 3: Replace the Tailwind config colors block**

Old `colors` block inside `tailwind.config`:
```js
colors: {
  primary:   '#F97316',
  'primary-dark': '#EA580C',
  accent:    '#FBBF24',
  warm:      '#FFFBF5',
  'warm-100':'#FEF3E2',
  'warm-200':'#FDE8C8',
},
```

New:
```js
colors: {
  primary:        '#8B2635',
  'primary-dark': '#6E1D29',
  accent:         '#C9963E',
  warm:           '#F5EFE6',
  'warm-100':     '#EDE0D0',
  'warm-200':     '#E5D9CC',
  surface:        '#FFFDF9',
  espresso:       '#1C1209',
  'text-muted':   '#7C6B5A',
},
```

**Step 4: Add Playfair Display to fontFamily**

Inside the `tailwind.config` `fontFamily` block, add:
```js
fontFamily: {
  sans:  ['Inter', 'system-ui', 'sans-serif'],
  serif: ['"Playfair Display"', 'Georgia', 'serif'],
},
```

**Step 5: Update body background color**

In `<body class="...">`, change `bg-warm` — this already maps to the new `#F5EFE6` via the token, so no change needed here.

**Step 6: Verify visually**

Start/reload the dev server and take a screenshot. The page background should shift from `#FFFBF5` (creamy white) to `#F5EFE6` (warmer linen). The nav "RecipeRoulette" text is orange — it should now turn burgundy `#8B2635`. Active filter chips should now be burgundy.

Expected screenshot: burgundy logo text, burgundy "All" chip, linen background.

**Step 7: Commit**

```bash
git add templates/base.html
git commit -m "style: update Tailwind tokens to cream/burgundy palette, add Playfair Display font"
```

---

### Task 2: Update style.css — Chips and Spin Animation Colors

**Files:**
- Modify: `static/style.css`

**Context:** `style.css` hardcodes orange hex values for chip states and the `ring-throb` box-shadow animation. These need to be swapped to the new burgundy/gold palette.

**Step 1: Read the file**

Open `static/style.css`. Locate:
- `.chip`, `.chip:hover`, `.chip-active`, `.chip-active:hover` (lines ~14-40)
- `@keyframes ring-throb` (lines ~56-60)

**Step 2: Replace chip styles**

Old:
```css
.chip {
  padding: 0.375rem 0.875rem;
  border-radius: 9999px;
  border: 2px solid #E7E5E4;
  background: #fff;
  color: #78716C;
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
  user-select: none;
}
.chip:hover {
  border-color: #F97316;
  color: #F97316;
}
.chip-active {
  background: #F97316;
  border-color: #F97316;
  color: #fff;
}
.chip-active:hover {
  background: #EA580C;
  border-color: #EA580C;
  color: #fff;
}
```

New:
```css
.chip {
  padding: 0.375rem 0.875rem;
  border-radius: 9999px;
  border: 1.5px solid #E5D9CC;
  background: #FFFDF9;
  color: #7C6B5A;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
  user-select: none;
}
.chip:hover {
  border-color: #8B2635;
  color: #8B2635;
}
.chip-active {
  background: #8B2635;
  border-color: #8B2635;
  color: #fff;
}
.chip-active:hover {
  background: #6E1D29;
  border-color: #6E1D29;
  color: #fff;
}
```

**Step 3: Replace ring-throb animation colors**

Old:
```css
@keyframes ring-throb {
  0%   { box-shadow: 0 0 0 0   rgba(249,115,22,0.55), 0 20px 40px rgba(249,115,22,0.25); }
  50%  { box-shadow: 0 0 0 18px rgba(249,115,22,0),   0 20px 40px rgba(249,115,22,0.25); }
  100% { box-shadow: 0 0 0 0   rgba(249,115,22,0.55), 0 20px 40px rgba(249,115,22,0.25); }
}
```

New (gold ring instead of orange):
```css
@keyframes ring-throb {
  0%   { box-shadow: 0 0 0 0    rgba(201,150,62,0.6),  0 20px 40px rgba(139,38,53,0.2); }
  50%  { box-shadow: 0 0 0 18px rgba(201,150,62,0),    0 20px 40px rgba(139,38,53,0.2); }
  100% { box-shadow: 0 0 0 0    rgba(201,150,62,0.6),  0 20px 40px rgba(139,38,53,0.2); }
}
```

**Step 4: Add filter drawer animation**

Append at the bottom of the file:
```css
/* ── Filter drawer ─────────────────────────────────────────────────────────── */

#filter-drawer {
  overflow: hidden;
  max-height: 0;
  transition: max-height 0.3s ease, opacity 0.2s ease;
  opacity: 0;
}
#filter-drawer.drawer-open {
  max-height: 200px;
  opacity: 1;
}

/* ── Spin button — artisanal style ─────────────────────────────────────────── */

#spin-btn {
  background: #FFFDF9;
  border: 2px solid #8B2635;
  color: #8B2635;
  transition: background 0.2s ease, color 0.2s ease, transform 0.1s ease;
}
#spin-btn:hover {
  background: #8B2635;
  color: #FFFDF9;
}
#spin-btn:hover .spin-btn-icon path,
#spin-btn:hover .spin-btn-icon line,
#spin-btn:hover .spin-btn-icon circle {
  stroke: #FFFDF9;
}
```

**Step 5: Verify**

Reload the preview. Filter chips should now use the burgundy palette. The spin button styles will take full effect after Task 3.

**Step 6: Commit**

```bash
git add static/style.css
git commit -m "style: update chip colors and spin animation to burgundy/gold palette, add filter drawer CSS"
```

---

### Task 3: Restructure index.html — Hero, Filter Drawer, Spin Button

**Files:**
- Modify: `templates/index.html`

**Context:** This is the biggest structural change. We're adding a hero heading, converting the always-visible filter chips into a collapsible drawer triggered by a "Filters" button, and replacing the large orange circle with a refined cream/burgundy circular button with a fork-knife SVG icon. The recipe card section is untouched in this task (handled in Task 4).

**Step 1: Replace the entire `{% block content %}` section up to (but not including) the `<!-- Recipe reveal card -->` comment**

Replace from line 1 of `{% block content %}` through the end of the `<!-- Spin button -->` div:

```html
{% block content %}

<!-- Hero heading -->
<div class="text-center mb-6 mt-2">
  <h1 class="font-serif text-3xl font-bold text-espresso leading-tight">What's for dinner?</h1>
  <p class="text-text-muted text-sm mt-1">Spin the wheel, discover your next recipe</p>
</div>

<!-- Filter toggle button -->
<div class="flex justify-center mb-2">
  <button
    id="filter-toggle"
    onclick="toggleFilterDrawer()"
    class="flex items-center gap-1.5 px-4 py-2 rounded-full border border-warm-200
           bg-surface text-text-muted text-sm font-medium hover:border-primary
           hover:text-primary transition-colors"
  >
    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2"
         viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round"
            d="M3 4h18M7 8h10M11 12h2M9 16h6"/>
    </svg>
    <span id="filter-toggle-label">Filters</span>
    <svg id="filter-chevron" class="w-3 h-3 transition-transform" fill="none"
         stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"/>
    </svg>
  </button>
</div>

<!-- Filter section (collapsible drawer) -->
<div id="filter-drawer" class="mb-4 px-1">
  <div class="pt-3 pb-1">
    <h2 class="text-xs font-semibold uppercase tracking-widest text-text-muted mb-2">Category</h2>
    <div class="flex gap-2 overflow-x-auto pb-1 scrollbar-hide" id="category-chips">
      <button
        class="chip chip-active flex-shrink-0"
        data-type="category" data-value="All"
        onclick="toggleFilter('category','All',this)"
      >All</button>
      {% for cat in categories %}
      {% if cat != "Uncategorized" %}
      <button
        class="chip flex-shrink-0"
        data-type="category" data-value="{{ cat }}"
        onclick="toggleFilter('category','{{ cat }}',this)"
      >{{ cat }}</button>
      {% endif %}
      {% endfor %}
      <button
        class="chip flex-shrink-0"
        data-type="category" data-value="Uncategorized"
        onclick="toggleFilter('category','Uncategorized',this)"
      >Uncategorized</button>
    </div>

    <h2 class="text-xs font-semibold uppercase tracking-widest text-text-muted mt-4 mb-2">Mood</h2>
    <div class="flex gap-2 overflow-x-auto pb-1 scrollbar-hide" id="mood-chips">
      <button
        class="chip chip-active flex-shrink-0"
        data-type="mood" data-value="All"
        onclick="toggleFilter('mood','All',this)"
      >All</button>
      {% for mood in moods %}
      {% if mood != "None" %}
      <button
        class="chip flex-shrink-0"
        data-type="mood" data-value="{{ mood }}"
        onclick="toggleFilter('mood','{{ mood }}',this)"
      >{{ mood }}</button>
      {% endif %}
      {% endfor %}
      <button
        class="chip flex-shrink-0"
        data-type="mood" data-value="None"
        onclick="toggleFilter('mood','None',this)"
      >No mood</button>
    </div>
  </div>
</div>

<!-- Spin button -->
<div class="flex justify-center my-8">
  <button
    id="spin-btn"
    onclick="spin()"
    class="relative w-40 h-40 rounded-full select-none
           flex flex-col items-center justify-center gap-2 active:scale-95"
    style="box-shadow: 0 4px 24px rgba(139,38,53,0.18), 0 1px 4px rgba(0,0,0,0.08);"
  >
    <!-- Fork and knife SVG icon -->
    <svg class="spin-btn-icon w-8 h-8" fill="none" stroke="#8B2635" stroke-width="1.75"
         stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
      <path d="M3 2v7c0 1.1.9 2 2 2h1v11h2V11h1a2 2 0 0 0 2-2V2H3z"/>
      <path d="M18 2v20M15 6c0-2.2 1.3-4 3-4s3 1.8 3 4-1.3 4-3 4-3-1.8-3-4z"/>
    </svg>
    <span id="spin-icon" class="hidden">🎲</span>
    <span class="text-base font-serif italic tracking-wide" id="spin-label">Spin</span>
  </button>
</div>
```

**Step 2: Verify the page renders correctly**

Reload the preview. You should see:
- "What's for dinner?" serif heading centered
- "Filters" button below it
- Cream/burgundy circular spin button with fork-knife icon and italic "Spin" label
- No filter chips visible by default
- Clicking "Filters" button does nothing yet (JS added in Task 5)

Take a screenshot to confirm layout.

**Step 3: Commit**

```bash
git add templates/index.html
git commit -m "feat: add hero heading, filter drawer structure, and redesigned spin button"
```

---

### Task 4: Redesign the Recipe Card in index.html

**Files:**
- Modify: `templates/index.html`

**Context:** The recipe card currently has an orange gradient header bar below the thumbnail that shows the title and badges. We're moving the title onto the thumbnail itself via a gradient overlay, removing the orange header bar, and cleaning up the card body.

**Step 1: Replace the `<!-- Recipe reveal card -->` section**

Replace from `<!-- Recipe reveal card (hidden until spin) -->` to the closing `</div>` of `reveal-card`:

```html
<!-- No results message (hidden by default) -->
<div id="no-results" class="hidden text-center text-text-muted text-sm py-4">
  No recipes match those filters. Try a different combo!
</div>

<!-- Recipe reveal card (hidden until spin) -->
<div id="reveal-card" class="hidden">
  <div class="bg-surface rounded-2xl shadow-lg border border-warm-200 overflow-hidden">

    <!-- Thumbnail with title overlay -->
    <div class="relative">
      <img id="reveal-thumb"
        src="" alt="Recipe preview"
        class="w-full object-cover"
        style="max-height: 260px;"
        onerror="this.style.display='none'; document.getElementById('thumb-fallback').style.display='flex';" />

      <!-- Gradient overlay with title -->
      <div class="absolute inset-0 bg-gradient-to-t from-espresso/75 via-transparent to-transparent
                  flex flex-col justify-end px-5 py-4" id="thumb-overlay">
        <p class="text-white/70 text-xs font-medium uppercase tracking-widest mb-1">Tonight's pick</p>
        <p id="reveal-title"
           class="text-white font-serif font-bold text-xl leading-snug drop-shadow-sm"></p>
      </div>

      <!-- Fallback (no thumbnail) -->
      <div id="thumb-fallback"
        class="hidden h-36 bg-warm-100 items-center justify-center flex-col gap-2">
        <span class="text-5xl">🍽️</span>
        <p id="reveal-title-fallback"
           class="font-serif font-bold text-espresso text-lg px-4 text-center leading-snug"></p>
      </div>
    </div>

    <!-- Card body -->
    <div class="px-5 py-4 flex flex-col gap-3">

      <!-- Badges row -->
      <div class="flex gap-2 flex-wrap items-center">
        <span id="reveal-category"
          class="px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-semibold">
        </span>
        <span id="reveal-mood"
          class="px-3 py-1 rounded-full bg-accent/15 text-[#7A5C1E] text-xs font-semibold">
        </span>
      </div>

      <!-- Thin rule -->
      <div class="border-t border-warm-200"></div>

      <!-- CTA -->
      <button
        id="cook-btn"
        onclick="openRecipe()"
        class="w-full py-4 rounded-xl bg-primary hover:bg-primary-dark text-white font-semibold
               text-base transition-colors shadow-sm active:scale-95 flex items-center justify-center gap-2"
      >
        <span>Let's Cook!</span>
        <span>👨‍🍳</span>
      </button>

      <!-- Spin again — text link style -->
      <button
        onclick="spin()"
        class="w-full py-2 text-text-muted hover:text-primary text-sm font-medium
               transition-colors hover:underline underline-offset-2"
      >
        Spin again
      </button>

      <!-- Extract recipe button -->
      <button
        id="analyze-btn"
        onclick="analyzeRecipe()"
        class="hidden w-full py-3 rounded-xl border border-accent/50 hover:border-accent
               text-[#7A5C1E] hover:text-accent font-medium text-sm transition-all
               flex items-center justify-center gap-2"
      >
        <span id="analyze-icon">✨</span>
        <span id="analyze-label">Extract recipe</span>
      </button>

      <!-- Ingredients + Instructions -->
      <div id="recipe-details" class="hidden border-t border-warm-200 pt-3 flex flex-col gap-4">
        <div id="ingr-section" class="hidden">
          <p class="text-xs font-semibold uppercase tracking-widest text-text-muted mb-2">Ingredients</p>
          <ul id="ingr-list" class="text-sm text-espresso space-y-1 pl-0 list-none"></ul>
        </div>
        <div id="instr-section" class="hidden">
          <p class="text-xs font-semibold uppercase tracking-widest text-text-muted mb-2">Instructions</p>
          <ol id="instr-list" class="text-sm text-espresso space-y-2 pl-0 list-none"></ol>
        </div>
      </div>

    </div>
  </div>
</div>
```

**Important:** The `no-results` div was previously above the spin button in the old template — make sure it doesn't appear twice. Remove any duplicate from the file after pasting.

**Step 2: Update app.js to also set the fallback title**

In `static/app.js`, find the `showReveal(recipe)` function. After the line that sets `reveal-title` text content, add:
```js
const titleFallback = document.getElementById('reveal-title-fallback');
if (titleFallback) titleFallback.textContent = recipe.title || recipe.shortcode || '';
```

Also find where `reveal-thumb`'s `src` is set. The current code sets it to the thumbnail URL. The overlay div `thumb-overlay` should be hidden when the fallback is shown — add:
```js
const overlay = document.getElementById('thumb-overlay');
const thumb = document.getElementById('reveal-thumb');
// show overlay only when thumb is visible
thumb.onload = () => { if (overlay) overlay.style.display = 'flex'; };
thumb.onerror already hides thumb — overlay hides too because it's inside the same relative container
```

Actually, the overlay is a sibling of the img inside `relative`, so it will be visible even when the img fails. Fix: in the img's `onerror`, also hide the overlay:

Find the img tag and update its `onerror` attribute:
```html
onerror="this.style.display='none'; document.getElementById('thumb-fallback').style.display='flex'; var ov=document.getElementById('thumb-overlay'); if(ov) ov.style.display='none';"
```

**Step 3: Verify**

Reload, click "Filters" to open drawer (JS not yet wired — just visually check the card structure exists). Temporarily use browser devtools or preview_eval to show the card and confirm it renders correctly.

```js
// Quick visual test via preview_eval
document.getElementById('reveal-card').classList.remove('hidden');
document.getElementById('reveal-title').textContent = 'Creamy Garlic Pasta';
document.getElementById('reveal-category').textContent = 'Pasta';
document.getElementById('reveal-mood').textContent = 'Quick';
document.getElementById('reveal-thumb').style.display = 'none';
document.getElementById('thumb-fallback').style.display = 'flex';
document.getElementById('reveal-title-fallback').textContent = 'Creamy Garlic Pasta';
```

Take a screenshot and confirm the card looks right.

**Step 4: Commit**

```bash
git add templates/index.html static/app.js
git commit -m "feat: redesign recipe card with thumbnail title overlay and artisanal card body"
```

---

### Task 5: Wire Filter Drawer in app.js

**Files:**
- Modify: `static/app.js`

**Context:** The filter drawer HTML exists from Task 3 but has no JS. We need a `toggleFilterDrawer()` function and need to close the drawer when a spin starts.

**Step 1: Add `toggleFilterDrawer` function**

Near the top of `static/app.js`, after the global state variables (`filters`, `currentRecipe`, `editingId`), add:

```js
// Filter drawer toggle
function toggleFilterDrawer() {
  const drawer = document.getElementById('filter-drawer');
  const chevron = document.getElementById('filter-chevron');
  const label = document.getElementById('filter-toggle-label');
  if (!drawer) return;
  const isOpen = drawer.classList.contains('drawer-open');
  drawer.classList.toggle('drawer-open', !isOpen);
  if (chevron) chevron.style.transform = isOpen ? '' : 'rotate(180deg)';
  if (label) label.textContent = isOpen ? 'Filters' : 'Filters';
}
```

**Step 2: Close the drawer when spin starts**

Find the `spin()` function in `app.js`. At the very start of the function body (before the `fetch` call), add:

```js
// Close filter drawer if open
const drawer = document.getElementById('filter-drawer');
if (drawer) drawer.classList.remove('drawer-open');
const chevron = document.getElementById('filter-chevron');
if (chevron) chevron.style.transform = '';
```

**Step 3: Verify**

Reload the preview.
- Click "Filters" button → chips should slide down smoothly
- Click "Filters" again → chips collapse
- Chevron rotates on open/close
- Clicking Spin while drawer is open → drawer closes

**Step 4: Commit**

```bash
git add static/app.js
git commit -m "feat: wire filter drawer toggle and auto-close on spin"
```

---

### Task 6: Reskin manage.html

**Files:**
- Modify: `templates/manage.html`

**Context:** The manage page needs the palette swap and the page heading upgraded to Playfair Display. No layout changes.

**Step 1: Update the page heading**

Old:
```html
<h1 class="text-xl font-bold text-stone-800">All Recipes
  <span class="ml-2 text-sm font-normal text-stone-400">({{ recipes|length }})</span>
</h1>
```

New:
```html
<h1 class="font-serif text-2xl font-bold text-espresso">Recipe Collection
  <span class="ml-2 text-sm font-normal text-text-muted font-sans">({{ recipes|length }})</span>
</h1>
```

**Step 2: Update search bar focus ring**

Old: `focus:ring-primary` is already using the Tailwind token — no change needed, the token update in Task 1 already makes it burgundy. ✓

**Step 3: Update category badge color**

Old:
```html
<span class="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs font-semibold">
```
No change needed — `primary` token already updated. ✓

**Step 4: Update mood badge color**

Old:
```html
<span class="px-2 py-0.5 rounded-full bg-accent/20 text-amber-700 text-xs font-semibold">
```

New (replace `text-amber-700` with a warmer brown that matches the new accent):
```html
<span class="px-2 py-0.5 rounded-full bg-accent/20 text-[#7A5C1E] text-xs font-semibold">
```

**Step 5: Update edit modal heading**

Old:
```html
<h2 class="text-lg font-bold text-stone-800 mb-1">Edit Recipe</h2>
```

New:
```html
<h2 class="font-serif text-xl font-bold text-espresso mb-1">Edit Recipe</h2>
```

**Step 6: Update modal background**

Old: `bg-white` on modal card
New: `bg-surface`

Find: `<div class="relative w-full max-w-sm bg-white rounded-2xl shadow-2xl p-6 z-10">`
Replace `bg-white` with `bg-surface`.

**Step 7: Update input/select backgrounds in modal**

The `bg-warm` class on inputs/selects already maps to the new linen color — no change needed. ✓

**Step 8: Verify**

Navigate to `/manage` in the preview. Confirm:
- "Recipe Collection" heading in Playfair Display
- No orange anywhere (all badges, buttons, focus rings should be burgundy/gold)

**Step 9: Commit**

```bash
git add templates/manage.html
git commit -m "style: reskin manage page to cream/burgundy palette with serif heading"
```

---

### Task 7: Final Visual QA

**Files:** None to modify (fix any issues found)

**Step 1: Desktop screenshot — main page**

Take a screenshot of `/` (spin page). Confirm:
- Linen background
- Playfair Display "What's for dinner?" heading
- "Filters" toggle button
- Cream/burgundy circular spin button with fork-knife icon and italic "Spin" label
- No orange anywhere

**Step 2: Open filter drawer**

Click "Filters" and take screenshot. Confirm chips slide down with burgundy active state.

**Step 3: Trigger a spin (use preview_eval if no DB data)**

```js
// If DB is empty, mock the reveal
document.getElementById('reveal-card').classList.remove('hidden');
document.getElementById('reveal-card').classList.add('card-pop');
document.getElementById('reveal-thumb').style.display = 'none';
document.getElementById('thumb-overlay').style.display = 'none';
document.getElementById('thumb-fallback').style.display = 'flex';
document.getElementById('reveal-title-fallback').textContent = 'Creamy Garlic Pasta';
document.getElementById('reveal-category').textContent = 'Pasta';
document.getElementById('reveal-mood').textContent = 'Quick';
```

Take screenshot. Confirm card looks like a premium food card.

**Step 4: Mobile view**

Resize preview to 375px wide. Take screenshot. Confirm no overflow, readable type, spin button fits.

**Step 5: Manage page screenshot**

Navigate to `/manage`. Take screenshot. Confirm serif heading and no orange.

**Step 6: Fix anything broken, then final commit**

```bash
git add -A
git commit -m "style: final QA fixes for cream/burgundy UI overhaul"
```
