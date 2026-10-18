# TEST REPORT — PDF Status Report Generator

**By Muhammad Bilal** · Tested 2026-10-16 · Python 3.12.3 · fpdf2==2.8.3, openpyxl==3.1.2.

## Test 1 — Full run (both projects)

```bash
python make_sample_data.py
python generate_report.py
```

Real output:

```text
Wrote project-data.xlsx: 2 projects, 11 milestones, 18 tasks, 6 risks, 6 next steps.
2026-10-16 10:13:06 [INFO] Riverdale ERP Rollout | RAG=GREEN | completion=50.0% | budget=62.4% -> Status-Report-Riverdale-ERP-Rollout-2026-10-16.pdf
2026-10-16 10:13:06 [INFO] Harbor CRM Upgrade | RAG=RED | completion=50.0% | budget=92.9% -> Status-Report-Harbor-CRM-Upgrade-2026-10-16.pdf
2026-10-16 10:13:06 [INFO] Done: 2 report(s) in .../output
```

Real output files:

| File | Pages | Size | RAG |
|---|---|---|---|
| `output/Status-Report-Riverdale-ERP-Rollout-2026-10-16.pdf` | 5, A4 | 6,165 B | GREEN |
| `output/Status-Report-Harbor-CRM-Upgrade-2026-10-16.pdf` | 5, A4 | 6,103 B | RED |

KPI verification (hand-checked against the workbook):

- ERP: 5/10 tasks Done = **50.0%** ✓ · PKR 7,800,000 / 12,500,000 = **62.4%** ✓ ·
  no delayed milestones → **GREEN** ✓
- CRM: 4/8 tasks Done = **50.0%** ✓ · PKR 3,900,000 / 4,200,000 = **92.9%** ✓ ·
  one Delayed milestone (training) → **RED** ✓

## Test 2 — Visual QA

All 10 pages rendered to PNG (`pdftoppm`) and inspected:

- Cover: title, project name, coloured RAG badge, manager/sponsor/period/date — clean.
- KPI page: 4 cards + budget bar (green at 62.4%), page footer "Page 2/5".
- Milestone page: colour-coded statuses (Done green, In Progress blue,
  Not Started grey), alternating row shading.
- Risks page: L×I ratings with High (red) / Medium (amber) fills, mitigation + owner.
- Next steps page: numbered steps with owner + due date.
- Result: **PASS** — professional layout, no overflow, no clipped text.

## Test 3 — Error paths

| Command | Expected | Actual |
|---|---|---|
| `generate_report.py --project NOPE` | clear error, exit 1 | `No project with ID 'NOPE' found…`, exit 1 — PASS |
| `generate_report.py --input missing.xlsx` | clear error, exit 1 | `Input workbook not found: missing.xlsx`, exit 1 — PASS |
| `generate_report.py --project CRM-02` | single PDF | generated only the CRM report — PASS |

## Bugs found & fixed during testing (honest log)

- **Bug 1:** `FPDFUnicodeEncodingException` — em-dash (—) in "GREEN — ON TRACK"
  is outside latin-1, which core PDF fonts require.
  Fix: added `safe()` sanitizer mapping common Unicode punctuation to ASCII,
  plus `cell()` / `multi_cell()` overrides so **every** string (including
  user data from Excel) is sanitized before rendering.
- **Bug 2 (introduced by the Bug-1 fix):** the `cell()` override sanitized
  positional arg 0 — but in fpdf2 `cell(w, h, text, ...)` text is arg index 2.
  It turned the width into a string → `ValueError: w and h must be numbers`.
  Fix: sanitize arg index 2 in both overrides. Re-ran — both PDFs generated.

## Coverage summary

| Check | Result |
|---|---|
| 2 projects → 2 PDFs, 5 pages each | PASS |
| KPI math (completion, budget) | PASS (hand-verified) |
| RAG logic (GREEN / RED) | PASS |
| Milestone / risks / next-steps tables | PASS |
| Page numbers + footers | PASS |
| Visual QA of all pages | PASS |
| Error paths (bad project, missing file) | PASS |
| Single-project mode | PASS |
