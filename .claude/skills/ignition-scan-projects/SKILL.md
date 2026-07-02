---
name: ignition-scan-projects
description: Use after editing any project resource on disk (view.json, style-classes, session-props, page-config) in this Ignition project when the change must appear in the running Gateway or Perspective client. Triggers on "make it show up", "update the webpage", "refresh the view", "why isn't my change visible", scan/projects, project scan, reload resource, X-Ignition-API-Token.
---

# Refresh Ignition After Editing a Resource on Disk

## Overview

The Ignition Gateway serves Perspective from the project resources it has **loaded in
memory**, not from disk per request. A file edit on disk is invisible until the Gateway
**scans the project** and re-ingests it.

**Force the scan with one authenticated POST — do NOT `touch` the file, wait for a timer,
or use the Gateway Web UI.**

## The command

```bash
curl -s -X POST http://localhost:8088/data/api/v1/scan/projects \
  -H "X-Ignition-API-Token: $(cut -d= -f2- .env.local)"
```

- The token lives in `.env.local` (gitignored) as `X-Ignition-API-Token=Postman:<token>`.
  The header value is the **whole string after the first `=`** (e.g. `Postman:chcow4...`) —
  keep the `Postman:` prefix.
- Success = HTTP 200 with a JSON body like
  `{"scanActive":true,"lastScanTimestamp":...,"lastScanDuration":...}`.
- Add `-w "\nHTTP %{http_code}\n"` if you want to see the status code.

## Full workflow

1. Edit the resource on disk (e.g. a `view.json`).
2. **POST to `scan/projects`** (command above) so the Gateway re-ingests it.
3. Reload the running client to see it: navigate the browser to
   `http://localhost:8088/data/perspective/client/<ProjectName>/<page>` (Playwright MCP
   `browser_navigate`), then `browser_take_screenshot` to verify. An already-open page
   holds the **old** view until you reload.

## Common mistakes

- ❌ `touch`-ing the file and waiting for the periodic scan — slow and unreliable; force it.
- ❌ Omitting the `X-Ignition-API-Token` header — the POST needs auth.
- ❌ Dropping the `Postman:` prefix from the token — send the full value from `.env.local`.
- ❌ Hand-editing `resource.json`'s `lastModificationSignature` to force a reload — the
  scan reconciles it; you don't author it.
- ❌ Expecting an already-loaded browser page to update on its own — reload it after the scan.
