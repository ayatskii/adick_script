# Edvibe Grader — Extracted UI Spec (Implementation-Ready)

> Source of truth for a pixel-perfect React build. All values below are **copied verbatim** from the design-canvas handoff bundle, not approximated.
>
> **Primary design file:** `/tmp/design_extract/design-specifications-summary/project/Edvibe Grader.dc.html`
> **Imported component:** `/tmp/design_extract/design-specifications-summary/project/StatusBadge.dc.html`
> **Design conversation:** `/tmp/design_extract/design-specifications-summary/chats/chat1.md`
> **Runtime:** `/tmp/design_extract/design-specifications-summary/project/support.js`
> Extracted: 2026-06-16

---

## 0. CRITICAL ORIENTATION — Which design is this?

The brief in `chat1.md` originally asked for an **early-2000s Saturday-morning cartoon / Y2K Flash** aesthetic. The agent built that, then **the user explicitly pivoted**: _"now i want fully change the stylistic of the app to the SamuraiJack style."_

**The shipping `Edvibe Grader.dc.html` is the SAMURAI JACK restyle, NOT the Y2K cartoon.** Its tokens, fonts (Shippori Mincho B1 / Yuji Syuku), markup (thin hairline borders, sharp corners, soft cinematic shadows, rising-sun + mountain-ridge backdrop, hanko "WIN" stamp), and palette (sand/sumi/vermilion in light, Aku indigo-black + red-sun glow in dark) are all the Tartakovsky-inspired version.

The Y2K cartoon version was preserved separately as `Edvibe Grader Y2K Cartoon.dc.html` (+ `StatusBadge Cartoon`). **Per instructions, we ignore those.** This spec describes ONLY the Samurai Jack design that lives in the primary file.

**Core visual inversion (vs. the rejected Y2K version):**
- NO thick black inked outlines → thin tonal **hairline borders** (`1.5px solid var(--line)`, where `--line` is a low-alpha ink color).
- NO hard offset "sticker" shadows → **soft cinematic cast shadows** (`Npx Npx 13-16px var(--shadowc)`, blurred, low-alpha brown/black).
- Sharp / near-sharp corners (`border-radius` mostly **3–7px**, pills `99px`) — angular, not blobby.
- Flat color blocking, muted earthy palette + vermilion/jade/ochre accents.
- Atmospheric fixed backdrop: faint red sun disc top-right + two layered flat mountain-silhouette SVGs at the bottom, behind all content.

### support.js verdict
`support.js` is the **design-canvas framework runtime** (a generated React renderer for `.dc.html` files: `parseDcDocument`, `DCLogic`, `sc-if`/`sc-for`/`dc-import` handling, `window.React`/`ReactDOM` bridge). **It is NOT design content.** Header comment: `// GENERATED from dc-runtime/src/*.ts — do not edit.` Do not transcribe it. In React, replace all `sc-if`/`sc-for`/`{{ }}`/`dc-import` mechanics with normal JSX + props/state.

### How to read the templates
- `{{ expr }}` = a value computed in `renderVals()` (the `<script type="text/x-dc">` block). Where a literal is shown in `renderVals()`, that literal is the real design value.
- `<sc-if value="X">` = conditional render. `<sc-for list="X" as="y">` = map/loop. `<dc-import name="StatusBadge" .../>` = render the StatusBadge component (`hint-size` is just an editor preview hint, not layout).
- The `data-props` JSON at the bottom of each file declares editor-tweakable props.

---

## 1. Design Tokens (verbatim)

### 1.1 Fonts
Loaded via Google Fonts (`<link href="https://fonts.googleapis.com/css2?family=Shippori+Mincho+B1:wght@600;700;800&family=Yuji+Syuku&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap">`):

| Role | Family | Weights | Used for |
|---|---|---|---|
| Brand wordmark | `'Yuji Syuku', serif` | 400 | The "Edvibe Grader" logo text in sidebar only |
| Display / headings / labels / badges / buttons / nav | `'Shippori Mincho B1', serif` | 600, 700, 800 | Almost all headings, nav items, button labels, badge text, big numeric scores, table headers |
| Body / dense data | `Inter, system-ui, sans-serif` | 400, 500, 600, 700 | `body` default, table cell text, textareas, paragraph copy |
| Monospace | `'JetBrains Mono', monospace` | 400, 500, 600 | Log console, audio time labels, timestamps |

`body { font-family: Inter, system-ui, sans-serif; }` `* { box-sizing: border-box; }` `html,body { margin:0; padding:0; }`

**Note on numeric scores:** big scores use `font-family:'Shippori Mincho B1',serif; font-weight:800; font-variant-numeric:tabular-nums;` (NOT a dedicated "bubbly" face — that was the Y2K idea; here scores are Mincho).

### 1.2 CSS Variables — LIGHT theme (`:root`)
```css
--bg:#e3d9c2;            /* page background (sand/parchment) */
--dot:rgba(35,30,20,.05);/* halftone dot color for main content radial-dot bg */
--panel:#f4eee0;         /* card/panel surface */
--panel2:#ece3d0;        /* panel header / secondary surface */
--panel3:#e6dcc6;        /* tertiary / score column / expanded-row bg */
--ink:#23211c;           /* primary text (sumi) */
--ink-soft:#746f60;      /* secondary/muted text */
--line:rgba(35,33,28,.16); /* hairline border color */
--shadow:#23211c;        /* (declared; rarely used directly) */
--shadowc:rgba(60,45,25,.22); /* soft cast-shadow color */
--violet:#2b3a5e;        /* primary accent — samurai blue/indigo */
--indigo:#1f2a44;        /* deep indigo (hero/emblem bg) */
--lime:#2f8f6b;          /* "graded"/success green (jade) */
--pink:#c62d1f;          /* error/danger red (vermilion) */
--sky:#3f72b0;           /* evaluating/info blue */
--yellow:#cf9a36;        /* flagged/caution ochre */
--chip:#ddd2bb;          /* neutral chip / idle / queued bg */
--c-skip:#b3aa98;        /* skipped/neutral dot */
--logbg:#171a22;         /* log console dark panel bg */
--logink:#d7d0bd;        /* log console default ink */
--sun:#c62d1f;           /* rising-sun disc (vermilion) */
--aku:#5f8f3a;           /* Aku-green accent */
```

### 1.3 CSS Variables — DARK theme (`[data-theme="dark"]`)
```css
--bg:#0f1219;            --dot:rgba(236,228,210,.05);
--panel:#191d29;         --panel2:#222838;         --panel3:#161a24;
--ink:#ece4d2;           --ink-soft:#969ab0;
--line:rgba(236,228,210,.13);  --shadow:#000000;  --shadowc:rgba(0,0,0,.55);
--violet:#3f538a;        --indigo:#2a3556;
--lime:#38a87f;          --pink:#d8392a;           --sky:#4f86c6;          --yellow:#d6a23f;
--chip:#28304a;          --c-skip:#5a6276;
--logbg:#0a0c12;         --logink:#cfc8b6;         --sun:#d8392a;          --aku:#8fd14a;
```

Theme is applied via `data-theme="{{ theme }}"` on the root flex container; default state `theme: 'light'`.

### 1.4 Hardcoded colors used in markup (outside the variables)
These appear inline and must be reproduced exactly. Some intentionally stay warm-lit even in dark mode (a noted compromise — see §10):
- `#ffffff` / `#fff` — white text on colored fills (lime/sky/violet/pink buttons, badges, run pill).
- `#3a2600` — dark brown text used on yellow/ochre fills (Localhost-adjacent? no — on `--yellow` chips, "Start a run" hero button text, advisory banner text, dialog header text, count badges on yellow).
- `#063` — dashboard "Pending students" icon fg (on sky bg).
- `#1a7a2e` — review footer "approved" count text; dashboard "Last run" value fg is `#1a7a2e`.
- `#c63` / `#c00` — review footer "rejected" text (`#c63`); Danger-zone button text (`#c00`).
- `#a06a00` / `#7a5a10` / `#7a5a40`(n/a) — flagged/advisory warm text tones: `--yellow`-related: New Run full-mode warning `#a06a00`; flagged card severity badge fg `#a06a00`; dashboard "Flagged" value fg `#a06a00`, label fg `#7a5a10`.
- Dashboard "Last run" tile bg `#dde7d8`, label fg `#3a5a3a`, sub fg `#3a5a3a`.
- Dashboard "Flagged" tile bg `#ece0c0`; advisory banner bg `#ece0c0` text `#3a2600`; flagged card bg `#ece2cf`, detail text tones `#3a2600`/`#7a5a10`/`#7a5a40`→ actual: title `#3a2600`, meta `#7a5a10`(via `#7a5a10`?) — use: `f.student` line color `#7a5a10`(rendered as `color:#7a5a10`? actual inline is `color:#7a5a10`)… **exact inline values:** flagged card header text `#3a2600`, sub `#7a5a10`→ inline shows `color:#7a5a40`? Re-check source: meta line uses `color:#7a5a10`. (Inline literal: `#7a5a10`.)
- Hero scene mountain SVG fills: `#0c1226` (opacity .5) and `#080d1c` (opacity .5); hero sub text `#e9e3d2`.
- Sidebar logo bottom mountain fill `#10121a`.
- Log console: header label `#7bf0a0`; filter button level colors `info #8fd0ff`, `ok #7bf0a0`, `warn #ffd27d`, `err #ff8f8f`; timestamp `#6a6090`; default line `#d9d2f0`.
- Dialog backdrop `rgba(18,14,28,.55)`.
- Theme sun icon: disc `#ffce2e`, stroke/eyes `#3a2600`. Moon icon fill `#d6a23f`, stroke `#3a2600`.
- Danger-zone hazard stripe: `repeating-linear-gradient(45deg,#c62d1f,#c62d1f 14px,#3a0a0a 14px,#3a0a0a 28px)`, border `#c62d1f`, header text `#fff` with `text-shadow:1px 1px 0 #3a0a0a`. Divider `1px dashed #c62d1f`.
- Dry-run hatch (timeline banner): `repeating-linear-gradient(45deg,rgba(164,92,247,.16),rgba(164,92,247,.16) 8px,transparent 8px,transparent 16px)` + `border-bottom:1.5px dashed var(--violet)`.

### 1.5 Spacing, radii, borders, shadows (observed scale)
- **Border (hairline):** `1.5px solid var(--line)` is the default everywhere. Nav active/segment buttons use `2.5px` / `3px` (`2.5px solid {{item.border}}` for nav, `3px {{borderStyle}} var(--line)` for mode segments). Log console header divider `2px solid rgba(255,255,255,.12)`. Internal table row separators `1px solid var(--line)`. Inner lesson list items `1px solid var(--line)`.
- **Border radius scale:** logo `4px`; nav buttons `4px`; cards/panels `6px` or `7px`; small buttons / inputs `3–4px`; icon tiles `3px`; pills / chips / progress track / toggle track `99px`; circular avatars/dots `50%`. Hero `7px`. Toast `5px`. Dialog `7px`.
- **Shadows (soft cast):** common values `2px 2px 13px var(--shadowc)`, `2.5px 2.5px 13px`, `3px 3px 13px`, `4px 4px 13px`, `4px 4px 16px`, `5px 5px 16px`, `6px 6px 16px`, `8px 8px 16px` (dialog). Sticky review footer uses `0 -8px 16px rgba(35,30,20,.10)`. Logo `2.5px 2.5px 13px var(--shadowc)`.
- **Padding rhythm:** card headers `~11–18px` vertical, `16–22px` horizontal; card bodies `15–22px`; nav buttons `9px 11px`; table cells `8–11px` × `8–18px`; top bar `13px 22px`; main content wrapper `max-width:1240px; margin:0 auto; padding:26px 28px 60px`.
- **Sidebar widths:** open `232px`, collapsed `74px`; `transition:width .18s ease`.
- **Layout heights:** full viewport `height:100vh; overflow:hidden`; top bar, banner are `flex:none`; main is `flex:1; overflow-y:auto`.

### 1.6 Keyframe animations (verbatim names; respect prefers-reduced-motion)
```
sbblink  0%,100%{opacity:1} 50%{opacity:.35}              /* evaluating dots */
popin    scale .5→1.06→1, translateY 6→0, opacity 0→1     /* toast & dialog entrance */
wiggle   rotate 0/-5deg/5deg                              /* WIN star */
bob      translateY 0→-4px→0                              /* advisory face, flagged mascot, evaluating tree row */
shimmer  background-position -300px→300px                 /* skeletons (defined, used for loading) */
speed    background-position 0→38px                       /* (defined; speed-lines, mostly unused in SJ) */
spin     rotate→360deg
float    translateY/rotate (sleeping mascot)              /* empty-state robot */
blinkz   translateY/opacity (z's)
inkrise  translateY 8→0, opacity 0→1
```
`.squish` class: `transition:transform .13s ease, box-shadow .13s, filter .13s;` `:hover{transform:translateY(-1px);filter:brightness(1.05)}` `:active{transform:translateY(1px) scale(.99)}`.

`@media (prefers-reduced-motion: reduce){ * { animation:none !important; transition:none !important; } }` — MUST be honored.

### 1.7 Scrollbar (custom)
`::-webkit-scrollbar{width:12px;height:12px}` `thumb{background:var(--ink-soft);border:3px solid var(--bg);border-radius:2px}` `track{background:transparent}`.

---

## 2. Global Layout / Chrome

Root: `display:flex; height:100vh; width:100%; overflow:hidden; background:var(--bg); color:var(--ink)`.

### 2.1 Atmospheric backdrop (fixed, behind everything, `z-index:0`, `pointer-events:none`)
1. Red sun disc: `position:absolute; top:-150px; right:-90px; width:560px; height:560px; border-radius:50%; background:var(--sun); opacity:.12` — plus a ring duplicate `border:6px solid var(--sun); opacity:.07`.
2. Mountain silhouettes SVG (`viewBox="0 0 1440 380"`, bottom 40% of viewport): two layered `<path>` ridgelines filled `var(--ink)` at `opacity:.05` and `.045`. (Exact path data in source lines 57.)

### 2.2 Sidebar (`<aside>`, `z-index:20`, `background:var(--panel)`, `border-right:1.5px solid var(--line)`)
- Width: `232px` open / `74px` collapsed.
- **Header (logo block):** 40×40 logo (`border-radius:4px`, `box-shadow:2.5px 2.5px 13px var(--shadowc)`) — an SVG emblem: indigo square (`#1f2a44`) + vermilion sun circle (`var(--sun)`, cx20 cy15 r9) + black mountain-ridge path (`#10121a`). Next to it (when open): wordmark **"Edvibe Grader"** in `'Yuji Syuku',serif`, 21px, `var(--ink)`, `letter-spacing:.5px`; subtitle **"GRADING MISSION-CONTROL"** 10px, `var(--ink-soft)`, weight 600, uppercase, `letter-spacing:1.5px`.
- **Nav** (`flex:1; overflow-y:auto; padding:12px 10px; gap:5px`). 8 items, fixed order. Each is a `<button class="squish">` with `border:2.5px solid {border}; border-radius:4px; font-family:'Shippori Mincho B1',serif; weight:700; font-size:14.5px; text-align:left; padding:9px 11px; gap:11px`.
  - **Inactive:** `bg:transparent; fg:var(--ink); border:transparent; shadow:none`.
  - **Active:** `bg:var(--violet); fg:#fff; border:var(--line); shadow:3px 3px 13px var(--shadowc)` ("pressed" look).
  - Each item has a 20×20 inline-SVG outline icon (stroke `currentColor`, `stroke-width:2.3`). See §6 for the icon set.
  - Items with a count get a trailing count badge: `min-width:20px; font 11px/800 Mincho; padding:1px 6px; border-radius:99px; border:1px solid var(--line); background:var(--yellow); color:#3a2600`. Counts: **Review Queue → number of pending review items (seed = 6)**, **Flagged → 5**. (Source: `counts = { review: pending count, flagged: 5 }`.)
  - Nav order + labels (exact): **Dashboard, New Run, Live Monitor, Review Queue, Students, History, Flagged, Settings**. (Internal screen ids: `dashboard, new, live, review, students, history, flagged, settings`.)
- **Collapse button** (bottom): `class="squish"`, `border:1.5px solid var(--line); border-radius:4px; background:var(--panel2); box-shadow:2px 2px 13px var(--shadowc)`. Glyph `«` (open) / `»` (collapsed), label "Collapse" when open.

### 2.3 Top bar (`<header>`, `flex:none`, `z-index:15`, `background:var(--panel)`, `border-bottom:1.5px solid var(--line)`, `padding:13px 22px; gap:14px`)
Left→right:
1. **Screen title** — `'Shippori Mincho B1',serif; weight:800; 20px; letter-spacing:-.4px`. Value = current screen's title (see title map §3.0).
2. **"Localhost" pill** — `padding:3px 10px; border:1.5px solid var(--line); border-radius:99px; background:var(--lime); color:#fff; Mincho 700 11.5px; box-shadow:1.5px 1.5px 13px var(--shadowc)`, with a leading 8px white dot.
3. Spacer (`flex:1`).
4. **RUN STATUS pill** — `<button class="squish" onClick=goLive>`, `padding:7px 9px 7px 14px; border:1.5px solid var(--line); border-radius:99px; box-shadow:3px 3px 13px var(--shadowc); Mincho 700`. Contains: 11px status dot (`background:{runDotColor}; border:1px solid var(--line)`), label (14px), and — when a run is active — a progress sub-pill (`padding:2px 9px; border-radius:99px; background:rgba(0,0,0,.18)`) reading `"{studentsDone}/{students} students"`. **States** (from `renderVals`):
   - **Idle** (default): label "Idle", dot `var(--c-skip)`, bg `var(--chip)`, fg `var(--ink)`.
   - **Active, dry-run:** label "Dry-run", dot `#6a5a9e`, bg `#3f72b0`, fg `#fff`.
   - **Active, review:** label "Drafting", dot `#3f72b0`, bg `#3f72b0`, fg `#fff`.
   - **Active, full:** label "Running", dot `#cf9a36`, bg `#cf9a36`, fg `#3a2600`.
   - **Finished:** label "Done", dot `#2f8f6b`, bg `#2f8f6b`, fg `#fff`.
5. **Theme toggle** — 42×42 `<button class="squish">`, `border:1.5px solid var(--line); border-radius:4px; box-shadow:2.5px 2.5px 13px var(--shadowc)`. bg = `var(--yellow)` in light, `var(--indigo)` in dark. Light shows a smiling sun (disc `#ffce2e`, eyes/smile/rays stroked `#3a2600`); dark shows a crescent moon (fill `#d6a23f`, eyes `#3a2600`). These are little cartoon faces.
6. **Local-credentials lock chip** — `title="Credentials stored locally only"`; `padding:7px 11px; border:1.5px solid var(--line); border-radius:4px; background:var(--panel2); box-shadow:2px 2px 13px var(--shadowc)`; 17px padlock SVG (stroke `var(--ink)`) + text **"local"** (11px/600, `var(--ink-soft)`).

### 2.4 Mode banner (conditional, only while a run is active, `flex:none`)
`padding:8px 22px; border-bottom:1.5px solid var(--line); Mincho 700 13px`. Two variants:
- **DRY-RUN:** bg `repeating-linear-gradient(45deg,#6a5a9e,#6a5a9e 10px,#4e4179 10px,#4e4179 20px)`, fg `#fff`, icon `👻`, text **"DRY-RUN — evaluating only. Nothing is being submitted to Edvibe."**
- **FULL-AUTO:** bg `repeating-linear-gradient(45deg,#cf9a36,#cf9a36 16px,#e0b85e 16px,#e0b85e 32px)`, fg `#3a2600`, icon `⚠️`, text **"FULL-AUTO — real grades are being submitted and lessons completed."**

### 2.5 Main content area (`<main>`, `flex:1; overflow-y:auto`)
`background-image:radial-gradient(var(--dot) 1.6px, transparent 1.7px); background-size:20px 20px` (halftone dots). Inner wrapper `max-width:1240px; margin:0 auto; padding:26px 28px 60px`.

---

## 3. Screens / Artboards

### 3.0 Screen title map (top bar)
`{ dashboard:'Dashboard', new:'New Run', live:'Live Monitor', review:'Review Queue', students:'Students', history:'History & Audit', flagged:'Flagged', settings:'Settings' }`. (Note: top-bar title for History reads **"History & Audit"** even though the nav label is "History".)

All 8 screens are present and fully built. Details below.

---

### 3.1 DASHBOARD (`screen === 'dashboard'`)
**Region 1 — Stat tiles:** `display:grid; grid-template-columns:repeat(4,1fr); gap:16px`. Each tile: `border:1.5px solid var(--line); border-radius:7px; box-shadow:5px 5px 16px var(--shadowc); padding:16px 17px`. Header row = uppercase label (Mincho 700 12.5px, `letter-spacing:.4px`) + a 30×30 icon tile (`border:1.5px solid var(--line); border-radius:3px`, emoji glyph). Below: value (`Mincho 800 42px; tabular-nums`) + sub text (13px/600). The 4 tiles (verbatim):

| Label | Value | Sub | Tile bg | Icon glyph | Icon bg | Value fg | Star? |
|---|---|---|---|---|---|---|---|
| Pending students | 17 | of 43 | `var(--panel)` | 🧑‍🎓 | `var(--sky)` | `var(--ink)` | no |
| Lessons awaiting | 41 | to grade | `var(--panel)` | 📚 | `var(--pink)` | `var(--ink)` | no |
| Last run | OK | today 09:14 | `#dde7d8` | 🚀 | `var(--lime)` | `#1a7a2e` | **yes** |
| Flagged | 5 | need review | `#ece0c0` | ⚑ | `var(--yellow)` | `#a06a00` | no |

The **WIN star** (`s.star`) on "Last run": absolutely positioned `top:-13px; right:-11px; 46×46`, `animation:wiggle 2.6s infinite`; SVG = vermilion disc (`var(--sun)`) with white ring (`opacity:.55`) and the text **"WIN"** (Mincho 800 12px white). This is the "hanko" stamp.

**Region 2 — Advisory banner** (`margin-top:18px`): speech-notice card, bg `#ece0c0`, `border:1.5px solid var(--line); border-radius:6px; box-shadow:4px 4px 16px var(--shadowc)`. 42px round amber face avatar (`background:var(--yellow)`, `animation:bob 2.4s`, raised-eyebrow expression SVG). Title **"Heads up — there's something to reconcile"** (Mincho 800 15px). Body: **"1 lesson was completed by a previous run. It looks like a leftover — review it in the Reconcile tab before your next full-auto run."** (13.5px; "Reconcile" bold). Right: button **"Reconcile →"** (`background:var(--yellow); color:#3a2600`) → navigates to History/Reconcile tab.

**Region 3 — Hero + Recent runs** (`margin-top:18px; grid-template-columns:340px 1fr; gap:18px; align-items:start`):
- **HERO (left, 340px):** `border:1.5px solid var(--line); border-radius:7px; box-shadow:6px 6px 16px var(--shadowc); background:var(--violet); padding:22px 20px`. Decorative scene (absolute): sun disc (`var(--sun)`, 148px, top-right) + white ring + a 2-layer mountain-ridge SVG at bottom (`#0c1226`/`#080d1c`, opacity .5). Content: title **"Ready to grade?"** (Mincho 800 22px white); sub **"17 students are waiting with 41 lessons. Kick off a run — start with a safe Dry-run."** (13px, `#e9e3d2`). Primary button **"Start a run"** (full width, `background:var(--yellow); color:#3a2600; Mincho 800 18px; box-shadow:4px 4px 13px var(--shadowc)`, play-triangle icon) → New Run. Secondary **"⚡ Quick Dry-run"** (`background:rgba(255,255,255,.16); color:#fff; Mincho 700 12.5px`) → immediately starts a dry-run.
- **RECENT RUNS (right):** card `background:var(--panel)`. Header bar (`background:var(--panel2)`): title **"Recent runs"** (Mincho 800 16px) + **"View all →"** link (`color:var(--violet)`). Table (`font-size:13px`), columns: **Mode · Started · Counts · Status** (uppercase 11px headers). Rows are zebra-striped (`var(--panel)` / `var(--panel2)`), clickable → History detail, `border-top:1px solid var(--line)`. Mode + Status are `StatusBadge` components. The 5 rows (verbatim):

| Mode | modeStatus(badge) | Started | Duration | Counts | Status(badge) | statusLabel |
|---|---|---|---|---|---|---|
| Dry-run | dryrun | Today 09:14 | 2m 41s | 14 ✓ · 3 skip · 1 ⚑ | graded | Success |
| Full-auto | flagged | Yesterday 18:02 | 11m 06s | 38 ✓ · 5 skip · 2 ⚑ | graded | Success |
| Review | queued | Yesterday 12:30 | 4m 12s | 12 draft · 2 ⚑ | flagged | 2 flagged |
| Full-auto | flagged | Mon 20:48 | 9m 33s | 31 ✓ · 1 ✗ | error | 1 error |
| Dry-run | dryrun | Mon 16:10 | 1m 58s | 9 ✓ · 2 skip | graded | Success |

(Note the quirky mapping: a `full` run's MODE badge uses status `flagged` (ochre), a `review` run's mode badge uses `queued` (neutral). Reproduce as-is.)

---

### 3.2 NEW RUN (`screen === 'new'`)
Centered card, `max-width:680px; margin:0 auto`, `background:var(--panel); border:1.5px solid var(--line); border-radius:7px; box-shadow:6px 6px 16px var(--shadowc)`.
- **Header** (`background:var(--panel2)`): title **"Set up a new run"** (Mincho 800 20px); sub **"Pick a mode, choose who to grade, set your safety caps."** (13px, `var(--ink-soft)`).
- **Body** (`padding:22px; gap:22px` column). Sections each have an uppercase Mincho-700 13px section label in `var(--ink-soft)`:
  - **Mode** — segmented `grid-template-columns:repeat(3,1fr); gap:10px`. Each segment `<button class="squish">`, `padding:13px; border:3px {borderStyle} var(--line); border-radius:5px`. Title row = face emoji (18px) + title (Mincho 800 15px); desc (11.5px, `line-height:1.4`). The 3 modes (verbatim):
    1. **Dry-run** — face `👻`, desc **"Evaluate everything, submit nothing. Totally safe."**, `borderStyle: dashed`. Active fill = `repeating-linear-gradient(45deg,#6a5a9e,#6a5a9e 9px,#4e4179 9px,#4e4179 18px)`, fg `#fff`.
    2. **Full-auto** — face `😬`, desc **"Grade AND complete lessons. Irreversible."**, `borderStyle: solid`. Active fill = `repeating-linear-gradient(45deg,#cf9a36,#cf9a36 13px,#e0b85e 13px,#e0b85e 26px)`, fg `#3a2600`.
    3. **Review-queue** — face `📝`, desc **"Draft grades for you to approve before submitting."**, `borderStyle: solid`. Active fill = `var(--sky)`, fg `#fff`.
    Inactive segments: bg `var(--panel2)`, fg `var(--ink)`, desc `var(--ink-soft)`, no shadow. Active adds `box-shadow:3px 3px 13px var(--shadowc)`. Default selected mode = prop `defaultRunMode` (default `dryrun`).
  - **Scope** — two buttons (`gap:10px`): **"All of Mr. Adilet's Pre-IELTS students"** (flex:1) and **"Pick students"** (flex:none). Active button bg `var(--violet)` fg `#fff` shadow `3px 3px 13px`; inactive bg `var(--panel2)` fg `var(--ink)`. When "Pick students" active, a chip panel appears (`background:var(--panel2)`): selected chips (default `['Анель','Dias','Аружан']`) as lime name-tags (`background:var(--lime); color:#fff; border-radius:99px`, each with a `×` remove button on `rgba(0,0,0,.15)` circle). Below: **"＋ add more"** label, then dashed-border suggestion chips from pool `['Timur','Нурайым','Madina','Ерлан','Aizhan','Daniyar','Алишер','Camila']` (first 5 not-yet-picked, prefixed `＋`).
  - **Safety caps** — `grid 1fr 1fr; gap:12px`: number input **"Max students"** (default 43) and **"Max lessons / student"** (default 5), both `Mincho 700 16px` inputs. Below, a full-width toggle button **"Run browser visibly (headed)"** (default off): label left, a 50×28 toggle track right (`border-radius:99px`; track bg `var(--lime)` on / `var(--c-skip)` off; 20px white knob, left `23px` on / `1px` off, `transition cubic-bezier(.34,1.56,.64,1)`).
  - **Confidence threshold** — header row: label + value `{confPct}%` (Mincho 800 18px, `var(--violet)`; default 70%). `<input type="range" min="0.4" max="0.95" step="0.01" value="0.7" style="accent-color:#2b3a5e">`. Hint: **"Below this, the bot flags the item for review instead of grading it."**
- **Footer** (`background:var(--panel2)`): a mode-specific note + the start button.
  - Full mode note: **"⚠️ Submits real grades & completes lessons."** (`color:#a06a00`).
  - Dry mode note: **"👻 Safe — nothing will be submitted."** (`color:var(--violet)`).
  - **Start button** (`<button class="squish">`, `padding:13px 24px; Mincho 800 16px; box-shadow:4px 4px 13px`, play-triangle icon). Label + style per mode:
    - dryrun → **"Start Dry-run"**, bg `var(--violet)`, fg `#fff`.
    - full → **"Start Full-auto run"**, bg `#cf9a36`, fg `#3a2600`.
    - review → **"Start Review-queue run"**, bg `var(--sky)`, fg `#fff`.
  - **Behavior:** full mode opens the confirm dialog (§5.1); other modes start the run immediately and navigate to Live Monitor.

---

### 3.3 LIVE MONITOR (`screen === 'live'`)
**Empty state** (`run.total === 0`): centered column. 140px floating sleeping-robot SVG (`animation:float 4s`; indigo body, panel "screen" face with two closed-eye arcs, antenna with a vermilion sun dot, faint sun halo, two "z" glyphs). Title **"{mascotName} is napping"** (Mincho 800 22px; mascotName prop default **"Vibe-Bot"**). Sub **"No run is in progress. Start one from New Run and the live tree + log will light up here."** Button **"Start a run →"** (`background:var(--violet); color:#fff`).

**Active/Done state** (`run.total > 0`): `grid-template-columns:300px 1fr; gap:18px; align-items:start`.
- **Left — Run tree** card (`background:var(--panel)`): header **"Run tree"** (Mincho 800 15px, `background:var(--panel2)`). Body `max-height:560px; overflow-y:auto`. Structure = **Student ▸ Lesson ▸ Exercise**:
  - Student row: 11px status dot (`background` per state: active blue `#3f72b0`, done `#2f8f6b`, else `var(--c-skip)`) + student name (Mincho 700 14px).
  - Lesson group: indented (`margin-left:18px; border-left:1.5px solid var(--chip); padding-left:10px`), short lesson name (e.g. "Lesson 14") in 12px/600 `var(--ink-soft)`.
  - Exercise row: `padding:4px 7px; border-radius:3px`; bg highlighted `var(--chip)` + `animation:bob 0.9s` when currently evaluating, else transparent. Contains: type icon (`🔊` audio / `✎` text), `"{ex} {label}"` (ex bold-ish 12px, label muted), and a `StatusBadge` (status = the node's current status).
- **Right column** (`gap:16px`):
  - **Progress card:** header row = **"Progress"** (Mincho 800 17px) + a mode `StatusBadge` (dryrun/flagged/queued depending) with label "Dry-run"/"Full-auto"/"Review" + `"{studentsDone}/{students} students · ETA {eta}"` (13px/700) + **Stop** button (only while active: `background:#c62d1f; color:#fff; Mincho 800 13px`, square-stop glyph, `box-shadow:3px 3px 13px`). Progress tube: `height:24px; border:1.5px solid var(--line); border-radius:99px; background:var(--panel2)`, fill = `repeating-linear-gradient(45deg,var(--violet),var(--violet) 11px,#4a5d8f 11px,#4a5d8f 22px)` (width = pct%, `transition:width .5s`, `border-right:1.5px solid var(--line)`). Right of tube: `{pct}%` (Mincho 800 22px, `var(--violet)`, tabular-nums, `min-width:54px`). Caption **"{current} of {total} exercises processed"**. ETA = `Math.max(1, ceil((total-current)*0.9))+'s'` while active, "done" when finished, "—" otherwise.
  - **Detail card** (when a current/last node exists): header = `"{student} · {lesson} · {ex}"` + a type chip ("Audio answer"/"Written answer", `background:var(--chip)`) + a status `StatusBadge`. Body grid `1fr 130px`: left = transcript/answer (italic 13px), an "AI comment" label + comment text, and an action chip; right = score column (`background:var(--panel3)`): "SCORE" label, big score `{score}/10` (Mincho 800 46px; "/10" 20px muted), "CONF {conf}". Action text per status: `skipped`→"Skipped — already auto-checked", `flagged`→"Flagged — confidence below threshold", `error`→"Error — audio download failed", `graded`→ dry: "Graded — NOT submitted (dry-run)" / live: "Graded & submitted ✓", `evaluating`→"Evaluating…". Transcript label = "Transcript" (audio) / "Answer" (text). When no review record exists, text falls back to "Transcribing audio answer…" / "Reading written answer…" and comment "Awaiting model output…".
  - **Log console** (`background:var(--logbg)`): header (`border-bottom:2px solid rgba(255,255,255,.12)`): **"● live log"** (`JetBrains Mono 600 12.5px`, `#7bf0a0`) + level filter buttons: **All · Info · OK · Warn · Error** (active bg `var(--violet)` fg `#fff`; inactive bg `rgba(255,255,255,.08)` fg `var(--logink)`). Body `max-height:220px; overflow-y:auto; JetBrains Mono 12px; line-height:1.65`. Each line = timestamp (`#6a6090`) + message, colored by level: `info #8fd0ff`, `ok #7bf0a0`, `warn #ffd27d`, `err #ff8f8f`.
  - **Live simulation log message templates** (verbatim, from `tick()`):
    - Start: `"Run started · mode={mode} · {n} students queued · headed={yes|no}"`.
    - Begin item: `"{student} ▸ {lessonShort} ▸ {ex} — transcribing audio…"` or `"… — evaluating answer…"`.
    - Graded: `"  → {student} {ex} scored {score}/10 · NOT submitted (dry-run)"` or `"· submitted ✓"`.
    - Skipped: `"  → {student} {ex} already auto-checked · skipped"`.
    - Flagged: `"  ⚑ {student} {ex} low confidence (0.61) · flagged for review"`.
    - Error: `"  ✗ {student} {ex} audio download failed · error (screenshot saved)"`.
    - Complete: `"Run complete · {n} processed"`.
  - Tick interval = **900ms**. On complete, toast: dry → "Dry-run finished — nothing was submitted" (info); else → "Run finished — {g} grades submitted" (ok).

---

### 3.4 REVIEW QUEUE (`screen === 'review'`)
**Empty/all-done state** (`review.every(submitted)`): centered. 120px bobbing green check-circle SVG (`fill:var(--lime)`, white check). Title **"Queue's all clear!"**; sub **"Every proposed grade has been reviewed and submitted. Nice work."**

**Active state:**
- **Filter bar** (flex, wrap, `gap:9px`): label **"FILTER"** (uppercase 12px/700) + type filter pills **"All types" · "🔊 Audio" · "✎ Text"** (active bg `var(--violet)` fg `#fff`; inactive bg `var(--panel)` fg `var(--ink)`; `box-shadow:2px 2px 13px`). Then a divider, plus two decorative dropdown buttons **"Student ▾"** and **"Confidence ▾"**. Right side: **"⚡ Approve high-confidence"** (`background:var(--sky); color:#fff`; approves items with conf ≥ 0.85) and **"✓ Approve all"** (`background:var(--lime); color:#fff`).
- **Cards** (`flex column; gap:14px; padding-bottom:80px`). Each card `border:1.5px solid var(--line); border-radius:6px; box-shadow:4px 4px 16px var(--shadowc)`; bg varies by status: pending `var(--panel)`, approved `rgba(31,207,93,.08)`, rejected `rgba(255,77,77,.07)`, submitted `var(--panel2)`.
  - **Card header** (`background:var(--panel2)`): type icon, student name (Mincho 800 15px), `"{lesson} · {section} · ex {ex}"` (12.5px muted). An **"EDITED"** badge (`background:var(--yellow); color:#3a2600`, 10.5px/800) when edited. When not pending, a status `StatusBadge` (approved→graded/"Approved", rejected→error/"Rejected", submitted→graded/"Submitted").
  - **Card body** grid `1fr 200px`:
    - Left: for audio items, an inline player (`border:1.5px solid var(--line); background:var(--panel)`): round violet play button, an 8px progress bar (24% filled `var(--violet)`), and a mono time label `"0:00 / {dur}"`. Then a content label ("Transcript" audio / "Written answer" text), the italic text, an "AI comment · editable" label, and an editable `<textarea>` (`min-height:58px; Inter 13px`) pre-filled with the comment.
    - Right (score column, `background:var(--panel3)`): "SCORE" label; a `−` / number / `＋` stepper (`34×34` buttons Mincho 800 20px; number Mincho 800 40px tabular, width 58px; clamps 0–10, marks item edited on change). "out of 10". A confidence meter: "CONFIDENCE" label + `{pct}%` (color by level), and a 5-segment battery bar (`height:11px; border:1px solid var(--line); border-radius:4px`; lit segments = `round(conf*5)`, lit color by level, unlit `var(--chip)`). Confidence color thresholds: ≥0.85 `#2f8f6b`, ≥0.70 `#3f72b0`, else `#cf9a36`. Reject/Approve buttons (`flex 1` each): reject = X icon (active bg `#c62d1f` fg `#fff`; inactive `var(--panel2)`/`var(--ink)`); approve = thumbs-up icon (active bg `#2f8f6b` fg `#fff`; inactive `var(--panel2)`/`var(--ink)`).
- **Sticky footer** (`position:sticky; bottom:0; margin:0 -28px -60px; background:var(--panel); box-shadow:0 -8px 16px rgba(35,30,20,.10)`): summary **"{approvedN} approved"** (`#1a7a2e`) **"{editedN} edited"** (`var(--ink-soft)`) **"{rejectedN} rejected"** (`#c63`), and a primary **"Submit {approvedN} grades →"** button (`background:var(--lime); color:#fff; Mincho 800 15px`).

**Seed review items (verbatim sample data — 6 items):**
1. **Анель** · Lesson 14 — Entertainment · Entertainment discussion · ex **1.2** · audio (02:04) · score **7** · conf **0.84** · text: _"In my free time I like watching the series and listen to podcasts about science. Last weekend I have watched a documentary about ocean, it was really interesting and I learn many new words…"_ · comment: **"Good task response and clear pronunciation; watch past-tense endings and link your ideas with connectors."**
2. **Dias** · Lesson 14 — Entertainment · Grammar · ex **2.1** · text · score **9** · conf **0.91** · text: _"If I _had_ more time, I _would learn_ to play the guitar. She _has been_ working here since 2019."_ · comment: **"Excellent — all conditional and perfect forms correct. Minor: spacing around blanks."**
3. **Аружан** · Lesson 12 — Travel · Vocabulary · ex **3.4** · text · score **6** · conf **0.66** · text: _"destination, itinerary, sightseeing, accomodation, departure"_ · comment: **"Most words used correctly. Spelling: "accomodation" → "accommodation". Add example sentences next time."**
4. **Timur** · Lesson 14 — Entertainment · Shadowing · ex **3.1** · audio (01:12) · score **8** · conf **0.88** · text: _"The film industry has changed dramatically over the past decade, with streaming platforms…"_ · comment: **"Strong rhythm and intonation. A couple of dropped word-endings — keep it up!"**
5. **Нурайым** · Lesson 13 — Health · Reading time. · ex **1.1** · text · score **5** · conf **0.62** · text: _"The passage is about how sleep affect our memory and the writer think teenagers need more sleep."_ · comment: **"Main idea captured but several grammar slips (affect/affects, think/thinks). Re-read for subject–verb agreement."**
6. **Madina** · Lesson 14 — Entertainment · Entertainment discussion · ex **1.3** · audio (01:48) · score **9** · conf **0.95** · text: _"I think social media changed how we consume entertainment completely. We can discover new artists instantly…"_ · comment: **"Fluent, well-organised and natural. Great use of linking phrases."**

---

### 3.5 STUDENTS (`screen === 'students'`)
Single card (`background:var(--panel)`). Header: title **"Students"** (Mincho 800 17px) + chip **"43 in marathon"** (`background:var(--sky); color:#fff`) + right-aligned **"Marathon: Pre-IELTS · Curator: Mister Adilet"**. Compact table (`font-size:13.5px`), header row `background:var(--panel3)`, columns: **(chevron) · Student · Awaiting · Last activity · Curator · Action** (uppercase 11px headers). Rows zebra (`var(--panel)`/`var(--panel2)`), clickable to expand (chevron `▸`/`▾`). Cells: name (Mincho 700 14.5px), Awaiting = a `StatusBadge` (status `idle` if 0 else `queued`, label = the count), Last activity (muted), Curator = "Mister Adilet", Action = **"▶ Run"** button (`background:var(--violet); color:#fff; Mincho 700 12px`) — stops propagation, toasts "Queued a run for {name}".
Expanded row (`background:var(--panel3)`): label **"Awaiting lessons"** then a list of lesson chips (`border:1px solid var(--line); background:var(--panel)`) each = lesson name + a `StatusBadge`. If no lessons: **"No awaiting lessons — all caught up. 🎉"** (italic).

**Student roster (verbatim, 12 rendered rows; "43 in marathon" is the headline count):**
| Student | Awaiting | Last | Lessons (name, status) |
|---|---|---|---|
| Анель | 3 | 2h ago | Lesson 14 — Entertainment (queued), Lesson 13 — Health (queued), Lesson 12 — Travel (flagged) |
| Dias | 2 | 4h ago | Lesson 14 — Entertainment (queued), Lesson 13 — Health (queued) |
| Аружан | 4 | 1d ago | Lesson 12 — Travel (flagged), Lesson 13 — Health (queued), Lesson 14 — Entertainment (queued), Lesson 11 — Work (queued) |
| Timur | 1 | 6h ago | Lesson 14 — Entertainment (error) |
| Нурайым | 3 | 3h ago | Lesson 13 — Health (queued), Lesson 12 — Travel (queued), Lesson 14 — Entertainment (queued) |
| Madina | 1 | 30m ago | Lesson 14 — Entertainment (queued) |
| Ерлан | 2 | 1d ago | Lesson 13 — Health (queued), Lesson 12 — Travel (queued) |
| Алишер | 0 | 5d ago | — (all caught up) |
| Camila | 2 | 8h ago | Lesson 14 — Entertainment (queued), Lesson 11 — Work (queued) |
| Бекзат | 3 | 2d ago | Lesson 12 — Travel (queued), Lesson 13 — Health (queued), Lesson 14 — Entertainment (queued) |
| Aizhan | 1 | 12h ago | Lesson 13 — Health (queued) |
| Daniyar | 0 | 1w ago | — (all caught up) |

---

### 3.6 HISTORY / AUDIT (`screen === 'history'`)
Two tabs (`gap:8px` buttons, active bg `var(--violet)` fg `#fff` shadow): **"Runs"** and **"Reconcile"** (Reconcile has a `1` count badge on `var(--yellow)`).

**Runs tab** — `grid-template-columns:1fr 1.1fr; gap:18px`:
- **Left — All runs** table (`font-size:12.5px`): rows = mode `StatusBadge` + started/duration + counts + status `StatusBadge`. Selected row highlighted `var(--chip)`. Same 5 runs as Dashboard Recent runs (h1–h5), counts formatted `"{g} ✓ · {sk} skip · {fl} ⚑ [· {er} ✗]"`:
  - h1 Dry-run, Today 09:14, 2m 41s, 14✓·3skip·1⚑, graded/Success
  - h2 Full-auto, Yesterday 18:02, 11m 06s, 38✓·5skip·2⚑, graded/Success
  - h3 Review, Yesterday 12:30, 4m 12s, 12✓·0skip·2⚑, flagged/2 flagged
  - h4 Full-auto, Mon 20:48, 9m 33s, 31✓·0skip·0⚑·1✗, error/1 error
  - h5 Dry-run, Mon 16:10, 1m 58s, 9✓·2skip·0⚑, graded/Success
- **Right — Run timeline** card: header = **"Run timeline"** + mode `StatusBadge` + **"⬇ Export"** button (`background:var(--sky); color:#fff`; toasts "Exported run {id} as CSV"). If selected run is dry: a dashed-purple hatch banner **"👻 Dry-run — proposed scores were computed but nothing was submitted."** Timeline = vertical track (`3px var(--chip)` rail) with 13px node dots (color by status: graded `#2f8f6b`, flagged `#cf9a36`, error `#c62d1f`, else `var(--c-skip)`). Each node: `"{student} · {ex}"` + optional **"HUMAN EDITED"** badge (`background:var(--yellow); color:#3a2600`) + mono timestamp + **"proposed {p} → submitted {s}"** (submitted shows "—" for dry-run; `submittedFg` muted when "—"). Timeline entries (verbatim, ts uses selected run's start time):
  - Анель 1.2 — proposed 7 → submitted 7(or — if dry) — graded
  - Анель 2.1 — proposed — → submitted — — skipped
  - Dias 1.2 — proposed 6 → submitted 7(or —) — graded — **HUMAN EDITED**
  - Dias 2.1 — proposed 9 → submitted 9(or —) — graded
  - Аружан 3.4 — proposed — → submitted — — flagged
  - Timur 3.1 — proposed — → submitted — — error

**Reconcile tab** — card, header **"Reconcile · what's complete on Edvibe"** + sub **"Read-only view. Anything the bot completed unexpectedly is flagged for your attention."** Table columns: **Student · Lesson · Completed by · (flag)**. Rows (verbatim):
| Student | Lesson | Completed by | Flag |
|---|---|---|---|
| Анель | Lesson 14 — Entertainment | This bot · today 09:14 | — |
| Dias | Lesson 14 — Entertainment | This bot · today 09:15 | — |
| Нурайым | Lesson 13 — Health | Previous run · yesterday | **StatusBadge flagged, label "Leftover — check"** |
| Madina | Lesson 12 — Travel | Manually completed | — |

---

### 3.7 FLAGGED (`screen === 'flagged'`)
`grid-template-columns:repeat(2,1fr); gap:14px`. Each card: bg `#ece2cf`, `border:1.5px solid var(--line); border-radius:6px; box-shadow:4px 4px 16px`. Left: 46px round amber raised-eyebrow mascot avatar (`background:var(--yellow)`, `animation:bob 2.6s`). Right: reason (Mincho 800 15px, text `#3a2600`) + severity badge (`background:#fff; color:#a06a00`), a meta line `"{student} · {lesson} · ex {ex}"` (`color:#7a5a10`), and the detail paragraph (`color:#3a2600`). Footer buttons: **"Resolve manually"** (`background:var(--violet); color:#fff`, flex:1; toasts "Opening {student} {ex} for manual review") and **"↻ Retry"** (`background:#fff; color:#3a2600`; toasts "Retrying {student} {ex}…").

**Flagged items (verbatim, 5 cards):**
1. **Аружан** · Lesson 12 — Travel · ex 3.4 · reason **"Low confidence"** · sev **"Needs a look"** · detail: **"Confidence 0.61 — below your 0.70 threshold. The answer mixes correct and misspelled vocabulary, so the bot held off."**
2. **Timur** · Lesson 14 — Entertainment · ex 3.1 · reason **"Audio download failed"** · sev **"Blocked"** · detail: **"The shadowing audio returned 403 from the Edvibe CDN after 3 retries. No transcript could be produced."**
3. **Dias** · Lesson 14 — Entertainment · ex 2.2 · reason **"Selector not found"** · sev **"Blocked"** · detail: **"The score input field did not appear within 15s. The lesson page layout may have changed."**
4. **Madina** · Lesson 13 — Health · ex 1.4 · reason **"OpenAI error"** · sev **"Transient"** · detail: **"Rate limit (429) hit during evaluation. The item will retry automatically on the next run."**
5. **Нурайым** · Lesson 12 — Travel · ex 2.1 · reason **"Low confidence"** · sev **"Needs a look"** · detail: **"Confidence 0.64 — the answer drifts partly off-topic, so a human should score it."**

---

### 3.8 SETTINGS (`screen === 'settings'`)
`max-width:760px; margin:0 auto; flex column; gap:16px`. All inputs `border:1.5px solid var(--line); border-radius:3px; background:var(--panel2); font-size:13.5px`.
- **Credentials** card: header icon tile (`background:var(--lime)` padlock) + title **"Credentials"** + chip **"🔒 stored locally only"** (`background:var(--lime); color:#fff`). Body grid `1fr 1fr`: **Edvibe login** = `mr.adilet@edvibe.com` (text); **Edvibe password** = `hunter2hunter2` (type=password, mono); **OpenAI API key** (full width) = `sk-proj-aBcD1234EfGh5678` (type=password, mono).
- **Models + Grading** (`grid 1fr 1fr; gap:16px`):
  - **Models:** Transcription model = `whisper-1`; Evaluation model = `gpt-4o`.
  - **Grading:** Score scale = `0 – 10`; Confidence threshold = `0.70`; Rubric notes (textarea) = **"Reward task response & coherence; be gentle on minor grammar."**
- **Behavior** card (`grid 1fr 1fr`): Default mode = `Dry-run`; Pacing delay (ms) = `900`; Marathon = `Pre-IELTS`; Curator = `Mister Adilet`.
- **Danger zone** card: `border:1.5px solid #c62d1f`. Header = hazard stripe `repeating-linear-gradient(45deg,#c62d1f,#c62d1f 14px,#3a0a0a 14px,#3a0a0a 28px)` with **"⚠️ Danger zone"** (white, `text-shadow:1px 1px 0 #3a0a0a`). Two rows separated by `1px dashed #c62d1f`:
  - **"Clear all local data"** — "Wipes credentials, run history and settings from this machine." — button **"Clear data"** (`background:#fff; color:#c00`).
  - **"Reset bot to defaults"** — "Restores all behavior settings, keeps your credentials." — button **"Reset"** (`background:#fff; color:#c00`).

---

## 4. StatusBadge Component (full spec)

Source: `StatusBadge.dc.html`. A `<span>` pill: `display:inline-flex; align-items:center; gap:5px; padding:3px 9px 3px 6px; border:{bd}; border-radius:3px; background:{bg}; color:{fg}; font-family:'Shippori Mincho B1',serif; font-weight:700; font-size:11px; letter-spacing:.4px; text-transform:uppercase; line-height:1; white-space:nowrap`. Contains a 15×15 inline-SVG **face/icon** (stroke `currentColor`) + the label text. `data-status` attribute carries the status.

**Props:** `status` (enum, default `graded`), `label` (text — overrides default label if provided). `$preview` hint 150×40.

**Variant map (verbatim from `renderVals`):**
| status | default label | bg | fg | border (`bd`) | face icon |
|---|---|---|---|---|---|
| `evaluating` | Evaluating | `#3f72b0` | `#ffffff` | none | 3 blinking dots (`animation:sbblink 1.1s`, decreasing opacity) |
| `graded` | Graded | `#2f8f6b` | `#ffffff` | none | smiley (two dot eyes + smile arc) |
| `skipped` | Skipped | `var(--c-skip)` | `var(--ink)` | none | neutral (eyes + flat mouth) |
| `flagged` | Flagged | `#cf9a36` | `#241a00` | none | raised-eyebrow (curved brow + eyes + smile) |
| `error` | Error | `#c62d1f` | `#ffffff` | none | X-eyes (two X eyes + frown) |
| `dryrun` | Dry-run | `repeating-linear-gradient(45deg,#6a5a9e,#6a5a9e 6px,#4e4179 6px,#4e4179 12px)` | `#ffffff` | `1.5px dashed rgba(255,255,255,.6)` | ghost shape (wavy hem + two dot eyes) |
| `idle` | Idle | `var(--chip)` | `var(--ink)` | none | sleepy (two arch brows + flat mouth) |
| `queued` | Queued | `var(--chip)` | `var(--ink-soft)` | none | sleepy (same as idle) |
| `running` | Running | `#3f72b0` | `#ffffff` | none | smiley (same icon group as graded) |

Icon groupings in template: `isGraded` (graded OR running) → smiley; `isEval` → blinking dots; `isSkipped` → neutral; `isFlag` → raised brow; `isErr` → X-eyes; `isDry` → ghost; `isIdle` (idle OR queued) → sleepy.

**Status semantics (preserved from brief, KEEP MEANINGS):** evaluating = blue, graded/done = green (jade), skipped = gray, flagged/needs-review = amber (ochre), error = red (vermilion), dry-run = dashed/striped purple ("ghost"). These map to the muted SJ palette but meanings are unchanged.

---

## 5. Overlays / Components

### 5.1 Confirm Dialog (`{{ dialog }}`)
Backdrop: `position:fixed; inset:0; z-index:70; background:rgba(18,14,28,.55)`, centered, closes on backdrop click. Modal: `width:440px; background:var(--panel); border:1.5px solid var(--line); border-radius:7px; box-shadow:8px 8px 16px var(--shadowc); animation:popin .28s`. Header (`background:{dialogHeadBg}`): a 52px white round avatar with a serious worried-face SVG (`#3a2600` strokes, X-ish brows + dot eyes + flat mouth) + title (Mincho 800 19px, `#3a2600`). Body: paragraph (14.5px) + a dashed note box (`🔒 {note}`) + Cancel/Confirm buttons. Two configs:
- **`dialog === 'full'`:** title **"Start a Full-auto run?"**; body **"This will submit REAL grades and mark lessons complete on edvibe.com. These actions are irreversible."**; note **"Credentials are stored locally only — nothing leaves this machine except grade submissions to Edvibe."**; confirm **"Yes, run full-auto"** (bg `#cf9a36`, fg `#3a2600`); header bg `repeating-linear-gradient(45deg,#ffe0a3,#ffe0a3 12px,#ffd27d 12px,#ffd27d 24px)`. On confirm → `startRun('full')`.
- **`dialog === 'stop'`:** title **"Stop this run?"**; body **"The bot will finish the current exercise and halt. Already-submitted grades stay submitted; remaining students will be left untouched."**; note **"You can resume later from New Run — completed students are skipped automatically."**; confirm **"Stop the run"** (bg `#c62d1f`, fg `#fff`); header bg `#e8d8d2`. On confirm → `stopRun()`.
Cancel button: `background:var(--panel2); color:var(--ink)`.

### 5.2 Toast (`{{ toast }}`)
`position:fixed; bottom:24px; left:50%; transform:translateX(-50%); z-index:60; padding:13px 20px; border:1.5px solid var(--line); border-radius:5px; box-shadow:5px 5px 13px; Mincho 700 14px; animation:popin .3s`. Auto-dismiss after **3200ms**. Variants by `kind`: `ok` → bg `#2f8f6b` fg `#fff` icon `🎉`; `err` → bg `#c62d1f` fg `#fff` icon `💥`; `warn` → bg `#cf9a36` fg `#3a2600` icon `⚠️`; `info`/default → bg `var(--violet)` fg `#fff` icon `👻`.

### 5.3 Buttons (general patterns)
All interactive controls carry `class="squish"` (hover lift + brightness, active dip). Primary buttons: `Mincho` 700–800, hairline border, soft shadow, sharp-ish radius (3–5px). Color = role accent (violet primary, lime confirm/success, sky info, ochre full-auto/caution, vermilion danger/stop).

### 5.4 Cards / Tables (general patterns)
Cards: `border:1.5px solid var(--line); border-radius:6–7px; box-shadow:5px 5px 16px var(--shadowc)`, header strip `background:var(--panel2)`. Tables: `border-collapse:collapse`, uppercase 11px Mincho headers, zebra rows (`var(--panel)`/`var(--panel2)`), `border-top:1px solid var(--line)` separators, tabular-nums for numeric/count cells.

---

## 6. Asset Inventory

- **Icons:** ALL **inline hand-authored SVG** (no icon font, no library). Nav icons (8, 20×20, stroke 2.3): dashboard = 4 rounded squares; new run = play-triangle + vertical bar; live = pulse/broadcast arcs + center dot; review = clipboard with check; students = two people; history = clock; flagged = flag pole; settings = gear. Status faces (15×15) live in StatusBadge. Other inline SVGs: theme sun/moon faces, padlock, hero & backdrop mountains + sun discs, sleeping robot mascot, raised-eyebrow & worried mascot faces, WIN hanko stamp, green check-circle (empty review), play/stop/thumbs/X glyphs.
- **Emoji glyphs** used as icons in markup (render as system emoji): 🧑‍🎓 📚 🚀 ⚑ 👻 😬 📝 ⚠️ 🔒 🔊 ✎ ⚡ ✓ ▶ ↻ ⬇ ▾ ▸ 🎉 💥 ● ＋ ×.
- **Images:** none real — only SVG decorative scenery (sun discs, mountain ridgelines). No photos/raster assets.
- **Fonts:** Google Fonts — Shippori Mincho B1, Yuji Syuku, Inter, JetBrains Mono (see §1.1).
- **Textures:** halftone radial-dot pattern on `<main>` (`var(--dot)`, 20px grid); hazard/ghost `repeating-linear-gradient` stripes; mountain-silhouette backdrop.

---

## 7. Interactions / Notes (what the user emphasized; rejected directions)

**Emphasized (carry forward):**
- **Unmissable DRY-RUN vs FULL-AUTO distinction.** Dry-run = "ghost" dashed-purple hatch accents + "nothing submitted" messaging everywhere (banner, badge, footer note, timeline note, toast). Full-auto = solid ochre hazard-stripe accents + an irreversible-action confirm dialog. The styling must make this distinction MORE obvious, not less.
- **Trustworthy & precise despite the stylized skin** — irreversible actions are gated by confirm dialogs; data tables stay compact and legible.
- **Status semantics are sacrosanct** (evaluating/graded/skipped/flagged/error/dry-run color meanings — see §4). Only the rendering changed (to muted SJ palette), never the meaning.
- **Live run simulation** — ticking progress, auto-advancing tree highlight (bob bounce on the evaluating item), streaming filterable log. Tick = 900ms.
- **Mascot presence** — sleeping robot in empty states, worried mascot in confirm dialogs, status faces in badges, raised-eyebrow on advisory/flagged.
- **Accessibility** — visible focus, AA+ contrast in both themes, and `prefers-reduced-motion` disables all animation/transition (already in CSS).
- **Editor-tweakable props:** `mascotName` (default "Vibe-Bot") and `defaultRunMode` (enum dryrun/full/review, default dryrun). In React, surface these as configurable props/settings.

**Rejected direction (DO NOT BUILD):** the original Y2K / early-2000s Saturday-morning cartoon look (thick black inked outlines, hard offset sticker shadows, blobby rounded-2xl corners, candy-violet/lime/hot-pink chaos palette, Baloo/Fredoka/Nunito fonts, speed-lines, "pow" callouts). That was explicitly replaced by Samurai Jack. (It survives only in the ignored backup file.)

**Open/ambiguous (from the agent's closing note):** the warm-lit "Last run" (`#dde7d8`) and "Flagged" (`#ece0c0`) dashboard tiles, the advisory banner (`#ece0c0`), and flagged cards (`#ece2cf`) keep light/warm backgrounds even in dark mode (reading as "lit scrolls"). The designer offered to darken these for full uniformity but left them warm. Confirm with the user before deciding.

---

## 8. Target stack reminder (from brief)
React + TypeScript + Tailwind CSS + shadcn/ui. Desktop-first (min 1280px), responsive down to a laptop. Light + dark themes (theme via a `data-theme` attribute / class strategy). Map the `.dc.html` runtime constructs to JSX: `sc-if`→conditional render, `sc-for`→`.map()`, `dc-import StatusBadge`→`<StatusBadge>`, `{{ }}`→props/state, `onClick={{...}}`→handlers. Replace inline styles with Tailwind utilities + CSS variables (keep the exact token values from §1).

---

## 9. "Screens to build" checklist (mapped to the app's 8 screens)

| App screen | Covered by design? | Maps to design screen | Notes |
|---|---|---|---|
| **Dashboard** | ✅ Yes, fully | `dashboard` (§3.1) | 4 stat tiles, advisory banner, hero + recent-runs table. |
| **New Run** | ✅ Yes, fully | `new` (§3.2) | Mode segments, scope picker, safety caps, confidence slider, mode-relabeled start button + full-auto confirm dialog. |
| **Live Monitor** | ✅ Yes, fully | `live` (§3.3) | Empty (napping mascot) + active states; tree, progress tube, detail card, log console + simulation. |
| **Review Queue** | ✅ Yes, fully | `review` (§3.4) | All-done empty state + filter bar + editable score/comment cards + sticky submit footer. |
| **Students** | ✅ Yes, fully | `students` (§3.5) | Compact zebra table, expandable rows, per-row Run action. (12 sample rows; headline "43 in marathon".) |
| **History/Audit** | ✅ Yes, fully | `history` (§3.6) | Two tabs: **Runs** (list + timeline + export) and **Reconcile** (leftover-flag table). Top-bar title is "History & Audit". |
| **Flagged** | ✅ Yes, fully | `flagged` (§3.7) | 5 amber notice cards with reason/severity/detail + Resolve/Retry. |
| **Settings** | ✅ Yes, fully | `settings` (§3.8) | Credentials, Models, Grading, Behavior, hazard-striped Danger zone. |

**All 8 app screens are covered by the design.** No screen is missing. Additional cross-cutting UI present: global confirm Dialog, Toast, Mode banner, custom StatusBadge, custom scrollbar. Not explicitly built (mentioned in brief but absent in shipped markup): a Command palette (⌘K) and standalone loading skeletons (shimmer keyframe exists but no skeleton components are wired up) — treat as optional/future per the agent's closing note.

---

## 10. Known inconsistencies / reproduce-as-is gotchas
1. **Mode→badge color mapping is non-literal:** a `full` run's MODE badge uses status `flagged` (ochre), and a `review` run's mode badge uses `queued` (neutral). This is intentional in the source — reproduce exactly (do not "fix" to a full-auto-specific color).
2. **Warm tiles in dark mode** (§7 open item): several warm backgrounds are hardcoded and don't invert. Confirm intent.
3. **Awaiting badge label** on Students table shows the raw count as the badge label (status idle/queued), not the default "Idle"/"Queued" text.
4. **Reconcile count badge** is hardcoded `1` on the tab; the reconcile table has exactly 1 flagged leftover (Нурайым). Keep in sync if data changes.
5. **Sidebar nav counts:** Review = live pending count (seed 6), Flagged = hardcoded 5 (the Flagged screen actually renders 5 cards; consistent).
6. **`--shadow` and `speed`/`shimmer` keyframes** are declared but largely unused in the SJ version (shimmer reserved for future skeletons). Keep tokens; wiring optional.
