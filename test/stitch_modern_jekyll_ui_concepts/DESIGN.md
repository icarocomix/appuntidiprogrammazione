# Design System Document: The Lucid Console

## 1. Overview & Creative North Star
The Creative North Star for this design system is **"The Lucid Console."** 

This system rejects the cluttered, chaotic aesthetic of traditional command-line interfaces in favor of a high-end, editorial developer experience. It bridges the gap between technical precision and sophisticated digital craft. We are moving away from "generic terminal" tropes—like neon-on-black or harsh grids—to embrace a layered, atmospheric environment.

The design breaks the standard Jekyll template look through **intentional asymmetry**, **glassmorphism**, and **tonal depth**. By utilizing extreme typographic scales and "ghost" boundaries, we create an interface that feels like a professional-grade IDE curated by a premium design house.

---

## 2. Colors & Surface Philosophy

The palette is rooted in deep technical neutrals punctuated by a vibrant Emerald/Forest accent. 

### Surface Hierarchy & Nesting
To move beyond the "flat" look, we utilize a hierarchy of nested surfaces rather than structural lines.
*   **Surface (Base):** `#131313` (Dark) / `#FFFFFF` (Light). This is your canvas.
*   **Surface-Container-Low:** Use for large structural blocks (e.g., sidebars).
*   **Surface-Container-High:** Use for interactive elements and cards.
*   **Surface-Container-Highest:** Reserved for floating elements or "active" states.

### The "No-Line" Rule
**Explicit Instruction:** Do not use `1px solid` borders to define sections. Layout boundaries must be established through background color shifts. For example, a code block (`surface-container-lowest`) should sit directly on the `surface` background, defined only by its tonal shift.

### The "Glass & Gradient" Rule
To elevate the "Modern Terminal" aesthetic, CTAs and hero elements should utilize a subtle gradient transitioning from `primary` (#4edea3) to `primary_container` (#10b981). Floating cards must use **Glassmorphism**: a semi-transparent `surface_container` with a `backdrop-blur` of 12px–20px.

---

## 3. Typography
We utilize a high-contrast pairing to balance technical utility with editorial elegance.

*   **Display & Headlines (Space Grotesk):** This font provides a "Tech-Grotesque" feel. Use `display-lg` (3.5rem) for main landing titles to create an authoritative, editorial impact.
*   **Body & Titles (Inter):** For the primary reading experience, Inter provides maximum legibility. 
    *   *Note:* While the user requested JetBrains Mono for titles, we have optimized the hierarchy: Use **JetBrains Mono** specifically for `label-md` and `label-sm` (the "Command" tags) and inline code to maintain the developer soul without sacrificing the readability of large headlines.
*   **The Hierarchy Goal:** Headlines should feel architectural; body text should feel transparent; labels should feel like code.

---

## 4. Elevation & Depth

### The Layering Principle
Depth is achieved by "stacking" surface tiers. To create a lift effect, place a `surface-container-lowest` card on a `surface-container-low` section. This creates a soft, natural transition that mimics physical depth without the clutter of shadows.

### Ambient Glow (The Signature Micro-interaction)
Instead of traditional drop shadows, interactive elements (cards, buttons) utilize an **Ambient Glow** on hover:
*   **Effect:** A 15px-30px blurred outer glow using the `primary` color at 15% opacity.
*   **Logic:** This mimics the light emission of a high-end CRT or OLED terminal screen.

### The "Ghost Border" Fallback
If a boundary is required for accessibility, use a **Ghost Border**.
*   **Token:** `outline_variant` at 15% opacity.
*   **Constraint:** Never use 100% opaque, high-contrast borders for containment.

---

## 5. Components

### Buttons & Tags (Command Inputs)
*   **Primary Button:** Background `primary`, text `on_primary`. Corner radius: `md` (0.375rem). No border.
*   **Command Tags:** These should look like terminal flags (e.g., `--version`). Use `surface-container-highest`, `label-md` typography (Monospaced), and a `sm` (0.125rem) radius.
*   **Interaction:** On hover, the text should slightly shift +2px to the right to simulate a terminal cursor movement.

### Cards (The Glass Module)
*   **Styling:** Background: `surface_variant` at 60% opacity.
*   **Effect:** `backdrop-filter: blur(10px)`. 
*   **Border:** A "Ghost Border" on the top and left edges only to simulate a light source.
*   **Spacing:** Use `xl` (0.75rem) internal padding to provide "editorial" breathing room.

### Sidebar & Navigation
*   **Structure:** No vertical divider line. Use a `surface-container-low` background color for the entire sidebar column.
*   **List Items:** Clean, monospaced text. Leading elements should be simple functional icons (e.g., `> `, `~ `).
*   **Active State:** A subtle `primary` glow behind the text, rather than a bold background color change.

### Input Fields
*   **Styling:** `surface-container-lowest` background. 
*   **Focus State:** The border transitions from "Ghost" to a solid `primary` glow. The cursor should be a solid block (blinking) to maintain the terminal aesthetic.

---

## 6. Do's and Don'ts

### Do:
*   **Use Asymmetry:** Place content off-center or use wide margins to create a custom, high-end feel.
*   **Leverage Monospace for Metadata:** Use monospaced fonts for dates, tags, and "technical" data points.
*   **Embrace Negative Space:** Let the `surface` color breathe. High-end design is defined by what you leave out.

### Don't:
*   **Don't use Divider Lines:** If you feel the need for a line, use a 16px white-space gap instead.
*   **Don't use Standard Shadows:** Avoid "drop shadows" that look like they belong in a 2014 office suite. Use tonal shifts or ambient glows.
*   **Don't Over-round:** Keep the `roundedness` to `DEFAULT` (0.25rem) or `md` (0.375rem). Anything more feels too "bubbly" and loses the technical edge.
*   **Don't use pure black/white for text:** Use `on_surface_variant` for secondary text to maintain a soft, professional contrast.