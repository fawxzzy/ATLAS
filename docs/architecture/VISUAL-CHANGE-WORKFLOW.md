# Pass 2.5 Visual Change Workflow

Goal
- Use `/settings` App Theme as the first runtime proof harness for the Pass 2 surface map.

Workflow
1. Open `/settings`.
2. Expand `App Theme`.
3. Apply `Test Theme`.
4. Capture before/after on representative routes.
5. Record each route family as `passed`, `failed`, or `blocked`.
6. Classify misses as:
   - token gap
   - intentional local exception
   - unmapped surface
   - component-specific styling debt

Current local evidence
- Public auth/install family:
  - Passed with screenshot evidence in `tmp/pass-2-5-screenshots/`
- Protected app family:
  - Blocked by auth redirect during automated capture

Rule
- Theme controls must mutate semantic UI groups, not individual route-local components.

Failure mode
- If a setting only changes the current screen, the harness is not validating the surface graph.

Failure mode
- If protected routes cannot be entered during capture, do not mark the family as passed from code inspection alone.
