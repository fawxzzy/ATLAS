# Pass 2.5 Surface Token Map

Implemented semantic controls
- Primary action color
  - Expected family: primary buttons, positive dock actions, accent-led CTA surfaces
- Destructive action color
  - Expected family: delete, discard, destructive confirmation, destructive pills/badges
- Surface/card color
  - Expected family: auth cards, install cards, shared panels, glass-backed cards
- Button radius
  - Expected family: `AppButton`, action chrome, bottom dock buttons
- Card radius
  - Expected family: `AppPanel`, `SurfaceCard`, `ExerciseCard`, `Glass` card shells, labeled editor shells

Current bridge status
- Strong color bridge:
  - Most shared color tokens already resolve through CSS variables.
- Partial radius bridge:
  - Shared card/button shells now read from runtime variables in the minimal harness path.
  - Some generated class names still embed fixed radius values from the frozen design-system pack.

Confirmed families
- Public auth/install family mutates through shared semantic tokens.
- Destructive family now has an explicit preferred contract:
  - darker shared surface
  - red border/text emphasis
  - shared behavior across `bottom-action`, `action-chrome`, and destructive badge/pill primitives

Unconfirmed families
- Settings, today, routines, edit-day, session, history, history-exercises remain unconfirmed visually because protected capture auth currently redirects to `/login`.

Known gap
- `fitnessDesignPrimitiveClassNames` still contains fixed radius literals for part of the compiled design-system surface map.
- Protected-route capture remains more fragile than the token map itself; route proof can fail even when the semantic lane change is correct.
