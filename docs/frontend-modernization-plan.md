# Frontend Modernization Plan (Django + Tailwind + HTMX/Alpine)

## Goal
- Keep Django server-side rendering.
- Modernize UI/UX without a risky full React migration.
- Replace legacy CSS incrementally.

## Recommended Stack
- Styling: Tailwind CSS
- Interaction: HTMX (server-driven partial updates)
- Small local state: Alpine.js (only where needed)
- Keep existing JS/jQuery during migration, then reduce.

## Phase 0 - Baseline (1 day)
1. Freeze current behavior screenshots (light/dark, home table, login/signup, inquiry).
2. Add visual QA checklist for desktop/mobile.
3. Define done criteria: no layout regressions, no major CLS on load.

Targets
- `templates/main.html`
- `templates/navbar.html`
- `static/styles/style.css`

## Phase 1 - Tailwind Infrastructure (1 day)
1. Add Tailwind build pipeline (PostCSS) and output CSS under static.
2. Keep existing `style.css` loaded; add new `tw.css` after it.
3. Introduce design tokens in `tailwind.config.js` matching current brand colors.

Targets
- `package.json` (new)
- `tailwind.config.js` (new)
- `postcss.config.js` (new)
- `static/styles/tw.css` (new generated output)
- `templates/main.html` (load order)

## Phase 2 - Navigation + Search Bar (2 days)
1. Refactor navbar layout to Tailwind utility classes.
2. Keep existing Django conditions (`is_authenticated`) unchanged.
3. Normalize tooltip style using tokens and mode-aware classes.
4. Preserve current feature set (theme toggle, v1/v2, date search, account menu).

Targets
- `templates/navbar.html`
- `static/styles/style.css` (remove overlapping navbar rules gradually)

## Phase 3 - Home Left Race Table Shell (2-3 days)
1. Keep table data/rendering logic intact.
2. Refactor container/tab/frame styling first; do not touch horse/rank logic.
3. Keep comment badge/modal behavior; move modal visuals to Tailwind classes.

Targets
- `base/templates/base/home_left.html`
- `base/templates/base/home_left_sub2.html`
- `static/styles/style.css`

## Phase 4 - Auth UX Modernization (2 days)
1. Upgrade login/signup screens to modern card layout.
2. Improve spacing, hierarchy, and validation message visibility.
3. Keep backend/auth flow unchanged.

Targets
- `templates/account/login.html`
- `templates/account/signup.html`
- `base/templates/base/update-user.html`
- `base/templates/base/profile.html`

## Phase 5 - Inquiry/Policy Pages (1 day)
1. Unify form components (input, textarea, button, error block).
2. Improve readability for terms/privacy modal or popup content.

Targets
- `base/templates/base/inquiry.html`
- `base/templates/base/terms_of_service.html`
- `base/templates/base/privacy_policy.html`

## Phase 6 - HTMX Introduction (optional but recommended)
1. Use HTMX for partial refresh areas first (comment counts, side panels).
2. Avoid full-page reloads for small interactions.
3. Keep API endpoints already in place and progressively swap front code.

Targets
- `base/templates/base/home_left.html`
- `apps/core/views.py`
- `apps/core/urls.py`

## Phase 7 - Debt Cleanup
1. Remove duplicated/obsolete CSS blocks from `style.css`.
2. Reduce inline style attributes in templates.
3. Keep only exceptions where dynamic server values require inline style.

Targets
- `static/styles/style.css`
- `templates/navbar.html`
- `base/templates/base/*.html`

## Guardrails
- Do not migrate business logic and templates in one PR.
- Keep each PR scope to one area (navbar, auth, inquiry, table shell).
- Add a rollback-safe checkpoint after each phase.

## First 3 PRs (practical order)
1. PR-1: Tailwind infra + token mapping + no UI changes.
2. PR-2: Navbar/search refactor only.
3. PR-3: Login/signup/profile form UI refactor.

## Why this path
- Lower risk than full React migration.
- Faster visible improvements.
- Better long-term maintainability than continuing large monolithic CSS.
