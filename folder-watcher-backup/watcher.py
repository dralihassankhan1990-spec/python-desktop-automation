"""
Folder Watcher & Auto-Backup — by Muhammad Bilal
================================================
PROBLEM IT SOLVES
-----------------
Project teams lose work when someone overwrites a shared file, deletes a
deliverable by accident, or a laptop crashes before the weekly backup.
Manual backups are forgotten; cloud sync keeps only one "latest" copy, so
an overwrite destroys the previous version forever.

WHAT THIS DOES (100% local — no APIs, no network, no cloud)
------------------------------------------------------------
1. Polls a watched folder every N seconds (plain polling — no native
   dependencies, works on Windows / macOS / Linux).
2. On any new or changed file, copies it to
   backup/<relative-path>/YYYY-MM-DD_HHMMSS_<filename>.
3. Keeps at most MAX_VERSIONS copies per file and auto-prunes older ones.
4. Appends every event to change-log.csv (timestamp, file, event, backup path).
5. Generates a daily backup-report.html summary (totals, per-file versions,
   recent events) at the end of a run and on demand (--report-only).

CONFIG: edit the block below, or override with command-line flags.
USAGE:
    python watcher.py                  # run forever (Ctrl+C stops, report written)
    python watcher.py --duration 120   # run for 120 seconds, then stop + report
    python watcher.py --report-only    # regenerate the HTML report and exit
    python watcher.py --interval 10 --watch ./demo-project
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import logging
import os
import shutil
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIG — edit these defaults, or override via CLI flags
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
WATCH_DIR = BASE_DIR / "demo-project"          # folder to watch
BACKUP_DIR = BASE_DIR / "backup"               # where versioned copies land
LOG_FILE = BASE_DIR / "watcher.log"            # run log
CHANGE_LOG = BASE_DIR / "change-log.csv"       # event ledger (CSV)
REPORT_FILE = BASE_DIR / "backup-report.html"  # daily summary (HTML)
INTERVAL_SECONDS = 5                           # poll interval
MAX_VERSIONS = 5                               # versions kept per file
RUN_SECONDS = 0                                # 0 = run until stopped (Ctrl+C)
IGNORE_NAMES = {".DS_Store", "Thumbs.db"}      # never backed up
IGNORE_SUFFIXES = {".tmp", ".part", ".crdownload", ".swp"}

# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("watcher")

STOP_REQUESTED = False


def _handle_stop(signum, _frame):
    global STOP_REQUESTED
    log.info("Stop signal received (%s). Finishing current scan, then exiting.",
             signal.Signals(signum).name)
    STOP_REQUESTED = True


signal.signal(signal.SIGINT, _handle_stop)
signal.signal(signal.SIGTERM, _handle_stop)


# ---------------------------------------------------------------------------
# SNAPSHOT + CHANGE DETECTION
# ---------------------------------------------------------------------------
def is_ignored(path: Path, watch_dir: Path, backup_dir: Path) -> bool:
    """Skip backup/log artefacts and OS junk so the watcher never backs up itself."""
    try:
        if path.resolve().is_relative_to(backup_dir.resolve()):
            return True
    except (ValueError, RuntimeError):
        pass
    if path.name in IGNORE_NAMES or path.suffix.lower() in IGNORE_SUFFIXES:
        return True
    if path.name.startswith("~$"):  # Office lock files
        return True
    return False


def snapshot(watch_dir: Path, backup_dir: Path) -> dict[str, tuple[int, int]]:
    """Return {relative_posix_path: (mtime_ns, size)} for every file under watch_dir."""
    snap: dict[str, tuple[int, int]] = {}
    if not watch_dir.exists():
        log.error("Watch folder does not exist: %s", watch_dir)
        return snap
    for root, dirs, files in os.walk(watch_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in files:
            full = Path(root) / name
            if is_ignored(full, watch_dir, backup_dir):
                continue
            try:
                st = full.stat()
                rel = full.relative_to(watch_dir).as_posix()
                snap[rel] = (st.st_mtime_ns, st.st_size)
            except OSError as exc:
                log.warning("Could not stat %s: %s", full, exc)
    return snap


def detect_changes(old: dict, new: dict) -> list[tuple[str, str]]:
    """Compare two snapshots. Returns [(event, rel_path)] — event in created/modified/deleted."""
    events: list[tuple[str, str]] = []
    for rel in sorted(new):
        if rel not in old:
            events.append(("created", rel))
        elif new[rel] != old[rel]:
            events.append(("modified", rel))
    for rel in sorted(old):
        if rel not in new:
            events.append(("deleted", rel))
    return events


# ---------------------------------------------------------------------------
# BACKUP + PRUNING
# ---------------------------------------------------------------------------
def backup_file(watch_dir: Path, backup_dir: Path, rel_path: str) -> str:
    """Copy the current file into a timestamped versioned slot. Returns the backup path."""
    src = watch_dir / rel_path
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    dest_dir = backup_dir / Path(rel_path).parent
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{stamp}_{Path(rel_path).name}"
    # Avoid a same-second collision when a file changes twice within one second.
    counter = 1
    while dest.exists():
        dest = dest_dir / f"{stamp}_{counter:02d}_{Path(rel_path).name}"
        counter += 1
    shutil.copy2(src, dest)
    prune_versions(backup_dir, rel_path)
    return dest.relative_to(backup_dir).as_posix()


def prune_versions(backup_dir: Path, rel_path: str) -> None:
    """Keep only the newest MAX_VERSIONS copies of one file; delete the rest."""
    folder = backup_dir / Path(rel_path).parent
    if not folder.exists():
        return
    name = Path(rel_path).name
    versions = sorted(
        (p for p in folder.iterdir() if p.is_file() and p.name.endswith("_" + name)),
        key=lambda p: p.stat().st_mtime,
    )
    for old in versions[:-MAX_VERSIONS]:
        try:
            old.unlink()
            log.info("Pruned old version (retention=%d): %s", MAX_VERSIONS, old.name)
        except OSError as exc:
            log.warning("Could not prune %s: %s", old, exc)


# ---------------------------------------------------------------------------
# CHANGE LOG (CSV)
# ---------------------------------------------------------------------------
def append_change_log(change_log: Path, event: str, rel_path: str, backup_rel: str) -> None:
    exists = change_log.exists()
    try:
        with change_log.open("a", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            if not exists:
                writer.writerow(["timestamp", "file", "event", "backup_path"])
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                rel_path,
                event,
                backup_rel,
            ])
    except OSError as exc:
        log.error("Could not write change log: %s", exc)


def read_change_log(change_log: Path) -> list[dict]:
    if not change_log.exists():
        return []
    try:
        with change_log.open(newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))
    except OSError as exc:
        log.error("Could not read change log: %s", exc)
        return []


# ---------------------------------------------------------------------------
# HTML DAILY REPORT
# ---------------------------------------------------------------------------
def count_versions(backup_dir: Path) -> dict[str, int]:
    """{relative source path: number of versions stored} — reconstructed from backup tree."""
    counts: dict[str, int] = {}
    if not backup_dir.exists():
        return counts
    for root, _dirs, files in os.walk(backup_dir):
        for name in files:
            full = Path(root) / name
            # strip the leading timestamp prefix (YYYY-MM-DD_HHMMSS_ or with _NN_)
            stem = name
            parts = stem.split("_", 3)
            original = parts[3] if len(parts) == 4 and len(parts[0]) == 10 else stem
            rel_dir = Path(root).relative_to(backup_dir).as_posix()
            rel = f"{rel_dir}/{original}" if rel_dir != "." else original
            counts[rel] = counts.get(rel, 0) + 1
    return counts


def generate_report(watch_dir: Path, backup_dir: Path, change_log: Path,
                    report_file: Path) -> Path:
    events = read_change_log(change_log)
    counts = count_versions(backup_dir)
    total_backups = sum(counts.values())
    today = datetime.now().strftime("%Y-%m-%d")
    today_events = [e for e in events if e.get("timestamp", "").startswith(today)]
    by_event: dict[str, int] = {}
    for e in today_events:
        by_event[e.get("event", "?")] = by_event.get(e.get("event", "?"), 0) + 1

    def row(e: dict) -> str:
        cls = {"created": "ok", "modified": "warn", "deleted": "bad"}.get(e.get("event"), "")
        return ("<tr>"
                f"<td>{html.escape(e.get('timestamp', ''))}</td>"
                f"<td>{html.escape(e.get('file', ''))}</td>"
                f"<td class='{cls}'>{html.escape(e.get('event', ''))}</td>"
                f"<td>{html.escape(e.get('backup_path', '—') or '—')}</td>"
                "</tr>")

    recent = "".join(row(e) for e in events[-50:][::-1])
    versions = "".join(
        f"<tr><td>{html.escape(k)}</td><td>{v}</td></tr>"
        for k, v in sorted(counts.items())
    ) or "<tr><td colspan='2'>No backups yet.</td></tr>"

    doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Backup Report — {today}</title>
<style>
 body {{ font-family: Arial, sans-serif; margin: 32px; color: #1e293b; }}
 h1 {{ color: #0e4c81; }} h2 {{ color: #0e4c81; border-bottom: 2px solid #0e4c81; padding-bottom: 4px; }}
 .kpi {{ display: flex; gap: 16px; flex-wrap: wrap; }}
 .card {{ background: #eef4fa; border-radius: 10px; padding: 16px 22px; min-width: 160px; }}
 .card b {{ font-size: 28px; color: #0e4c81; display: block; }}
 table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
 th {{ background: #0e4c81; color: #fff; text-align: left; padding: 8px; }}
 td {{ border: 1px solid #cbd5e1; padding: 8px; }}
 .ok {{ color: #15803d; font-weight: bold; }} .warn {{ color: #b45309; font-weight: bold; }}
 .bad {{ color: #b91c1c; font-weight: bold; }}
 .foot {{ color: #64748b; font-size: 13px; margin-top: 24px; }}
</style></head><body>
<h1>Folder Watcher — Daily Backup Report</h1>
<p>Watched folder: <code>{html.escape(str(watch_dir))}</code> &nbsp;|&nbsp; Date: {today}</p>
<div class="kpi">
 <div class="card"><b>{len(today_events)}</b>events today</div>
 <div class="card"><b>{by_event.get('created', 0)}</b>files created</div>
 <div class="card"><b>{by_event.get('modified', 0)}</b>files modified</div>
 <div class="card"><b>{by_event.get('deleted', 0)}</b>files deleted</div>
 <div class="card"><b>{total_backups}</b>versioned backups stored</div>
 <div class="card"><b>{len(counts)}</b>files protected</div>
</div>
<h2>Versions per file (retention: max {MAX_VERSIONS} each)</h2>
<table><tr><th>File</th><th>Versions stored</th></tr>{versions}</table>
<h2>Recent events (newest first)</h2>
<table><tr><th>Timestamp</th><th>File</th><th>Event</th><th>Backup path</th></tr>{recent}</table>
<p class="foot">Generated by Folder Watcher &amp; Auto-Backup — by Muhammad Bilal. 100% local: no cloud, no API.</p>
</body></html>"""
    report_file.write_text(doc, encoding="utf-8")
    log.info("Report written: %s", report_file)
    return report_file


# ---------------------------------------------------------------------------
# MAIN WATCH LOOP
# ---------------------------------------------------------------------------
def run(watch_dir: Path, backup_dir: Path, interval: float, duration: float) -> int:
    watch_dir.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)
    log.info("Watching %s  |  backup -> %s  |  interval=%ss  |  retention=%d",
             watch_dir, backup_dir, interval, MAX_VERSIONS)
    previous = snapshot(watch_dir, backup_dir)
    log.info("Initial snapshot: %d file(s) tracked.", len(previous))
    started = datetime.now()
    scans = 0
    handled = 0
    while not STOP_REQUESTED:
        if duration > 0 and (datetime.now() - started).total_seconds() >= duration:
            log.info("Duration reached (%.0fs). Stopping.", duration)
            break
        time.sleep(interval)
        if STOP_REQUESTED:
            break
        current = snapshot(watch_dir, backup_dir)
        scans += 1
        for event, rel in detect_changes(previous, current):
            if event == "deleted":
                log.info("DELETED  %s", rel)
                append_change_log(CHANGE_LOG, event, rel, "")
            else:
                try:
                    backup_rel = backup_file(watch_dir, backup_dir, rel)
                except (OSError, shutil.Error) as exc:
                    log.error("Backup failed for %s: %s", rel, exc)
                    continue
                log.info("%s  %s  ->  %s", event.upper(), rel, backup_rel)
                append_change_log(CHANGE_LOG, event, rel, backup_rel)
            handled += 1
        previous = current
    log.info("Stopped after %d scan(s); %d event(s) handled.", scans, handled)
    generate_report(watch_dir, backup_dir, CHANGE_LOG, REPORT_FILE)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Folder Watcher & Auto-Backup (100% local)")
    parser.add_argument("--watch", type=Path, default=WATCH_DIR, help="folder to watch")
    parser.add_argument("--backup", type=Path, default=BACKUP_DIR, help="backup folder")
    parser.add_argument("--interval", type=float, default=INTERVAL_SECONDS, help="poll seconds")
    parser.add_argument("--duration", type=float, default=RUN_SECONDS,
                        help="seconds to run (0 = until Ctrl+C)")
    parser.add_argument("--report-only", action="store_true",
                        help="regenerate backup-report.html from the existing log and exit")
    args = parser.parse_args()
    if args.report_only:
        generate_report(args.watch, args.backup, CHANGE_LOG, REPORT_FILE)
        return 0
    if args.interval <= 0:
        parser.error("--interval must be > 0")
    return run(args.watch, args.backup, args.interval, args.duration)


if __name__ == "__main__":
    raise SystemExit(main())
