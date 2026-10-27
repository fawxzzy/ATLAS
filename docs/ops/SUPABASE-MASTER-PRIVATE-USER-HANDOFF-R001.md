Quick summary: This uninstalled source candidate integrates an in-memory, capture-excluded recovery-code handoff with the recovery bridge. Tests use public vectors only; the bridge's top-level live action remains disabled.

# Private recovery-code handoff source R001

Status: `SOURCE_ONLY; LIVE_HANDOFF_HELD`  
Owner: `platform.supabase-migration`  
Packet: `PLATFORM-DOD20-HANDOFF-BRIDGE-INTEGRATION-SOURCE-R001-20261026`

## Contract and boundary

DOD-20 requires a recovery factor held by Zac outside the current Windows profile, the archive vault, Google Drive, ATLAS, and chat. This candidate reuses the reviewed PR #224 bridge and the settled handoff prototype. It implements their missing internal handoff seam in five isolated source files. It does not alter PR #224, install the candidate, or establish live custody. The bridge still rejects top-level `SealLive` before marker or vault access.

The library function `Invoke-PrivateRecoveryCodeHandoff -RecoveryCode <in-process byte[]> -Interactive` requires exactly 32 bytes and explicit interaction opt-in. It owns and clears a clone of the caller's buffer on confirmation, cancellation, or exception. The caller retains ownership of its original buffer. `Show-PrivateRecoveryCodeDialog` closes the display before masked re-entry. The host must report Windows 10 build 19041 or newer; both windows require a successful `WDA_EXCLUDEFROMCAPTURE` call and exact `GetWindowDisplayAffinity` readback before displaying the value or enabling entry. Cancellation or an affinity failure yields a negative result. Entry comparison uses constant-time byte equality. The function returns a Boolean only; it does not generate a code, read a key, create a capsule, use a clipboard, or persist the value.

The synthetic entry point remains `Invoke-SyntheticPrivateRecoveryCodeHandoff -Interactive`. Its wrapper rejects every vector except the fixed public bytes 0 through 31. This restriction belongs to the rehearsal wrapper, rather than substituting fixture-only behavior for the real in-memory primitive. Automated tests mock the display using public vectors; they do not open a GUI.

`Confirm-OfflineCodeHandoff` requires explicit interaction and a 32-byte buffer. It reads the companion handoff source once, rejects reparse paths or hash drift, and executes those same pinned public source bytes. It accepts exactly one Boolean result. Cancellation, unexpected pipeline output, or a display fault stops before the bridge can read the protected descriptor/key or write a capsule. The dormant bridge caller clears its original recovery-code buffer in its existing `finally` block. Dot-sourcing or invoking these functions is not an authority boundary: a future installed action wrapper must independently prove the exact action grant, both complete source identities, one-use marker/intent, and current preimages before any live invocation.

The later admitted action must pass a generated code as in-process bytes from the reviewed bridge. It must never pass that code through Codex, a shell command argument, transcript, log, file, environment variable, provider connector, or repository. The code must be shown only to Zac in the local desktop session; no automation may inspect or capture that window. A successful same-host re-entry proves only that the human copied the code once. Independent custody requires the human to retain it offline and a fresh-host restore drill using the separately held encrypted capsule and archive.

## Future action gates

1. Independently review this source, the actual Windows display-affinity behavior, PR #224 integration, no-output property, and negative paths on the target host. A source review or synthetic test does not validate a live handoff.
2. Obtain a separate canonical owner packet, exclusive writer reservation, exact current preimages, one-use intent and effect-specific authority for any DPAPI key read, capsule creation, upload or external-provider operation. Keep existing R012 and off-host archive effects settled.
3. Verify exact private Drive account/folder/sharing/cost, preserve the current DPAPI key and accepted archive, and reconcile uncertain upload state before another attempt.
4. Require Zac to retain the offline factor outside the listed failure domains. Prove fresh-host recovery with wrong-code rejection, exact capsule/archive hashes, and the existing restore parity; only that later receipt can support DOD-20 acceptance.

## Risk and rollback

Windows display affinity limits supported screen capture; it is not a promise against cameras, accessibility tools, compromised desktops, or memory inspection. Microsoft documents that `WDA_EXCLUDEFROMCAPTURE` was introduced in Windows 10 version 2004 and may behave as `WDA_MONITOR` on older hosts; the build and exact readback gates reject that downgrade. See [SetWindowDisplayAffinity](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowdisplayaffinity). Display and entry strings are immutable .NET strings and cannot be reliably erased from managed memory; clearing controls and byte buffers does not prove their erasure. These risks require independent security review and a trusted local session before live action. This source packet has no live value, provider call, root install, Git publication, scheduler write, or merge. Its rollback is abandonment of the five isolated unstaged files under the existing custody rules, preserving the dirty root, source receipts and immutable parent.

Verification covers fixed public vectors, wrong/malformed entry, explicit opt-in, buffer ownership/cleanup, simulated display-affinity faults, companion hash drift, rejected pipeline output, cancellation before capsule output, and the retained top-level `SealLive` rejection. Temporary integration fixtures replace only the public-vector display and bind their own source hash; candidate source is not changed by tests. Actual GUI behavior, real-window affinity readback, private code handling and independent fresh-host custody are `NOT_RUN` in this source packet.
