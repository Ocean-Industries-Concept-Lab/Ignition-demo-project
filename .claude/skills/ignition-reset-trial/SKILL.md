---
name: ignition-reset-trial
description: Use when a Perspective client page shows "Trial Expired" ("Your Perspective client trial period has expired") or the Gateway's 2-hour trial timer has run out, so screenshots/verification of views are blank. Resets the Ignition Gateway trial via the Gateway web UI with Playwright. Triggers on "trial expired", "reset trial", "reset the demo timer", "2 hour trial", blank Perspective screenshot.
---

# Reset the Ignition Gateway Trial

## Overview

This Gateway runs Ignition in **trial mode**: every 2 hours Perspective clients stop rendering
and show **"Trial Expired"** instead of the view. Nothing in the project is wrong — the trial
just needs resetting from the Gateway home page (requires login). There is no API call for it;
use the Playwright MCP browser.

Credentials (local dev Gateway): **username `admin`, password `admin`**.

## Steps (Playwright MCP)

1. `browser_navigate` → `http://localhost:8088/app/home`
2. Click the **"Log In"** link in the top-right header (`log-in-button`, href `/data/app/login`).
   - If the header already shows a user menu with `admin`, you're logged in — skip to step 5.
3. Login is a **two-step form**: type `admin` in **Username** and press Enter (submit).
4. A **Password** field appears ("Log in as: admin"): type `admin` and press Enter.
   You land back on `/app` → `/app/home`.
5. `browser_snapshot` and find the trial banner at the bottom of the home page:
   `Trial Expired · 0:00:00 · ...` with buttons **"Reset Trial"** and "Activate Ignition".
   Click **"Reset Trial"**. (Never click "Activate Ignition".)
6. Verify: a new snapshot shows **`Trial Mode`** with a timer near **`1:59:59`**.
7. Reload any open Perspective client page
   (`http://localhost:8088/data/perspective/client/OpenBridge_demo/<page>`) — an already-open
   client keeps showing "Trial Expired" until reloaded.

## Notes

- Snapshots may also include a hidden "Browser Not Supported" block — ignore it; the real UI is
  the first part of the snapshot.
- The banner is only shown when logged in; logged out, the home page has no reset button.
- Expect to repeat this every 2 hours during long sessions. Check for "Trial Expired" in a page
  snapshot before trusting a blank screenshot.
