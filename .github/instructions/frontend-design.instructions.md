---
applyTo: "**/*.tsx,**/*.jsx,**/*.css"
---

# Frontend design standards

This file provides concrete design guidance for generated React frontends.
It fills the reference made by `react.instructions.md` to a frontend design standard.

## Design system defaults
When the user and host repo do not establish a design system:
- Use shadcn/ui components built on Radix UI primitives.
- Use Tailwind CSS for utility-first styling.
- Use Lucide React for icons.
- Use class-variance-authority (cva) for component variants.

## Layout
- Use a consistent page shell: sidebar or top nav, main content area, optional footer.
- Max content width: `max-w-7xl` (1280px) for page content. Full-bleed for dashboards.
- Use CSS Grid or Flexbox for page-level layout. Avoid absolute positioning for layout.
- Responsive breakpoints: mobile-first. Use Tailwind's `sm:`, `md:`, `lg:`, `xl:` prefixes.
- Minimum tap target size: 44x44px for all interactive elements.

## Typography
- Use the system font stack or the host repo's established typeface.
- Heading scale: `text-4xl` (h1), `text-2xl` (h2), `text-xl` (h3), `text-lg` (h4).
- Body text: `text-base` (16px). Secondary text: `text-sm` (14px). Caption: `text-xs` (12px).
- Line height: `leading-relaxed` for body text, `leading-tight` for headings.
- Never use more than 3 font weights on a single page.

## Spacing
- Use Tailwind's spacing scale consistently: `p-4`, `gap-4`, `space-y-4`.
- Section spacing: `py-8` or `py-12` between major page sections.
- Card/panel padding: `p-4` (compact), `p-6` (standard).
- Form field spacing: `space-y-4` between fields, `space-y-2` between label and input.
- Never mix arbitrary pixel values with the spacing scale.

## Color tokens
- Use Tailwind's built-in palette or the host repo's design tokens.
- Background: `bg-background` / `bg-card` (light), dark mode variants automatic with shadcn/ui.
- Text: `text-foreground` (primary), `text-muted-foreground` (secondary).
- Interactive: `bg-primary` / `text-primary-foreground` for primary actions.
- Destructive: `bg-destructive` / `text-destructive` for danger actions.
- Border: `border-border` for all borders and dividers.
- Focus ring: `ring-ring` with `focus-visible:ring-2`.
- Never use raw hex colors. Always use semantic tokens.

## Component states
Every interactive component must handle and visually represent:
- **Default**: normal appearance.
- **Hover**: subtle background or shadow change.
- **Focus**: visible focus ring (`focus-visible:ring-2 ring-ring ring-offset-2`).
- **Active/pressed**: slightly darker background or scale transform.
- **Disabled**: reduced opacity (`opacity-50`), `cursor-not-allowed`, `pointer-events-none`.
- **Loading**: spinner or skeleton, `aria-busy="true"`.
- **Error**: red border, error text below the input, `aria-describedby` linking to error message.
- **Empty state**: descriptive message with optional illustration or action.

## Dark mode
- All generated UIs must work in both light and dark mode.
- Use shadcn/ui's CSS variable system for automatic dark mode.
- Test contrast ratios in both modes. Minimum 4.5:1 for text, 3:1 for UI elements.
- Never rely on color alone to convey information.

## Design completeness checklist
Before marking a UI task complete, verify:
- [ ] All interactive elements have hover, focus, active, and disabled states.
- [ ] Loading states show skeletons or spinners, not blank screens.
- [ ] Empty states show helpful messages, not blank containers.
- [ ] Error states show clear, actionable messages.
- [ ] Typography scale is consistent across the page.
- [ ] Spacing is consistent and uses the design system scale.
- [ ] Color usage follows semantic tokens, not arbitrary values.
- [ ] Dark mode works and passes contrast checks.
- [ ] All interactive elements meet minimum 44x44px touch target.
- [ ] Keyboard navigation works through all interactive elements.
