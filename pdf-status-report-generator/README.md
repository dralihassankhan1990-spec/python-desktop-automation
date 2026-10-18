# PDF Status Report Generator

**By Muhammad Bilal** · 100% local — no APIs, no network, no cloud, no keys.

## Problem it solves

Every week a PM rebuilds the same status report by hand: copy numbers from a
tracker into slides, recolour RAG cells, retype milestones and risks. It takes
1–2 hours, the numbers drift between versions, and no two projects' reports
ever look the same. Stakeholders stop trusting the figures.

## How it works

1. **Read** `project-data.xlsx` — five sheets: `Projects`, `Milestones`,
   `Tasks`, `Risks`, `NextSteps`.
2. **Compute** (nothing is typed): task completion %, budget used %,
   milestones on track, and a deterministic **RAG** status —
   RED if budget used > 95% or any milestone is Delayed,
   AMBER if budget used > 85% or any task is Delayed, else GREEN.
3. **Generate** a polished multi-page PDF per project:
   cover page (with RAG badge) → KPI summary (cards + budget bar) →
   milestone timeline (colour-coded) → risks & issues (L×I rating) →
   next steps. Headers, coloured tables, page numbers on every page.

## Run it

```bash
# macOS / Linux
./run.sh                          # builds sample data + all project reports
./run.sh --project ERP-01         # one project only

# Windows
run.bat
run.bat --project ERP-01
```

`run.sh` / `run.bat` create a local `.venv`, install the two pinned
dependencies, rebuild the sample workbook, and generate the reports.

Manual run (if you already have the deps):

```bash
pip install -r requirements.txt
python make_sample_data.py        # (re)builds project-data.xlsx
python generate_report.py --project CRM-02
```

Output: `output/Status-Report-<ProjectName>-<YYYY-MM-DD>.pdf`

## Use your own data

Keep the five sheet names and column headers, replace the rows, re-run.
The generator validates the workbook (missing sheet → clear error) and
skips blank rows.

| Sheet | Key columns |
|---|---|
| `Projects` | ProjectID, ProjectName, Manager, Sponsor, StartDate, EndDate, BudgetPKR, SpentPKR |
| `Milestones` | ProjectID, Milestone, DueDate, Status (Done / In Progress / Delayed / Not Started), Owner |
| `Tasks` | ProjectID, Task, Owner, Status, DueDate |
| `Risks` | ProjectID, Risk, Likelihood(1-3), Impact(1-3), Mitigation, Owner |
| `NextSteps` | ProjectID, NextStep, Owner, DueDate |

## Error handling & scaling

- Missing workbook or sheet → clear log error, exit code 1 (never a silent
  half-report).
- Unknown `--project` ID → clear error listing nothing generated.
- Blank rows ignored; missing budget treated as 0 (logged via the math).
- Scales to any number of projects: one PDF per project, one command.
  Add a project by adding rows — no code change.

## Demo video

`pdf-status-report-generator-demo.mp4` — problem → solution → live run
(real terminal output, real generated PDF pages) → result.
