# ican-health-sync

Turn a Sibionics / iCan CGM `.xls` export into JSON that an Apple Shortcut can
write straight into Apple Health.

Share the export from the CGM app, tap the Shortcut, done. Readings land in
Health with their real measurement times.

## "I read that this is impossible"

Search results and forum answers commonly say the iCan / Sinocare CGM app has
no HealthKit support and no export, and that the only route is an Android phone
running xDrip+ or Juggluco feeding Nightscout, plus a native iOS app to write
HealthKit.

That is out of date, at least for the Thai-language iCan app on i3/i6:

- **The app does export.** Its share button hands over an `.xls` file.
- **You do not need Android, xDrip+, Nightscout, or Xcode.**
- **You do not need to write a native app.** Apple's own Shortcuts app is
  native and can write HealthKit — `Log Health Sample` is a built-in action.

The only genuinely missing piece is that Shortcuts cannot read `.xls`. That is
the single gap this project fills. Everything else is stock iOS.

Built and verified end to end on an iPhone: readings land in Apple Health with
their real measurement times, not the import time.

## Install

On the iPhone, download the shortcut for the unit your Health app should
record, open it from Downloads, and add it:

- **mg/dL** (most Thai users): [iCan-to-Health-mg-dL.shortcut](https://github.com/Nice0w0/ican-health-sync/releases/latest/download/iCan-to-Health-mg-dL.shortcut)
- **mmol/L**: [iCan-to-Health-mmol-L.shortcut](https://github.com/Nice0w0/ican-health-sync/releases/latest/download/iCan-to-Health-mmol-L.shortcut)

These always fetch the [latest release](https://github.com/Nice0w0/ican-health-sync/releases/latest).
Shortcuts names it after the file; rename it to anything you like. Then in the
iCan app share / export → pick the shortcut. The first run
asks for Health access. No account, no token, nothing to configure.

With no Blood Glucose in Health from the last 7 days, the first run imports the
whole export, which can take a few minutes. After that only readings newer than
the latest one in Health come in.

## Why this exists

Apple Health can only be written from iOS, and the Shortcuts app cannot read
`.xls` — the export is a real OLE2/BIFF8 binary, not a spreadsheet Shortcuts
understands. Something has to do the conversion. This is that something: a
small HTTP endpoint at `https://ican-health-sync.vercel.app/api/convert`, which
the shortcut calls.

## What happens to your data

The shortcut sends your export to that endpoint, which runs on Vercel. It
parses the upload, returns the readings, and forgets: no database, no
accounts, and the code logs no readings. The export does pass through the
server, though — if you would rather it never left your own machine, run your
own copy (below) and point the shortcut at it.

De-duplication is handled by **Apple Health itself**: the Shortcut asks Health
for its newest Blood Glucose sample and sends that timestamp as `?since=`, so
only genuinely new readings come back. HealthKit has no upsert — `Log Health
Sample` only ever appends — so this filtering has to happen before logging.

## Run your own copy (optional)

### Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Nice0w0/ican-health-sync)

Click, connect your GitHub account, done. You get an HTTPS URL like
`https://your-project.vercel.app`, and your endpoint is
`https://your-project.vercel.app/api/convert`. Set `CGM_TZ_OFFSET` if you are
not in UTC+7, and `CGM_TOKEN` if only you should be able to use it.

### Self-hosted

No dependencies at all, so plain Python works:

```bash
git clone https://github.com/Nice0w0/ican-health-sync.git && cd ican-health-sync
python3 server.py        # http://127.0.0.1:8000/api/convert
```

Or with Docker:

```bash
cp .env.example .env
docker compose up -d --build
```

The container binds to `127.0.0.1` only. Put a TLS proxy in front — glucose
readings should not cross the internet in plaintext. With Caddy:

```
cgm.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

### Configuration

| Variable | Default | Meaning |
|---|---|---|
| `CGM_TOKEN` | *(unset)* | If set, requests must carry `X-Token` or `?token=`. Leave it unset for an instance anyone may use, as the public one is. |
| `CGM_TZ_OFFSET` | `7` | **The wearer's** UTC offset in hours. The export contains no timezone, so this is how local reading times are reconstructed — a server running in UTC still produces correct times. |

## API

### `POST /convert`

Body: the `.xls`, either as a multipart file field (any name) or as the raw
request body.

| Query | Meaning |
|---|---|
| `since` | ISO 8601 or a unix timestamp. Returns only readings **strictly newer**. A value without a timezone is read in `CGM_TZ_OFFSET`. |
| `every` | Thin to at most one reading per this many minutes. See [Speed](#speed). |
| `unit` | `mg/dL` (default) or `mmol/L`. Values are converted from whatever the export declares. |
| `limit` | At most this many readings, newest first. Useful for a first run. |
| `verbose` | `1` also returns `date_iso` and `unit` per reading. Off by default — the Shortcut does not read them and it doubles the payload. |
| `token` | Alternative to the `X-Token` header, for clients that cannot set headers easily. Only needed when `CGM_TOKEN` is set. |
| `on_error` | `empty` turns any error into `200 []`, with the reason in `X-Error`. The published shortcut sets it — see below. |

Returns a JSON array, oldest first — only what the Shortcut logs:

```json
[{"value": 72, "date_text": "Sep 01, 2026 at 07:46 PM"}]
```

`date_text` exists because Shortcuts' date detector parses that exact shape
reliably — including on a non-English device. Feed *that* to **Get Dates from
Input**.

Filtering happens before formatting: rows Health already has are dropped before
any timestamp is rendered or any value converted.

Response headers `X-Readings-Total`, `X-Readings-Returned`, `X-Unit`,
`X-Source-Unit` and `X-Since` let a client report what happened without walking
the array. `X-Since` echoes the cursor the server actually parsed, which is the
quick way to tell *"nothing new"* from *"the cursor never arrived"* — an empty
array looks the same either way.

### Speed

Two different things can make a share slow, and they have different fixes.

**The import loop.** The Shortcut spends four on-device actions per reading. A
CGM samples every three minutes — ~480 readings a day — so a large catch-up
import really does take minutes. Normally it does not matter: `?since=` means a
routine share carries only the handful of readings taken since the last one.
`?every=N` is there for the catch-up case, returning one reading per N minutes
instead of all of them. It walks newest-first, so **the most recent reading is
always kept**. Off by default — every reading the CGM recorded is kept.

**The Health lookup.** Action 1 asks Health for its newest Blood Glucose sample.
Unbounded, that search grows with every import you have ever done, so the
Shortcut gets slower over time *even when only one reading is new*. The
generated Shortcut bounds it to the last 7 days (`--window`), which keeps the
cursor lookup constant. If a share ever takes far longer than the number of new
readings can explain, this is where to look — not the loop.

### Units

Older exports declare their unit in the value column header,
`ค่ากลูโคส (mg/dL)`. Exports since about late September 2026 say only
`ค่ากลูโคส`, so the unit is read off the values instead — but only when they
leave no doubt: whole numbers with one above 35 are mg/dL (no mmol/L reading
goes that high), decimals all at or below 35 are mmol/L, and anything else is
refused. Either way the service converts to whatever `?unit=` asks for — so the number returned always matches
the unit the Shortcut is configured to log.

This matters because Shortcuts' **Log Health Sample** takes its unit from a
fixed picker that cannot be driven by a variable. If the two disagree, Health
records a badly wrong number with no error: `7.2 mmol/L` written as
`7.2 mg/dL` reads as severe hypoglycaemia. Pinning both from one place is the
only way they cannot drift.

An unrecognised unit is rejected with `422` rather than assumed. Both English
and Thai spellings of mg/dL and mmol/L are understood.

Errors: `400` unreadable request, `401` bad token, `413` oversized,
`422` not a CGM export.

**Why the shortcut asks for `on_error=empty`.** Shortcuts does not treat a
`4xx` as a failure. It hands the error body on, Repeat with Each walks the
`{"error": ...}` dictionary, and Log Health Sample writes an empty value — a
glucose of **0**, stamped with the current time, that only the wearer can
delete. An empty array logs nothing. If a share imports nothing and you expected
readings, the reason is in the `X-Error` response header.

### `GET /healthz`

`{"ok": true}`.

## The Shortcut

The files under [`shortcut/`](shortcut/) point at the public instance with no
token, one per unit (see [Install](#install)). To build one for your own
deployment on macOS:

```bash
python3 build_shortcut.py \
  --url https://your-project.vercel.app/api/convert \
  --unit mg/dL -o mine.shortcut          # add --token X if you set CGM_TOKEN
shortcuts sign -m anyone -i mine.shortcut -o "iCan to Health.shortcut"
```

`--unit` pins the URL parameter and the Log Health Sample picker together so
they cannot disagree. `--every N` thins a big catch-up import; `--window DAYS`
sets how far back action 1 looks for its cursor.

> **Never publish a shortcut built with `--token`.** The token is embedded in
> its URL.

### What it does, in order

1. **Find Health Samples** — Blood Glucose in the last 7 days, newest first, limit 1 → the import cursor
2. **Get Dates from Input** → that sample's Start Date
3. **Format Date** — ISO 8601, so neither locale nor calendar can mangle it
4. **Get Contents of URL** — POST the shared `.xls`, with the cursor as `?since=`
5. **Get Dictionary from Input**
6. **Repeat with Each**
7. **Get Dictionary Value** — `value`
8. **Get Dictionary Value** — `date_text`
9. **Get Dates from Input**
10. **Log Health Sample** — Blood Glucose, value ← 7, date ← 9
11. **End Repeat**

Before the first real run, check that action 1 shows **Start Date is in the
last 7 days**, **Sort by Start Date, Latest First, Limit 1**. Without that the cursor is wrong and readings import
repeatedly — and Health has no way to overwrite a sample, so duplicates have to
be deleted by hand.

Then add `&limit=1` to the URL for one run and confirm in Health that the
sample carries the right value **and** the CGM's measurement time rather than
the import time. Remove it once both check out.

## The `.xls` reader

`xlsmini.py` is a standalone OLE2 + BIFF8 reader in the standard library only —
no `xlrd`, no `pandas`. It handles both the mini-stream (small exports) and the
regular FAT chain, and is verified cell-for-cell against `xlrd` on real
exports.

The subtle part is the shared string table spanning `CONTINUE` records, where
the encoding can flip between compressed and UTF-16 mid-string. Getting that
wrong does not crash — it shifts every subsequent string index, which would
attach a glucose value to the wrong timestamp. If you change the reader, diff
the full grid against `xlrd` on real files before trusting it.

## Limitations

- Written against Sibionics/iCan Thai-language exports: it locates the header
  row by its `เวลากลูโคส` column and parses times as `%H:%M,%m/%d/%Y`. Other
  exporters will need adjusting.
- The export has no timezone. The public instance reads it as UTC+7
  (`CGM_TZ_OFFSET`), which is right for the Thai app; wearers elsewhere should
  run their own copy with their own offset.
- Blood glucose only.
- A full day is ~480 readings and `Repeat with Each` is slow in Shortcuts, so
  import regularly rather than in one batch. `?every=N` thins a catch-up.

## Licence

MIT.
