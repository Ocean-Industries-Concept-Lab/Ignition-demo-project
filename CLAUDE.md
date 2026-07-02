# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

This directory is a single **Ignition 8.3 project** (`OpenBridge_demo`) living inside a running
Gateway's data folder (`/usr/local/ignition/data/projects/OpenBridge_demo`). There is no build
step, package manager, or test runner — the "source" is the tree of JSON/CSS/Python resource
files that the Gateway loads into memory and serves as a **Perspective** web app. Editing a file
on disk does nothing until the Gateway re-scans the project (see workflow below).

The app is a maritime/industrial HMI built largely from **OpenBridge**, **automation**, and
**navigation-instruments** Perspective component modules (tanks, valves, motors, pumps, compasses,
gauges).

## Editing → seeing your change (critical workflow)

The Gateway serves Perspective from resources **loaded in memory**, not from disk per request. After
editing any resource on disk you MUST force a project scan, then reload the client:

```bash
curl -s -X POST http://localhost:8088/data/api/v1/scan/projects \
  -H "X-Ignition-API-Token: $(cut -d= -f2- .env.local)"
```

- Token is in `.env.local` (gitignored); the header value is the whole string after the first `=`,
  including its `claude:`/`Postman:` prefix. Success = HTTP 200 with a JSON scan-status body.
- Then reload the running page (an already-open client holds the OLD view until reloaded):
  `http://localhost:8088/data/perspective/client/OpenBridge_demo/<page>` — use the Playwright MCP
  `browser_navigate` + `browser_take_screenshot` to verify.
- Do NOT `touch` files and wait for the periodic scan, edit via the Gateway Web UI, or hand-edit a
  resource.json `lastModificationSignature` (the scan recomputes it).
- The **`ignition-scan-projects` skill** covers this in full — use it after any resource edit.
- `./restart_gateway.sh` does a full Gateway restart (`../../../ignition.sh restart`) — only needed
  for module/config-level changes, not resource edits.

## Resource layout

Ignition modules own top-level folders (`com.inductiveautomation.perspective`,
`com.inductiveautomation.vision`, `com.inductiveautomation.mcp`). Perspective is where nearly all the
work happens:

- `views/` — the screens. Each view is a folder with `view.json` (the component tree),
  `resource.json` (metadata), and a `thumbnail.png`. Pages live under `views/Page/*`; the shared
  left menu and top header under `views/Docks/*`.
- `page-config/config.json` — the URL→view routing table and the shared docks (menu, header). A new
  page needs both a view under `views/Page/` AND an entry here.
- `style-classes/` — named reusable CSS bundles (see below).
- `stylesheet/stylesheet.css` — project-wide raw CSS; mostly thin, delegates to theme tokens.
- `session-props/props.json` — session config; note `theme: "light-cool"`.

Each `resource.json` carries a `lastModificationSignature` content hash — **omit it** when creating
resources by hand; the Gateway recomputes it on scan.

## view.json structure

A `view.json` is a nested component tree. Every component node has `meta.name`, `position`
(`x`/`y`/`width`/`height` for coord containers), `type` (e.g. `automation.digital-valve.digital-valve`,
`openbridge.manual.card`, `ia.container.flex`), and `props`. Containers hold `children`. Layout is
either absolute (`ia.container.coord`) or flex (`ia.container.flex`).

Note (from project memory): OpenBridge valve/motor/pump active state is `open`/`on`, which renders
**white** under the `light-cool` theme — these components have no color prop for the active state.

## Style classes

A style class name **is its folder path** under `style-classes/` (folder `font/body/` → class
`font/body`). A class is a leaf folder with `style.json` (camelCase CSS in `base.style`, optional
`variants` for pseudo-states) + `resource.json`. Intermediate folders (`font/`, `text-color/`) are
grouping only.

The idiom: combine **one `font/*`** (typography only) with **one `text-color/*`** (color only),
space-separated, in a component's `style.classes` string. When restyling, **replace** the class
string — don't stack a new font onto legacy `Title/*`/`Page/*`/`Menu/*` classes that bundle
typography+color+structure. Use the **`ignition-style-classes` skill** for lookups and creating
classes (it has the exact `resource.json` template).

## MCP / Gateway API

`.mcp.json` registers an `ignition` HTTP MCP server at `http://localhost:8088/data/mcp/testing`
(auth via `X-Ignition-API-Token`). Custom Gateway-side MCP tools live under
`com.inductiveautomation.mcp/tools/<ToolName>/onToolCalled.py`.
