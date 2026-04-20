---
applyTo: "**/*.html,**/*.tsx,**/*.jsx"
---

# Accessibility standards (WCAG 2.1 AA)

## Semantic HTML
- Use semantic elements: `<button>` for actions, `<a>` for navigation, `<nav>`, `<main>`,
  `<header>`, `<footer>`, `<section>`, `<article>`, `<aside>`.
- Never `<div onClick>` or `<span onClick>` for interactive elements.
- Heading hierarchy must be sequential: `h1` → `h2` → `h3`. Never skip levels.

## Interactive elements
- All interactive elements must have an accessible name:
  - Buttons: visible text, or `aria-label` if icon-only.
  - Links: descriptive text. Never "click here" or "read more" alone.
  - Form inputs: associated `<label>` element (via `for`/`id` or wrapping).
- Minimum touch/click target size: 44×44 CSS pixels.
- Focus must be visible on all interactive elements. Never `outline: none` without replacement.

## Keyboard navigation
- All interactive elements must be reachable via Tab.
- Tab order must be logical (matches visual order).
- Modal dialogs: trap focus inside the modal while open, return focus on close.
- Dropdown menus: Arrow keys navigate options, Escape closes.

## Colour and contrast
- Text contrast: minimum 4.5:1 (WCAG AA). Target 7:1 (WCAG AAA) for body text.
- UI component contrast (borders, icons): minimum 3:1.
- Never convey information by colour alone. Always add a secondary indicator
  (icon, pattern, text label).
- Test with `prefers-color-scheme: dark` — all contrast ratios must hold in dark mode.

## Images and media
- All images: meaningful `alt` text describing content and purpose.
  Decorative images: `alt=""` (empty string, not omitted).
- Icons that convey meaning: `aria-label` or `aria-hidden="true"` + visible text sibling.
- Video: captions required. Audio description for visual-only content.

## Dynamic content
- Use `aria-live` regions for content that updates without a page load.
  `aria-live="polite"` for non-urgent updates, `aria-live="assertive"` for errors.
- Loading states: `aria-busy="true"` on the container being updated.
- Error messages: associate with the input via `aria-describedby`.
- Route-level status, success, and error banners should be announced without stealing focus unless the interaction is blocking.

## Testing accessibility
- Automated: run `axe-core` or `@axe-core/playwright` in E2E suite.
- Manual: tab through every new feature to verify keyboard navigation.
- Screen reader: test with VoiceOver (macOS) or NVDA (Windows) for complex interactions.
- In React tests, prefer queries by role, label, and accessible name so accessibility regressions surface naturally.
