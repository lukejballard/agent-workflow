# Skill: Frontend Accessibility

**Scope:** All React components and pages in `frontend/src/`.

**Purpose:** Ensure the dashboard is usable by people with disabilities and meets WCAG 2.1 AA.

---

## Checklist

### Semantic HTML
- [ ] Page structure uses semantic elements (`<header>`, `<main>`, `<nav>`, `<section>`, `<article>`, `<footer>`).
- [ ] Headings are used in logical order (H1 → H2 → H3); no skipped levels.
- [ ] Tables use `<th>` with `scope` attributes for headers.
- [ ] Lists use `<ul>`, `<ol>`, or `<dl>` rather than styled `<div>` elements.

### Interactive elements
- [ ] Every `<button>` has visible text or `aria-label`.
- [ ] Every `<a>` has descriptive text (not "click here" or "read more").
- [ ] Every form `<input>` is associated with a `<label>` (via `htmlFor`/`id` or `aria-labelledby`).
- [ ] Custom interactive widgets (dropdowns, modals, tabs) have correct ARIA roles and keyboard support.

### Focus management
- [ ] All interactive elements are reachable via keyboard (`Tab` / `Shift+Tab`).
- [ ] Focus is not trapped except inside open modals.
- [ ] Focus is moved to the correct element after modal open/close.
- [ ] Focus ring is visible (not suppressed with `outline: none` without a replacement).

### Colour and contrast
- [ ] Text meets WCAG 2.1 AA contrast ratio (4.5:1 for normal text, 3:1 for large text).
- [ ] Information is not conveyed by colour alone (e.g. error states also have an icon or text).
- [ ] Charts and graphs have accessible text descriptions or `aria-label` on the SVG container.

### Images and icons
- [ ] All `<img>` elements have an `alt` attribute.
- [ ] Decorative images have `alt=""`.
- [ ] Icon-only buttons have `aria-label` or a visually hidden label.

### Dynamic content
- [ ] Loading states announce themselves to screen readers (`aria-live="polite"` or `aria-busy`).
- [ ] Error messages are associated with their input fields via `aria-describedby`.
- [ ] Toast notifications use `role="alert"` or `aria-live="assertive"`.

---

## How to verify

```bash
# 1. Run ESLint with jsx-a11y plugin (if configured)
cd frontend && npm run lint

# 2. Run automated a11y tests
# (Install axe-core: npm install --save-dev axe-core vitest-axe)
npm test

# 3. Manual check: keyboard navigation
# Open the dashboard, press Tab repeatedly — every interactive element should receive focus.

# 4. Manual check: screen reader
# Use VoiceOver (macOS), NVDA (Windows), or Orca (Linux) to navigate the dashboard.
```

---

## Expected output

No axe-core violations. All interactive elements reachable by keyboard. All images have alt text. Colour contrast meets WCAG 2.1 AA for all text.
