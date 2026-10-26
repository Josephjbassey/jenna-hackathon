# Jenna AI OS — Executive Suite · DESIGN.md

Design contract for the Jenna unified local voice agent dashboard. Every screen inherits
these tokens. Single-surface desktop application, dark-first, no light theme in v1.

## Product frame

A command console for a five-agent local squad on an 8 GB CPU laptop. It must read like
avionics, not like a SaaS marketing page: dense, monospaced numerals, hairline structure,
one accent color doing all the emphasis. Nothing on screen that does not carry state.

Target canvas: 1512 × 945 desktop, min 1240 × 780. Grid: 4 px base, 12 px rail gutters.

## Palette

Surfaces
- `--bg-base` #0A0B0D — app background, never pure black
- `--bg-surface` #101215 — rails, cards
- `--bg-raised` #15181C — hovered/selected rows, popovers
- `--hairline` rgba(255,255,255,0.07) — 1px dividers, card borders
- `--hairline-strong` rgba(255,255,255,0.13) — focused edges, dock top edge

Ink
- `--ink-1` #F2F4F7 — primary text
- `--ink-2` #9AA3AE — secondary labels, captions
- `--ink-3` #5C6570 — disabled, axis ticks, placeholders

Accent (use sparingly — under 5% of any screen)
- `--crimson` #DC143C — primary action, active selection, focus ring, brand mark

State hues (reserved meaning, never decorative)
- `--idle` #3F4750 — dormant, disconnected
- `--listening` #22D3EE — mic open, capture active
- `--thinking` #F59E0B — inference in flight, LangGraph planning
- `--speaking` #10B981 — TTS playback, completed write-back
- `--error` #EF4444 — engine down, refusal, overrun

Tint rule: state hues render at 12–18% alpha for fills, 100% for 1–2px strokes and dots.
Never fill a whole panel in a state hue.

## Typography

- Display / zone labels: **Space Grotesk** 600, 11 px, uppercase, tracking +0.08em
- UI body: **Geist Sans** 400/500, 13 px (rows), 14 px (transcript), line-height 1.45
- Numerals, model tags, paths, hotkeys: **JetBrains Mono** 400, 11–12 px, tabular figures
- Headings inside panels: Geist Sans 500, 15 px — no bold display type in the console
- Self-hosted fonts only (zero CDN). Latin + full OpenType numerals.

## Layout — five zones, asymmetric

Row 1 — Telemetry bar, 44 px, full width, `--bg-surface`, hairline bottom.
Left: brand mark + OS/host badge. Center: dual-engine pills (Ollama :11434, LM Studio
:1234) each with a 6 px state dot and model count. Right: CPU / RAM / disk as three
compact meter groups (label, mono value, 48 px micro-bar) + clock.

Row 2 — three columns, unequal: left rail 296 px, center stage flexible, right rail 336 px.
The center stage is deliberately the widest and is the only place with breathing room.

Left rail — Squad roster. Five stacked agent cards, 72 px each: role glyph (16 px),
role name in Space Grotesk caps, model tag in JetBrains Mono, provider chip, 3 px
activity meter along the card's bottom edge, state dot top-right. Selected card lifts to
`--bg-raised` with a 1px crimson left edge and expands an inline inspector (context tokens
used, last prompt hash, force-delegate action). Rail footer: "New delegation" ghost button.

Center stage — Audio core. Off-centre, biased slightly left of optical centre. A
particle/noise-displaced sphere, 320 px diameter, rendered as concentric displaced rings
with a soft rim glow in the current state hue; a thin 1px orbit ring carries the state
label. Beneath it the transcript ribbon: last user line, then assistant line, mono
timestamps in `--ink-3`, 14 px body, max 3 lines before scroll. Above the sphere: a row of
thinking-trace chips (retrieve → plan → delegate → verify) — completed chips crimson-outlined,
current chip amber-filled at 15%, pending chips `--ink-3`.

Right rail — Memory stream. Tab strip: Wiki / Memory / Log. Active tab shows a markdown
note card (frontmatter block in mono, 3 lines of body), then a knowledge-graph mini canvas
(180 px tall: nodes as 5 px dots, edges as hairlines, one crimson node = current entity),
then the daily log feed as a compact timestamped list, 6 rows visible. Rail footer: solid
crimson "Quick add" button with mic glyph.

Row 3 — Action dock, 88 px, floating, inset 16 px from the app edges, single
`backdrop-filter: blur(18px)` layer over `rgba(16,18,21,0.72)`, 14 px radius, hairline-top,
only shadow in the app: 0 12px 32px rgba(0,0,0,0.55).
Left: push-to-talk orb, 56 px, with hotkey caption `Ctrl+Alt+Space`. Center: 32-bar live
spectrum, bars 2 px wide, 2 px gap, state-hued. Right: three quick-tool tiles (AgentPhone,
AgentMail, Sandbox Terminal) as 20 px icon + 11 px label, then a model switcher select.

## Components

- Chips: 3 px radius, 1px stroke in their hue at 100%, fill at 14%, 10 px mono label
- Cards: 10 px radius, `--bg-surface`, 1px `--hairline`, no shadow
- Buttons primary: crimson fill, `#0A0B0D` text, 6 px radius, 13 px Geist 500, 32 px tall
- Buttons ghost: transparent, 1px `--hairline-strong`, `--ink-1` text
- Meters: 48 × 3 px track `--hairline`, fill in state hue, square caps
- Focus ring: 1px crimson offset 2 px — always visible, never removed
- Scrollbars: 4 px, `--hairline-strong` thumb, invisible track
- Icons: Phosphor, 16 px in rails, 20 px in dock, regular weight; duotone only for state

## Motion

120–180 ms ease-out on hover/selection. Sphere pulse 2.4 s loop while listening; spectrum
runs at 60 Hz while capture is open; trace chips advance with a 160 ms cross-fade.
`prefers-reduced-motion: reduce` → static rings, frozen spectrum at last amplitude, no pulse.

## Anti-patterns (reject on sight)

No purple/blue gradients, no rainbow conic-gradient orb, no glass on more than the dock,
no rounded-2xl cards, no emoji glyphs, no three-equal-feature-card row, no centred hero,
no Inter or Roboto, no drop shadows except the dock, no all-caps body text, no percentage
values without their meter.
