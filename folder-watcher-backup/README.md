# Folder Watcher & Auto-Backup

**By Muhammad Bilal** · 100% local — no APIs, no network, no cloud, no keys.

## Problem it solves

A PM team shares a project folder. Someone overwrites the status tracker, a
deliverable gets deleted by accident, a laptop crashes before the weekly
backup. Manual backups are forgotten, and cloud sync keeps only one "latest"
copy — so one overwrite destroys the previous version forever. Recovery
becomes a search through chat history and email attachments.

## How it works

1. **Poll** the watched folder every N seconds (plain polling — zero native
   dependencies, works on Windows / macOS / Linux).
2. **Detect** created / modified / deleted files by comparing
   `(mtime, size)` snapshots.
3. **Versioned backup** — every new or changed file is copied to
   `backup/<relative-path>/YYYY-MM-DD_HHMMSS_<filename>`.
4. **Auto-prune** — at most 5 versions per file are kept (configurable);
   older ones are deleted automatically.
5. **Audit trail** — every event is appended to `change-log.csv`
   (`timestamp, file, event, backup_path`).
6. **Daily report** — `backup-report.html` summarizes today's events,
   versions per file, and recent history. Regenerated at the end of every
   run, or on demand with `--report-only`.

## Run it

```bash
# macOS / Linux
./run.sh                      # run until Ctrl+C (report written on stop)
./run.sh --duration 120       # run for 120 seconds, then stop + report

# Windows
run.bat                       # run until Ctrl+C
run.bat --duration 120
```

Prove it in 20 seconds — two terminals:

```bash
# Terminal 1
./run.sh --duration 60
# Terminal 2 (while Terminal 1 runs)
python demo_changes.py
```

Then open `backup/` (timestamped copies), `change-log.csv` (the event ledger)
and `backup-report.html` (the summary).

## Configuration

Edit the CONFIG block at the top of `watcher.py`, or pass flags:

| Flag | Default | Meaning |
|---|---|---|
| `--watch` | `./demo-project` | Folder to watch |
| `--backup` | `./backup` | Where versioned copies go |
| `--interval` | `5` | Poll interval in seconds |
| `--duration` | `0` (= until Ctrl+C) | Seconds to run |
| `--report-only` | — | Regenerate the HTML report from the log and exit |

`MAX_VERSIONS = 5` lives in the CONFIG block (retention per file).

## Outputs

| File | What it is |
|---|---|
| `backup/<path>/YYYY-MM-DD_HHMMSS_<file>` | Versioned copies, grouped by original path |
| `change-log.csv` | Full event ledger (created / modified / deleted) |
| `backup-report.html` | Daily summary — KPIs, versions per file, recent events |
| `watcher.log` | Detailed run log |

## Error handling & scaling

- Missing watch folder → created automatically; unreadable files are logged
  and skipped, never crash the loop.
- Backup failures are logged and retried on the next scan.
- Deletions are logged (no copy possible) so nothing disappears silently.
- The backup folder itself, OS junk files (`.DS_Store`, `Thumbs.db`,
  Office lock files `~$...`) and temp files are never backed up.
- Scales to thousands of files: snapshots are cheap `(mtime, size)` tuples;
  for very large folders, raise `--interval` or point it at one project
  folder per watcher instance.

## Demo video

`folder-watcher-backup-demo.mp4` — problem → solution → live run
(real terminal output, real versioned backups, real report) → result.
