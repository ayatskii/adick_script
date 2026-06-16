# Edvibe Grader Web Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the scaffold, design tokens, app shell, shared components, seed data, and 8 stub screens for the Edvibe Grader React frontend so screen-implementers can fill each screen next.

**Architecture:** Vite + React 18 + TypeScript + Tailwind CSS in `/home/ayatskii/adick_script/web`. Design tokens live exclusively as CSS custom properties in `src/index.css`; Tailwind uses `bg-[var(--panel)]`-style arbitrary values to reference them. App state is held in `App.tsx` and passed down via props/a small context — no Redux or Zustand needed at this stage.

**Tech Stack:** Vite 5, React 18, TypeScript 5, Tailwind CSS 3, PostCSS, Autoprefixer, @vitejs/plugin-react, Google Fonts (Shippori Mincho B1, Yuji Syuku, Inter, JetBrains Mono).

**Working directory:** `/home/ayatskii/adick_script/web`
**Git branch:** `edvibe-grader-build`

---

## File Map

```
web/
├── index.html                      # root HTML + Google Fonts link + <div id="root">
├── package.json                    # dependencies & scripts
├── vite.config.ts                  # Vite config
├── tsconfig.json                   # TypeScript project config
├── tsconfig.node.json              # TypeScript for vite.config
├── tailwind.config.js              # content paths only; no theme extension needed
├── postcss.config.js               # autoprefixer
└── src/
    ├── main.tsx                    # ReactDOM.createRoot + <App />
    ├── index.css                   # ALL tokens (:root, [data-theme="dark"]), keyframes, scrollbar, .squish, @media prefers-reduced-motion
    ├── types.ts                    # Domain TypeScript types
    ├── data.ts                     # All verbatim seed data
    ├── App.tsx                     # Root shell + state + routing
    ├── AppContext.tsx              # React context for app state/handlers
    ├── components/
    │   ├── icons.tsx               # 8 nav SVG icons + sun/moon + padlock
    │   ├── StatusBadge.tsx         # Full §4 StatusBadge component
    │   ├── Backdrop.tsx            # Fixed atmospheric backdrop
    │   ├── Sidebar.tsx             # Sidebar nav + collapse
    │   ├── TopBar.tsx              # Top bar: title, localhost pill, run status pill, theme toggle, lock chip
    │   ├── ModeBanner.tsx          # Conditional mode banner (dry-run / full-auto)
    │   ├── Toast.tsx               # Auto-dismiss toast overlay
    │   └── Dialog.tsx              # Confirm dialog overlay
    └── screens/
        ├── Dashboard.tsx           # STUB
        ├── NewRun.tsx              # STUB
        ├── LiveMonitor.tsx         # STUB
        ├── ReviewQueue.tsx         # STUB
        ├── Students.tsx            # STUB
        ├── History.tsx             # STUB
        ├── Flagged.tsx             # STUB
        └── Settings.tsx            # STUB
```

---

## Task 1: Git branch + scaffold package.json and config files

**Files:**
- Create: `/home/ayatskii/adick_script/web/package.json`
- Create: `/home/ayatskii/adick_script/web/vite.config.ts`
- Create: `/home/ayatskii/adick_script/web/tsconfig.json`
- Create: `/home/ayatskii/adick_script/web/tsconfig.node.json`
- Create: `/home/ayatskii/adick_script/web/tailwind.config.js`
- Create: `/home/ayatskii/adick_script/web/postcss.config.js`

- [ ] **Step 1: Create the git branch and web directory**

```bash
cd /home/ayatskii/adick_script
git checkout -b edvibe-grader-build
mkdir -p web/src/components web/src/screens
```

- [ ] **Step 2: Create package.json**

Create `/home/ayatskii/adick_script/web/package.json`:
```json
{
  "name": "edvibe-grader",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.4",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.16",
    "typescript": "^5.6.3",
    "vite": "^5.4.11"
  }
}
```

- [ ] **Step 3: Create vite.config.ts**

Create `/home/ayatskii/adick_script/web/vite.config.ts`:
```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
```

- [ ] **Step 4: Create tsconfig.json**

Create `/home/ayatskii/adick_script/web/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 5: Create tsconfig.node.json**

Create `/home/ayatskii/adick_script/web/tsconfig.node.json`:
```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true,
    "strict": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 6: Create tailwind.config.js**

Create `/home/ayatskii/adick_script/web/tailwind.config.js`:
```js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

- [ ] **Step 7: Create postcss.config.js**

Create `/home/ayatskii/adick_script/web/postcss.config.js`:
```js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 8: Commit**

```bash
cd /home/ayatskii/adick_script
git add web/
git commit -m "feat(web): scaffold config files (package.json, vite, tsconfig, tailwind)"
```

---

## Task 2: index.html + src/main.tsx

**Files:**
- Create: `/home/ayatskii/adick_script/web/index.html`
- Create: `/home/ayatskii/adick_script/web/src/main.tsx`

- [ ] **Step 1: Create index.html** with Google Fonts link and root div

Create `/home/ayatskii/adick_script/web/index.html`:
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Edvibe Grader</title>
    <link href="https://fonts.googleapis.com/css2?family=Shippori+Mincho+B1:wght@600;700;800&family=Yuji+Syuku&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 2: Create src/main.tsx**

Create `/home/ayatskii/adick_script/web/src/main.tsx`:
```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

- [ ] **Step 3: Commit**

```bash
cd /home/ayatskii/adick_script
git add web/index.html web/src/main.tsx
git commit -m "feat(web): add index.html with Google Fonts and src/main.tsx entry"
```

---

## Task 3: src/index.css — all design tokens, keyframes, scrollbar, .squish

**Files:**
- Create: `/home/ayatskii/adick_script/web/src/index.css`

- [ ] **Step 1: Create src/index.css** with Tailwind directives, CSS variables (verbatim from spec §1.2/§1.3), keyframes (§1.6), scrollbar (§1.7), .squish, and prefers-reduced-motion

Create `/home/ayatskii/adick_script/web/src/index.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* ============================================================
   BASE RESETS
   ============================================================ */
html, body {
  margin: 0;
  padding: 0;
}

* {
  box-sizing: border-box;
}

body {
  font-family: Inter, system-ui, sans-serif;
}

/* ============================================================
   DESIGN TOKENS — LIGHT THEME (verbatim from spec §1.2)
   ============================================================ */
:root {
  --bg: #e3d9c2;
  --dot: rgba(35, 30, 20, .05);
  --panel: #f4eee0;
  --panel2: #ece3d0;
  --panel3: #e6dcc6;
  --ink: #23211c;
  --ink-soft: #746f60;
  --line: rgba(35, 33, 28, .16);
  --shadow: #23211c;
  --shadowc: rgba(60, 45, 25, .22);
  --violet: #2b3a5e;
  --indigo: #1f2a44;
  --lime: #2f8f6b;
  --pink: #c62d1f;
  --sky: #3f72b0;
  --yellow: #cf9a36;
  --chip: #ddd2bb;
  --c-skip: #b3aa98;
  --logbg: #171a22;
  --logink: #d7d0bd;
  --sun: #c62d1f;
  --aku: #5f8f3a;
}

/* ============================================================
   DESIGN TOKENS — DARK THEME (verbatim from spec §1.3)
   ============================================================ */
[data-theme="dark"] {
  --bg: #0f1219;
  --dot: rgba(236, 228, 210, .05);
  --panel: #191d29;
  --panel2: #222838;
  --panel3: #161a24;
  --ink: #ece4d2;
  --ink-soft: #969ab0;
  --line: rgba(236, 228, 210, .13);
  --shadow: #000000;
  --shadowc: rgba(0, 0, 0, .55);
  --violet: #3f538a;
  --indigo: #2a3556;
  --lime: #38a87f;
  --pink: #d8392a;
  --sky: #4f86c6;
  --yellow: #d6a23f;
  --chip: #28304a;
  --c-skip: #5a6276;
  --logbg: #0a0c12;
  --logink: #cfc8b6;
  --sun: #d8392a;
  --aku: #8fd14a;
}

/* ============================================================
   KEYFRAME ANIMATIONS (verbatim from spec §1.6)
   ============================================================ */

/* evaluating dots blink */
@keyframes sbblink {
  0%, 100% { opacity: 1; }
  50% { opacity: .35; }
}

/* toast & dialog entrance */
@keyframes popin {
  0% { transform: scale(.5) translateY(6px); opacity: 0; }
  80% { transform: scale(1.06) translateY(0); opacity: 1; }
  100% { transform: scale(1) translateY(0); opacity: 1; }
}

/* WIN star wiggle */
@keyframes wiggle {
  0%, 100% { transform: rotate(0deg); }
  33% { transform: rotate(-5deg); }
  66% { transform: rotate(5deg); }
}

/* advisory face bob, flagged mascot, evaluating tree row */
@keyframes bob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}

/* skeletons (defined; reserved for future loading states) */
@keyframes shimmer {
  from { background-position: -300px 0; }
  to { background-position: 300px 0; }
}

/* speed-lines (defined; mostly unused in SJ version) */
@keyframes speed {
  from { background-position: 0 0; }
  to { background-position: 38px 0; }
}

/* spin */
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* float — sleeping mascot in empty states */
@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  33% { transform: translateY(-6px) rotate(-2deg); }
  66% { transform: translateY(-4px) rotate(2deg); }
}

/* blinkz — z's on sleeping mascot */
@keyframes blinkz {
  0%, 100% { transform: translateY(0); opacity: 1; }
  50% { transform: translateY(-4px); opacity: 0; }
}

/* ink rise — text entrance */
@keyframes inkrise {
  from { transform: translateY(8px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* ============================================================
   .squish — interactive press effect (spec §1.6)
   ============================================================ */
.squish {
  transition: transform .13s ease, box-shadow .13s, filter .13s;
  cursor: pointer;
}

.squish:hover {
  transform: translateY(-1px);
  filter: brightness(1.05);
}

.squish:active {
  transform: translateY(1px) scale(.99);
}

/* ============================================================
   CUSTOM SCROLLBAR (spec §1.7)
   ============================================================ */
::-webkit-scrollbar {
  width: 12px;
  height: 12px;
}

::-webkit-scrollbar-thumb {
  background: var(--ink-soft);
  border: 3px solid var(--bg);
  border-radius: 2px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

/* ============================================================
   REDUCED MOTION — MUST be honored (spec §1.6)
   ============================================================ */
@media (prefers-reduced-motion: reduce) {
  * {
    animation: none !important;
    transition: none !important;
  }
}
```

- [ ] **Step 2: Commit**

```bash
cd /home/ayatskii/adick_script
git add web/src/index.css
git commit -m "feat(web): design tokens, keyframes, scrollbar, .squish in index.css"
```

---

## Task 4: src/types.ts — TypeScript domain types

**Files:**
- Create: `/home/ayatskii/adick_script/web/src/types.ts`

- [ ] **Step 1: Create src/types.ts**

Create `/home/ayatskii/adick_script/web/src/types.ts`:
```ts
// ============================================================
// Screen routing
// ============================================================
export type ScreenId =
  | 'dashboard'
  | 'new'
  | 'live'
  | 'review'
  | 'students'
  | 'history'
  | 'flagged'
  | 'settings'

// ============================================================
// Status kinds (spec §4 + §2.3)
// ============================================================
export type StatusKind =
  | 'evaluating'
  | 'graded'
  | 'skipped'
  | 'flagged'
  | 'error'
  | 'dryrun'
  | 'idle'
  | 'queued'
  | 'running'

// ============================================================
// Run modes
// ============================================================
export type RunMode = 'dryrun' | 'full' | 'review'

// ============================================================
// Run state (lives in App.tsx)
// ============================================================
export interface RunState {
  /** Whether a run is currently active */
  active: boolean
  mode: RunMode
  /** Total exercises in this run */
  total: number
  /** Exercises processed so far */
  current: number
  /** Students finished */
  studentsDone: number
  /** Total students in this run */
  students: number
  /** Whether the run has completed */
  finished: boolean
}

// ============================================================
// Toast
// ============================================================
export type ToastKind = 'ok' | 'err' | 'warn' | 'info'

export interface ToastState {
  kind: ToastKind
  message: string
}

// ============================================================
// Dialog
// ============================================================
export type DialogKind = 'full' | 'stop' | null

// ============================================================
// Dashboard: run rows (spec §3.1 recent runs + §3.6 history)
// ============================================================
export interface RunRow {
  id: string
  /** RunMode for the MODE badge (with the non-literal quirk: full→'flagged', review→'queued') */
  modeBadgeStatus: StatusKind
  modeBadgeLabel: string
  started: string
  duration: string
  counts: string
  /** Status for the STATUS badge */
  statusBadgeStatus: StatusKind
  statusBadgeLabel: string
}

// ============================================================
// Review Queue items (spec §3.4)
// ============================================================
export type ReviewItemType = 'audio' | 'text'
export type ReviewItemStatus = 'pending' | 'approved' | 'rejected' | 'submitted'

export interface ReviewItem {
  id: string
  student: string
  lesson: string
  section: string
  ex: string
  type: ReviewItemType
  duration?: string  // for audio items e.g. "02:04"
  score: number
  conf: number
  transcript: string
  comment: string
  status: ReviewItemStatus
  edited: boolean
}

// ============================================================
// Students (spec §3.5)
// ============================================================
export interface LessonEntry {
  name: string
  status: StatusKind
}

export interface StudentRow {
  id: string
  name: string
  awaiting: number
  lastActivity: string
  lessons: LessonEntry[]
}

// ============================================================
// History (spec §3.6)
// ============================================================
export interface TimelineEntry {
  student: string
  ex: string
  proposedScore: number | null
  submittedScore: number | null
  status: StatusKind
  humanEdited: boolean
  /** Relative timestamp offset in seconds from run start (for display) */
  tsOffset: number
}

export interface ReconcileRow {
  student: string
  lesson: string
  completedBy: string
  flagStatus: StatusKind | null
  flagLabel: string | null
}

// ============================================================
// Flagged cards (spec §3.7)
// ============================================================
export interface FlaggedItem {
  id: string
  student: string
  lesson: string
  ex: string
  reason: string
  severity: string
  detail: string
}

// ============================================================
// App-level props interface (passed to all screens)
// ============================================================
export interface AppHandlers {
  showToast: (kind: ToastKind, message: string) => void
  startRun: (mode: RunMode) => void
  stopRun: () => void
  openDialog: (kind: DialogKind) => void
  setScreen: (screen: ScreenId) => void
}

export interface AppSharedState {
  screen: ScreenId
  theme: 'light' | 'dark'
  run: RunState
  /** mascot name, editor-tweakable */
  mascotName: string
  /** default run mode, editor-tweakable */
  defaultRunMode: RunMode
}

/** Props all screen components receive */
export interface ScreenProps extends AppHandlers, AppSharedState {}
```

- [ ] **Step 2: Commit**

```bash
cd /home/ayatskii/adick_script
git add web/src/types.ts
git commit -m "feat(web): TypeScript domain types (ScreenId, StatusKind, RunMode, etc.)"
```

---

## Task 5: src/data.ts — verbatim seed data

**Files:**
- Create: `/home/ayatskii/adick_script/web/src/data.ts`

- [ ] **Step 1: Create src/data.ts** with all seed data from spec §3.1/§3.4/§3.5/§3.6/§3.7/§3.8

Create `/home/ayatskii/adick_script/web/src/data.ts`:
```ts
import type { RunRow, ReviewItem, StudentRow, TimelineEntry, ReconcileRow, FlaggedItem } from './types'

// ============================================================
// Run history rows (spec §3.1 + §3.6) — 5 rows verbatim
// Used by: Dashboard "Recent runs", History "Runs" tab
// NOTE: full mode badge uses 'flagged' status; review uses 'queued' — non-literal, intentional
// ============================================================
export const RUN_ROWS: RunRow[] = [
  {
    id: 'h1',
    modeBadgeStatus: 'dryrun',
    modeBadgeLabel: 'Dry-run',
    started: 'Today 09:14',
    duration: '2m 41s',
    counts: '14 ✓ · 3 skip · 1 ⚑',
    statusBadgeStatus: 'graded',
    statusBadgeLabel: 'Success',
  },
  {
    id: 'h2',
    modeBadgeStatus: 'flagged',
    modeBadgeLabel: 'Full-auto',
    started: 'Yesterday 18:02',
    duration: '11m 06s',
    counts: '38 ✓ · 5 skip · 2 ⚑',
    statusBadgeStatus: 'graded',
    statusBadgeLabel: 'Success',
  },
  {
    id: 'h3',
    modeBadgeStatus: 'queued',
    modeBadgeLabel: 'Review',
    started: 'Yesterday 12:30',
    duration: '4m 12s',
    counts: '12 draft · 2 ⚑',
    statusBadgeStatus: 'flagged',
    statusBadgeLabel: '2 flagged',
  },
  {
    id: 'h4',
    modeBadgeStatus: 'flagged',
    modeBadgeLabel: 'Full-auto',
    started: 'Mon 20:48',
    duration: '9m 33s',
    counts: '31 ✓ · 1 ✗',
    statusBadgeStatus: 'error',
    statusBadgeLabel: '1 error',
  },
  {
    id: 'h5',
    modeBadgeStatus: 'dryrun',
    modeBadgeLabel: 'Dry-run',
    started: 'Mon 16:10',
    duration: '1m 58s',
    counts: '9 ✓ · 2 skip',
    statusBadgeStatus: 'graded',
    statusBadgeLabel: 'Success',
  },
]

// ============================================================
// Review queue items (spec §3.4) — 6 items verbatim
// ============================================================
export const REVIEW_ITEMS: ReviewItem[] = [
  {
    id: 'r1',
    student: 'Анель',
    lesson: 'Lesson 14 — Entertainment',
    section: 'Entertainment discussion',
    ex: '1.2',
    type: 'audio',
    duration: '02:04',
    score: 7,
    conf: 0.84,
    transcript: 'In my free time I like watching the series and listen to podcasts about science. Last weekend I have watched a documentary about ocean, it was really interesting and I learn many new words…',
    comment: 'Good task response and clear pronunciation; watch past-tense endings and link your ideas with connectors.',
    status: 'pending',
    edited: false,
  },
  {
    id: 'r2',
    student: 'Dias',
    lesson: 'Lesson 14 — Entertainment',
    section: 'Grammar',
    ex: '2.1',
    type: 'text',
    score: 9,
    conf: 0.91,
    transcript: 'If I had more time, I would learn to play the guitar. She has been working here since 2019.',
    comment: 'Excellent — all conditional and perfect forms correct. Minor: spacing around blanks.',
    status: 'pending',
    edited: false,
  },
  {
    id: 'r3',
    student: 'Аружан',
    lesson: 'Lesson 12 — Travel',
    section: 'Vocabulary',
    ex: '3.4',
    type: 'text',
    score: 6,
    conf: 0.66,
    transcript: 'destination, itinerary, sightseeing, accomodation, departure',
    comment: 'Most words used correctly. Spelling: "accomodation" → "accommodation". Add example sentences next time.',
    status: 'pending',
    edited: false,
  },
  {
    id: 'r4',
    student: 'Timur',
    lesson: 'Lesson 14 — Entertainment',
    section: 'Shadowing',
    ex: '3.1',
    type: 'audio',
    duration: '01:12',
    score: 8,
    conf: 0.88,
    transcript: 'The film industry has changed dramatically over the past decade, with streaming platforms…',
    comment: 'Strong rhythm and intonation. A couple of dropped word-endings — keep it up!',
    status: 'pending',
    edited: false,
  },
  {
    id: 'r5',
    student: 'Нурайым',
    lesson: 'Lesson 13 — Health',
    section: 'Reading time.',
    ex: '1.1',
    type: 'text',
    score: 5,
    conf: 0.62,
    transcript: 'The passage is about how sleep affect our memory and the writer think teenagers need more sleep.',
    comment: 'Main idea captured but several grammar slips (affect/affects, think/thinks). Re-read for subject–verb agreement.',
    status: 'pending',
    edited: false,
  },
  {
    id: 'r6',
    student: 'Madina',
    lesson: 'Lesson 14 — Entertainment',
    section: 'Entertainment discussion',
    ex: '1.3',
    type: 'audio',
    duration: '01:48',
    score: 9,
    conf: 0.95,
    transcript: 'I think social media changed how we consume entertainment completely. We can discover new artists instantly…',
    comment: 'Fluent, well-organised and natural. Great use of linking phrases.',
    status: 'pending',
    edited: false,
  },
]

// ============================================================
// Student roster (spec §3.5) — 12 rows verbatim
// ============================================================
export const STUDENT_ROWS: StudentRow[] = [
  {
    id: 's1',
    name: 'Анель',
    awaiting: 3,
    lastActivity: '2h ago',
    lessons: [
      { name: 'Lesson 14 — Entertainment', status: 'queued' },
      { name: 'Lesson 13 — Health', status: 'queued' },
      { name: 'Lesson 12 — Travel', status: 'flagged' },
    ],
  },
  {
    id: 's2',
    name: 'Dias',
    awaiting: 2,
    lastActivity: '4h ago',
    lessons: [
      { name: 'Lesson 14 — Entertainment', status: 'queued' },
      { name: 'Lesson 13 — Health', status: 'queued' },
    ],
  },
  {
    id: 's3',
    name: 'Аружан',
    awaiting: 4,
    lastActivity: '1d ago',
    lessons: [
      { name: 'Lesson 12 — Travel', status: 'flagged' },
      { name: 'Lesson 13 — Health', status: 'queued' },
      { name: 'Lesson 14 — Entertainment', status: 'queued' },
      { name: 'Lesson 11 — Work', status: 'queued' },
    ],
  },
  {
    id: 's4',
    name: 'Timur',
    awaiting: 1,
    lastActivity: '6h ago',
    lessons: [
      { name: 'Lesson 14 — Entertainment', status: 'error' },
    ],
  },
  {
    id: 's5',
    name: 'Нурайым',
    awaiting: 3,
    lastActivity: '3h ago',
    lessons: [
      { name: 'Lesson 13 — Health', status: 'queued' },
      { name: 'Lesson 12 — Travel', status: 'queued' },
      { name: 'Lesson 14 — Entertainment', status: 'queued' },
    ],
  },
  {
    id: 's6',
    name: 'Madina',
    awaiting: 1,
    lastActivity: '30m ago',
    lessons: [
      { name: 'Lesson 14 — Entertainment', status: 'queued' },
    ],
  },
  {
    id: 's7',
    name: 'Ерлан',
    awaiting: 2,
    lastActivity: '1d ago',
    lessons: [
      { name: 'Lesson 13 — Health', status: 'queued' },
      { name: 'Lesson 12 — Travel', status: 'queued' },
    ],
  },
  {
    id: 's8',
    name: 'Алишер',
    awaiting: 0,
    lastActivity: '5d ago',
    lessons: [],
  },
  {
    id: 's9',
    name: 'Camila',
    awaiting: 2,
    lastActivity: '8h ago',
    lessons: [
      { name: 'Lesson 14 — Entertainment', status: 'queued' },
      { name: 'Lesson 11 — Work', status: 'queued' },
    ],
  },
  {
    id: 's10',
    name: 'Бекзат',
    awaiting: 3,
    lastActivity: '2d ago',
    lessons: [
      { name: 'Lesson 12 — Travel', status: 'queued' },
      { name: 'Lesson 13 — Health', status: 'queued' },
      { name: 'Lesson 14 — Entertainment', status: 'queued' },
    ],
  },
  {
    id: 's11',
    name: 'Aizhan',
    awaiting: 1,
    lastActivity: '12h ago',
    lessons: [
      { name: 'Lesson 13 — Health', status: 'queued' },
    ],
  },
  {
    id: 's12',
    name: 'Daniyar',
    awaiting: 0,
    lastActivity: '1w ago',
    lessons: [],
  },
]

// ============================================================
// History timeline entries (spec §3.6) — 6 entries verbatim
// ============================================================
export const TIMELINE_ENTRIES: TimelineEntry[] = [
  {
    student: 'Анель',
    ex: '1.2',
    proposedScore: 7,
    submittedScore: 7,
    status: 'graded',
    humanEdited: false,
    tsOffset: 0,
  },
  {
    student: 'Анель',
    ex: '2.1',
    proposedScore: null,
    submittedScore: null,
    status: 'skipped',
    humanEdited: false,
    tsOffset: 45,
  },
  {
    student: 'Dias',
    ex: '1.2',
    proposedScore: 6,
    submittedScore: 7,
    status: 'graded',
    humanEdited: true,
    tsOffset: 90,
  },
  {
    student: 'Dias',
    ex: '2.1',
    proposedScore: 9,
    submittedScore: 9,
    status: 'graded',
    humanEdited: false,
    tsOffset: 135,
  },
  {
    student: 'Аружан',
    ex: '3.4',
    proposedScore: null,
    submittedScore: null,
    status: 'flagged',
    humanEdited: false,
    tsOffset: 180,
  },
  {
    student: 'Timur',
    ex: '3.1',
    proposedScore: null,
    submittedScore: null,
    status: 'error',
    humanEdited: false,
    tsOffset: 225,
  },
]

// ============================================================
// Reconcile rows (spec §3.6) — 4 rows verbatim
// ============================================================
export const RECONCILE_ROWS: ReconcileRow[] = [
  {
    student: 'Анель',
    lesson: 'Lesson 14 — Entertainment',
    completedBy: 'This bot · today 09:14',
    flagStatus: null,
    flagLabel: null,
  },
  {
    student: 'Dias',
    lesson: 'Lesson 14 — Entertainment',
    completedBy: 'This bot · today 09:15',
    flagStatus: null,
    flagLabel: null,
  },
  {
    student: 'Нурайым',
    lesson: 'Lesson 13 — Health',
    completedBy: 'Previous run · yesterday',
    flagStatus: 'flagged',
    flagLabel: 'Leftover — check',
  },
  {
    student: 'Madina',
    lesson: 'Lesson 12 — Travel',
    completedBy: 'Manually completed',
    flagStatus: null,
    flagLabel: null,
  },
]

// ============================================================
// Flagged items (spec §3.7) — 5 cards verbatim
// ============================================================
export const FLAGGED_ITEMS: FlaggedItem[] = [
  {
    id: 'f1',
    student: 'Аружан',
    lesson: 'Lesson 12 — Travel',
    ex: '3.4',
    reason: 'Low confidence',
    severity: 'Needs a look',
    detail: 'Confidence 0.61 — below your 0.70 threshold. The answer mixes correct and misspelled vocabulary, so the bot held off.',
  },
  {
    id: 'f2',
    student: 'Timur',
    lesson: 'Lesson 14 — Entertainment',
    ex: '3.1',
    reason: 'Audio download failed',
    severity: 'Blocked',
    detail: 'The shadowing audio returned 403 from the Edvibe CDN after 3 retries. No transcript could be produced.',
  },
  {
    id: 'f3',
    student: 'Dias',
    lesson: 'Lesson 14 — Entertainment',
    ex: '2.2',
    reason: 'Selector not found',
    severity: 'Blocked',
    detail: 'The score input field did not appear within 15s. The lesson page layout may have changed.',
  },
  {
    id: 'f4',
    student: 'Madina',
    lesson: 'Lesson 13 — Health',
    ex: '1.4',
    reason: 'OpenAI error',
    severity: 'Transient',
    detail: 'Rate limit (429) hit during evaluation. The item will retry automatically on the next run.',
  },
  {
    id: 'f5',
    student: 'Нурайым',
    lesson: 'Lesson 12 — Travel',
    ex: '2.1',
    reason: 'Low confidence',
    severity: 'Needs a look',
    detail: 'Confidence 0.64 — the answer drifts partly off-topic, so a human should score it.',
  },
]

// ============================================================
// Settings defaults (spec §3.8)
// ============================================================
export const SETTINGS_DEFAULTS = {
  edvibeLogin: 'mr.adilet@edvibe.com',
  edvibePassword: 'hunter2hunter2',
  openaiApiKey: 'sk-proj-aBcD1234EfGh5678',
  transcriptionModel: 'whisper-1',
  evaluationModel: 'gpt-4o',
  scoreScale: '0 – 10',
  confidenceThreshold: 0.70,
  rubricNotes: 'Reward task response & coherence; be gentle on minor grammar.',
  defaultMode: 'Dry-run',
  pacingDelayMs: 900,
  marathon: 'Pre-IELTS',
  curator: 'Mister Adilet',
} as const
```

- [ ] **Step 2: Commit**

```bash
cd /home/ayatskii/adick_script
git add web/src/data.ts
git commit -m "feat(web): verbatim seed data (runs, review items, students, timeline, flagged, settings)"
```

---

## Task 6: src/components/icons.tsx — nav icons, sun/moon, padlock

**Files:**
- Create: `/home/ayatskii/adick_script/web/src/components/icons.tsx`

- [ ] **Step 1: Create src/components/icons.tsx**

All icons are inline hand-authored SVG. Nav icons: 20×20, stroke `currentColor`, strokeWidth 2.3, fill none. From spec §6:
- dashboard = 4 rounded squares (2×2 grid)
- new run = play-triangle + vertical bar
- live = pulse/broadcast arcs + center dot
- review = clipboard with check
- students = two people silhouettes
- history = clock with hands
- flagged = flag pole with flag
- settings = gear/cog

Create `/home/ayatskii/adick_script/web/src/components/icons.tsx`:
```tsx
import React from 'react'

// ============================================================
// NAV ICONS — 20×20, stroke currentColor, strokeWidth 2.3
// ============================================================

export function IconDashboard() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
      {/* 4 rounded squares in a 2×2 grid */}
      <rect x="2" y="2" width="6" height="6" rx="1.5" />
      <rect x="12" y="2" width="6" height="6" rx="1.5" />
      <rect x="2" y="12" width="6" height="6" rx="1.5" />
      <rect x="12" y="12" width="6" height="6" rx="1.5" />
    </svg>
  )
}

export function IconNewRun() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
      {/* vertical bar (pause-like) left + play triangle right */}
      <line x1="4" y1="4" x2="4" y2="16" />
      <polygon points="8,4 17,10 8,16" />
    </svg>
  )
}

export function IconLive() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
      {/* broadcast arcs (3 concentric) + center dot */}
      <circle cx="10" cy="10" r="1.5" fill="currentColor" stroke="none" />
      <path d="M6.5 13.5a5 5 0 0 1 0-7" />
      <path d="M13.5 13.5a5 5 0 0 0 0-7" />
      <path d="M3.5 16.5a9.5 9.5 0 0 1 0-13" />
      <path d="M16.5 16.5a9.5 9.5 0 0 0 0-13" />
    </svg>
  )
}

export function IconReview() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
      {/* clipboard body */}
      <rect x="4" y="4" width="12" height="14" rx="1.5" />
      {/* clipboard top tab */}
      <path d="M7 4V3a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v1" />
      {/* check mark */}
      <polyline points="7,11 9,13 13,9" />
    </svg>
  )
}

export function IconStudents() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
      {/* primary person */}
      <circle cx="8" cy="7" r="2.5" />
      <path d="M3 17c0-3 2-5 5-5s5 2 5 5" />
      {/* secondary person (partially behind) */}
      <circle cx="14" cy="7" r="2" />
      <path d="M14 12c1.5 0 3 1 3.5 3" />
    </svg>
  )
}

export function IconHistory() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
      {/* clock face */}
      <circle cx="10" cy="10" r="7.5" />
      {/* clock hands */}
      <polyline points="10,5.5 10,10 13.5,12.5" />
    </svg>
  )
}

export function IconFlagged() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
      {/* flag pole */}
      <line x1="5" y1="3" x2="5" y2="18" />
      {/* flag */}
      <path d="M5 3 L16 6 L5 9 Z" />
    </svg>
  )
}

export function IconSettings() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
      {/* gear outline (simplified cog: circle + 6 teeth) */}
      <circle cx="10" cy="10" r="3" />
      <path d="M10 2v2M10 16v2M2 10h2M16 10h2M4.22 4.22l1.42 1.42M14.36 14.36l1.42 1.42M4.22 15.78l1.42-1.42M14.36 5.64l1.42-1.42" />
    </svg>
  )
}

// ============================================================
// THEME ICONS — Sun (light mode) and Moon (dark mode)
// Used in TopBar theme toggle
// ============================================================

/** Smiling sun face: disc #ffce2e, stroked features #3a2600 */
export function IconSun() {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
      {/* sun disc */}
      <circle cx="11" cy="11" r="7" fill="#ffce2e" stroke="#3a2600" strokeWidth="1.5" />
      {/* rays */}
      <line x1="11" y1="1" x2="11" y2="3.5" stroke="#3a2600" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="11" y1="18.5" x2="11" y2="21" stroke="#3a2600" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="1" y1="11" x2="3.5" y2="11" stroke="#3a2600" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="18.5" y1="11" x2="21" y2="11" stroke="#3a2600" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="3.64" y1="3.64" x2="5.47" y2="5.47" stroke="#3a2600" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="16.53" y1="16.53" x2="18.36" y2="18.36" stroke="#3a2600" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="3.64" y1="18.36" x2="5.47" y2="16.53" stroke="#3a2600" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="16.53" y1="5.47" x2="18.36" y2="3.64" stroke="#3a2600" strokeWidth="1.5" strokeLinecap="round" />
      {/* dot eyes */}
      <circle cx="8.5" cy="10" r="1" fill="#3a2600" />
      <circle cx="13.5" cy="10" r="1" fill="#3a2600" />
      {/* smile */}
      <path d="M8 13 Q11 15.5 14 13" stroke="#3a2600" strokeWidth="1.2" strokeLinecap="round" fill="none" />
    </svg>
  )
}

/** Crescent moon face: fill #d6a23f, stroke #3a2600 */
export function IconMoon() {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
      {/* crescent shape */}
      <path d="M17 11.5A7 7 0 1 1 10.5 4a5.5 5.5 0 0 0 6.5 7.5z" fill="#d6a23f" stroke="#3a2600" strokeWidth="1.5" strokeLinejoin="round" />
      {/* dot eyes */}
      <circle cx="9" cy="10" r="0.9" fill="#3a2600" />
      <circle cx="13" cy="9" r="0.9" fill="#3a2600" />
      {/* small smile */}
      <path d="M8.5 12.5 Q11 14.5 13.5 12.5" stroke="#3a2600" strokeWidth="1.1" strokeLinecap="round" fill="none" />
    </svg>
  )
}

// ============================================================
// PADLOCK — used in TopBar "local credentials" chip
// 17×17, stroke var(--ink)
// ============================================================

export function IconPadlock() {
  return (
    <svg width="17" height="17" viewBox="0 0 17 17" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      {/* shackle */}
      <path d="M4.5 7V5.5a4 4 0 0 1 8 0V7" />
      {/* body */}
      <rect x="2.5" y="7" width="12" height="8.5" rx="1.5" />
      {/* keyhole dot */}
      <circle cx="8.5" cy="11.5" r="1.2" fill="currentColor" stroke="none" />
    </svg>
  )
}
```

- [ ] **Step 2: Commit**

```bash
cd /home/ayatskii/adick_script
git add web/src/components/icons.tsx
git commit -m "feat(web): hand-authored nav SVG icons + sun/moon/padlock"
```

---

## Task 7: src/components/StatusBadge.tsx

**Files:**
- Create: `/home/ayatskii/adick_script/web/src/components/StatusBadge.tsx`

- [ ] **Step 1: Create src/components/StatusBadge.tsx**

Full spec from §4: pill with 15×15 inline-SVG face, all variant bg/fg/border. The face SVG groups: graded+running→smiley, evaluating→blinking dots, skipped→neutral, flagged→raised-brow, error→X-eyes, dryrun→ghost, idle+queued→sleepy.

Create `/home/ayatskii/adick_script/web/src/components/StatusBadge.tsx`:
```tsx
import React from 'react'
import type { StatusKind } from '../types'

interface StatusBadgeProps {
  status: StatusKind
  label?: string
}

// ============================================================
// Face icon components — 15×15, stroke currentColor
// ============================================================

function FaceSmiley() {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
      {/* dot eyes */}
      <circle cx="5.5" cy="6" r="0.8" fill="currentColor" stroke="none" />
      <circle cx="9.5" cy="6" r="0.8" fill="currentColor" stroke="none" />
      {/* smile */}
      <path d="M4.5 9.5 Q7.5 12 10.5 9.5" fill="none" />
    </svg>
  )
}

function FaceBlinkingDots() {
  // 3 dots with staggered animation — sbblink keyframe (spec §1.6)
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="currentColor">
      <circle cx="3.5" cy="7.5" r="1.5" style={{ animation: 'sbblink 1.1s 0s infinite' }} />
      <circle cx="7.5" cy="7.5" r="1.5" style={{ animation: 'sbblink 1.1s 0.18s infinite', opacity: 0.7 }} />
      <circle cx="11.5" cy="7.5" r="1.5" style={{ animation: 'sbblink 1.1s 0.36s infinite', opacity: 0.45 }} />
    </svg>
  )
}

function FaceNeutral() {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
      {/* eyes */}
      <circle cx="5.5" cy="6" r="0.8" fill="currentColor" stroke="none" />
      <circle cx="9.5" cy="6" r="0.8" fill="currentColor" stroke="none" />
      {/* flat mouth */}
      <line x1="5" y1="10" x2="10" y2="10" />
    </svg>
  )
}

function FaceRaisedBrow() {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
      {/* curved brow (raised on one side) */}
      <path d="M4 4.5 Q5.5 3 7 4.5" />
      <path d="M8 4 Q9.5 3.5 11 4" />
      {/* eyes */}
      <circle cx="5.5" cy="6.5" r="0.8" fill="currentColor" stroke="none" />
      <circle cx="9.5" cy="6.5" r="0.8" fill="currentColor" stroke="none" />
      {/* slight smile */}
      <path d="M5 10 Q7.5 11.5 10 10" />
    </svg>
  )
}

function FaceXEyes() {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
      {/* X left eye */}
      <line x1="3.5" y1="4.5" x2="6.5" y2="7.5" />
      <line x1="6.5" y1="4.5" x2="3.5" y2="7.5" />
      {/* X right eye */}
      <line x1="8.5" y1="4.5" x2="11.5" y2="7.5" />
      <line x1="11.5" y1="4.5" x2="8.5" y2="7.5" />
      {/* frown */}
      <path d="M4.5 11 Q7.5 9 10.5 11" />
    </svg>
  )
}

function FaceGhost() {
  // Ghost shape: wavy hem + two dot eyes
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      {/* ghost body outline */}
      <path d="M3 12 Q3 3 7.5 3 Q12 3 12 12 Q10.5 11 9 12 Q7.5 13 6 12 Q4.5 11 3 12Z" />
      {/* dot eyes */}
      <circle cx="5.5" cy="7.5" r="1" fill="currentColor" stroke="none" />
      <circle cx="9.5" cy="7.5" r="1" fill="currentColor" stroke="none" />
    </svg>
  )
}

function FaceSleepy() {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
      {/* droopy arch brows */}
      <path d="M4 5 Q5.5 4 7 5" />
      <path d="M8 5 Q9.5 4 11 5" />
      {/* half-closed / flat eyes */}
      <line x1="4.5" y1="7.5" x2="7" y2="7.5" />
      <line x1="8" y1="7.5" x2="10.5" y2="7.5" />
      {/* flat mouth */}
      <line x1="5" y1="10.5" x2="10" y2="10.5" />
    </svg>
  )
}

// ============================================================
// Variant table (verbatim from spec §4)
// ============================================================
interface Variant {
  defaultLabel: string
  bg: string
  fg: string
  border: string
  face: React.ReactNode
}

function getVariant(status: StatusKind): Variant {
  switch (status) {
    case 'evaluating':
      return {
        defaultLabel: 'Evaluating',
        bg: '#3f72b0',
        fg: '#ffffff',
        border: 'none',
        face: <FaceBlinkingDots />,
      }
    case 'graded':
      return {
        defaultLabel: 'Graded',
        bg: '#2f8f6b',
        fg: '#ffffff',
        border: 'none',
        face: <FaceSmiley />,
      }
    case 'running':
      return {
        defaultLabel: 'Running',
        bg: '#3f72b0',
        fg: '#ffffff',
        border: 'none',
        face: <FaceSmiley />,
      }
    case 'skipped':
      return {
        defaultLabel: 'Skipped',
        bg: 'var(--c-skip)',
        fg: 'var(--ink)',
        border: 'none',
        face: <FaceNeutral />,
      }
    case 'flagged':
      return {
        defaultLabel: 'Flagged',
        bg: '#cf9a36',
        fg: '#241a00',
        border: 'none',
        face: <FaceRaisedBrow />,
      }
    case 'error':
      return {
        defaultLabel: 'Error',
        bg: '#c62d1f',
        fg: '#ffffff',
        border: 'none',
        face: <FaceXEyes />,
      }
    case 'dryrun':
      return {
        defaultLabel: 'Dry-run',
        bg: 'repeating-linear-gradient(45deg,#6a5a9e,#6a5a9e 6px,#4e4179 6px,#4e4179 12px)',
        fg: '#ffffff',
        border: '1.5px dashed rgba(255,255,255,.6)',
        face: <FaceGhost />,
      }
    case 'idle':
      return {
        defaultLabel: 'Idle',
        bg: 'var(--chip)',
        fg: 'var(--ink)',
        border: 'none',
        face: <FaceSleepy />,
      }
    case 'queued':
      return {
        defaultLabel: 'Queued',
        bg: 'var(--chip)',
        fg: 'var(--ink-soft)',
        border: 'none',
        face: <FaceSleepy />,
      }
  }
}

// ============================================================
// StatusBadge component
// ============================================================

export function StatusBadge({ status, label }: StatusBadgeProps) {
  const v = getVariant(status)
  const displayLabel = label ?? v.defaultLabel

  return (
    <span
      data-status={status}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        padding: '3px 9px 3px 6px',
        border: v.border === 'none' ? undefined : v.border,
        borderRadius: '3px',
        background: v.bg,
        color: v.fg,
        fontFamily: "'Shippori Mincho B1', serif",
        fontWeight: 700,
        fontSize: '11px',
        letterSpacing: '.4px',
        textTransform: 'uppercase',
        lineHeight: 1,
        whiteSpace: 'nowrap',
      }}
    >
      {v.face}
      {displayLabel}
    </span>
  )
}

export default StatusBadge
```

- [ ] **Step 2: Commit**

```bash
cd /home/ayatskii/adick_script
git add web/src/components/StatusBadge.tsx
git commit -m "feat(web): StatusBadge component — all 9 variants with inline-SVG faces"
```

---

## Task 8: src/components/Backdrop.tsx

**Files:**
- Create: `/home/ayatskii/adick_script/web/src/components/Backdrop.tsx`

- [ ] **Step 1: Create Backdrop.tsx**

From spec §2.1: fixed, z-0, pointer-events:none. Sun disc + ring, then two-layer mountain SVG.

Create `/home/ayatskii/adick_script/web/src/components/Backdrop.tsx`:
```tsx
import React from 'react'

export function Backdrop() {
  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 0,
        pointerEvents: 'none',
        overflow: 'hidden',
      }}
      aria-hidden="true"
    >
      {/* Rising sun disc (vermilion) */}
      <div
        style={{
          position: 'absolute',
          top: '-150px',
          right: '-90px',
          width: '560px',
          height: '560px',
          borderRadius: '50%',
          background: 'var(--sun)',
          opacity: 0.12,
        }}
      />
      {/* Sun ring */}
      <div
        style={{
          position: 'absolute',
          top: '-150px',
          right: '-90px',
          width: '560px',
          height: '560px',
          borderRadius: '50%',
          border: '6px solid var(--sun)',
          opacity: 0.07,
        }}
      />

      {/* Mountain silhouettes — two layered paths */}
      <svg
        viewBox="0 0 1440 380"
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          width: '100%',
          height: '40%',
        }}
        preserveAspectRatio="xMidYMax slice"
      >
        {/* Back ridge — lighter opacity */}
        <path
          d="M0 380 L0 260 L120 200 L240 260 L360 140 L480 220 L600 120 L720 200 L840 100 L960 180 L1080 80 L1200 160 L1320 60 L1440 140 L1440 380 Z"
          fill="var(--ink)"
          opacity="0.05"
        />
        {/* Front ridge — slightly denser */}
        <path
          d="M0 380 L0 310 L160 270 L280 310 L400 230 L520 290 L640 200 L760 270 L880 180 L1000 250 L1140 170 L1280 240 L1440 200 L1440 380 Z"
          fill="var(--ink)"
          opacity="0.045"
        />
      </svg>
    </div>
  )
}

export default Backdrop
```

- [ ] **Step 2: Commit**

```bash
cd /home/ayatskii/adick_script
git add web/src/components/Backdrop.tsx
git commit -m "feat(web): Backdrop component — sun disc + mountain silhouettes"
```

---

## Task 9: src/components/Sidebar.tsx

**Files:**
- Create: `/home/ayatskii/adick_script/web/src/components/Sidebar.tsx`

- [ ] **Step 1: Create Sidebar.tsx**

From spec §2.2: 232px/74px, logo block (emblem SVG + wordmark when open), 8 nav buttons with active/inactive states + count badges for Review (6) and Flagged (5), collapse toggle.

Create `/home/ayatskii/adick_script/web/src/components/Sidebar.tsx`:
```tsx
import React from 'react'
import type { ScreenId } from '../types'
import {
  IconDashboard, IconNewRun, IconLive, IconReview,
  IconStudents, IconHistory, IconFlagged, IconSettings,
} from './icons'

interface SidebarProps {
  screen: ScreenId
  open: boolean
  onNavigate: (screen: ScreenId) => void
  onToggle: () => void
  reviewCount: number
  flaggedCount: number
}

const NAV_ITEMS: Array<{
  id: ScreenId
  label: string
  Icon: React.FC
  countKey?: 'review' | 'flagged'
}> = [
  { id: 'dashboard', label: 'Dashboard', Icon: IconDashboard },
  { id: 'new', label: 'New Run', Icon: IconNewRun },
  { id: 'live', label: 'Live Monitor', Icon: IconLive },
  { id: 'review', label: 'Review Queue', Icon: IconReview, countKey: 'review' },
  { id: 'students', label: 'Students', Icon: IconStudents },
  { id: 'history', label: 'History', Icon: IconHistory },
  { id: 'flagged', label: 'Flagged', Icon: IconFlagged, countKey: 'flagged' },
  { id: 'settings', label: 'Settings', Icon: IconSettings },
]

export function Sidebar({ screen, open, onNavigate, onToggle, reviewCount, flaggedCount }: SidebarProps) {
  const width = open ? '232px' : '74px'

  function getCount(key?: 'review' | 'flagged') {
    if (key === 'review') return reviewCount
    if (key === 'flagged') return flaggedCount
    return 0
  }

  return (
    <aside
      style={{
        width,
        minWidth: width,
        transition: 'width .18s ease',
        background: 'var(--panel)',
        borderRight: '1.5px solid var(--line)',
        display: 'flex',
        flexDirection: 'column',
        zIndex: 20,
        overflow: 'hidden',
      }}
    >
      {/* Logo block */}
      <div
        style={{
          padding: open ? '18px 14px 14px' : '18px 17px 14px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          borderBottom: '1.5px solid var(--line)',
          flexShrink: 0,
        }}
      >
        {/* Emblem SVG: indigo square + vermilion sun + mountain path */}
        <svg
          width="40"
          height="40"
          viewBox="0 0 40 40"
          style={{
            borderRadius: '4px',
            boxShadow: '2.5px 2.5px 13px var(--shadowc)',
            flexShrink: 0,
          }}
        >
          {/* Indigo background */}
          <rect width="40" height="40" fill="#1f2a44" rx="4" />
          {/* Vermilion sun circle */}
          <circle cx="20" cy="15" r="9" fill="var(--sun)" />
          {/* Mountain path */}
          <path d="M0 40 L0 30 L12 22 L20 28 L28 18 L40 28 L40 40 Z" fill="#10121a" />
        </svg>

        {/* Wordmark (only when open) */}
        {open && (
          <div style={{ overflow: 'hidden', minWidth: 0 }}>
            <div
              style={{
                fontFamily: "'Yuji Syuku', serif",
                fontSize: '21px',
                color: 'var(--ink)',
                letterSpacing: '.5px',
                lineHeight: 1.1,
                whiteSpace: 'nowrap',
              }}
            >
              Edvibe Grader
            </div>
            <div
              style={{
                fontSize: '10px',
                color: 'var(--ink-soft)',
                fontFamily: "'Shippori Mincho B1', serif",
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '1.5px',
                whiteSpace: 'nowrap',
              }}
            >
              Grading Mission-Control
            </div>
          </div>
        )}
      </div>

      {/* Nav items */}
      <nav
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '12px 10px',
          display: 'flex',
          flexDirection: 'column',
          gap: '5px',
        }}
      >
        {NAV_ITEMS.map(({ id, label, Icon, countKey }) => {
          const isActive = screen === id
          const count = countKey ? getCount(countKey) : 0

          return (
            <button
              key={id}
              className="squish"
              onClick={() => onNavigate(id)}
              title={open ? undefined : label}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '11px',
                padding: '9px 11px',
                borderRadius: '4px',
                border: isActive ? '2.5px solid var(--line)' : '2.5px solid transparent',
                background: isActive ? 'var(--violet)' : 'transparent',
                color: isActive ? '#fff' : 'var(--ink)',
                boxShadow: isActive ? '3px 3px 13px var(--shadowc)' : 'none',
                fontFamily: "'Shippori Mincho B1', serif",
                fontWeight: 700,
                fontSize: '14.5px',
                textAlign: 'left',
                cursor: 'pointer',
                width: '100%',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
              }}
            >
              <span style={{ flexShrink: 0, display: 'flex' }}>
                <Icon />
              </span>
              {open && (
                <>
                  <span style={{ flex: 1 }}>{label}</span>
                  {count > 0 && (
                    <span
                      style={{
                        minWidth: '20px',
                        fontFamily: "'Shippori Mincho B1', serif",
                        fontSize: '11px',
                        fontWeight: 800,
                        padding: '1px 6px',
                        borderRadius: '99px',
                        border: '1px solid var(--line)',
                        background: 'var(--yellow)',
                        color: '#3a2600',
                        textAlign: 'center',
                        flexShrink: 0,
                      }}
                    >
                      {count}
                    </span>
                  )}
                </>
              )}
            </button>
          )
        })}
      </nav>

      {/* Collapse toggle */}
      <div style={{ padding: '10px', borderTop: '1.5px solid var(--line)', flexShrink: 0 }}>
        <button
          className="squish"
          onClick={onToggle}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: open ? 'flex-start' : 'center',
            gap: '8px',
            padding: '8px 11px',
            borderRadius: '4px',
            border: '1.5px solid var(--line)',
            background: 'var(--panel2)',
            boxShadow: '2px 2px 13px var(--shadowc)',
            color: 'var(--ink)',
            fontFamily: "'Shippori Mincho B1', serif",
            fontWeight: 700,
            fontSize: '13px',
            cursor: 'pointer',
          }}
        >
          <span>{open ? '«' : '»'}</span>
          {open && <span>Collapse</span>}
        </button>
      </div>
    </aside>
  )
}

export default Sidebar
```

- [ ] **Step 2: Commit**

```bash
cd /home/ayatskii/adick_script
git add web/src/components/Sidebar.tsx
git commit -m "feat(web): Sidebar component — logo, 8 nav items, count badges, collapse"
```

---

## Task 10: src/components/TopBar.tsx

**Files:**
- Create: `/home/ayatskii/adick_script/web/src/components/TopBar.tsx`

- [ ] **Step 1: Create TopBar.tsx**

From spec §2.3: screen title, Localhost pill, run status pill (all states), theme toggle, lock chip.

Create `/home/ayatskii/adick_script/web/src/components/TopBar.tsx`:
```tsx
import React from 'react'
import type { ScreenId, RunState } from '../types'
import { IconSun, IconMoon, IconPadlock } from './icons'

const SCREEN_TITLES: Record<ScreenId, string> = {
  dashboard: 'Dashboard',
  new: 'New Run',
  live: 'Live Monitor',
  review: 'Review Queue',
  students: 'Students',
  history: 'History & Audit',
  flagged: 'Flagged',
  settings: 'Settings',
}

interface TopBarProps {
  screen: ScreenId
  theme: 'light' | 'dark'
  run: RunState
  onThemeToggle: () => void
  onRunPillClick: () => void
}

function getRunPillStyle(run: RunState): {
  label: string
  dotColor: string
  bg: string
  fg: string
} {
  if (!run.active && !run.finished) {
    return { label: 'Idle', dotColor: 'var(--c-skip)', bg: 'var(--chip)', fg: 'var(--ink)' }
  }
  if (run.finished) {
    return { label: 'Done', dotColor: '#2f8f6b', bg: '#2f8f6b', fg: '#fff' }
  }
  // Active run states by mode
  switch (run.mode) {
    case 'dryrun':
      return { label: 'Dry-run', dotColor: '#6a5a9e', bg: '#3f72b0', fg: '#fff' }
    case 'review':
      return { label: 'Drafting', dotColor: '#3f72b0', bg: '#3f72b0', fg: '#fff' }
    case 'full':
      return { label: 'Running', dotColor: '#cf9a36', bg: '#cf9a36', fg: '#3a2600' }
  }
}

export function TopBar({ screen, theme, run, onThemeToggle, onRunPillClick }: TopBarProps) {
  const pill = getRunPillStyle(run)
  const isRunning = run.active || run.finished

  return (
    <header
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '14px',
        padding: '13px 22px',
        background: 'var(--panel)',
        borderBottom: '1.5px solid var(--line)',
        zIndex: 15,
        flexShrink: 0,
      }}
    >
      {/* Screen title */}
      <h1
        style={{
          margin: 0,
          fontFamily: "'Shippori Mincho B1', serif",
          fontWeight: 800,
          fontSize: '20px',
          letterSpacing: '-.4px',
          color: 'var(--ink)',
          whiteSpace: 'nowrap',
        }}
      >
        {SCREEN_TITLES[screen]}
      </h1>

      {/* Localhost pill */}
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '3px 10px',
          border: '1.5px solid var(--line)',
          borderRadius: '99px',
          background: 'var(--lime)',
          color: '#fff',
          fontFamily: "'Shippori Mincho B1', serif",
          fontWeight: 700,
          fontSize: '11.5px',
          boxShadow: '1.5px 1.5px 13px var(--shadowc)',
          whiteSpace: 'nowrap',
        }}
      >
        <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#fff', display: 'inline-block' }} />
        Localhost
      </span>

      {/* Spacer */}
      <div style={{ flex: 1 }} />

      {/* RUN STATUS pill */}
      <button
        className="squish"
        onClick={onRunPillClick}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '7px 9px 7px 14px',
          border: '1.5px solid var(--line)',
          borderRadius: '99px',
          background: pill.bg,
          color: pill.fg,
          boxShadow: '3px 3px 13px var(--shadowc)',
          fontFamily: "'Shippori Mincho B1', serif",
          fontWeight: 700,
          fontSize: '14px',
          cursor: 'pointer',
        }}
      >
        {/* Status dot */}
        <span
          style={{
            width: '11px',
            height: '11px',
            borderRadius: '50%',
            background: pill.dotColor,
            border: '1px solid var(--line)',
            flexShrink: 0,
          }}
        />
        {pill.label}
        {/* Progress sub-pill (only when run is active) */}
        {run.active && (
          <span
            style={{
              padding: '2px 9px',
              borderRadius: '99px',
              background: 'rgba(0,0,0,.18)',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            {run.studentsDone}/{run.students} students
          </span>
        )}
      </button>

      {/* Theme toggle */}
      <button
        className="squish"
        onClick={onThemeToggle}
        aria-label={theme === 'light' ? 'Switch to dark theme' : 'Switch to light theme'}
        style={{
          width: '42px',
          height: '42px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          border: '1.5px solid var(--line)',
          borderRadius: '4px',
          background: theme === 'light' ? 'var(--yellow)' : 'var(--indigo)',
          boxShadow: '2.5px 2.5px 13px var(--shadowc)',
          cursor: 'pointer',
          flexShrink: 0,
        }}
      >
        {theme === 'light' ? <IconSun /> : <IconMoon />}
      </button>

      {/* Local credentials lock chip */}
      <div
        title="Credentials stored locally only"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '7px 11px',
          border: '1.5px solid var(--line)',
          borderRadius: '4px',
          background: 'var(--panel2)',
          boxShadow: '2px 2px 13px var(--shadowc)',
          color: 'var(--ink-soft)',
          flexShrink: 0,
        }}
      >
        <IconPadlock />
        <span
          style={{
            fontFamily: 'Inter, system-ui, sans-serif',
            fontSize: '11px',
            fontWeight: 600,
            color: 'var(--ink-soft)',
          }}
        >
          local
        </span>
      </div>
    </header>
  )
}

export default TopBar
```

- [ ] **Step 2: Commit**

```bash
cd /home/ayatskii/adick_script
git add web/src/components/TopBar.tsx
git commit -m "feat(web): TopBar — title, localhost pill, run-status pill, theme toggle, lock chip"
```

---

## Task 11: src/components/ModeBanner.tsx + Toast.tsx + Dialog.tsx

**Files:**
- Create: `/home/ayatskii/adick_script/web/src/components/ModeBanner.tsx`
- Create: `/home/ayatskii/adick_script/web/src/components/Toast.tsx`
- Create: `/home/ayatskii/adick_script/web/src/components/Dialog.tsx`

- [ ] **Step 1: Create ModeBanner.tsx**

From spec §2.4: shown only while a run is active. Two variants: DRY-RUN (purple hatch) and FULL-AUTO (ochre hatch).

Create `/home/ayatskii/adick_script/web/src/components/ModeBanner.tsx`:
```tsx
import React from 'react'
import type { RunMode } from '../types'

interface ModeBannerProps {
  mode: RunMode
}

export function ModeBanner({ mode }: ModeBannerProps) {
  if (mode === 'dryrun') {
    return (
      <div
        style={{
          padding: '8px 22px',
          borderBottom: '1.5px solid var(--line)',
          fontFamily: "'Shippori Mincho B1', serif",
          fontWeight: 700,
          fontSize: '13px',
          color: '#fff',
          background: 'repeating-linear-gradient(45deg,#6a5a9e,#6a5a9e 10px,#4e4179 10px,#4e4179 20px)',
          flexShrink: 0,
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}
      >
        <span>👻</span>
        <span>DRY-RUN — evaluating only. Nothing is being submitted to Edvibe.</span>
      </div>
    )
  }

  if (mode === 'full') {
    return (
      <div
        style={{
          padding: '8px 22px',
          borderBottom: '1.5px solid var(--line)',
          fontFamily: "'Shippori Mincho B1', serif",
          fontWeight: 700,
          fontSize: '13px',
          color: '#3a2600',
          background: 'repeating-linear-gradient(45deg,#cf9a36,#cf9a36 16px,#e0b85e 16px,#e0b85e 32px)',
          flexShrink: 0,
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}
      >
        <span>⚠️</span>
        <span>FULL-AUTO — real grades are being submitted and lessons completed.</span>
      </div>
    )
  }

  // review mode — no special banner in spec (ModeBanner only shown for dryrun & full)
  return null
}

export default ModeBanner
```

- [ ] **Step 2: Create Toast.tsx**

From spec §5.2: fixed bottom-center, auto-dismiss 3200ms, 4 variants (ok/err/warn/info).

Create `/home/ayatskii/adick_script/web/src/components/Toast.tsx`:
```tsx
import React, { useEffect } from 'react'
import type { ToastState } from '../types'

interface ToastProps extends ToastState {
  onDismiss: () => void
}

const TOAST_STYLE: Record<string, { bg: string; fg: string; icon: string }> = {
  ok: { bg: '#2f8f6b', fg: '#fff', icon: '🎉' },
  err: { bg: '#c62d1f', fg: '#fff', icon: '💥' },
  warn: { bg: '#cf9a36', fg: '#3a2600', icon: '⚠️' },
  info: { bg: 'var(--violet)', fg: '#fff', icon: '👻' },
}

export function Toast({ kind, message, onDismiss }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onDismiss, 3200)
    return () => clearTimeout(timer)
  }, [message, onDismiss])

  const style = TOAST_STYLE[kind] ?? TOAST_STYLE.info

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '24px',
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 60,
        display: 'inline-flex',
        alignItems: 'center',
        gap: '10px',
        padding: '13px 20px',
        border: '1.5px solid var(--line)',
        borderRadius: '5px',
        boxShadow: '5px 5px 13px var(--shadowc)',
        background: style.bg,
        color: style.fg,
        fontFamily: "'Shippori Mincho B1', serif",
        fontWeight: 700,
        fontSize: '14px',
        animation: 'popin .3s ease both',
        cursor: 'pointer',
        maxWidth: '90vw',
      }}
      onClick={onDismiss}
    >
      <span>{style.icon}</span>
      <span>{message}</span>
    </div>
  )
}

export default Toast
```

- [ ] **Step 3: Create Dialog.tsx**

From spec §5.1: fixed backdrop, 440px modal, two configs (full / stop), worried-face avatar, popin animation.

Create `/home/ayatskii/adick_script/web/src/components/Dialog.tsx`:
```tsx
import React from 'react'
import type { DialogKind, RunMode } from '../types'

interface DialogProps {
  kind: DialogKind
  onCancel: () => void
  onConfirm: (mode?: RunMode) => void
}

// Worried face SVG — used in dialog header avatar
function WorriedFace() {
  return (
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none" stroke="#3a2600" strokeWidth="1.8" strokeLinecap="round">
      {/* X-ish brows */}
      <path d="M10 10 L14 12M14 10 L10 12" />
      <path d="M18 10 L22 12M22 10 L18 12" />
      {/* dot eyes */}
      <circle cx="12" cy="15" r="1.5" fill="#3a2600" stroke="none" />
      <circle cx="20" cy="15" r="1.5" fill="#3a2600" stroke="none" />
      {/* flat worried mouth */}
      <path d="M11 22 Q16 20 21 22" />
    </svg>
  )
}

interface DialogConfig {
  title: string
  body: string
  note: string
  confirmLabel: string
  confirmBg: string
  confirmFg: string
  headerBg: string
}

const DIALOG_CONFIGS: Record<NonNullable<DialogKind>, DialogConfig> = {
  full: {
    title: 'Start a Full-auto run?',
    body: 'This will submit REAL grades and mark lessons complete on edvibe.com. These actions are irreversible.',
    note: 'Credentials are stored locally only — nothing leaves this machine except grade submissions to Edvibe.',
    confirmLabel: 'Yes, run full-auto',
    confirmBg: '#cf9a36',
    confirmFg: '#3a2600',
    headerBg: 'repeating-linear-gradient(45deg,#ffe0a3,#ffe0a3 12px,#ffd27d 12px,#ffd27d 24px)',
  },
  stop: {
    title: 'Stop this run?',
    body: 'The bot will finish the current exercise and halt. Already-submitted grades stay submitted; remaining students will be left untouched.',
    note: 'You can resume later from New Run — completed students are skipped automatically.',
    confirmLabel: 'Stop the run',
    confirmBg: '#c62d1f',
    confirmFg: '#fff',
    headerBg: '#e8d8d2',
  },
}

export function Dialog({ kind, onCancel, onConfirm }: DialogProps) {
  if (!kind) return null

  const config = DIALOG_CONFIGS[kind]

  function handleBackdropClick(e: React.MouseEvent) {
    if (e.target === e.currentTarget) onCancel()
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 70,
        background: 'rgba(18,14,28,.55)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      onClick={handleBackdropClick}
    >
      <div
        style={{
          width: '440px',
          maxWidth: '95vw',
          background: 'var(--panel)',
          border: '1.5px solid var(--line)',
          borderRadius: '7px',
          boxShadow: '8px 8px 16px var(--shadowc)',
          animation: 'popin .28s ease both',
          overflow: 'hidden',
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
            padding: '16px 20px',
            background: config.headerBg,
          }}
        >
          {/* Worried face avatar */}
          <div
            style={{
              width: '52px',
              height: '52px',
              borderRadius: '50%',
              background: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <WorriedFace />
          </div>
          <h2
            style={{
              margin: 0,
              fontFamily: "'Shippori Mincho B1', serif",
              fontWeight: 800,
              fontSize: '19px',
              color: '#3a2600',
            }}
          >
            {config.title}
          </h2>
        </div>

        {/* Body */}
        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <p style={{ margin: 0, fontSize: '14.5px', color: 'var(--ink)', lineHeight: 1.5 }}>
            {config.body}
          </p>
          {/* Dashed note box */}
          <div
            style={{
              border: '1.5px dashed var(--line)',
              borderRadius: '4px',
              padding: '10px 14px',
              fontSize: '13px',
              color: 'var(--ink-soft)',
              lineHeight: 1.5,
            }}
          >
            🔒 {config.note}
          </div>
        </div>

        {/* Footer buttons */}
        <div
          style={{
            display: 'flex',
            gap: '10px',
            padding: '0 20px 20px',
            justifyContent: 'flex-end',
          }}
        >
          <button
            className="squish"
            onClick={onCancel}
            style={{
              padding: '10px 18px',
              borderRadius: '4px',
              border: '1.5px solid var(--line)',
              background: 'var(--panel2)',
              color: 'var(--ink)',
              fontFamily: "'Shippori Mincho B1', serif",
              fontWeight: 700,
              fontSize: '14px',
              cursor: 'pointer',
            }}
          >
            Cancel
          </button>
          <button
            className="squish"
            onClick={() => onConfirm(kind === 'full' ? 'full' : undefined)}
            style={{
              padding: '10px 18px',
              borderRadius: '4px',
              border: '1.5px solid var(--line)',
              background: config.confirmBg,
              color: config.confirmFg,
              fontFamily: "'Shippori Mincho B1', serif",
              fontWeight: 700,
              fontSize: '14px',
              cursor: 'pointer',
              boxShadow: '3px 3px 13px var(--shadowc)',
            }}
          >
            {config.confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}

export default Dialog
```

- [ ] **Step 4: Commit**

```bash
cd /home/ayatskii/adick_script
git add web/src/components/ModeBanner.tsx web/src/components/Toast.tsx web/src/components/Dialog.tsx
git commit -m "feat(web): ModeBanner, Toast (auto-dismiss 3200ms), Dialog (full/stop configs)"
```

---

## Task 12: src/AppContext.tsx — React context for shared state/handlers

**Files:**
- Create: `/home/ayatskii/adick_script/web/src/AppContext.tsx`

- [ ] **Step 1: Create AppContext.tsx**

Create `/home/ayatskii/adick_script/web/src/AppContext.tsx`:
```tsx
import React, { createContext, useContext } from 'react'
import type { ScreenProps } from './types'

export const AppContext = createContext<ScreenProps | null>(null)

export function useApp(): ScreenProps {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used inside AppContext.Provider')
  return ctx
}
```

- [ ] **Step 2: Commit**

```bash
cd /home/ayatskii/adick_script
git add web/src/AppContext.tsx
git commit -m "feat(web): AppContext for shared screen props"
```

---

## Task 13: src/screens/*.tsx — 8 stub screens

**Files:**
- Create: `/home/ayatskii/adick_script/web/src/screens/Dashboard.tsx`
- Create: `/home/ayatskii/adick_script/web/src/screens/NewRun.tsx`
- Create: `/home/ayatskii/adick_script/web/src/screens/LiveMonitor.tsx`
- Create: `/home/ayatskii/adick_script/web/src/screens/ReviewQueue.tsx`
- Create: `/home/ayatskii/adick_script/web/src/screens/Students.tsx`
- Create: `/home/ayatskii/adick_script/web/src/screens/History.tsx`
- Create: `/home/ayatskii/adick_script/web/src/screens/Flagged.tsx`
- Create: `/home/ayatskii/adick_script/web/src/screens/Settings.tsx`

- [ ] **Step 1: Create all 8 stub screens**

Each stub renders its title and a TODO placeholder. All import ScreenProps for type safety.

Create `/home/ayatskii/adick_script/web/src/screens/Dashboard.tsx`:
```tsx
import React from 'react'
import type { ScreenProps } from '../types'

export function Dashboard(_props: ScreenProps) {
  return (
    <div>
      <h2 style={{ fontFamily: "'Shippori Mincho B1', serif", fontWeight: 800, color: 'var(--ink)' }}>Dashboard</h2>
      <p style={{ color: 'var(--ink-soft)' }}>TODO: implement — stat tiles, advisory banner, hero, recent runs table</p>
    </div>
  )
}

export default Dashboard
```

Create `/home/ayatskii/adick_script/web/src/screens/NewRun.tsx`:
```tsx
import React from 'react'
import type { ScreenProps } from '../types'

export function NewRun(_props: ScreenProps) {
  return (
    <div>
      <h2 style={{ fontFamily: "'Shippori Mincho B1', serif", fontWeight: 800, color: 'var(--ink)' }}>New Run</h2>
      <p style={{ color: 'var(--ink-soft)' }}>TODO: implement — mode segments, scope picker, safety caps, confidence slider, start button</p>
    </div>
  )
}

export default NewRun
```

Create `/home/ayatskii/adick_script/web/src/screens/LiveMonitor.tsx`:
```tsx
import React from 'react'
import type { ScreenProps } from '../types'

export function LiveMonitor(_props: ScreenProps) {
  return (
    <div>
      <h2 style={{ fontFamily: "'Shippori Mincho B1', serif", fontWeight: 800, color: 'var(--ink)' }}>Live Monitor</h2>
      <p style={{ color: 'var(--ink-soft)' }}>TODO: implement — empty (napping mascot) + active states, run tree, progress tube, detail card, log console + simulation</p>
    </div>
  )
}

export default LiveMonitor
```

Create `/home/ayatskii/adick_script/web/src/screens/ReviewQueue.tsx`:
```tsx
import React from 'react'
import type { ScreenProps } from '../types'

export function ReviewQueue(_props: ScreenProps) {
  return (
    <div>
      <h2 style={{ fontFamily: "'Shippori Mincho B1', serif", fontWeight: 800, color: 'var(--ink)' }}>Review Queue</h2>
      <p style={{ color: 'var(--ink-soft)' }}>TODO: implement — all-done empty state, filter bar, editable score/comment cards, sticky submit footer</p>
    </div>
  )
}

export default ReviewQueue
```

Create `/home/ayatskii/adick_script/web/src/screens/Students.tsx`:
```tsx
import React from 'react'
import type { ScreenProps } from '../types'

export function Students(_props: ScreenProps) {
  return (
    <div>
      <h2 style={{ fontFamily: "'Shippori Mincho B1', serif", fontWeight: 800, color: 'var(--ink)' }}>Students</h2>
      <p style={{ color: 'var(--ink-soft)' }}>TODO: implement — compact zebra table, expandable rows, per-row Run action</p>
    </div>
  )
}

export default Students
```

Create `/home/ayatskii/adick_script/web/src/screens/History.tsx`:
```tsx
import React from 'react'
import type { ScreenProps } from '../types'

export function History(_props: ScreenProps) {
  return (
    <div>
      <h2 style={{ fontFamily: "'Shippori Mincho B1', serif", fontWeight: 800, color: 'var(--ink)' }}>History &amp; Audit</h2>
      <p style={{ color: 'var(--ink-soft)' }}>TODO: implement — Runs tab (list + timeline + export) and Reconcile tab (leftover-flag table)</p>
    </div>
  )
}

export default History
```

Create `/home/ayatskii/adick_script/web/src/screens/Flagged.tsx`:
```tsx
import React from 'react'
import type { ScreenProps } from '../types'

export function Flagged(_props: ScreenProps) {
  return (
    <div>
      <h2 style={{ fontFamily: "'Shippori Mincho B1', serif", fontWeight: 800, color: 'var(--ink)' }}>Flagged</h2>
      <p style={{ color: 'var(--ink-soft)' }}>TODO: implement — 5 amber notice cards with reason/severity/detail + Resolve/Retry</p>
    </div>
  )
}

export default Flagged
```

Create `/home/ayatskii/adick_script/web/src/screens/Settings.tsx`:
```tsx
import React from 'react'
import type { ScreenProps } from '../types'

export function Settings(_props: ScreenProps) {
  return (
    <div>
      <h2 style={{ fontFamily: "'Shippori Mincho B1', serif", fontWeight: 800, color: 'var(--ink)' }}>Settings</h2>
      <p style={{ color: 'var(--ink-soft)' }}>TODO: implement — credentials, models, grading, behavior, danger zone</p>
    </div>
  )
}

export default Settings
```

- [ ] **Step 2: Commit**

```bash
cd /home/ayatskii/adick_script
git add web/src/screens/
git commit -m "feat(web): 8 stub screens with correct props interface and TODO placeholders"
```

---

## Task 14: src/App.tsx — root shell + state + routing

**Files:**
- Create: `/home/ayatskii/adick_script/web/src/App.tsx`

- [ ] **Step 1: Create App.tsx**

Root shell holding all app state. Renders: root flex container with `data-theme`, Backdrop, Sidebar, column with TopBar + ModeBanner (conditional) + `<main>` (halftone dots bg). Wire nav, theme toggle, run state, toast, dialog. Pass all state/handlers to screens via AppContext.

Create `/home/ayatskii/adick_script/web/src/App.tsx`:
```tsx
import React, { useState, useCallback } from 'react'
import type {
  ScreenId, RunState, RunMode, ToastState, ToastKind, DialogKind,
  AppHandlers, AppSharedState,
} from './types'
import { AppContext } from './AppContext'
import { Backdrop } from './components/Backdrop'
import { Sidebar } from './components/Sidebar'
import { TopBar } from './components/TopBar'
import { ModeBanner } from './components/ModeBanner'
import { Toast } from './components/Toast'
import { Dialog } from './components/Dialog'
import { Dashboard } from './screens/Dashboard'
import { NewRun } from './screens/NewRun'
import { LiveMonitor } from './screens/LiveMonitor'
import { ReviewQueue } from './screens/ReviewQueue'
import { Students } from './screens/Students'
import { History } from './screens/History'
import { Flagged } from './screens/Flagged'
import { Settings } from './screens/Settings'
import { REVIEW_ITEMS, FLAGGED_ITEMS } from './data'

// Count of pending review items for nav badge
const INITIAL_REVIEW_COUNT = REVIEW_ITEMS.filter(r => r.status === 'pending').length
const INITIAL_FLAGGED_COUNT = FLAGGED_ITEMS.length

const INITIAL_RUN: RunState = {
  active: false,
  mode: 'dryrun',
  total: 0,
  current: 0,
  studentsDone: 0,
  students: 0,
  finished: false,
}

function ScreenRenderer(props: AppSharedState & AppHandlers) {
  switch (props.screen) {
    case 'dashboard': return <Dashboard {...props} />
    case 'new': return <NewRun {...props} />
    case 'live': return <LiveMonitor {...props} />
    case 'review': return <ReviewQueue {...props} />
    case 'students': return <Students {...props} />
    case 'history': return <History {...props} />
    case 'flagged': return <Flagged {...props} />
    case 'settings': return <Settings {...props} />
  }
}

export function App() {
  const [screen, setScreen] = useState<ScreenId>('dashboard')
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [run, setRun] = useState<RunState>(INITIAL_RUN)
  const [toast, setToast] = useState<ToastState | null>(null)
  const [dialog, setDialog] = useState<DialogKind>(null)
  const [reviewCount] = useState(INITIAL_REVIEW_COUNT)
  const [flaggedCount] = useState(INITIAL_FLAGGED_COUNT)

  // editor-tweakable props (can be overridden via Settings in future)
  const mascotName = 'Vibe-Bot'
  const defaultRunMode: RunMode = 'dryrun'

  // ============================================================
  // Handlers
  // ============================================================

  const showToast = useCallback((kind: ToastKind, message: string) => {
    setToast({ kind, message })
  }, [])

  const dismissToast = useCallback(() => setToast(null), [])

  const startRun = useCallback((mode: RunMode) => {
    setRun({
      active: true,
      mode,
      total: 41, // spec: 41 lessons awaiting
      current: 0,
      studentsDone: 0,
      students: 17, // spec: 17 pending students
      finished: false,
    })
    setDialog(null)
    setScreen('live')
  }, [])

  const stopRun = useCallback(() => {
    setRun(prev => ({ ...prev, active: false, finished: true }))
    setDialog(null)
    showToast('warn', 'Run stopped — in-progress exercise will finish, then halt.')
  }, [showToast])

  const openDialog = useCallback((kind: DialogKind) => {
    setDialog(kind)
  }, [])

  const handleDialogConfirm = useCallback((mode?: RunMode) => {
    if (dialog === 'full') {
      startRun(mode ?? 'full')
    } else if (dialog === 'stop') {
      stopRun()
    }
  }, [dialog, startRun, stopRun])

  const handleRunPillClick = useCallback(() => {
    if (run.active) {
      openDialog('stop')
    } else {
      setScreen('live')
    }
  }, [run.active, openDialog])

  // ============================================================
  // Shared state + handlers (passed to screens)
  // ============================================================

  const sharedState: AppSharedState = {
    screen,
    theme,
    run,
    mascotName,
    defaultRunMode,
  }

  const handlers: AppHandlers = {
    showToast,
    startRun,
    stopRun,
    openDialog,
    setScreen,
  }

  const screenProps = { ...sharedState, ...handlers }

  return (
    <AppContext.Provider value={screenProps}>
      {/* Root flex container — data-theme drives CSS variable switching */}
      <div
        data-theme={theme}
        style={{
          display: 'flex',
          height: '100vh',
          width: '100%',
          overflow: 'hidden',
          background: 'var(--bg)',
          color: 'var(--ink)',
          position: 'relative',
        }}
      >
        {/* Atmospheric backdrop (fixed, z-0) */}
        <Backdrop />

        {/* Sidebar (z-20) */}
        <Sidebar
          screen={screen}
          open={sidebarOpen}
          onNavigate={setScreen}
          onToggle={() => setSidebarOpen(o => !o)}
          reviewCount={reviewCount}
          flaggedCount={flaggedCount}
        />

        {/* Main column */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            position: 'relative',
            zIndex: 1,
          }}
        >
          {/* Top bar */}
          <TopBar
            screen={screen}
            theme={theme}
            run={run}
            onThemeToggle={() => setTheme(t => t === 'light' ? 'dark' : 'light')}
            onRunPillClick={handleRunPillClick}
          />

          {/* Mode banner (only when run is active) */}
          {run.active && (
            <ModeBanner mode={run.mode} />
          )}

          {/* Main content area with halftone dot pattern */}
          <main
            style={{
              flex: 1,
              overflowY: 'auto',
              backgroundImage: 'radial-gradient(var(--dot) 1.6px, transparent 1.7px)',
              backgroundSize: '20px 20px',
            }}
          >
            {/* Inner wrapper */}
            <div
              style={{
                maxWidth: '1240px',
                margin: '0 auto',
                padding: '26px 28px 60px',
              }}
            >
              <ScreenRenderer {...screenProps} />
            </div>
          </main>
        </div>

        {/* Overlays */}
        {toast && (
          <Toast kind={toast.kind} message={toast.message} onDismiss={dismissToast} />
        )}

        <Dialog
          kind={dialog}
          onCancel={() => setDialog(null)}
          onConfirm={handleDialogConfirm}
        />
      </div>
    </AppContext.Provider>
  )
}

export default App
```

- [ ] **Step 2: Commit**

```bash
cd /home/ayatskii/adick_script
git add web/src/App.tsx
git commit -m "feat(web): App.tsx — root shell, state, routing, overlays, all 8 screens wired"
```

---

## Task 15: npm install + npm run build verification

**Files:** none (verification only)

- [ ] **Step 1: Install dependencies**

```bash
cd /home/ayatskii/adick_script/web && npm install
```

Expected: packages installed without errors. If network is blocked, note it and continue.

- [ ] **Step 2: Run the build**

```bash
cd /home/ayatskii/adick_script/web && npm run build
```

Expected: `✓ built in Xs` with no TypeScript errors.

- [ ] **Step 3: Fix any type errors found**

If `tsc` reports errors, fix them in the relevant files. Common issues to watch for:
- Unused imports (strict TS flags)
- Missing type annotations
- `_props` parameter should be named with `_` prefix to suppress unused-parameter errors

- [ ] **Step 4: Final commit with build-confirmed note**

```bash
cd /home/ayatskii/adick_script
git add web/
git commit -m "feat(web): frontend foundation — tokens, shell, shared components, seed data, screen stubs"
```

---

## Component API Reference (for screen implementers)

### How to implement a screen

1. Open the stub in `/home/ayatskii/adick_script/web/src/screens/YourScreen.tsx`
2. Replace the `TODO` placeholder with the full screen body
3. Use `const app = useApp()` from `'../AppContext'` to get all state and handlers, OR use the passed-in `props: ScreenProps`
4. Use CSS variables via Tailwind arbitrary values: `className="bg-[var(--panel)] border-[var(--line)]"` or inline styles
5. Use `className="squish"` on all interactive buttons
6. Import `StatusBadge` from `'../components/StatusBadge'`, seed data from `'../data'`

### StatusBadge props

```ts
<StatusBadge status={StatusKind} label?: string />
```
- `status` — one of: `evaluating | graded | skipped | flagged | error | dryrun | idle | queued | running`
- `label` — optional override; if omitted, uses default from variant table

### Toast

Triggered via `app.showToast(kind, message)`:
- `kind`: `'ok' | 'err' | 'warn' | 'info'`
- Auto-dismisses after 3200ms

### Dialog

Triggered via `app.openDialog(kind)`:
- `'full'` — shows "Start Full-auto run?" confirmation → calls `app.startRun('full')` on confirm
- `'stop'` — shows "Stop this run?" confirmation → calls `app.stopRun()` on confirm
- `null` — closes dialog

### App state available on ScreenProps

```ts
interface ScreenProps {
  // State
  screen: ScreenId           // current screen id
  theme: 'light' | 'dark'
  run: RunState              // { active, mode, total, current, studentsDone, students, finished }
  mascotName: string         // default 'Vibe-Bot'
  defaultRunMode: RunMode    // default 'dryrun'

  // Handlers
  showToast(kind, message): void
  startRun(mode: RunMode): void   // sets run active, navigates to Live Monitor
  stopRun(): void
  openDialog(kind: DialogKind): void
  setScreen(screen: ScreenId): void
}
```

### data.ts exports

| Export | Type | Count | Used by |
|---|---|---|---|
| `RUN_ROWS` | `RunRow[]` | 5 | Dashboard recent runs, History runs tab |
| `REVIEW_ITEMS` | `ReviewItem[]` | 6 | Review Queue |
| `STUDENT_ROWS` | `StudentRow[]` | 12 | Students table |
| `TIMELINE_ENTRIES` | `TimelineEntry[]` | 6 | History timeline |
| `RECONCILE_ROWS` | `ReconcileRow[]` | 4 | History reconcile tab |
| `FLAGGED_ITEMS` | `FlaggedItem[]` | 5 | Flagged screen |
| `SETTINGS_DEFAULTS` | `const` object | — | Settings screen initial values |

### CSS token usage example

```tsx
// Prefer Tailwind arbitrary values for layout:
<div className="bg-[var(--panel)] border-[1.5px] border-[var(--line)] rounded-[6px]">

// For complex gradient/shadow values, use inline style:
<div style={{ boxShadow: '5px 5px 16px var(--shadowc)', background: 'var(--panel)' }}>

// Cards pattern:
<div style={{ border: '1.5px solid var(--line)', borderRadius: '6px', boxShadow: '5px 5px 16px var(--shadowc)', background: 'var(--panel)' }}>
  <div style={{ background: 'var(--panel2)', padding: '11px 16px' }}>Header</div>
  <div style={{ padding: '16px' }}>Body</div>
</div>
```
