"""
demo_changes.py — proves the watcher works in a short, observable run.

Simulates a PM team editing files in demo-project/ while watcher.py runs:
  1. create  a brand-new file
  2. modify an existing file (twice — creates two versions)
  3. create a file inside a subfolder
  4. delete a scratch file (watcher logs the deletion)

Run in a SECOND terminal while watcher.py is running:
    python demo_changes.py

All data is fictional demo content.
"""
from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEMO = HERE / "demo-project"


def stamp(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def main() -> None:
    (DEMO / "docs").mkdir(parents=True, exist_ok=True)
    (DEMO / "data").mkdir(parents=True, exist_ok=True)

    # 1 — create a brand-new file
    stamp("DEMO 1/4: creating meeting-notes.txt …")
    (DEMO / "meeting-notes.txt").write_text(
        "Weekly stand-up notes (demo)\n- Sprint velocity: 21 points\n"
        "- Blocker: vendor delivery delayed by 2 days\n", encoding="utf-8")
    time.sleep(3)

    # 2 — modify an existing file, twice (two backup versions)
    plan = DEMO / "docs" / "project-plan.md"
    stamp("DEMO 2/4: modifying docs/project-plan.md (version A) …")
    plan.write_text("# Demo Project — Plan\n\n- Phase 1: Discovery — DONE\n"
                    "- Phase 2: Build — IN PROGRESS\n", encoding="utf-8")
    time.sleep(3)
    stamp("DEMO 2/4: modifying docs/project-plan.md (version B) …")
    plan.write_text("# Demo Project — Plan\n\n- Phase 1: Discovery — DONE\n"
                    "- Phase 2: Build — DONE\n- Phase 3: UAT — IN PROGRESS\n",
                    encoding="utf-8")
    time.sleep(3)

    # 3 — create a file inside a subfolder
    stamp("DEMO 3/4: creating data/tasks.csv …")
    (DEMO / "data" / "tasks.csv").write_text(
        "id,task,owner,status\n1,Prepare UAT scripts,Ali,Done\n"
        "2,Sign off test environment,Fatima,In Progress\n", encoding="utf-8")
    time.sleep(3)

    # 4 — delete a scratch file (watcher logs it, no backup copy)
    scratch = DEMO / "scratch-to-delete.txt"
    scratch.write_text("temporary scratch file — will be deleted\n", encoding="utf-8")
    stamp("DEMO 4/4: created scratch-to-delete.txt, now deleting it …")
    time.sleep(3)
    scratch.unlink()
    time.sleep(2)
    stamp("Done. Check backup/, change-log.csv and backup-report.html.")


if __name__ == "__main__":
    main()
