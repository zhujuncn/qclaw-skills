#!/usr/bin/env python3
"""GitHub auto-sync for betangel-x2 skill."""
import os
import subprocess, sys, json, logging

SKILL_DIR = r"C:\Users\zhuju\.qclaw\skills\betangel-x2"
TOKEN = os.environ.get("GITHUB_TOKEN")
REMOTE = "https://github.com/zhujuncn/betangel-x2.git"
if TOKEN:
    REMOTE = f"https://{TOKEN}@github.com/zhujuncn/betangel-x2.git"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    handlers=[
        logging.FileHandler(SKILL_DIR + "\\scripts\\_cron_sync.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def run(cmd, cwd=SKILL_DIR, capture=True):
    log.info(f"[CMD] {cmd}")
    kw = {"cwd": cwd, "shell": True}
    if capture:
        kw["capture_output"] = True
        kw["text"] = True
    r = subprocess.run(cmd, **kw)
    if r.returncode != 0 and capture:
        log.error(f"  stderr: {r.stderr.strip()}")
    return r


def main():
    # Check status
    r = run("git status --porcelain")
    changed = r.stdout.strip()

    if not changed:
        log.info("No changes — skip push.")
        print("NO_CHANGES")
        return

    log.info(f"Changes detected:\n{changed}")

    # Stage all
    run("git add -A")

    # Commit with timestamp
    import datetime
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    r = run(f'git commit -m "Auto-sync {ts}"')
    if r.returncode != 0:
        log.error(f"Commit failed: {r.stderr}")
        print("COMMIT_FAILED")
        return

    # Push
    r = run(f"git push {REMOTE} main")
    if r.returncode != 0:
        log.error(f"Push failed: {r.stderr}")
        print("PUSH_FAILED")
        return

    log.info("Push OK")
    print("OK")


if __name__ == "__main__":
    main()
