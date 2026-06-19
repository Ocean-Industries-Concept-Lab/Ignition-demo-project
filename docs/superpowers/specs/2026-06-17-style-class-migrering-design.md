# Migrering av style-classes i OpenBridge_demo

**Dato:** 2026-06-17
**Mål:** Endre gamle style-class-navn i `OpenBridge_demo` til de nye semantiske klassene som brukes i `OpenBridge`-prosjektet, og lage en liste over klasser hvor migreringen er usikker.

## Bakgrunn

De to prosjektene bruker to ulike system for style-classes:

- **OpenBridge_demo (gammelt):** Klasser organisert per komponent — `Title/*`, `Page/*`, `Menu/*`, `Header/*`, `card/card`. Hver klasse blander typografi + farge + struktur, og refererer tema-tokens som `--neutral-90`, `--neutral-30`.
- **OpenBridge (nytt):** Rent *semantiske* klasser — `font/*` (kun typografi), `text-color/*` (kun farge), `divider/*`, `card/card`. Farge hentes fra `--element-neutral-color` o.l.

Idiomet i det nye systemet er å kombinere én font-klasse + én text-color-klasse. Dette er bekreftet direkte fra OpenBridge sine egne views, f.eks. `"classes": "font/overline text-color/element-neutral"`.

## Avgrensning (besluttet med bruker)

1. **Kun trygge 1:1-mappinger migreres.** Strukturelle klasser uten semantisk ekvivalent i det nye systemet (border/bakgrunn/fill/marginer) lar vi stå urørt og listes opp som usikre. Ingen visuell endring uten brukers godkjenning.
2. **Variabler verifiseres.** CSS-variablene de nye klassene bruker finnes ikke i prosjektets egen `stylesheet.css` — de leveres av OpenBridge HMI-temaet på gateway-nivå. Dette flagges.

## Hvilke klasser brukes faktisk i demo-views

Kun disse gamle klasse-tokenene refereres i views (resten av style-class-mappene er ubrukt i views):

| Token | Forekomster (view:linje) |
|---|---|
| `Page/Page` | Home:49, Charts:55, Alarms:61 |
| `Page/Alarm/Alarm` | Alarms:48 |
| `Page/Alarm/Page` | Alarms:61 (sammen med `Page/Page`) |
| `Title/Icon` | Embedded/Title:46 |
| `Title/Text` | Embedded/Title:73 |
| `Title/Title` | Embedded/Title:84 |
| `Title/overline` | Format:27, Format:315, Format:605, Format:724 |
| `Title/label` | Format:210, Format:337, Format:491 |
| `card/card` | Format:295, Format:585, Format:704, Format:826 |
| `Menu/Menu` | Docks/Menu:72 |

## Migrering — trygge mappinger (DETTE GJØRES)

| Gammel klasse-streng | Ny klasse-streng | Begrunnelse |
|---|---|---|
| `Title/overline` | `font/overline text-color/element-neutral` | Gammel `Title/overline` = overline-font (12px/600/letterSpacing/16px) + `--element-neutral-color`. Splittes i font + farge. Identisk idiom som i OpenBridge sine views. |
| `Title/label` | `font/label text-color/element-neutral` | Gammel `Title/label` = label-font (`--global-typography-ui-label-*`) + `--element-neutral-color`. Splittes i font + farge. |
| `card/card` | `card/card` | Allerede identisk i begge prosjekter — ingen endring nødvendig. |

Berørte views: **Format** (`Title/overline` ×4, `Title/label` ×3). `card/card` står uendret.

## Usikre klasser (DISSE STÅR URØRT — krever brukers avgjørelse)

Disse har ingen ren semantisk ekvivalent i det nye systemet (de er strukturelle: border / bakgrunn / `fill` / marginer, bundet til `--neutral-XX`-tokens som ikke finnes som `font/`- eller `text-color/`-klasser).

| Gammel klasse | View(er) | Hva den gjør | Hvorfor usikker |
|---|---|---|---|
| `Title/Text` | Page/Embedded/Title:73 | `color`+`fill` `--neutral-90`, 16px bold, `marginLeft:6px` | Nærmest `font/title`/`font/body-active` + `text-color`, men ingen ny klasse har `fill` eller `marginLeft`. Ville endret utseende. |
| `Title/Title` | Page/Embedded/Title:84 | Bakgrunn `--neutral-30` + topp/bunn-border `--neutral-60` | Rent strukturell. Ingen ekvivalent i nytt system. |
| `Title/Icon` | Page/Embedded/Title:46 | `fill: --neutral-90` (ikon-farge) | Ingen ikon-fill-klasse i nytt system. |
| `Page/Page` | Home:49, Charts:55, Alarms:61 | Venstre-border `--neutral-60` + fontSize/lineHeight | Strukturell border + font blandet; ingen ekvivalent. |
| `Page/Alarm/Alarm` | Alarms:48 | Venstre/høyre-border `--neutral-40` | Rent strukturell. Ingen ekvivalent. |
| `Page/Alarm/Page` | Alarms:61 | Bakgrunn `--neutral-20` | Rent strukturell. Ingen ekvivalent. |
| `Menu/Menu` | Docks/Menu:72 | Bakgrunn `--neutral-30` | Ingen ekvivalent — **og OpenBridge-prosjektet selv refererer fortsatt `Menu/Menu` i sine egne views.** |

## Variabel-verifisering (flagg)

CSS-variablene de nye klassene bruker er **ikke** definert i `OpenBridge_demo/.../stylesheet/stylesheet.css`. De leveres av OpenBridge HMI-temaet på gateway-nivå:

| Variabel | Definert i demo-prosjekt? | Brukt av |
|---|---|---|
| `--global-typography-ui-overline-font-weight/-font-size/-line-height/-letter-spacing` | Nei | `font/overline` (ny) |
| `--global-typography-ui-label-font-weight` | Nei | `font/label` (ny) |
| `--global-typography-ui-label-font-size/-line-height` | Ja (brukes alt av gammel `Title/label`) | `font/label` (ny) |
| `--font-family-main` | Nei | `font/overline`, `font/label` (ny) |
| `--element-neutral-color` | Ja (brukes alt av gammel `Title/overline`/`Title/label`) | `text-color/element-neutral` (ny) |

**Konsekvens:** Migreringen er trygg *forutsatt* at OpenBridge HMI-temaet er aktivt på gatewayen. `--font-family-main` og `--global-typography-ui-overline-*` brukes ikke av noen gammel demo-klasse, så de er nye avhengigheter introdusert av migreringen. Hvis temaet ikke er installert, vil disse falle tilbake til nettleserens standard (font-family arves, font-weight/size blir tom → ingen effekt). Dette er samme avhengighet som OpenBridge-prosjektet allerede har.

## Forutsetning

De nye klassene `font/overline`, `font/label`, `text-color/element-neutral` må **finnes i demo-prosjektets style-classes** for at view-referansene skal virke. I dag finnes de kun i OpenBridge-prosjektet. Migreringen må derfor også **kopiere disse 3 klasse-definisjonene** inn i `OpenBridge_demo/.../style-classes/` (font/overline, font/label, text-color/element-neutral), ellers peker views på ikke-eksisterende klasser.

## Endringsomfang

**Filer som endres:**
- `views/Page/Format/view.json` — 7 `classes`-strenger (`Title/overline` ×4 → `font/overline text-color/element-neutral`; `Title/label` ×3 → `font/label text-color/element-neutral`)

**Filer/mapper som opprettes (nye klassedefinisjoner kopiert fra OpenBridge):**
- `style-classes/font/overline/{resource.json,style.json}`
- `style-classes/font/label/{resource.json,style.json}`
- `style-classes/text-color/element-neutral/{resource.json,style.json}`

**Urørt:** Alle views med usikre klasser (Home, Charts, Alarms, Embedded/Title, Docks/Menu) og `card/card`-referansene i Format.

## Verifisering

- Etter endring: `grep -rn '"classes"' views/` viser ingen `Title/overline` eller `Title/label` igjen.
- JSON-validitet på hver endret/ny fil (`python -m json.tool`).
- De usikre klassene fortsatt til stede og uendret.
