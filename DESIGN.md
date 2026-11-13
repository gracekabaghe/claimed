---
name: Claimed
description: Editorial/magazine visual world. Trusted publication aesthetic applied to a SaaS tool — headlines carry weight, typography leads, the product serves the story.

colors:
  # Primary brand
  indigo: "#4338CA"
  indigo-hover: "#3730A3"
  indigo-light: "#E0E7FF"
  indigo-subtle: "#EEF2FF"

  # Accent — warm, human, used sparingly for CTAs and highlights
  amber: "#D97706"
  amber-light: "#FEF3C7"

  # Surfaces
  page: "#FAFBFC"
  surface: "#FFFFFF"
  surface-hover: "#F8FAFC"
  surface-raised: "#FFFFFF"

  # Text
  text-primary: "#0F172A"
  text-secondary: "#475569"
  text-muted: "#94A3B8"
  text-disabled: "#CBD5E1"

  # Borders and rules
  border: "#E2E8F0"
  border-strong: "#CBD5E1"
  rule: "#F1F5F9"

  # State
  success: "#059669"
  success-light: "#ECFDF5"
  warning: "#D97706"
  warning-light: "#FFFBEB"
  error: "#DC2626"
  error-light: "#FEF2F2"

typography:
  display:
    fontFamily: "DM Sans, Inter, system-ui, sans-serif"
    weight: 700
    letterSpacing: "-0.02em"
  heading:
    fontFamily: "DM Sans, Inter, system-ui, sans-serif"
    weight: 600
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Inter, system-ui, sans-serif"
    weight: 400
    lineHeight: 1.7
  mono:
    fontFamily: "JetBrains Mono, SF Mono, monospace"
    weight: 500
    letterSpacing: "0"

  scale:
    xs: "0.75rem"
    sm: "0.875rem"
    base: "1rem"
    lg: "1.125rem"
    xl: "1.25rem"
    "2xl": "1.5rem"
    "3xl": "1.875rem"
    "4xl": "2.25rem"
    "5xl": "3rem"
    "6xl": "3.75rem"

rounded:
  none: "0"
  sm: "4px"
  md: "8px"
  lg: "12px"
  xl: "16px"
  pill: "999px"

spacing:
  xs: "8px"
  sm: "16px"
  md: "24px"
  lg: "32px"
  xl: "48px"
  "2xl": "64px"
  "3xl": "96px"

shadows:
  card: "0 1px 3px 0 rgba(0, 0, 0, 0.06), 0 1px 2px -1px rgba(0, 0, 0, 0.06)"
  card-hover: "0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.05)"
  modal: "0 20px 60px -12px rgba(0, 0, 0, 0.15)"
  button: "0 1px 2px 0 rgba(0, 0, 0, 0.05)"

components:
  button-primary:
    backgroundColor: "{colors.indigo}"
    textColor: "#FFFFFF"
    hoverBackgroundColor: "{colors.indigo-hover}"
    fontWeight: 600
    rounded: "{rounded.md}"
    padding: "12px 32px"
    fontSize: "{typography.scale.base}"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.indigo}"
    borderColor: "{colors.border-strong}"
    hoverBorderColor: "{colors.indigo}"
    hoverBackgroundColor: "{colors.indigo-subtle}"
    rounded: "{rounded.md}"
    padding: "12px 32px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    borderColor: "{colors.border}"
    focusBorderColor: "{colors.indigo}"
    focusRing: "0 0 0 3px {colors.indigo-light}"
    rounded: "{rounded.md}"
    padding: "12px 16px"
  card:
    backgroundColor: "{colors.surface}"
    borderColor: "{colors.border}"
    rounded: "{rounded.lg}"
    padding: "24px"
    shadow: "{shadows.card}"
    hoverShadow: "{shadows.card-hover}"
---

# Design System: Claimed

## 1. Overview: Trustworthy & Professional

Claimed helps business owners navigate a confusing new platform (ChatGPT). The design must convey trust, competence, and clarity — like a knowledgeable guide who's done this a thousand times.

**Key characteristics:**
- Clean, high-contrast light surfaces. No dark mode default.
- Indigo as the primary brand color — professional, distinctive, not corporate-blue generic.
- Amber as the accent — warm, human, used only for highlights and premium CTAs.
- One type scale, deliberately chosen. No random font sizes.
- Hairline borders, no heavy shadows. The UI feels precise, not decorative.
- Real content driving every section. No lorem ipsum, no placeholder metrics.

## 2. Mode: Persuade + Operate

The landing page is **Persuade**: "Claim your ChatGPT presence before your competitors do." The dashboard is **Operate**: scan, guide, monitor — task completion with precision.

## 3. Anti-Slop Rules (enforced)

These are the Impeccable-detected patterns we NEVER ship:

- ❌ Purple-to-blue gradients
- ❌ Glassmorphism / backdrop-blur decoration
- ❌ Cards nested in cards
- ❌ Gray text on colored backgrounds
- ❌ Rounded-square icon tiles above every heading
- ❌ Inter used as the only font with no hierarchy
- ❌ Sparkline decorations / meaningless metrics
- ❌ "Boost your productivity" / "Revolutionize your workflow" copy
- ❌ Dark mode as the only mode
- ❌ Neon accents or glowing elements
- ❌ Lorem ipsum in any shipped surface

## 4. Color Rules

- **Indigo carries the brand.** CTAs, links, active states, the wordmark.
- **Amber marks premium and urgency.** Use only for the highest-value CTA on a page, or for "limited" / "beta" badges. Never for navigation or secondary actions.
- **Text stays neutral.** Body text is always Slate-900 on light backgrounds. Secondary is Slate-600. No colored body text.
- **Borders are quiet.** Slate-200 borders define space without demanding attention.

## 5. Typography Rules

- **DM Sans for headings.** Bold weight (700 for h1, 600 for h2-h4). Tight letter-spacing (-0.02em for display, -0.01em for headings).
- **Inter for body.** 400 weight, line-height 1.7. Max width 65ch for readability.
- **JetBrains Mono for code and data.** 500 weight. Used for email addresses, verification codes, URLs.
- **No italic for UI.** Italic is for editorial emphasis in body copy only, never for labels or navigation.
- **The scale is fixed.** Every font-size lands on one of the 12 scale stops. No `font-size: 13.7px`.

## 6. Component Rules

- **Buttons are decisive.** Primary buttons use indigo fill with white text. Secondary uses transparent with indigo border. No gradient buttons. No shadow buttons. Height 48px minimum for touch targets.
- **Cards are simple.** White surface, 1px Slate-200 border, 8px radius, subtle shadow. Hover lifts the shadow slightly. No nested cards. No colored card backgrounds except for state (success/warning/error).
- **Inputs are obvious.** White background, Slate-200 border, indigo focus ring. Labels are above, not inside. Help text is below, Slate-500.
- **The readiness checker is the hero.** The first thing visitors see is an input field asking for their business URL. No carousel. No video. No hero illustration. The product IS the hero.

## 7. Imagery Rules

- **No generic stock photos.** No diverse-team-in-office, no handshake, no laptop-at-coffee-shop.
- **Screenshots of the product.** If we need to show value, we show the actual dashboard, the actual report, the actual insights.
- **Data visualizations only when they're real.** No decorative charts. If we show a graph, it's pulling from actual business insights data.