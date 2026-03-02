# RecipeRoulette UI Beautify — Design Document

**Date:** 2026-03-02
**Status:** Approved
**Scope:** Complete UI overhaul — palette, typography, layout, all pages

---

## Goals

Transform the app from a functional orange-on-cream UI into a warm, artisanal, magazine-quality experience. Keep all functionality identical; change only visual presentation and layout structure.

---

## Design Decisions

| Dimension | Decision |
|---|---|
| Approach | Complete overhaul |
| Aesthetic | Warm & artisanal (NYT Cooking / Bon Appétit) |
| Palette | Cream & burgundy (replacing orange) |
| Layout | Reimagined — filter drawer, centered hero |

---

## Typography

| Usage | Font | Weight |
|---|---|---|
| Page headings, recipe title, section labels | Playfair Display | 700 (Bold) |
| Subheadings, card metadata | Playfair Display | 400 (Regular italic) |
| Body text, buttons, chips, metadata | Inter | 400 / 500 / 600 |
| Shortcodes | System monospace (unchanged) | 400 |

Add Playfair Display to the Google Fonts import in `base.html`:
```
family=Playfair+Display:ital,wght@0,700;1,400&family=Inter:wght@400;500;600;700;800
```

---

## Color Palette

Replace all orange references throughout templates and CSS.

| Token | Old Value | New Value | Usage |
|---|---|---|---|
| `primary` | `#F97316` | `#8B2635` | CTA buttons, active states |
| `primary-dark` | `#EA580C` | `#6E1D29` | Hover/press states |
| `accent` | `#FBBF24` | `#C9963E` | Mood badges, gold accents |
| `warm` | `#FFFBF5` | `#F5EFE6` | Page background (linen) |
| `warm-100` | `#FEF3E2` | `#EDE0D0` | Filter drawer background |
| `warm-200` | `#FDE8C8` | `#E5D9CC` | Borders, dividers |
| `surface` | (white) | `#FFFDF9` | Card/modal backgrounds |
| `text` | `#1C1917` (stone-900) | `#1C1209` | Body text (espresso) |
| `text-muted` | `#78716C` (stone-500) | `#7C6B5A` | Labels, placeholders |

---

## Main Page (`index.html`) — Layout Redesign

### Before
```
[Nav]
[Category chips — always visible]
[Mood chips — always visible]
[Big orange spin circle]
[Recipe card]
```

### After
```
[Nav — Playfair wordmark, muted nav links]
[Hero: "What's for dinner?" (Playfair Display)]
[  "Spin the wheel, discover your next recipe" (Inter muted)]
[⚙ Filters ▾ button — expands drawer below]
[  Filter drawer (animated slide): Category chips + Mood chips]
[Spin button — cream/burgundy circle, fork-knife SVG, "Spin" italic]
[Recipe card]
```

### Spin Button
- Shape: circular, ~176px diameter (slightly smaller than current 176px)
- Default state: cream (`#FFFDF9`) background, `2px` burgundy border
- Icon: fork-and-knife SVG (inline, ~32px), burgundy
- Label: "Spin" in Playfair Display italic, burgundy, below icon
- Hover state: burgundy fill, white icon and text
- Spinning state: gold ring pulses (replacing orange glow); button stays burgundy fill

### Filter Drawer
- Toggle button: small pill — `⚙ Filters ▾` — positioned below hero text, center-aligned
- Drawer: slides down with CSS `max-height` transition
- Chips: same rows as today (Category, Mood) but restyled
  - Default chip: `#FFFDF9` bg, `#E5D9CC` border, `#7C6B5A` text
  - Active chip: `#8B2635` bg, `#8B2635` border, `#FFFFFF` text
- Drawer auto-closes when spin is triggered

---

## Recipe Card Redesign

### Thumbnail Section
- Full-width image, `max-h-64` (slightly taller than current `max-h-56`)
- Deep gradient overlay: `linear-gradient(to bottom, transparent 30%, rgba(28,18,9,0.75) 100%)`
- **Recipe title** positioned over the gradient (absolute, bottom of image): Playfair Display, white, `text-xl font-bold leading-snug`
- Remove the separate gradient header bar (the orange `from-primary to-accent` strip is gone)
- Fallback (no thumbnail): warm linen background + fork-knife emoji, title shown below

### Card Body
- Background: `#FFFDF9` (warm white)
- Top row: category badge (burgundy pill) + mood badge (gold pill) + thin ornamental rule (`border-t border-warm-200`)
- **"Let's Cook!" button**: full-width, burgundy fill, white Inter semibold, `rounded-xl`
- **"Spin again"**: text-link style — muted brown, no border, hover underline. No button box.
- Analyze/Extract button: gold border, gold text (replacing amber)
- Ingredients/Instructions: same structure, Playfair Display `text-xs uppercase tracking-widest` for section labels

---

## Manage Page (`manage.html`) — Visual Reskin

- Page heading: "Recipe Collection" in Playfair Display h1
- Count badge: muted warm pill (no color change, just palette)
- Search bar: warm linen bg, burgundy focus ring
- Recipe rows: unchanged structure, palette swap only
  - Category badge: burgundy pill (`bg-primary/10 text-primary`)
  - Mood badge: gold/amber pill (`bg-accent/20 text-amber-700` → `text-[#7A5C1E]`)
  - Edit button: burgundy on hover
- Edit modal: same structure, palette swap, Playfair Display for "Edit Recipe" heading

---

## CSS Changes (`style.css`)

1. Update `.chip` / `.chip-active` to use burgundy instead of orange
2. Update `ring-throb` animation to use gold (`rgba(201,150,62,…)`) instead of orange
3. Update `.toast-success` / `.toast-error` — no change needed (semantic colors)
4. No new animation classes needed — all existing animations are kept, just colors adjusted via token changes

---

## Files to Touch

| File | Change type |
|---|---|
| `templates/base.html` | Font import, Tailwind color tokens |
| `templates/index.html` | Full restructure (hero, filter drawer, spin button, recipe card) |
| `templates/manage.html` | Palette reskin only |
| `static/style.css` | Chip colors, ring-throb animation color |
| `static/app.js` | Minor: filter drawer toggle function, close drawer on spin |

---

## Out of Scope

- Login page reskin (not requested)
- New animations (keep existing ones)
- Mobile/responsive breakpoints (existing structure is already mobile-first)
- Backend changes (zero)
