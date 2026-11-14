# Design System

## Theme

An editorial operations desk. Scene: a dispatch office with white walls, periwinkle paperwork, and one very large serif headline. The reference is a designer's portfolio, not a cockpit: oversized display type, a portrait card with stickers and badges, a ticker strip, and a fan of work cards. The shell is fullscreen — no simulated desktop, no fake browser window, no traffic lights.

The playfulness is in the composition, not the data. Navigation, chips, tables, and status labels stay operational and legible. No CRT scanlines, no neon, no glassmorphism, no fake live telemetry.

## Color

Strategy: Restrained. White carries the page, periwinkle carries the structure, near-black ink carries the reading, and a single blue accent marks the current place and the one pull-quote. Semantic colors are reserved for state.

| Token | Value | Role |
|---|---|---|
| `--bg` | `#FFFFFF` | Page field |
| `--bg-soft` | `#FAFBFF` | Ticker and footer bands |
| `--periwinkle` | `#E5EAFA` | Portrait card, module covers |
| `--periwinkle-deep` | `#D5DEF9` | Cover variant, rail lines |
| `--periwinkle-soft` | `#F1F4FE` | Nav pill, aside panels, halo fills |
| `--accent` | `#5B74E0` | Active marker, arrow, outline stroke |
| `--accent-soft` | `#8FA3F2` | Ticker type, "My modules" wordmark, sticker |
| `--accent-deep` | `#3D4EB8` | Emphasis italics, link hover, focus ring |
| `--ink` | `#17171C` | Primary text, brand pill, dark covers |
| `--ink-soft` | `#3A3B45` | Body copy |
| `--ink-muted` | `#6E7180` | Metadata, captions |
| `--ink-faint` | `#A2A5B2` | Disabled, inactive dots |
| `--line` / `--line-strong` | `#E4E6EF` / `#CDD2E2` | Rules and borders |

Status pairs always combine a background, a border, and an ink color: `live`, `warn`, `danger`, plus a neutral `queued`. Never signal state with color alone.

## Typography

- Display: **Fraunces**, 600/900 with `SOFT 40` and `WONK 1`. Hero wordmark, page titles, path numerals, CTA, module numbers. Uppercase only for the hero; sentence case everywhere else. Tracking `-0.03em` to `-0.05em`, line height `0.84` to `0.96`.
- UI: **DM Sans**, 400/500/600. Navigation, buttons, labels, chips, footer links.
- Prose: **Fraunces**, 400/600 plus italic. Page ledes, module descriptions, footnotes, pull-quotes.
- Data: **DM Mono**, 400/500. UTC clock, issue keys, eyebrows, at-a-glance values, footer metadata.

Body is `0.9375rem` (or `1rem`) with `1.6` line height. The hero clamps from `2.9rem` to `7.2rem`. Module titles clamp from `2.8rem` to `5.4rem`. The "My modules" wordmark clamps from `2.6rem` to `6.4rem`.

The hero outline treatment — transparent fill with a 2px accent-deep `-webkit-text-stroke` — is the one loud gesture. Use it once per page, never on body copy.

## Layout

- The app fills the viewport edge to edge: no outer desk, no window border, no rounded shell.
- Sticky white header: dark brand pill on the left, light periwinkle pill nav on the right, UTC clock at the far edge. The nav wraps at narrow widths instead of collapsing into a hamburger.
- Hero is a two-column split: stacked display wordmark and lede on the left; a rounded portrait card on the right, with a slight rotation on its "24/7" sticker and a caption bar at the bottom.
- A full-bleed ticker strip separates the hero from the intro. Italic serif type, accent-soft, one line, decorative only.
- The intro pairs a map-preview card with a serif statement, an ink speech bubble, and a hand-drawn arrow. The arrow is decoration and hides below 1040px.
- The three-step path uses a hairline three-column grid with oversized periwinkle numerals, collapsing to stacked rows under 880px.
- The CTA centers a large serif line over a radial periwinkle halo.
- The works section fans six module cards in an arc. Cards straighten and lift on hover. Under 860px the fan becomes a horizontal snap-scroll row.
- Module pages reuse the same split: serif title and honest queued copy on the left, a giant numbered cover card on the right, then a two-column panel with at-a-glance metadata.
- Content maxes at `82rem` with fluid padding; the header and footer stay full bleed.
- The app is a flex column with `min-height: 100dvh`, so the footer sits at the bottom on short pages. The footer is four columns, collapsing to two under 880px and one under 640px.

## Components

- **Brand pill**: ink capsule with an accent-soft dot and "Fleet Control" in uppercase DM Sans. Links home.
- **Nav pill**: periwinkle-soft capsule containing seven links. Each link is a pill; hover turns white, active turns ink with white text. `aria-current="page"` marks the current route.
- **Button**: pill. `--dark` is ink filling, `--outline` is accent border on white, `--ghost` is a hairline outline, `--accent` is blue filling. Hover lifts 2px and shifts color. All states include focus-visible, active, and disabled.
- **Chip**: mono capsule for issue keys, sprints, and states. `queued`, `ready`, `live`, `warn`, `danger`.
- **Badge**: uppercase sans capsule. `--dark` for "Preview unit", `--light` for "Autonomous".
- **Portrait card**: periwinkle gradient panel, rounded `32px`, with an SVG robot, a status badge, a circular sticker, and a white caption bar showing unit, sector, and a sample battery bar.
- **Map preview card**: dotted periwinkle field with dashed route, four markers, a "Built for the night shift!" bubble, and a caption bar. Sample data only.
- **Module card**: a 4:5 cover with a huge Fraunces numeral and a mono sprint tag, plus a white body with the module name and issue key. Four cover variants: periwinkle, deep, ink, outline.
- **Page cover**: the same language at larger scale, `32px` radius, with a numbered display glyph, italic label, and a "Queued" badge.
- **Panel**: two-column card, white main and periwinkle-soft aside, hairline divider, `24px` radius.
- **Meta list**: label/value rows with a hairline between, mono uppercase labels, right-aligned values.

Every interactive component must ship with default, hover, focus-visible, active, disabled, loading, and error states.

## Motion

140 to 320ms, ease out with `cubic-bezier(0.22, 1, 0.36, 1)`. Motion only conveys state: hover, focus, press. The fan cards straighten on hover; nothing pulses, floats, or parallaxes. No page-load choreography. Reduced-motion users get instant state changes.

## Accessibility

- WCAG 2.2 AA. Body text meets 4.5:1; large text and UI borders meet 3:1.
- Visible 2px accent-deep focus ring with 3px offset, white ring on dark pills.
- Status is a dot plus a text label, never color alone.
- Skip link to main content on every page.
- `aria-current="page"` on the active nav link.
- Decorative SVGs, the ticker, and the fan's rotations are `aria-hidden` or non-essential; hover-only transforms are never required to reach a route.
- Nav wraps instead of hiding, so every destination stays reachable at any width.
- The ticker and marquee-like decoration are static text; nothing scrolls automatically.
