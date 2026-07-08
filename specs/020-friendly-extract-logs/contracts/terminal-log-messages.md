# Contract: Extraction Terminal Log Messages

This contract defines the user-facing expectations for extraction terminal logs.

## Scope

- Inventory extraction terminal messages
- Sales extraction terminal messages
- Shared download helper messages used by extraction flows

## Message Requirements

Each changed message must:

- Explain the current phase in user-facing language.
- Avoid raw implementation jargon where a simple operational phrase exists.
- Avoid secrets, credentials, cookies, raw selectors, and unnecessary stack traces.
- Preserve the original meaning and ordering of the automation step.
- Stay short enough for terminal display.

## Examples

| Old style | Preferred style |
| --- | --- |
| `Login successful. Session established.` | `Login berhasil. Bot sedang membuka halaman distributor.` |
| `Intercepting download link...` | `Menunggu file dari Newspage. Proses ini bisa beberapa menit.` |
| `ZIP target identified: ...` | `File data ditemukan di dalam ZIP dan siap dibaca.` |
| `Browser closed. Ready for download.` | `Extract selesai. File siap diunduh.` |

## Non-Goals

- Do not change terminal styling.
- Do not change Playwright waits, selectors, clicks, downloads, or file parsing.
- Do not change Supabase log records or dashboard activity logic.
