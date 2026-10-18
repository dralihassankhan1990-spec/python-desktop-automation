# TEST REPORT — Folder Watcher & Auto-Backup

**By Muhammad Bilal** · Tested 2026-10-16 · Python 3.12.3 · 100% local, no dependencies.

## Test 1 — Full demo run (the proof run)

Command (two terminals, as documented):

```bash
# Terminal 1
python watcher.py --duration 45 --interval 3
# Terminal 2
python demo_changes.py
```

Real watcher output:

```text
2026-10-16 10:08:18 [INFO] Watching .../folder-watcher-backup/demo-project
2026-10-16 10:08:18 [INFO] Initial snapshot: 2 file(s) tracked.
2026-10-16 10:08:24 [INFO] CREATED  meeting-notes.txt  ->  2026-10-16_100824_meeting-notes.txt
2026-10-16 10:08:27 [INFO] MODIFIED  docs/project-plan.md  ->  docs/2026-10-16_100827_project-plan.md
2026-10-16 10:08:30 [INFO] MODIFIED  docs/project-plan.md  ->  docs/2026-10-16_100830_project-plan.md
2026-10-16 10:08:33 [INFO] CREATED  data/tasks.csv  ->  data/2026-10-16_100833_tasks.csv
2026-10-16 10:08:36 [INFO] CREATED  scratch-to-delete.txt  ->  2026-10-16_100836_scratch-to-delete.txt
2026-10-16 10:08:39 [INFO] DELETED  scratch-to-delete.txt
2026-10-16 10:09:03 [INFO] Duration reached (45s). Stopping.
2026-10-16 10:09:03 [INFO] Stopped after 15 scan(s); 6 event(s) handled.
2026-10-16 10:09:03 [INFO] Report written: .../backup-report.html
```

Result: **PASS** — 6/6 demo events detected (3 created, 2 modified, 1 deleted).
`project-plan.md` got **two** timestamped versions (version A and B both preserved).

Real `backup/` tree after the run:

```text
backup/2026-10-16_100824_meeting-notes.txt
backup/2026-10-16_100836_scratch-to-delete.txt
backup/data/2026-10-16_100833_tasks.csv
backup/docs/2026-10-16_100827_project-plan.md
backup/docs/2026-10-16_100830_project-plan.md
```

Real `change-log.csv`:

```csv
timestamp,file,event,backup_path
2026-10-16 10:08:24,meeting-notes.txt,created,2026-10-16_100824_meeting-notes.txt
2026-10-16 10:08:27,docs/project-plan.md,modified,docs/2026-10-16_100827_project-plan.md
2026-10-16 10:08:30,docs/project-plan.md,modified,docs/2026-10-16_100830_project-plan.md
2026-10-16 10:08:33,data/tasks.csv,created,data/2026-10-16_100833_tasks.csv
2026-10-16 10:08:36,scratch-to-delete.txt,created,2026-10-16_100836_scratch-to-delete.txt
2026-10-16 10:08:39,scratch-to-delete.txt,deleted,
```

## Test 2 — Retention pruning (7 edits → max 5 versions)

7 rapid modifications to `retention-test.txt` with `--interval 1`:

```text
[INFO] Pruned old version (retention=5): 2026-10-16_100932_retention-test.txt
[INFO] Pruned old version (retention=5): 2026-10-16_100934_retention-test.txt
```

Versions kept: **exactly 5** (the 5 newest). Result: **PASS**.

## Test 3 — Report generation

`backup-report.html` regenerated at end of run and via
`python watcher.py --report-only`. Contains KPI cards, versions-per-file
table, and the recent-events table. Result: **PASS** (opened and checked).

## Bug found & fixed during testing (honest log)

- **Bug 1:** first run reported "0 files tracked" and detected nothing.
  Cause: `is_ignored()` called `path.is_relative_to(...)` and returned
  `True` unconditionally — `is_relative_to` returns a bool, it does not
  raise. Every file was ignored.
  Fix: `if path.resolve().is_relative_to(backup_dir.resolve()): return True`.
  Re-ran — all 6 demo events detected. This is why Test 1 was run twice.

## Coverage summary

| Check | Result |
|---|---|
| Created-file detection | PASS |
| Modified-file detection + versioning | PASS (2 versions kept) |
| Deleted-file detection + logging | PASS |
| Subfolder files (`docs/`, `data/`) | PASS |
| Retention pruning (max 5) | PASS |
| change-log.csv completeness | PASS (6/6 events) |
| backup-report.html | PASS |
| `--report-only` mode | PASS |
| No third-party dependencies | PASS (stdlib only) |
