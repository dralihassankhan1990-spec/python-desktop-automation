# 04 — Python Desktop Automation

**By Muhammad Bilal** · Two production-ready desktop automations for project
management teams. **100% local** — no external APIs, no API keys, no network
calls, no cloud services. All demo data is fictional.

## The automations

### 1. `folder-watcher-backup/` — Folder Watcher & Auto-Backup

A PM team's shared folder, protected. Polls a folder every few seconds;
on any new or changed file it saves a timestamped versioned copy
(`backup/<path>/YYYY-MM-DD_HHMMSS_<file>`), keeps the last **5 versions** per
file (auto-prunes older), logs every event to `change-log.csv`, and
generates a daily `backup-report.html` summary.

- **Stack:** Python 3.9+ standard library only — zero dependencies.
- **Run:** `./run.sh --duration 120` (or `run.bat` on Windows).
  Prove it: run the watcher in one terminal, `python demo_changes.py` in another.
- **Verified:** 6/6 demo events detected, retention pruning proven
  (7 edits → exactly 5 versions), full TEST-REPORT.md inside.
- **Video:** `folder-watcher-backup-demo.mp4` (94 s).

### 2. `pdf-status-report-generator/` — PDF Status Report Generator

Turns one Excel workbook (`project-data.xlsx`) into polished multi-page PDF
status reports — one per project. Cover page with RAG badge → KPI summary
(completion %, budget used, milestones on track, open risks) → milestone
timeline → risks & issues (L×I rating) → next steps. KPIs and RAG are
**computed**, never typed.

- **Stack:** Python + `fpdf2==2.8.3` + `openpyxl==3.1.2` (pinned).
- **Run:** `./run.sh` (or `run.bat` on Windows) — creates a local `.venv`,
  installs deps, rebuilds sample data, generates the reports.
- **Verified:** 2 projects → 2 PDFs (5 pages each, A4), KPI math hand-checked,
  error paths tested, all pages visually inspected. Full TEST-REPORT.md inside.
- **Video:** `pdf-status-report-generator-demo.mp4` (94 s).

## Folder layout

```text
04-Python-Desktop-Automation/
├── README.md                      # this file
├── build_videos.py                # rebuilds both demo videos (TTS + ffmpeg)
├── folder-watcher-backup/
│   ├── watcher.py                 # the automation
│   ├── demo_changes.py            # proves it works in ~20 s
│   ├── demo-project/              # sample watched folder
│   ├── backup/                    # real versioned backups from the test run
│   ├── change-log.csv             # real event ledger from the test run
│   ├── backup-report.html         # real daily report from the test run
│   ├── README.md  requirements.txt  run.sh  run.bat  TEST-REPORT.md
│   └── folder-watcher-backup-demo.mp4
└── pdf-status-report-generator/
    ├── generate_report.py         # the automation
    ├── make_sample_data.py        # builds project-data.xlsx (2 fictional projects)
    ├── project-data.xlsx          # sample input
    ├── output/                    # the 2 real generated PDFs
    ├── README.md  requirements.txt  run.sh  run.bat  TEST-REPORT.md
    └── pdf-status-report-generator-demo.mp4
```

## How to demo (2 minutes each)

1. **Watcher:** `./run.sh --duration 60` in one terminal,
   `python demo_changes.py` in another. Open `backup/`, `change-log.csv`,
   `backup-report.html`.
2. **PDF generator:** `./run.sh` — then open the two PDFs in `output/`.

## Notes

- Everything runs on the user's own machine. No data leaves it.
- The demo videos show **real execution**: actual terminal output, the real
  change log, the real HTML report, and the real generated PDF pages —
  no mockups. Narration is TTS-generated.
- `build_videos.py` regenerates both videos (needs `ffmpeg` + the TTS CLI).
- Known limitation: the watcher uses polling (not OS file events) by design —
  zero native dependencies, works identically on Windows / macOS / Linux.
  For very large folders, raise `--interval`.
