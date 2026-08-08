# Spec: WiFi Onboarding + Gift Device Dashboard

Status: Draft
Author: Claude (drafted on request), for benleeburke@gmail.com
Date: 2026-08-08

## 1. Problem

Today `touch_point.py` assumes the Pi is already on a network (or needs none —
it only reads NFC tags and drives LEDs/sound locally). To gift a Touch Point
to someone else, they need a way to:

1. Get the device onto **their own home WiFi**, without SSH/keyboard/monitor
   access and without needing to know anything technical.
2. Have that moment feel like part of the gift, not a device-setup chore.

And I need a way to:

3. Know when a device I've given away comes online, and see its status
   over time (online/offline, last seen, uptime).
4. See a list of every device I've sent out, in one place.
5. Remotely reach a given device's shell if something needs debugging or
   fixing, without asking the recipient to do anything technical.

This spec covers WiFi onboarding ("WiFi login screen") and the fleet
dashboard + remote access. It does not change the existing NFC/LED/sound
runtime behavior in `touch_point.py`.

## 2. Assumptions (please correct any of these)

These were defaulted because this session couldn't get interactive answers.
Flagging each one so they're easy to override before implementation starts:

- **Same physical device.** This spec assumes the gifted device *is* the
  existing Touch Point (Pi + RC522 + NeoPixel ring + speaker), now also
  WiFi-connected — not a new/separate product.
- **No attached screen.** The Pi has no monitor/touchscreen. "Whimsical WiFi
  login screen" means a **captive portal web page on the recipient's own
  phone**, not an on-device display. If a physical screen is planned for a
  future revision, the portal design below still works as the page shown on
  it.
- **Remote access via Tailscale.** Simplest way to reach a device behind an
  arbitrary home router/NAT without me operating a public relay server.
  Each Pi joins my personal tailnet on first successful WiFi connect; I SSH
  to it by its Tailscale hostname. Alternative (self-hosted reverse SSH
  relay) is noted in §7 as a fallback if Tailscale is a non-starter.
- **Dashboard is a small self-hosted service**, not a spreadsheet/Notion
  integration — devices need an API to phone home to, and a spreadsheet
  can't receive pushes from a Pi cleanly. Concretely: FastAPI + SQLite,
  deployable as one more `pm2`-managed process next to the existing
  deployment tooling in `commands/`, or on a cheap always-on host.
- **v1 scope:** WiFi onboarding, phone-home status ping, dashboard list +
  detail view, "how to reach this device" info (Tailscale hostname/SSH
  command). Full in-browser remote shell (e.g. a web terminal) is v2 —
  v1 gives you the SSH command/hostname, you SSH from your own machine.
- Recipients are one-time setup users — no recipient login/accounts. The
  dashboard itself is single-user (just me), no multi-tenant auth needed
  beyond a basic password/allowlist.

## 3. WiFi Onboarding ("WiFi Login Screen")

### 3.1 Flow

1. **First boot with no known WiFi** (or held-button reset — see §3.4): the
   Pi brings up its own WiFi access point instead of trying to join a home
   network. SSID something like `✨ Touch Point Setup ✨`, open (no
   password) so there's zero friction for a gift recipient.
2. Recipient joins that WiFi from their phone. iOS/Android both auto-detect
   a captive portal (no internet behind the AP) and pop the setup page
   automatically; worst case they open any `http://` URL and get redirected.
3. **The whimsical page**: recipient picks their home WiFi network from a
   scanned list and enters the password. See §3.3 for tone/design.
4. On submit, the Pi:
   - Tears down the AP.
   - Attempts to join the chosen network.
   - On success: shows a success/celebration state (can be the same page,
     polling a status endpoint, since the phone briefly keeps the portal
     tab open even as the AP drops — with a fallback "you can close this
     page now, your Touch Point is coming to life" message since captive
     portal tabs don't reliably survive the AP teardown on all phones).
   - On failure (bad password, network out of range): Pi re-raises its own
     AP so they can retry, page shows a friendly retry state.
5. Once online, the device registers/checks in with the dashboard backend
   (§4) using its pre-provisioned device identity (§3.5) — this is the "I
   want to know about it" moment.
6. Device persists the WiFi credentials (via NetworkManager/wpa_supplicant,
   whichever the Pi OS build uses) and boots straight to normal
   `touch_point.py` behavior from then on, retrying the AP-fallback flow
   only if it can't reach the last-known network for some grace period
   (e.g. they move house and change routers — see §3.4).

### 3.2 Why captive portal over alternatives

| Approach | Why not chosen for v1 |
|---|---|
| On-device touchscreen UI | No screen in current BOM; adds cost/complexity to every unit |
| Bluetooth + companion app | Requires shipping/maintaining a mobile app; captive portal needs nothing installed |
| QR code → hosted web app that talks to the device | Needs the device reachable from the cloud *before* it has WiFi — circular; would need BLE or similar anyway |

Captive portal (Pi-as-AP) is the standard pattern for exactly this
problem (same idea as smart plugs, Sonos, etc.) and needs nothing installed
on the recipient's phone.

### 3.3 Whimsical design direction

Tone: an invitation into the magic, not a router settings page. Suggested
copy/beats (final copy is a separate pass, not blocking this spec):

- Page title: something like "Let's wake up your Touch Point ✨" rather than
  "WiFi Setup."
  - Optional: a magic-band-tap visual motif, or the network selection framed
    as "Which magic connects your home?"
- Network list presented as a simple tappable list (icons for signal
  strength are enough — no need to reproduce OS-native WiFi UI chrome).
- Password field: standard show/hide toggle, no cleverness that gets in the
  way of actually typing a WiFi password correctly.
- Connecting state: use the existing hardware's presence — LEDs on the ring
  can pulse while the page shows a matching "waking up..." animation, so the
  physical object visibly participates in the "typing on the page → thing
  in your hand comes alive" moment.
- Success state: an actual name for the moment — e.g. "🎉 Your Touch Point
  is alive! Tap it with a MagicBand and see what happens." — ties straight
  into the existing NFC party-trick.
- Visual style: reuse a Disney-attraction-poster feel (matches the
  project's own framing in `README.md`) — warm colors, a little sparkle,
  rounded/friendly typography. No corporate SaaS look.
- Must still be legible/usable on a small phone screen with one thumb —
  whimsy shouldn't cost usability. A "just get me set up" affordance
  (skip animation, minimal-motion mode) is worth keeping for accessibility.

### 3.4 Recovery / re-onboarding

- **Physical reset**: holding a button (or a specific NFC "reset tag"
  shipped alongside the device, thematically fitting for a MagicBand-style
  device) for N seconds clears saved WiFi and re-raises the setup AP. Useful
  if the recipient moves or changes routers.
- **Boot-time fallback**: if the device can't join its last-known network
  within a timeout on boot, it automatically falls back to AP mode rather
  than silently failing forever — so "recipient changed their WiFi password"
  self-heals into a re-onboarding prompt instead of a dead device.

### 3.5 Device identity

Each unit gets a stable identity baked in before it's gifted (e.g. at
`commands/setup/setup_script.sh` time): a generated `device_id` (UUID) +
a human label I assign (e.g. "Mom's kitchen", "Cora's room") stored locally
on the Pi and used as the phone-home identifier. This is what ties a
physical unit to a row in the dashboard regardless of whatever WiFi network
it ends up joining.

## 4. Phone-Home / Status Reporting

### 4.1 What the device reports

On WiFi connect, and periodically thereafter (e.g. every 5–10 min, plus a
graceful "going offline" isn't reliably possible so rely on a heartbeat
timeout instead):

- `device_id`, `label`
- timestamp
- online heartbeat (implicit — arrival of the request itself)
- basic health: uptime, IP on local LAN, WiFi SSID it's joined to, signal
  strength
- Tailscale status: whether tailscaled is up and its assigned Tailscale
  hostname/IP (this is the "how do I reach it" info for §5)
- optional: last NFC scan event / sound played, count of scans since boot —
  nice-to-have for "is anyone actually using it" visibility, not required
  for v1

### 4.2 Transport

Simple authenticated HTTPS POST from the device to the dashboard backend
(`POST /api/devices/{device_id}/checkin`), auth'd with a per-device token
provisioned at the same time as `device_id` (§3.5) — not a shared secret
across all units, so one compromised/lost unit doesn't expose the others.

Runs as its own small daemon/cron job on the Pi (separate from
`touch_point.py`, so a bug in one doesn't take down the other) — fits the
existing pattern of `commands/pull.sh` + pm2/cron already used for updates.

## 5. Remote Access

- Each device runs `tailscaled` and auto-joins my tailnet using a
  **pre-generated, single-use Tailscale auth key** baked in at setup/imaging
  time (rotated per batch, not one long-lived key reused forever).
- Dashboard surfaces, per device: online/offline (derived from checkin
  heartbeat + Tailscale's own online status), and the Tailscale
  hostname/IP plus a copy-pasteable `ssh pi@<tailscale-hostname>` command.
- v1: I SSH in manually from my own machine once I have the tailnet
  hostname from the dashboard. No in-browser terminal yet (see §7 for v2).
- Access control: Tailscale ACLs scope these device nodes so only my
  account can reach them — recipients are never on my tailnet and never see
  any of this.

## 6. Dashboard

### 6.1 Views

- **Fleet list** (`/`): every device I've sent out. Columns: label, online
  status (dot + "online" / "last seen 3d ago"), WiFi SSID it's currently
  on, gift date, quick "SSH command" copy button.
- **Device detail** (`/devices/{device_id}`): full check-in history/log
  (a simple timeline — "came online", "went offline", WiFi network
  changes), health fields from §4.1, remote-access info from §5, and an
  editable label/notes field (e.g. "gave this to Mom for her birthday,
  kitchen counter").
- No recipient-facing UI at all — this whole section is for me only.

### 6.2 Data model (sketch)

```
Device
  id (uuid, = device_id)
  label
  notes
  auth_token_hash
  tailscale_hostname
  gifted_at
  created_at

CheckIn
  id
  device_id (fk)
  received_at
  uptime_seconds
  wifi_ssid
  wifi_signal
  local_ip
  tailscale_online (bool)
  scan_count_since_boot (nullable)
```

`online` for the list view = most recent `CheckIn.received_at` within, say,
2x the heartbeat interval; older than that = offline/stale.

### 6.3 Auth

Single-user dashboard behind a basic login (or Tailscale-only access to the
dashboard itself, reusing the same tailnet rather than building separate
auth) — since it's just me using it, don't over-build this.

### 6.4 Hosting

Deployed as one more process managed the same way the device-side update
loop already is (`commands/pull.sh`-style pattern) — e.g. on a small
always-on host (could even be a Pi at home, or a cheap VPS). Exact hosting
choice isn't load-bearing for this spec; flag if you'd rather target a
specific platform (Fly.io, a home server, etc.).

## 7. Out of scope for v1 (candidate v2 items)

- In-browser remote shell/web terminal (vs. copy-paste SSH command).
- Push/email notification the moment a gifted device first comes online
  ("Mom just set up her Touch Point!") — easy add once check-in exists,
  deliberately left out of v1 to keep the first cut small.
- Recipient-visible "your device is online" confirmation beyond the setup
  page's own success state.
- Fallback remote-access transport (self-hosted reverse SSH relay) if
  Tailscale turns out to be unwanted — noted here as the alternative but
  not designed in detail since Tailscale is the assumed default.
- Multi-recipient/shared dashboard access.

## 8. Suggested build order

1. WiFi onboarding (AP mode + captive portal + credential persistence +
   reset flow) — device is unusable as a gift without this.
2. Device identity provisioning step added to `commands/setup/setup_script.sh`.
3. Phone-home checkin daemon + minimal backend endpoint (no UI yet, just
   confirm data lands).
4. Tailscale auto-enrollment on first connect.
5. Dashboard UI (list + detail views) on top of the data already flowing in.
6. Whimsical visual/copy pass on the portal page (can iterate independently
   of the functional flow above).

## 9. Open questions for you

- Confirm or correct the assumptions in §2 — especially: is this really the
  same NFC Touch Point device, and is Tailscale acceptable (vs. you already
  running some other remote-access solution I should reuse)?
- Any devices already out in the wild that need retroactive onboarding, or
  is this greenfield for all future units?
- Preferred hosting target for the dashboard backend (§6.4)?
- Any existing design/brand language (colors, fonts) from other Touch Point
  materials (e.g. the 3D-printed reader) the portal page should match?
