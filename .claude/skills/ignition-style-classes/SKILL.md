---
name: ignition-style-classes
description: Use when working with Perspective style classes in this Ignition project — looking up what a class does, creating a new style class, or applying classes via the "classes" property in a view.json. Triggers on "style class", "klasse", "styles", the classes property, font/*, text-color/*, or style-classes folder.
---

# Ignition Perspective Style Classes

## Overview

A Perspective **style class** is a named bundle of CSS that components reference by name.
In this project, **the class name IS its folder path** under
`com.inductiveautomation.perspective/style-classes/`.

Folder `style-classes/font/body/` → class name **`font/body`**.

Intermediate folders (`font/`, `text-color/`) are just grouping — they hold no files of
their own. Only a **leaf** folder (one containing a `style.json`) is a real class.

## How a class is stored

A class = a leaf folder with exactly two files:

| File | What it is |
|------|------------|
| `style.json` | The CSS — `base.style` (camelCase props), optional `variants` for pseudo-states |
| `resource.json` | Ignition resource metadata (scope, version, file list) — same shape for every class |

`style.json`:
```json
{
  "base": {
    "style": {
      "fontSize": "var(--global-typography-ui-body-font-size)",
      "fontWeight": "var(--font-weight-regular)"
    }
  },
  "variants": [
    { "pseudo": "hover", "style": { "backgroundColor": "var(--callToActionHighlight)" } }
  ]
}
```
- Props are **camelCase** (`backgroundColor`, `borderTopWidth`), not kebab-case.
- Values are usually theme tokens: `var(--token-name)`.
- `variants` is **optional**; omit it for a plain class. Each variant has a `pseudo`
  (e.g. `hover`, `last-child`) and its own `style`.

## The convention map (this project)

| Group | Holds ONLY | Example |
|-------|-----------|---------|
| `font/*` | typography (fontSize, fontWeight, lineHeight…) | `font/body`, `font/title` |
| `text-color/*` | color | `text-color/element-neutral` |
| `divider/*` | borders | `divider/bottom` |
| `Utils/*` | spacing | `Utils/p-8` |
| `card/card` | card surface | `card/card` |

The **semantic idiom is one `font/*` + one `text-color/*`** — typography and color are
separate classes you combine. (Older classes `Title/*`, `Page/*`, `Menu/*`, `Header/*`
predate this and mix typography + color + structure in one class.)

## Looking up a class

The class name is the path — read the file directly:
```
style-classes/<class-name>/style.json
```
e.g. class `font/title` → `style-classes/font/title/style.json`.

To find a class for a desired look, browse the relevant group folder (typography →
`font/`, color → `text-color/`) and read the `style.json` files.

## Creating a new class

1. The folder path you choose **is** the class name. Put it in the right group
   (typography → `font/`, color → `text-color/`). Make a `font/*` class hold *only*
   typography and a `text-color/*` class hold *only* color — don't mix.
2. Create `style.json` with `base.style` (+ `variants` only if you need pseudo-states).
3. Create `resource.json` from this exact template:
```json
{
  "scope": "G",
  "version": 1,
  "restricted": false,
  "overridable": true,
  "files": [
    "style.json"
  ],
  "attributes": {
    "lastModification": {
      "actor": "admin",
      "timestamp": "2026-01-01T00:00:00Z"
    }
  }
}
```
**Omit `lastModificationSignature`.** It is a content hash the gateway recomputes when it
loads the resource — you cannot author it by hand and you don't need to. The `timestamp`
value is not significant; any valid ISO timestamp is fine.

## Applying classes in a view

In `view.json`, a component references classes through the `classes` property **inside its
`style` object**:
```json
"style": { "classes": "font/body text-color/element-neutral" }
```
- **Space-separated** to combine multiple classes.
- Combine **one** `font/*` with **one** `text-color/*` — that's the idiom.

When *replacing* a component's look, **replace** the old class string — don't append a new
font on top of an old `Title/*`/`Page/*` class, since those already carry their own font
and color (you'd get two fonts fighting). Stack only classes that own disjoint concerns
(font + color + spacing).

## Common mistakes

- ❌ Treating the leaf name alone as the class (`body`) — the class is the **full path**
  (`font/body`).
- ❌ Adding a `resource.json` to a grouping folder — only leaf folders have one.
- ❌ kebab-case CSS props in `style.json` — use camelCase.
- ❌ Appending `font/x` onto an existing `Title/*` class — replace it instead.
- ❌ Hand-writing a `lastModificationSignature` — omit it.
