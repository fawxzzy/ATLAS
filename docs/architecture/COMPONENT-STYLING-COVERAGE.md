# Pass 2.5 Component Styling Coverage

Covered by the harness now
- `src/components/ui/AppThemeBootstrap.tsx`
- `src/lib/app-theme.ts`
- `src/components/settings/AppThemeSettings.tsx`
- `src/components/settings/SettingsAccordionClient.tsx`
- `src/components/ui/app/AppPanel.tsx`
- `src/components/layout/bottomActionIntents.ts`
- `src/components/ui/LabeledEditorField.tsx`
- `src/components/ui/AppButton.tsx`
- `src/components/ui/Pill.tsx`
- `src/components/ui/app/designSystem.ts`

Confirmed semantic mutation coverage
- Primary action lane:
  - `BottomDockButton`
  - public auth/install CTA surfaces
- Destructive action lane:
  - `BottomDockButton` danger
  - `AppButton` destructive / `action-chrome` danger
  - destructive badges and pill-style chips
- Surface/card lane:
  - auth/install cards
  - `AppPanel`
  - `Glass` consumers that already read `--card-radius` or shared surface vars
- Radius lane:
  - `AppPanel`
  - `BottomDockButton`
  - `LabeledEditorField`
  - `ExerciseCard` and `HistorySessionCard` already use `--card-radius`

Remaining styling debt
- Some compiled design-system classes still use fixed rounded values and will not fully follow the card radius lane until they are converted to semantic runtime variables.

Coverage note
- Public-route proof is complete enough to verify bootstrap + token application.
- Protected-route proof is incomplete until the capture auth path stops redirecting to `/login`.
- Live current-session proof is now available through the mobile regression route, but the environment remains sensitive to stale `:3000` listeners and stale `.next` state.
