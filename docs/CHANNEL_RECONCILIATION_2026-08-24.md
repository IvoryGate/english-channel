# Channel Inventory Reconciliation — 2026-08-24

## Outcome

The reviewed local control-plane database at
`H:/english-channel/workspace/channel/channel.sqlite` is on schema version 4;
the remote reconciliation tables were introduced in version 3 and the later
release-reservation migration does not change the captured evidence.
Every item in the immutable public YouTube RSS capture resolves to one local
canonical publication:

| Check | Result |
| --- | ---: |
| public remote items in capture | 15 |
| canonical local publications | 15 |
| matched remote IDs | 15 |
| remote-only IDs | 0 |
| local publications outside this capture | 0 |
| title disagreements | 0 |
| unresolved identity collisions | 0 |

This is a complete reconciliation of the **captured public RSS window**, not a
claim of complete YouTube Studio inventory. Private and unlisted videos are
excluded, and the feed may omit older public videos beyond its recent-item
window.

## Remote Evidence Boundary

- Public name: `English Listening Room`
- Public handle: `@english-listening-room`
- YouTube channel ID: `UC9QpAkVpv8l1ZQ3X4UtU37A`
- Capture source: public YouTube channel RSS
- Capture scope: `public_rss_recent_max_15_no_private_unlisted`
- Captured at: `2026-08-24T03:09:11Z`
- Immutable source:
  `H:/english-channel/workspace/channel/raw/youtube-public-rss-20260824T030911Z.xml`
- Source SHA-256:
  `59453fe6220fe285b4ead35c8cf15e71c420fb430573ee36f5da38ae82bc75d5`
- Database capture ID:
  `capture:c62e4ef8-41cf-4b45-a9ae-802706701516`

Public oEmbed responses independently confirmed the channel author and titles
for the three video IDs already present in the Dialogue publication ledger.
The signed-in browser path could not be inspected because the app browser
runtime was denied while resolving the migrated `C:/Users/27370/.codex`
junction to `D:/CodexData/.codex`. No browser page was reached and no remote
state was modified. This environment limitation is why private, unlisted,
playlist, and older public inventory remain outside the verified boundary.

## Local Evidence Imported

All imports were read-only with respect to their source files. Hashes were
unchanged before and after import.

| Source | Accepted | SHA-256 |
| --- | ---: | --- |
| `workspace/channel_ops/publications.json` | 3 Dialogue publications | `ae37012c4e05067e74eb8984719cd478c39de98dd6607370e198497757cc57e8` |
| `workspace/channel/operations/recovered-dialogue-publications-2026-08-24.json` | 8 recovered Dialogue publications | `8fe21b553c0040cda9cf64ceff1a1decb28f3303a84af7cce1f746a3af558d8f` |
| `workspace/channel/operations/recovered-shorts-publications-2026-08-24.json` | 4 recovered Shorts publications | `70a874631dc84e323e20d9f9142eff1c7ae756558c5597e6779dc82b337ab7fc` |

The expected legacy Shorts ledger at
`workspace/shorts/operations/publication_ledger.json` did not exist, and the
entire `workspace/shorts/` runtime directory was absent. No Classic Listening
operations ledger existed under `workspace/classics/operations/`. These
absences were recorded; no ledger, media fingerprint, or publication was
invented for content without evidence.

## Dialogue Recovery

Eight public long-form videos missing from the surviving publication ledger
were mapped to canonical episodes using exact title equality, the local title
record, and the fingerprint of the existing canonical MP4. The recovery ledger
retains all evidence.

| Canonical item | YouTube ID | MP4 SHA-256 |
| --- | --- | --- |
| `series_b/episode_016` | `hO3iJhJtodQ` | `8111c1fd31c573455874915fdbeab948a040dcc4212facc3b6bea8a085135559` |
| `series_c/episode_016` | `ui1kF7ttwfM` | `3a63ee6619631f719dadefdfb4cc8b7ae139cd4b7c5486e82315ed3dd6097051` |
| `series_a/episode_017` | `0_kAYcUX9vA` | `d1d99074be7f93ba61190eafa0ffd33e8eb891554afdd485a4a103469db3bf6e` |
| `series_b/episode_017` | `7-RbFK6Yyyg` | `dc7efb433dedc7c8e61915c5e16ff1ac5bd95179863afa1f77ac204f48a625c5` |
| `series_c/episode_017` | `LMQUCFp05gU` | `14339ca7009a5b37eda739528cf2ce14f6280acedc3e04360d1b5b69d51b925b` |
| `series_a/episode_018` | `GOem5kPy454` | `20066fb6cad19b7dc726f0722b19ce30f24afe207f4fe9bc63a2aa5e89383705` |
| `series_b/episode_018` | `tGfTQk42w_4` | `b93ed65709dbf57a5d6b1b845503c42197226d4cd5c22aaabc0f3c1e9a61d885` |
| `series_c/episode_018` | `NyEIE2aVy5A` | `be75dbb96704da768906839ab37855e251f050d54104c556201eb7c44eb92d47` |

## Shorts Recovery

The four public Shorts map exactly by title to stable IDs in the tracked
`configs/shorts/pilot-2026-08.json` portfolio (SHA-256
`7862d3f9c13497a1ed20b684d1d5e8d5d8073d61d2d8d3a82d3dbe7a76a1edf0`).
Because their historical runtime artifacts are absent, the recovery ledger
does not claim media fingerprints.

| Canonical item | YouTube ID | Title |
| --- | --- | --- |
| `shorts_main/elr-s-001` | `88mr41WwBT4` | Can You Understand This Simple Morning Story? |
| `shorts_main/elr-s-002` | `LxVsIX80N34` | A Tiny Mistake Changed His Whole Morning |
| `shorts_main/elr-s-003` | `toQIFDOsSS0` | What Did She Forget at the Supermarket? |
| `shorts_main/elr-s-004` | `gHAQBuOYX-g` | The Bus Driver Remembered Her Name |

## Operator Conclusion

The control plane may use the 15 mapped publications as the reviewed baseline
for this public capture. It must continue to report
`completeRemoteInventory: false` until a credentialed YouTube provider,
export, or working signed-in Studio inspection captures private, unlisted,
older public, playlist, and visibility state. Reconciliation grants no upload,
edit, schedule, visibility, playlist, or deletion authority.
