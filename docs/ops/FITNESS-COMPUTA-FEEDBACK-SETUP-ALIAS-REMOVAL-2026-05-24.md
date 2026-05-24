# Fitness Computa Feedback Setup Alias Removal

Date: 2026-05-24
Lane: Discord OS / command-surface cleanup
Status: complete

## Scope
- remove the legacy `computa feedback setup` alias
- keep `computa setup feedback` as the only approved feedback-setup phrase
- align the public and owner Computa command cards in Discord with the deployed command contract

## What Changed
- Fitness command parsing no longer accepts `computa feedback setup`
- Fitness docs and tests now describe only `computa setup feedback`
- the live `Computa` card in `#main` was patched in place:
  - message id: `1508161587012177960`
- the live `Computa Owner` card in `#main` was patched in place:
  - message id: `1508143826764828725`

## Resulting Public Command Copy
- `computa`
- `computa setup feedback`
- `computa setup music sesh`

Owner card retains the same owner-only commands as before, but no longer shows the removed alias.

## Why
The alias set had drifted:
- code and tests already removed the old phrase
- the visible Discord cards still showed it

That left operator truth split between the deployed parser and the public command reference. This package collapses that drift back to one phrase.

## Verification
- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/interactions-route.test.ts`
- `node --test scripts/discord-feedback-gateway-worker.test.mjs`
- `npm run verify`
- live Discord message fetch confirmed both cards no longer include `computa feedback setup`

## Rules Reinforced
- command aliases must be reflected in the live command-reference posts
- visible Discord command cards are operator truth surfaces and must not lag behind deployed parser changes
- prefer one approved setup phrase over multiple overlapping aliases when the extra alias adds no real value
