# Sync iCan to Apple Health

Get glucose readings from an **iCan (i3, i6)** or **Sibionics / Sinocare** CGM
into **Apple Health** on iPhone, with a free iOS Shortcut. Share the export from
the iCan app, pick the shortcut, done — readings land in Health with their real
measurement times, and syncing again never duplicates them.

No Android, xDrip+, Juggluco, Nightscout or Xcode.

Tested end to end on an iPhone with exports from the Thai-language iCan app,
including the format it switched to in September 2026.

### **[Download → ican-health-sync.vercel.app](https://ican-health-sync.vercel.app)**

[ภาษาไทย](#ภาษาไทย) · [English](#english) · [How it works](#how-it-works) ·
[Troubleshooting](#troubleshooting) · [For developers](#for-developers)

---

## ภาษาไทย

ซิงก์ค่าน้ำตาลจากเครื่องวัดน้ำตาลต่อเนื่อง (CGM) iCan i3, i6 และ Sibionics
เข้าแอปสุขภาพบน iPhone ด้วยคำสั่งลัดฟรี ค่าเข้าพร้อมเวลาวัดจริง และไม่ซ้ำ
ทดสอบบน iPhone จริงแล้ว ทั้งไฟล์จากแอป iCan แบบเดิมและแบบใหม่หลังอัปเดตเดือนกันยายน 2026

### ติดตั้ง

1. เปิด **<https://ican-health-sync.vercel.app>** บน iPhone
2. กดดาวน์โหลดตามหน่วยที่ต้องการให้แอปสุขภาพบันทึก (คนไทยส่วนใหญ่ใช้ **mg/dL**)
3. เปิดไฟล์ที่ดาวน์โหลด แล้วกด **เพิ่มคำสั่งลัด**

ไม่ต้องสมัคร ไม่ต้องตั้งค่าอะไร

### วิธีใช้

1. ในแอป iCan กดส่งออก / แชร์ข้อมูล จะได้ไฟล์ `.xls`
2. ในเมนูแชร์ เลือก **Sync iCan to Apple Health**
3. ครั้งแรกระบบจะขอสิทธิ์เข้าถึงแอปสุขภาพ ให้กดอนุญาต
4. รอจนเสร็จ ค่าจะอยู่ในแอปสุขภาพ → น้ำตาลในเลือด

ครั้งแรกจะนำเข้าทั้งไฟล์ ถ้ามีหลายร้อยค่าอาจใช้เวลาหลายนาที
ครั้งต่อไปจะนำเข้าเฉพาะค่าที่ใหม่กว่าค่าล่าสุดในแอปสุขภาพ

### ถ้ามีปัญหา

- **กดแล้วไม่มีค่าใหม่เข้า** — ถ้าแอปสุขภาพมีค่าล่าสุดอยู่แล้ว ถือว่าปกติ
  แต่ถ้าไม่ใช่ แปลว่าอ่านไฟล์ไม่ได้ ให้[เปิด issue](https://github.com/Nice0w0/ican-to-apple-health/issues)
  พร้อมบอกรุ่นเครื่องและภาษาของแอป iCan
- **มีค่า 0 ในแอปสุขภาพ** — เกิดจากคำสั่งลัดเวอร์ชันก่อนตุลาคม 2026 ให้ลบคำสั่งลัดเก่า
  ติดตั้งใหม่จากเว็บ แล้วลบค่า 0 เอง (แอปสุขภาพ → น้ำตาลในเลือด → แสดงข้อมูลทั้งหมด → ปัดลบ)
- **ค่าซ้ำกัน** — เช็คว่าใช้คำสั่งลัดตัวเดียว และไม่ได้แก้ action แรกของคำสั่งลัด

### ข้อมูลของคุณ

ไฟล์ถูกส่งไปแปลงที่ server บน Vercel แล้วส่งค่ากลับมาทันที server ไม่มีฐานข้อมูล
ไม่มีบัญชีผู้ใช้ และไม่เก็บค่าน้ำตาลไว้ ค่าถูกบันทึกในแอปสุขภาพบน iPhone ของคุณเท่านั้น
ถ้าไม่อยากให้ไฟล์ผ่าน server ของคนอื่นเลย รันของตัวเองได้ ดู[สำหรับนักพัฒนา](#for-developers)

---

## English

### Install

1. Open **<https://ican-health-sync.vercel.app/en/>** on your iPhone.
2. Download the version for the unit Apple Health should record: **mg/dL** or
   **mmol/L**.
3. Open the downloaded file and tap **Add Shortcut**.

No account, no token, nothing to configure.

### Use

1. In the iCan app, export / share your data. You get an `.xls` file.
2. In the share sheet, pick **Sync iCan to Apple Health**.
3. The first time, allow access to Apple Health.
4. Readings appear in Health → Blood Glucose.

The first run imports the whole export, which takes a few minutes for hundreds
of readings. After that, only readings newer than the latest one in Health come
in.

### "I read that this is impossible"

Forum answers often say the iCan app has no HealthKit support and no export,
and that the only route is an Android phone running xDrip+ or Juggluco feeding
Nightscout, plus a native iOS app to write HealthKit.

That is out of date, at least for the Thai-language iCan app on i3/i6. The app's
share button exports an `.xls` file, and Apple's own Shortcuts app can write to
HealthKit with its built-in **Log Health Sample** action. The one missing piece
is that Shortcuts cannot read `.xls`. That is the gap this project fills;
everything else is stock iOS.

---

## How it works

```
iCan app ──share .xls──▶ Shortcut ──POST + cursor──▶ /api/convert
                            │                            │
                            │◀──── JSON readings ────────┘
                            ▼
                      Apple Health
```

1. The shortcut asks Apple Health for its newest Blood Glucose reading. That
   timestamp is the **cursor**.
2. It sends the `.xls` and the cursor to `/api/convert`.
3. The server parses the export and returns only readings newer than the
   cursor, already converted to the unit the shortcut logs in.
4. The shortcut logs each reading with its real measurement time.

Apple Health is the only state. HealthKit has no upsert — **Log Health Sample**
only ever appends — so duplicates have to be filtered out before logging, and
the cursor is how that happens without the server remembering anything.

### Privacy

The server parses the upload, returns the readings, and forgets: no database,
no accounts, and the code logs no readings. The export does pass through it,
though. If you would rather it never left a machine you control, run your own
copy and point the shortcut at it.

## Troubleshooting

**Nothing was imported.** Either Health already had every reading, or the
export could not be read. The published shortcut asks the server to answer
errors with an empty list (see [`on_error`](#post-apiconvert)), so the shortcut
cannot show the reason. To see it, send the export yourself:

```bash
curl -s -D - -X POST --data-binary @export.xls \
  "https://ican-health-sync.vercel.app/api/convert?on_error=empty" | grep -i x-error
```

If the reason is a header or unit it does not recognise, please
[open an issue](https://github.com/Nice0w0/ican-to-apple-health/issues) with
the app's language and the header row of your export.

**Readings of 0 in Health.** Shortcuts made before October 2026 logged a server
error as a glucose of 0. Delete the old shortcut, install the current one, and
delete the 0 readings in Health by hand.

**Duplicates.** The cursor is wrong. Open the shortcut and check that action 1
reads *Blood Glucose, Start Date is in the last 7 days, Sort by Start Date,
Latest First, Limit 1*. Health cannot overwrite a sample, so existing
duplicates have to be deleted by hand.

**Slow.** Each reading costs four on-device actions, and a CGM records one every
three minutes, about 480 a day. A first run or a long gap is slow; routine syncs
carry only the handful of readings since the last one. Sync often rather than
in one big batch.

---

## For developers

The whole thing is the Python standard library: no dependencies, no build step.

| Path | What it is |
|---|---|
| [`api/xlsmini.py`](api/xlsmini.py) | Minimal OLE2 + BIFF8 `.xls` reader |
| [`api/cgm.py`](api/cgm.py) | Export → readings: header, unit, cursor, thinning |
| [`api/convert.py`](api/convert.py) | HTTP handler, run by Vercel or [`server.py`](server.py) |
| [`build_shortcut.py`](build_shortcut.py) | Generates the `.shortcut` plist |
| [`public/`](public/) | The download site, served by Vercel, and the signed shortcuts |

### Run your own copy

**Vercel:**
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Nice0w0/ican-to-apple-health)

**Locally:**

```bash
git clone https://github.com/Nice0w0/ican-to-apple-health.git && cd ican-to-apple-health
python3 server.py        # http://127.0.0.1:8000/api/convert
```

**Docker:**

```bash
cp .env.example .env
docker compose up -d --build
```

The container binds to `127.0.0.1` only. Put a TLS proxy such as Caddy in
front: glucose readings should not cross the internet in plaintext.

| Variable | Default | Meaning |
|---|---|---|
| `CGM_TZ_OFFSET` | `7` | **The wearer's** UTC offset in hours. The export has no timezone, so this is how reading times are reconstructed — a server running in UTC still gets them right. |
| `CGM_TOKEN` | *(unset)* | If set, requests must carry `X-Token` or `?token=`. The public instance leaves it unset. |

Then build a shortcut that points at it (macOS):

```bash
python3 build_shortcut.py --url https://your-host/api/convert --unit mg/dL -o mine.shortcut
shortcuts sign -m anyone -i mine.shortcut -o "Sync iCan to Apple Health.shortcut"
```

| Flag | Meaning |
|---|---|
| `--unit` | `mg/dL` or `mmol/L`. Sets the URL parameter and the Log Health Sample picker together, so they cannot disagree. |
| `--token` | Only if you set `CGM_TOKEN`. **Never publish a shortcut built with it** — the token is in its URL. |
| `--every N` | Keep at most one reading per N minutes. |
| `--window DAYS` | How far back action 1 looks for the cursor (default 7). |

### `POST /api/convert`

Body: the `.xls`, as the raw request body or as a multipart file field (any
name).

| Query | Meaning |
|---|---|
| `since` | The cursor: ISO 8601, a unix timestamp, or a date with a named Thai or English month. Only readings **strictly newer** are returned. A value without a timezone is read in `CGM_TZ_OFFSET`; one before 2000 is refused as corrupted. |
| `unit` | `mg/dL` (default) or `mmol/L`. Values are converted from the export's own unit. |
| `every` | At most one reading per this many minutes, walking newest first so the latest is always kept. |
| `limit` | At most this many readings, newest first. |
| `verbose` | `1` adds `date_iso` and `unit` to each reading. |
| `on_error` | `empty` answers any error with `200 []` and the reason in `X-Error`. |
| `token` | Alternative to the `X-Token` header. |

Returns a JSON array, oldest first:

```json
[{"value": 117, "date_text": "Oct 01, 2026 at 01:17 PM"}]
```

`date_text` is in that exact shape because Shortcuts' **Get Dates from Input**
parses it reliably, including on a non-English phone.

Headers `X-Readings-Total`, `X-Readings-Returned`, `X-Unit`, `X-Source-Unit` and
`X-Since` say what happened without walking the array. `X-Since` echoes the
cursor the server actually parsed: the quick way to tell "nothing new" from
"the cursor never arrived".

Errors: `400` unreadable request, `401` bad token, `413` over 10 MB, `422` not
a readable CGM export.

`GET /api/convert` returns `{"ok": true}`.

#### Why `on_error=empty` exists

Shortcuts does not treat a `4xx` as a failure. It passes the error body on,
**Repeat with Each** walks the `{"error": ...}` dictionary, and **Log Health
Sample** writes an empty value: a glucose of **0** at the current time, which
only the wearer can delete. An empty array logs nothing. The published shortcut
always sends it.

### Export formats

Exports from the Thai-language iCan app have a few rows of account details,
then a header row and one row per reading, newest first:

| Version | Header row |
|---|---|
| Until September 2026 | `เลขที่` · `เวลากลูโคส` · `ค่ากลูโคส (mg/dL)` |
| Since September 2026 | `หมายเลขประจำตัวผลิตภัณฑ์` · `เวลากลูโคส` · `ค่ากลูโคส` |

The header row is found by `เวลากลูโคส`, which both share. Times are parsed as
`%H:%M,%m/%d/%Y`, never guessed: `09/01/2026` is ambiguous, and a wrong guess
moves a reading by months.

When the header declares no unit, it is read off the values, but only when they
leave no doubt: whole numbers with one above 35 are mg/dL, since no mmol/L
reading goes that high; values with decimals, all at or below 35, are mmol/L.
Anything else is refused. This matters because the shortcut's unit picker is
fixed: `7.2 mmol/L` logged as `7.2 mg/dL` reads as severe hypoglycaemia.

### The `.xls` reader

[`api/xlsmini.py`](api/xlsmini.py) reads OLE2 + BIFF8 with the standard library
only, covering both the mini-stream (small exports) and the regular FAT chain.
It is verified cell-for-cell against `xlrd` on real exports.

The subtle part is the shared string table spanning `CONTINUE` records, where
the encoding can flip between compressed and UTF-16 mid-string. Getting that
wrong does not crash; it shifts every later string index, which would attach a
glucose value to the wrong timestamp. If you change the reader, diff the full
grid against `xlrd` on real files before trusting it.

### Limitations

- Written for exports from the **Thai-language** iCan app. Exports in other
  languages likely have other headers and will be refused until added.
- The export has no timezone. The public instance reads it as UTC+7. Wearers
  elsewhere should run their own copy with their own `CGM_TZ_OFFSET`.
- Blood glucose only.
- Manual sync (share → tap), not live background sync.

## Licence

MIT.
