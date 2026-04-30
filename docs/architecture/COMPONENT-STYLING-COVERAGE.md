# Pass 2.5 Component Styling Coverage

Harness foundation
- `repos/fawxzzy-fitness/src/components/ui/AppThemeBootstrap.tsx`
- `repos/fawxzzy-fitness/src/lib/app-theme.ts`
- `repos/fawxzzy-fitness/src/components/settings/AppThemeSettings.tsx`
- `repos/fawxzzy-fitness/src/app/globals.css`

Shared primitive path now covered
- `repos/fawxzzy-fitness/src/components/layout/bottomActionIntents.ts`
- `repos/fawxzzy-fitness/src/components/ui/AppButton.tsx`
- `repos/fawxzzy-fitness/src/components/ui/Pill.tsx`
- `repos/fawxzzy-fitness/src/components/ui/app/designSystem.ts`
- `repos/fawxzzy-fitness/src/components/ui/MetricItem.tsx`
- `repos/fawxzzy-fitness/src/components/ui/app/SignatureSeparator.tsx`

V1.1 semantic-lane consumers now bridged
- `repos/fawxzzy-fitness/src/components/ExerciseCard.tsx`
- `repos/fawxzzy-fitness/src/components/ExercisePicker.tsx`
- `repos/fawxzzy-fitness/src/components/SessionExerciseFocus.tsx`
- `repos/fawxzzy-fitness/src/app/today/TodayDayPicker.tsx`
- `repos/fawxzzy-fitness/src/app/today/TodayExerciseRows.tsx`
- `repos/fawxzzy-fitness/src/app/routines/RoutinesPageClient.tsx`
- `repos/fawxzzy-fitness/src/components/history/HistorySessionCard.tsx`
- `repos/fawxzzy-fitness/src/components/history/HistoryExerciseCard.tsx`
- `repos/fawxzzy-fitness/src/components/history/HistoryDetailExerciseCard.tsx`
- `repos/fawxzzy-fitness/src/components/RouteLoading.tsx`
- `repos/fawxzzy-fitness/src/components/stretch/StretchLibraryPanel.tsx`

Confirmed semantic mutation coverage
- Primary action lane:
  - dock/button CTA surfaces
- Secondary action lane:
  - toggle and secondary action surfaces
- Accent / Divider lane:
  - separators, pipes, dots, weekday accents, history dividers
- Surface / Card lane:
  - app panels, glass shells, exercise/history cards
- Success / Complete lane:
  - completed current-session surfaces
  - success badges/messages
- Selection / Active lane:
  - selected picker rails/pills
  - selected exercise states
- Loader / Scan lane:
  - route loading overlay
- Warning lane:
  - rest-day and warning cards/badges
- Destructive lane:
  - already normalized separately as shared destructive primitives

Remaining styling debt
- Some generated design-system classes still use fixed rounded values and do not fully follow the card radius lane.
- Protected-route proof still needs refreshed screenshots after the current semantic-lane expansion.
- If `:3000` is stale or owned by the wrong process, capture evidence is invalid even when the code is correct.

Coverage note
- Public-route proof is sufficient to verify bootstrap and token application.
- Protected-route proof is required to call the V1.1 surface family complete.
- Session/edit-day/history screens should be treated as high-value validation surfaces for every follow-up App Theme patch.
