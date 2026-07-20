# ELR YouTube Playlists

Channel: **English Listening Room** (`UC9QpAkVpv8l1ZQ3X4UtU37A`)

## Playlist map

| Playlist | Series | Visibility | Purpose |
| --- | --- | --- | --- |
| Pride & Prejudice · Audiobook | Classic | Public | Existing traffic base; drama-hook chapter titles |
| First Steps · Easy English | B | Public | A2-B1 entry ladder |
| Daily Talk · English Conversations | A | Public | B1-B2 growth engine |
| Polished English · Real Talk | C | Public | B2-C1 retention / depth |

## Creation checklist (Studio)

1. YouTube Studio → Content → Playlists → New playlist
2. Use exact public names above (adjust only if Studio character limit forces a trim)
3. Description template per series (see bibles in `docs/shows/series_*/bible.md`)
4. Add episodes only from the matching `workspace/shows/series_*/` archive
5. Pin **Daily Talk** or the best-performing series on channel Home after 6+ episodes

## Episode ordering

- Sort by **date added** (newest first) for podcast series during growth phase
- Audiobook playlist: chapter order via title suffix `| Ch. NN` or internal meta

## Cross-linking

- End-screen default: suggest **next step up** (B→A, A→C) or **Classic** for relaxation
- Description footer: link all four playlists once each series has ≥3 episodes

## Automation note

Playlist creation is manual in YouTube Studio for now. When browser automation is authorized, use `youtube-browser-automation` skill; store playlist IDs in `workspace/shows/playlists.json` after creation.
