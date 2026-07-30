# 00 Main — historical compatibility only

logical_role: atlas.main

This fragment preserves the former `atlas.main` contract as immutable history.
It is not an active standing-role prompt and must never be used to bind,
recreate, activate, schedule, wake, or target a Main task. Existing receipts and
legacy envelopes remain readable without converting them into current authority.

Historical behavior included dependency ordering, Inbox consumption, and receipt
acceptance. Those statements are not current authority. Current workflow source
assigns exact-state reconciliation to `atlas.workflow-operations`, source
contracts to `atlas.workflow-architect`, independent review to
`atlas.release-control-plane`, genuine human authority to `manual.messages`,
and normal execution plus owner returns to exact owner lanes.

Stale Main-targeted events are rejected or durably reclassified. No recovery,
restart, selector, or compatibility reader may translate this historical
fragment into a current runtime binding or execution target.

Rename, archive, source deletion, runtime cutover, and compatibility-ledger
retirement remain separately gated lifecycle actions.
