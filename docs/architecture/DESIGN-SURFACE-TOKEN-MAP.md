# Pass 2.5 Surface Token Map

Current contract
- App Theme is not a raw color picker.
- App Theme is the runtime proof harness for the Fitness surface map.
- Controls must mutate semantic UI families, not route-local one-off colors.

Implemented semantic lanes
- Primary action:
  - primary CTA buttons
  - positive dock actions
  - primary action chrome
- Secondary action:
  - secondary dock buttons
  - toggle-style action chrome
  - yellow/default secondary button lane
- Accent / Divider:
  - signature pipes and dots
  - thin separators
  - history divider bars
  - weekday accent text
  - thin image/card separator lines
  - decorative accent strips
- Surface / Card:
  - shared panels
  - glass-backed cards
  - card shells
  - settings/install/auth surfaces
- Success / Complete:
  - completed exercise/session text
  - completed shells and state strips
  - success badges/messages
- Selection / Active:
  - selected exercise cards
  - selected picker rails/pills
  - active badges and selection highlights
- Loader / Scan:
  - route loading scan animation
  - loading glow energy line
- Warning:
  - rest-day chips
  - warning cards
  - yellow attention states
- Destructive:
  - still treated as a shared global family, separate from the App Theme lanes above

Mapped V1.1 families
- `/today`
  - weekday title accents
  - rest-day header subtitle suppression
  - today-state badges
- `/session/[id]`
  - completed row text/shells
  - stats strips
  - logger and disclosure success states
- `/routines/[id]/edit/day/[dayId]`
  - selected exercise rows
  - add-exercise selection rail
  - goal dock accent border
- `/history` and `/history/exercises`
  - compact card image separator lines
  - detailed card strips
  - PR labels
  - metric divider bars

Bridge status
- Strong runtime bridge:
  - color lanes above now resolve through CSS variables across shared components and design-system utility classes.
- Partial radius bridge:
  - card/button shells read runtime variables in the main shared path.
  - some generated design-system classes still hold fixed radius literals.

Intentional constraint
- Do not add one giant raw "green" setting.
- Green/yellow surfaces are split by meaning:
  - accent/divider
  - success/complete
  - selection/active
  - loader/scan
  - warning

Open proof gap
- Protected-route capture still needs fresh evidence after the V1.1 lane expansion.
- If a surface does not mutate in capture, classify it as one of:
  - token gap
  - intentional local exception
  - unmapped surface
  - component-specific styling debt
