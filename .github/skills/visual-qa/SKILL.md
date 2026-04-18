# Visual QA Skill

## When to use
Use when a UI change is implemented and needs visual and UX validation before merge,
or when a design review is needed for a component or page.

Auto-consider this skill for user-facing frontend changes, navigation changes,
new empty states, changed error states, or documentation/UI workflow changes that
affect how contributors exercise the interface.

## Step 1 — Layout and spacing audit
- Are spacing values consistent with the existing frontend patterns in `frontend/src/`?
- No elements overflowing their containers?
- No unintended element collisions or overlaps?
- Text wrapping correctly at all content lengths?

## Step 2 — Responsive validation
Test at three breakpoints:
- Mobile: 375px viewport
- Tablet: 768px viewport
- Desktop: 1280px viewport

Check at each breakpoint:
- No horizontal scrollbar
- Navigation remains usable
- Touch targets at least 44×44px on mobile
- No truncated or hidden critical content

## Step 3 — Accessibility audit
- All images have descriptive `alt` text (or `alt=""` for decorative)
- All form inputs have associated `<label>` elements
- All interactive elements have accessible names
- Colour contrast: WCAG AA minimum (4.5:1 for text, 3:1 for UI components)
- Keyboard: Tab through all interactive elements — order is logical
- Focus indicators are visible on all focusable elements
- No information conveyed by colour alone

## Step 4 — Interaction states
Verify each interactive element has:
- Default state
- Hover state
- Focus state (visible outline)
- Active/pressed state
- Disabled state (if applicable)
- Loading state (if applicable)
- Error state (if applicable)

## Step 5 — Playwright capture (if MCP available)
Run these Playwright actions and capture screenshots:

```typescript
// Capture at three breakpoints
for (const width of [375, 768, 1280]) {
  await page.setViewportSize({ width, height: 800 });
  await page.goto("/target-page");
  await page.screenshot({ path: `screenshots/visual-qa-${width}.png`, fullPage: true });
}

// Run axe accessibility scan
const { AxeBuilder } = require("@axe-core/playwright");
const results = await new AxeBuilder({ page }).analyze();
// Report any violations
```

## Output
Issues table:
| Element | Issue | Severity | Fix |
|---|---|---|---|

Severity: Critical (blocks use) / High (poor UX) / Medium (inconsistency) / Low (polish)

Screenshot paths (if captured).
Accessibility violations from axe-core (if captured).
List the regression-prone UI states that were checked explicitly.
