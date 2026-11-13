# Design System

## Theme

Dark control-room surface. Scene: a security operator on a night shift, scanning a patrol map and an alert queue on a wide monitor in a dim room. Warm graphite neutrals keep glare low; safety amber marks action and attention.

Not a navy "observability" theme and not neon-on-black. Warm, matte, industrial.

## Color

Strategy: Restrained. One signal accent carries primary action, current selection, and attention. Semantic colors are reserved for state.

| Token | Role |
|---|---|
| `--bg` | App background, warm graphite |
| `--surface` | Panels and the top bar |
| `--line` | Default borders |
| `--ink` | Primary text |
| `--ink-soft` / `--ink-muted` | Secondary and tertiary text |
| `--signal` | Safety amber: primary buttons, active nav, focus ring |
| `--success` | Active robot, ready state |
| `--danger` | Intrusion alerts, destructive actions |
| `--warning` | Obstacles and battery warnings |
| `--info` | Neutral system messages |

All values live in OKLCH in `frontend/css/tokens.css`. Never use pure black or pure white.

## Typography

- UI: IBM Plex Sans (fallback system sans). 400/500/600.
- Data: IBM Plex Mono for timestamps, serial numbers, coordinates, and issue keys.
- Fixed rem scale, roughly 1.2 between steps. Body 0.9375rem, page title 2.375rem.
- Body prose caps at 68ch; tables may run wider.
- Uppercase eyebrow labels at 0.12em tracking, used sparingly.

## Layout

- Top command bar: brand, primary navigation, UTC clock, build chip.
- Page content maxes at 90rem with generous horizontal padding.
- Panels use 1px borders and a soft shadow; no nested cards.
- Overview uses a 1.55 / 0.85 split that collapses to one column under 1000px.
- Tables scroll horizontally on small screens; navigation collapses under 980px.

## Components

- **Button**: primary (amber), ghost (bordered), disabled, focus ring.
- **Chip**: queued, ready, live, danger. Uppercase, pill, small.
- **Status dot**: always paired with a text label.
- **Panel**: header, body, optional note footer.
- **Table**: thin rules, uppercase header, hover row, right-aligned data when numeric.
- **Field**: label, input, hint, error. Base styles are ready for SCRUM-20 forms.

Every interactive component must ship with default, hover, focus-visible, active, disabled, loading, and error states.

## Motion

150 to 250 ms. Ease out with `cubic-bezier(0.22, 1, 0.36, 1)`. Motion only conveys state (hover, focus, open navigation). No page-load choreography. Reduced-motion users get instant state changes.

## Accessibility

- Minimum target 2.5rem for controls.
- Visible 2px focus ring in safety amber with 2px offset.
- Status colors pair with labels and shapes.
- Skip link to main content on every page.
- `aria-current` on the active nav link, `aria-expanded` on the mobile toggle.
