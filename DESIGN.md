# Design System

## Theme

A retro-technical operations desk. Scene: a security operator at a well-kept control station, with the console filling the whole screen. The reference is the Susan Kare era of interface design: flat pale-blue fields, chunky pixel artwork, capsule labels, off-white panels, and a single warm yellow accent. The shell is fullscreen — no simulated desktop, no fake browser window.

The nostalgia is the surface, not the behaviour. Navigation, tables, focus states, and status labels stay operational and legible. No fake CRT scanlines, no neon, no glassmorphism.

## Color

Strategy: Restrained. Light surfaces carry the screen; near-black ink carries the reading; yellow marks the current place and the one pull-quote. Semantic colors are reserved for state.

| Token | Value | Role |
|---|---|---|
| `--desk` | `#E8E8E8` | Desk behind the app window, dotted grid |
| `--paper` | `#F0EFEC` | Neutral page field |
| `--panel` | `#F5F5F5` | Window body and panels |
| `--panel-strong` | `#EDEBE6` | Panel headers, footer, chips |
| `--cream` / `--cream-deep` | `#F6F3D4` / `#EFE9BD` | Pull-quote panel |
| `--blue` / `--blue-deep` | `#B8DDF8` / `#A2D0F2` | Masthead field |
| `--ink` | `#0E0E0E` | Primary text, icons, capsule fill |
| `--ink-soft` | `#2E2C29` | Body and secondary labels |
| `--ink-muted` | `#6B6862` | Metadata |
| `--pill` | `#26221F` | Navigation capsules |
| `--pill-ink` | `#D9D4CE` | Capsule label |
| `--yellow` | `#F5C736` | Active capsule, icon tiles, stamp |
| `--line` / `--line-strong` | `#D8D5CF` / `#B9B5AD` | Rules and borders |

Status pairs always combine a background, a border, and an ink color: `success`, `danger`, `warn`, `info`. Never signal state with color alone.

## Typography

- Display: **Silkscreen** (pixel bitmap), 700. Used for the wordmark, page titles, panel titles, section titles, and small headings. Uppercase with `0.03em` to `0.06em` tracking. Never for body copy.
- UI: **IBM Plex Sans**, 400/500/600. Navigation, buttons, labels, table content.
- Prose: **IBM Plex Serif**, 400/600 plus italic. Page ledes, module descriptions, pull-quotes, panel notes.
- Data: **IBM Plex Mono**, 400/500. UTC clock, issue keys, eyebrows, table data, footer.

Body is `0.9375rem` with `1.55` line height. Page titles clamp from `1.6rem` to `2.5rem`. The masthead wordmark clamps from `1.7rem` to `5.25rem` and may wrap at narrow widths.

## Layout

- The app fills the viewport edge to edge: no outer desk, no window border, no rounded shell.
- Slim top bar across the full width: UTC date on the left, UTC clock and build badge on the right.
- Pale blue masthead, full bleed: huge centered wordmark, one mono subtitle line, two centered rows of dark capsule navigation.
- Floating pixel icons sit at the masthead edges. They are decoration only, hidden below 1000px, and never overlap the wordmark or navigation.
- Page content maxes at `76rem` with fluid padding; the header and footer stay full bleed.
- The app is a flex column with `min-height: 100dvh`, so the footer sits at the bottom on short pages.
- Overview is a `1.45 / 0.8` split that collapses to one column under 1040px.
- Module pages use a white card with a 5rem yellow pixel-icon tile on the left; it stacks under 1040px.
- The cream pull-quote panel closes the overview. One per page at most.
- Below 640px the footer stacks and the top bar drops the date; navigation still wraps instead of hiding.

## Components

- **Top bar**: UTC date, live UTC clock, build badge. Always present, never interactive except the clock text. No traffic lights or fake window title.
- **Wordmark**: links home. Underline on hover.
- **Nav capsule**: dark pill, light label, uppercase `0.625rem`. Hover darkens and lifts 1px. Active is yellow with ink text.
- **Button**: capsule. Default is white with a strong border; primary is near-black; accent is yellow; ghost is transparent. Hover inverts to ink. All states include focus-visible, active, and disabled.
- **Chip**: small capsule for issue keys and states. `queued`, `ready`, `live`, `warn`, `danger`.
- **Panel**: 1px border, 2px radius, inset highlight, soft shadow. Header on `--panel-strong`. Optional serif note footer.
- **Table**: thin rules, uppercase mono header, warm hover row. Links get a yellow highlight on hover.
- **Module card**: white, icon tile, serif body, mono metadata, action row.
- **Field note**: cream gradient panel, italic serif quote, mono citation, rotated yellow stamp with a pixel star.
- **Pixel icon**: 12 × 12 SVG built from a character map in `frontend/js/layout.js`. `#` ink, `y` yellow, `w` paper. Rendered with `shape-rendering: crispEdges`.

Every interactive component must ship with default, hover, focus-visible, active, disabled, loading, and error states.

## Motion

120 to 260ms, ease out with `cubic-bezier(0.22, 1, 0.36, 1)`. Motion only conveys state: hover, focus, press. No page-load choreography, no floating-icon animation. Reduced-motion users get instant state changes.

## Accessibility

- WCAG 2.2 AA. Body text meets 4.5:1; large text and UI borders meet 3:1.
- Visible 2px ink focus ring with 2px offset; yellow ring inside inputs.
- Status is a square LED plus a text label, never color alone.
- Skip link to main content on every page.
- `aria-current="page"` on the active nav capsule.
- Decorative pixel icons are `aria-hidden` and non-interactive.
- Nav wraps instead of hiding, so every destination stays reachable at any width.
