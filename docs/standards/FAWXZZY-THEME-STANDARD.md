# Fawxzzy Theme Standard

## Status
Canonical ATLAS-wide visual scheme for Fawxzzy applications.

## Canonical theme pack
Tracked source:
- `docs/standards/fawxzzy-sage-theme/`

Mirrored prebuilt export:
- `packages/prebuilt/fawxzzy-sage-theme/`

Files:
- `fawxzzy-sage-theme.css`
- `fawxzzy-sage-theme.ts`
- `fawxzzy-sage-mapping.md`
- `fawxzzy-sage-preview.html`

## Visual direction
- Backgrounds: dark forest black-green, not graphite gray and not olive wash
- Text: dusty sage instead of white-heavy neutrals
- Highlights: light sage used for buttons, focus, and premium glow
- Motion: slow atmospheric wisps, blur fields, floating particles, and a soft pulse
- Material split: brown and earth may exist only as a separate shadow and surface undertone, never as a yellow tint over the whole app

Core anchors:
- App background: `#070D08`
- Dusty sage text: `#8BA888`
- Light sage highlight and button: `#A3BCAC`

## Canonical token set
These roles are the shared contract.

Base roles:
- `--bg-core: #070D08`
- `--bg-elevated: #0A100B`
- `--bg-panel: #0E150F`
- `--bg-panel-2: #111912`

Text roles:
- `--text-primary: #8BA888`
- `--text-secondary: #A3BCAC`
- `--text-muted: #637762`
- `--text-strong: #D6E3D2`

Accent roles:
- `--accent: #A3BCAC`
- `--accent-soft: #B7CBB9`
- `--accent-strong: #6F866D`
- `--accent-pressed: #8FA792`

Structure roles:
- `--border-soft: #4A604C`
- `--border-strong: #6F866D`
- `--card-bg: #0A100B`
- `--box-bg: #0E150F`
- `--modal-bg: #111912`
- `--app-bg: #070D08`

Material undertones:
- `--earth: #31291F`
- `--earth-soft: #564838`

## Semantic fallback mapping
For legacy roles that do not map cleanly, keep them inside the same family.

- Info and old blue: `#7F9D98`
- Success and old green: `#8BA888`
- Warning and old orange: `#948D6F`
- Danger and old red: `#967B7B`
- Purple replacement: `#879786`

## Motion layer
The ambient layer is part of the standard, not an app-specific flourish.

Required qualities:
- dark radial forest base
- blurred sage and emerald glow blobs
- slow diagonal wisps
- floating particles
- optional central breathing pulse
- reduced-motion fallback that disables or heavily softens animation

## Adoption rules
1. Import the canonical CSS theme or consume the TypeScript object.
2. Apply `app-theme-sage` at the root shell.
3. Map existing semantic roles into the canonical token set instead of hardcoding app-local variations.
4. Keep the ambient motion subtle enough that cards, forms, and metrics remain readable.
5. Do not mix in old saturated blues, purples, oranges, or reds without remapping them first.

## Current reference adopter
- FawxzzyWeb (`trove` at `repos/trove`)

## Rollout guidance
Adopt per repo with small, targeted visual changes. Reuse the shared palette and ambient motion layer before inventing repo-specific theme forks.
