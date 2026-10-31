# OmniStore AI — Semantic Design System · DESIGN.md
*Theme: "Build for Your World" · High-Agency Physical-to-Digital Micro-Commerce*

This document defines the strict visual language, spatial architecture, color calibration, and motion standards for OmniStore AI. All frontend screens, canvas overlays, and generated micro-storefront components must adhere to these directives.

---

## 1. Product Frame & Atmosphere

- **Context:** An autonomous physical-to-digital inventory compiler empowering market stall keepers, kiosk vendors, and non-technical traders in emerging economies (Lagos, Nairobi, Accra, São Paulo).
- **Aesthetic Stance:** Tactical, high-density, editorial utility. Reads like a field-grade logistics tool meets modern Swiss typography — NOT a generic AI neon dashboard.
- **Atmosphere Calibration:**
  - **Density:** 7/10 (Cockpit Balanced — high information density, compact data chips, tabular numerals).
  - **Variance:** 6/10 (Asymmetric split — visual perception canvas on the left, cognitive market reasoning on the right).
  - **Motion:** 5/10 (Subtle, purposeful spring physics — 120ms to 180ms easing, no sluggish transitions).
- **Anti-Patterns Banned:**
  - ❌ Neon purple/cyan glow buttons or AI gradient borders.
  - ❌ Pure black backgrounds (`#000000`).
  - ❌ Floating decorative shapes or cartoon illustrations.
  - ❌ Flashing status rings.

---

## 2. Color Calibration

Strict single-accent system grounded in neutral carbon and agricultural commerce:

| Role | Token | Hex | Usage |
|---|---|---|---|
| **Base Surface** | `--bg-base` | `#090B0E` | Main application background (never `#000000`). |
| **Panel Surface** | `--bg-surface` | `#11141A` | Bounded containers, canvas viewport, and inspector drawers. |
| **Card / Row Surface** | `--bg-raised` | `#161B23` | Active item rows, table cells, and elevated cards. |
| **Hairline Dividers** | `--border-subtle` | `rgba(255, 255, 255, 0.08)` | 1px clean grid dividers and element borders. |
| **Hairline Strong** | `--border-strong` | `rgba(255, 255, 255, 0.16)` | Selected cards, focus outlines, and active tab indicators. |
| **Primary Ink** | `--ink-1` | `#F1F3F5` | Primary headlines, active numbers, and SKU titles. |
| **Secondary Ink** | `--ink-2` | `#96A0AD` | Descriptions, metadata, and table subtext. |
| **Tertiary Ink** | `--ink-3` | `#58626F` | Inactive labels, placeholder text, and axis marks. |
| **Singular Accent** | `--accent-palm` | `#10B981` | Action buttons, active badges, and WhatsApp checkout (calibrated 70% saturation). |
| **Currency / Valuation** | `--accent-gold` | `#E5A93C` | Local currency figures (`NGN`, `KES`, `GHS`), total shelf value. |
| **Visual Eye (SAM 3.1)** | `--sam-eye` | `#38BDF8` | Bounding box spatial overlays and coordinate tags. |

---

## 3. Typographic Architecture

- **Primary Interface:** Modern clean sans-serif (`Geist Sans` / `Outfit` / `Inter-tight`).
- **Numerals & Metrics:** Monospaced tabular figures (`JetBrains Mono` / `Geist Mono`) for all prices, stock counts, and timestamps.
- **Scale:**
  - Display Title: 18px (600 weight, -0.02em letter spacing).
  - Section Headers: 13px (600 weight, uppercase, +0.05em tracking).
  - Body: 13px (400 weight, 1.4 leading).
  - Telemetry & Badges: 10–11px monospace.

---

## 4. Visual Perception Canvas & Spatial Overlays

The canvas visualizes physical goods on wooden market stall shelves:
- **Shelf Rendering:** Renders high-fidelity vector stall architecture with physical goods (Yam tubers, Tomato baskets, Garri tubs, Palm oil bottles, Plantains) using clean SVG elements and reliable data encoding.
- **Bounding Boxes:**
  - Hairline 1.5px stroke with translucent fill (12% opacity).
  - Hover state: Stroke brightens, fill lifts to 24% opacity.
  - Active selection: Solid white 2px stroke with high-contrast label pill.
- **Labels:** Crisp monospace pill positioned at the top-left of each bounding box displaying semantic label + confidence IOU.

---

## 5. Mobile Storefront Simulator (The Hands)

- **Device Frame:** Sleek 380px mobile device mockup with subtle edge reflection and top sensor notch.
- **Storefront Theme:** Mobile-first, low-bandwidth optimized for 3G/4G connections.
- **Instant Commerce Action:** Sticky bottom drawer with cart tally and a 1-click `#25D366` WhatsApp order button that generates an encoded WhatsApp chat URL.

---

## 6. Vercel Architecture

- **Frontend:** Next.js 14 App Router, dynamic server rendering, pre-rendered static assets.
- **Backend API:** Python FastAPI deployed as a Vercel Serverless Function via `@vercel/python` or proxy rewrites to `/api/v1`.
- **Environment:** Seamless variable binding (`META_MODEL_API_KEY`, `ALLOWED_ORIGINS`).
